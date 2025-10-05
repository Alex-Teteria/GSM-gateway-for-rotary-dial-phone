# Author: Olexandr Teteria
# v0.2
# 11.07.2025
# Implemented and tested on Pi Pico with RP2040
# Released under the MIT license
'''
contains a class library:
Send_call -
        forms ring signal - a 25 Hz pulse and logical "1" - pause
Dial_tone -
        forms a dial tone signal - 425Hz
'''
import machine, time
import uasyncio as asyncio


class Send_call:
    def __init__(self, number_calls,
                 pin_out=16,
                 pin_out_inv=17,
                 pin_pulse=25,
                 enable=lambda: False,
                 **kwargs):
        self.freq = 25  # частота сигнала в імпульсі посилки виклику, Гц 
        self.time_pulse = 400  # тривалість імпульса в мс
        self.time_pause = 800  # тривалість паузи в мс
        self.number_calls = number_calls  # кількість імпульсів в посилці імпульс-пауза
        self.cnt_calls = self.number_calls * 2  # лічильник імпульсів
        self.enable = enable
        self.out_send = machine.Pin(pin_out, machine.Pin.OUT)  # вихід посилки виклику
        self.out_inv_send = machine.Pin(pin_out_inv, machine.Pin.OUT)
        self.out_pulse = machine.Pin(pin_pulse, machine.Pin.OUT)
        self.out_send.value(1)
        self.out_inv_send.value(1)
        self.out_pulse.value(0)
        self.tim_freq = machine.Timer(freq=self.freq*2,
                                      mode=machine.Timer.PERIODIC,
                                      callback=self.tim_freq_callback)
        self.gen_freq = 0
        self.tim_pulse = machine.Timer()  # таймер тривалості імпульсу в посилці виклику
        self.tim_pause = machine.Timer()  # таймер паузи в посилці виклику
        self.pulse_en = True
        self.tim_pulse_en = True
        self.tim_pause_en = False
        if kwargs:
            self.callback = kwargs['func']
            self.args = kwargs['args']
        else:
            self.callback = self.null_func
            self.args = None
    
    def null_func(self, *args):
        pass
    
    def tim_freq_callback(self, t):
        self.gen_freq = not self.gen_freq
    
    def tim_pulse_callback(self, t):
        self.pulse_en = not self.pulse_en
        self.tim_pulse_en = True
        if self.cnt_calls == 0:
            self.tim_pause_en = True
        
    def tim_pause_callback(self, t):
        self.cnt_calls = self.number_calls * 2
        self.pulse_en = True
        self.tim_pulse_en = True
            
    def send(self):

        while self.enable():
            if self.cnt_calls and self.tim_pulse_en:
                self.tim_pulse.init(period=self.time_pulse,
                                   mode=machine.Timer.ONE_SHOT,
                                   callback=self.tim_pulse_callback)
                self.cnt_calls -= 1
                self.tim_pulse_en = False
            if self.tim_pause_en:
                self.tim_pause.init(period=self.time_pause,
                                    mode=machine.Timer.ONE_SHOT,
                                    callback=self.tim_pause_callback)
                self.pulse_en = False
                self.tim_pause_en = False
                self.tim_pulse_en = False
                                             
            if self.pulse_en:
                self.out_send.value(self.gen_freq)
                self.out_inv_send.value(not self.gen_freq)
                self.out_pulse(1)
            else:
                self.out_send.value(1)
                self.out_inv_send.value(1)
                self.out_pulse(0)
                    
            self.callback(self.out_pulse(), self.args)    
        self.tim_pulse.deinit()
        self.tim_pause.deinit()
        self.pulse_en = True
        self.tim_pulse_en = True
        self.tim_pause_en = False
        self.cnt_calls = self.number_calls * 2
        self.out_send.value(1)
        self.out_inv_send.value(1)
        self.out_pulse(0)
        self.callback(self.out_pulse(), self.args)

