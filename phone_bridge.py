# Author: Oleksandr Teteria
# v0.2
# 05.10.2025
# Implemented and tested on Pi Pico with RP2040
# Released under the MIT license

import machine, time
from machine import Pin, Timer, UART
import json
from phone_bridge_lib import Send_ring, Dial_tone, Handset
from measuring_time_intervals import Pulse_measure
from sim800L_lib import SIM800L
import _thread
import uasyncio as asyncio
import sys, gc


flag_ring = False      # True, коли надходять дзвінки
dial_tone_en = False   # True, дозвіл на dial_tone (425Hz)

uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
tim_ring = Timer()

filename = "phone_directory.json" # файл телефонний довідник
with open(filename, 'r', encoding='utf-8') as f:
    phone_directory = json.load(f)
voice_menu = '0800205433'

# dial tone enable func
def dial_tone_enable():
    '''Dial tone (425Hz) enable when return False!'''
    if handset.dial_start and dial_tone_en:
        return False
    return True

async def off_hook(event, name):
    global dial_tone_en
    await event.wait()
    if handset.dial_start and not flag_ring:
        uart.write('Off-hook!\n')
        print(f'{name}!')
        dial_tone_en = True
        asyncio.create_task(dial_num())
        
        while handset.dial_start: # перевіряємо чи трубка не лежить
            # запустивши асинхронні функції відслідковуємо dial_start:
            await asyncio.sleep(0.04)
                
        response = sim800.send_command('ATH')
        if b"OK" in response:
            uart.write('On-hook!\n')
            print('On-hook, Ok!')
        else:
            print(response)
        dial_tone_en = False    
    event.clear()
        
async def dial_num():
    global dial_tone_en
    phone_num = ''
    while handset.dial_start: # перевіряємо чи трубка не лежить
        if dial_number.data_en:
            dial_digit = dial_number.pulse if dial_number.pulse != 10 else 0
            if not phone_num:
                num_len = 3 if dial_digit == 2 else 10
            dial_tone_en = False
            phone_num += str(dial_digit)
            uart.write('Dialing Number:\n' + phone_num)
            
            if len(phone_num) == num_len:
                if num_len == 3:
                    phone_num = phone_directory.get(phone_num, voice_menu)
                uart.write('Dialed Number:\n' + phone_num)
                #print(phone_num)
                response = sim800.send_command(f'ATD{phone_num};')
                #await asyncio.sleep(0.1)
                print(response)
                talking_mode(phone_num)
        # запустивши асинхронні функції відслідковуємо dial_start:
        await asyncio.sleep(0.03)  # > 40mc, щоб не ловило дані двічі

def read_sim800(word, *args):
    # word - a sequence of bytes, i.e. b'...' that should be listened to
    # args - tuple of functions to be run
    buffer = b''
    if sim800.uart.any():
        data = sim800.uart.read()
        if data:
            buffer += data
            # Look for the bytes "word" in the buffer
            if word in buffer:
                for func in args:
                    func(buffer)
                buffer = b''  # Reset buffer to avoid repeated triggers
                return True
            # Prevent buffer from growing indefinitely
            if len(buffer) > 100:
                buffer = buffer[-20:]    
    
async def on_hook(event):
    read_sim800(b"RING", get_number, answer_incoming_call)
    event.set()

def get_number(buffer):
    try:
        in_str = buffer.decode()
        in_str = in_str.replace('\r', '').replace('\n', '')
        phone_num, *_ = in_str.split(',')
        if 'RING' in phone_num:
            uart.write('RING\n' + phone_num[11:])
        elif 'NO CARRIER' in phone_num:
            uart.write('NO CARRIER\n')
        print(phone_num)
    except:
        print('Data of bytes not define!')
    
def answer_incoming_call(*args):
    global flag_ring
    print("Received RING!")
    tim_ring.init(period=4100,
                  mode=machine.Timer.ONE_SHOT,
                  callback=tim_ring_callback)
    
    flag_ring = True
    #led.value(1)  # Turn on LED
    if handset_local(6):
        flag_ring = False
        print('Answer...')
        response = sim800.send_command('ATA')
        if b"OK" in response:
            print('Ok! Розмову розпочато')
            talking()
        else:
            print(response)
            print('Error!')
            response = sim800.send_command('ATH')
        

def handset_local(num_delay):
    ''' вертає True, якщо слухавку знято
        num_delay - затримка для визначення піднятої слухавки
    '''
    if not pin_handset.value(): # слухавку знято
        for i in range(num_delay):
            time.sleep_ms(10)
            if pin_handset.value():
                break
        else:
            return True
    return False
                
