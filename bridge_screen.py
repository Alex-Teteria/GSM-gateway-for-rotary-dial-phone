from machine import I2C, Pin, UART, Timer
from lcd_i2c_16x2 import LCDI2C16x2
import json


# Initialize I2C
i2c=I2C(1, scl=Pin(15), sda=Pin(14))

# Initialize LCD
lcd = LCDI2C16x2(i2c)

# Setup LSD
lcd.backlight_on()
lcd.clear()

# init UART
uart_0 = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# init Timer
tim = Timer()

filename = "phone_dir_screen.json" # файл телефонний довідник
with open(filename, 'r', encoding='utf-8') as f:
    phone_directory = json.load(f)

def tim_callback(t):
    lcd.backlight_off()

def phone_dir(phone_num):
    print(phone_num)
    for i in range(1, 8):
        if phone_num[:-i] + i*'X' in phone_directory:
            return phone_directory[phone_num[:-i] + i*'X']
    return phone_directory.get(phone_num, phone_num)

tim.init(mode=Timer.ONE_SHOT, period=60_000, callback=tim_callback)
lcd.set_cursor(0, 0)
lcd.write('GSM Phone bridge')
lcd.set_cursor(0, 1)
lcd.write('ver.02')
while True:
    lcd.set_cursor(0, 0)
    data = uart_0.read(32)
    if data:
        try:
            line_1, line_2 = data.decode().split('\n')
            lcd.backlight_on()
            if line_1 == 'RING':
                line_2 = '"' + phone_dir(line_2[1:-1]) + '"'
            if line_1 != 'Off-hook!':
                tim.init(mode=Timer.ONE_SHOT, period=60_000, callback=tim_callback)
            print(line_1)
            print(line_2)
            lcd.clear()
            lcd.write(line_1)
            lcd.set_cursor(0, 1)
            lcd.write(line_2)
        except:
            lcd.clear()
            lcd.write('Error!')
            print(data)