class Send_ring:
    def __init__(self, number_calls,
                 pin_out=16,
                 pin_out_inv=17,
                 pin_pulse=25
                 ):
        self.freq = 25  # частота сигнала в імпульсі посилки виклику, Гц 
        self.time_pulse = 400  # тривалість імпульса в мс
        self.time_pause = 800  # тривалість паузи в мс
        self.number_calls = number_calls  # кількість імпульсів в посилці імпульс-пауза
        self.cnt_calls = self.number_calls * 2  # лічильник імпульсів
        self.out_send = machine.Pin(pin_out, machine.Pin.OUT)  # вихід посилки виклику
        self.out_inv_send = machine.Pin(pin_out_inv, machine.Pin.OUT)
        self.out_pulse = machine.Pin(pin_pulse, machine.Pin.OUT)
        self.out_send.value(1)
        self.out_inv_send.value(1)
        self.out_pulse.value(0)
        self.tim_freq = machine.Timer(freq=self.freq*2,
                                      mode=machine.Timer.PERIODIC,
                                      callback=self.tim_freq_callback,
                                      hard=True)
        self.gen_freq = 0
        self.tim_pulse = machine.Timer()  # таймер тривалості імпульсу в посилці виклику
        self.tim_pause = machine.Timer()  # таймер паузи в посилці виклику
        self.pulse_en = True
        self.tim_pulse_en = True
        self.tim_pause_en = False

    def tim_freq_callback(self, t):
        self.gen_freq = not self.gen_freq
    
    def tim_pulse_callback(self, t):
        self.pulse_en = not self.pulse_en
        self.tim_pulse_en = True
        if self.cnt_calls == 0:
            self.tim_pause_en = True
        
    def tim_pause_callback(self, t):
        self.cnt_calls = self.number_calls * 2
        self.pulse_en = True
        self.tim_pulse_en = True
            
    def send(self):
        if self.cnt_calls and self.tim_pulse_en:
            self.tim_pulse.init(period=self.time_pulse,
                               mode=machine.Timer.ONE_SHOT,
                               callback=self.tim_pulse_callback)
            self.cnt_calls -= 1
            self.tim_pulse_en = False
        if self.tim_pause_en:
            self.tim_pause.init(period=self.time_pause,
                                mode=machine.Timer.ONE_SHOT,
                                callback=self.tim_pause_callback)
            self.pulse_en = False
            self.tim_pause_en = False
            self.tim_pulse_en = False
                                             
        if self.pulse_en:
            self.out_send.value(self.gen_freq)
            self.out_inv_send.value(not self.gen_freq)
            self.out_pulse(1)
        else:
            self.out_send.value(1)
            self.out_inv_send.value(1)
            self.out_pulse(0)


class Dial_tone:
    '''Формує dial tone (425Hz), коли функція enable вертає False
       pin_out - int, номер Pin, вихід 425Hz
       enable - function, повинна вертати True, або False
                         коли True - на виході pin_out логічний "0"
                         коли False - меандр 425Hz
       freq - int, частота, за замовчуванням 425Hz                  
    '''
    def __init__(self, pin_out, enable=lambda: False, freq=425):
        self.pin_out = pin_out
        self.enable = enable
        self.freq = freq
        self.out_425Hz = machine.Pin(pin_out, machine.Pin.OUT)
        self.tim_freq = machine.Timer(freq=self.freq*2,
                                      mode=machine.Timer.PERIODIC,
                                      callback=self.tim_callback,
                                      hard=True)
        
    def tim_callback(self, t):
        if not self.enable():
            self.out_425Hz.toggle()
        else:
            self.out_425Hz.value(0)


class Handset:
    " "
    def __init__(self, pin_handset, pin_led):
        self.pin_handset = pin_handset # примірник об'єкта Pin
        self.pin_led = pin_led         # примірник об'єкта Pin
        self.dial_start = False        # слухавка лежить (False), піднята (True)
                    
    async def handset_on(self):
        '''якщо слухавку піднято,
           то змінна dial_start = True
        '''
        while True:
            if not self.pin_handset.value(): # слухавку знято
                for i in range(20):
                    await asyncio.sleep_ms(40)
                    if self.pin_handset.value():
                        break
                else:
                    self.dial_start = True
            await asyncio.sleep(0.04)
                
    async def handset_off(self):
        '''якщо слухавку покладено,
           то змінна dial_start = False
        '''
        while True:
            if self.pin_handset.value(): # слухавка лежить
                for i in range(20):
                    await asyncio.sleep_ms(40)
                    if not self.pin_handset.value():
                        break
                else:
                    self.dial_start = False
            await asyncio.sleep(0.04)

    async def run_led_handset(self):
        while True:
            self.pin_led.value(1) if self.dial_start else self.pin_led.value(0)
            await asyncio.sleep(0.04)


# for testing callback
def callback(call, args):
    onboard_led, *_ = args
    if call:
        onboard_led.value(1)
    else:
        onboard_led.value(0)

def ring_enable():
    if pin_ring_en.value() and pin_tone425_en.value():
        return True
    return False

if __name__ == '__main__':
    from onboard_led import Onboard_led

    led = Onboard_led()
    '''
    ring = Send_call(2,              # два імпульси в посилці дзвінка
                     pin_out=14,     # вихід 25Гц
                     pin_out_inv=15, # інверсний вихід 25Гц
                     pin_pulse=26,   # "1", коли є сигнал ring (25Гц)
                     func=callback,  # функція, яка буде викликатись (за потреби)
                     args=(led, )    # аргументи функції func
                     )

    pin_ring_en = machine.Pin(8, machine.Pin.IN, machine.Pin.PULL_UP)
    pin_tone425_en = machine.Pin(7, machine.Pin.IN, machine.Pin.PULL_UP)
    ring.enable = ring_enable
    tone_425 = Dial_tone(27, freq=425)
    tone_425.enable = pin_tone425_en.value
    '''
    ring = Send_ring(2,              # два імпульси в посилці дзвінка
                     pin_out=14,     # вихід 25Гц
                     pin_out_inv=15, # інверсний вихід 25Гц
                     pin_pulse=26,   # "1", коли є сигнал ring (25Гц)
                     )

    while True:
        ring.send()

        
        
            
                
            
            
        
        

    