def talking_mode(num=''):
    global dial_tone_en
    print('Talking in progress...')
    uart.write('Talking...\n')
    while handset_local(20): # режим "Talking", перевіряємо чи трубка не лежить
        # response = sim800.send_command('AT+CPAS')
        #if b"0" in response and num[:4] != '0800':
        if read_sim800('NO CARRIER', get_number):
            while handset_local(20):
                dial_tone_en = True
                time.sleep(0.2)
                dial_tone_en = False
    response = sim800.send_command('ATH')
    if b"OK" in response:
        uart.write('On-hook\n')
        print('On-hook, Ok!')
    else:
        print(response)
    # machine.soft_reset()
    gc.collect()

def talking():
    response = sim800.send_command('AT+CPAS')
    if b"4" in response:
        talking_mode()
    else:
        print(response)

def tim_ring_callback(t):
    global flag_ring
    # led.value(0)
    flag_ring = False

async def print_mem():
    while True:
        print("Allocated memory:", gc.mem_alloc())
        print("Free memory:", gc.mem_free())
        await asyncio.sleep(4)  

async def print_signal():
    while True:
        _, sign_level, ber = sim800.signal_quality()
        signal = sign_level.split(',')
        signal_text = signal[1].split(' ')
        uart.write(signal[0] + '\n' + signal_text[1] + ' ' + signal_text[2])
        await asyncio.sleep(120)  

tone_425 = Dial_tone(27)
tone_425.enable = dial_tone_enable

pin_handset = machine.Pin(7, machine.Pin.IN, machine.Pin.PULL_UP)
pin_led_handset = machine.Pin(6, machine.Pin.OUT)

handset = Handset(pin_handset, pin_led_handset)

pin_dial = machine.Pin(8, machine.Pin.IN, machine.Pin.PULL_UP)
dial_number = Pulse_measure(pin_dial)

pin_ring_en = machine.Pin(28, machine.Pin.IN, machine.Pin.PULL_DOWN)
pin_ring = machine.Pin(29, machine.Pin.OUT)

# -------------------------------------
# func for second core
async def ring_enable():
    while True:
        if not handset_local(4) and flag_ring:
            pin_ring.value(1)
        else:
            pin_ring.value(0)
        await asyncio.sleep(0.04)    

def run():
    ring = Send_ring(2,          # два імпульси в посилці дзвінка
                 pin_out=14,     # вихід 25Гц
                 pin_out_inv=15, # інверсний вихід 25Гц
                 pin_pulse=26,   # "1", коли є сигнал ring (25Гц)
                 )
    
    while True:
        if pin_ring_en.value():
            ring.send()

# second core
_thread.start_new_thread(run, ())
# ---------------------------------------

async def main():
    # Create regular tasks
    asyncio.create_task(handset.handset_on())
    asyncio.create_task(handset.handset_off())
    asyncio.create_task(handset.run_led_handset())
    asyncio.create_task(ring_enable())
    #asyncio.create_task(print_signal())
    #asyncio.create_task(print_mem())

    #Create tasks with event
    while True:
        task_off_hook = asyncio.create_task(off_hook(event, "Task Off-hook")) # waiter
        task_on_hook = asyncio.create_task(on_hook(event))  # setter
      
        # Wait for all tasks to complete
        await task_off_hook
        await task_on_hook
        #event.clear()


sim800 = SIM800L(0, 115200, tx=0, rx=1)
sim800.init_sim800()
# рівень гучності динаміка (0-100), максимальний = 100:
response = sim800.send_command('AT+CLVL=100')
print(response)

# встановлюємо рівень мікрофона для каналу №0
response = sim800.send_command('AT+CMIC=0,0')
print(response)
response = sim800.send_command('AT+CMIC?')
print(response)

# розгорнута відповідь на ATD###
response = sim800.send_command('AT+COLP=1')
print(response)

# вибираємо аудіо канал для мікрофона:
#  0 = NORMAL_AUDIO
#  1 = AUX_AUDIO
#  2 = HANDFREE_AUDIO
#  3 = AUX_HANDFREE_AUDIO
#  4 = PCM_AUDIO
response = sim800.send_command('AT+CHFA=0')
print(response)

response = sim800.send_command('AT+CMEE=2')
print(response)

event = asyncio.Event()  # Create an Event object

_, sign_level, ber = sim800.signal_quality()
signal = sign_level.split(',')
signal_text = signal[1].split(' ')
uart.write(signal[0] + '\n' + signal_text[1] + ' ' + signal_text[2])
time.sleep(1)
uart.write(ber + '\n')
# Run the main coroutine
asyncio.run(main())
    

