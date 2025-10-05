# Author: Alex Teteria
# v0.2
# 11.07.2025
# Implemented and tested on Pi Pico with RP2040
# Released under the MIT license

import time
from machine import Pin
from machine import Timer


class Pulse_measure:
        """  """
           
        def __init__(self, pin):
            #self.pin_id = pin_id
            self.pin = pin
            self.pin.irq(trigger=(Pin.IRQ_FALLING | Pin.IRQ_RISING), handler=self.measuring)
            self.last = 0
            self.cnt = 0
            self.tim_end_dial = Timer()
            self.data_en = False
            self.pulse = None
            self.tim_data_en = Timer()
            # -----------------------
            # Для налаштувань тривалостей імпульсів
            #self.imp_short_min = float('inf')
            #self.imp_short_max = 0
            #self.imp_long_min = float('inf')
            #self.imp_long_max = 0
        
        def measuring(self, pin):
            now = time.ticks_us()
            diff = now - self.last
            self.last = now
            if 48_000 <= diff < 80_000:
                #print(diff)
                #self.imp_long_max = max(self.imp_long_max, diff)
                #self.imp_long_min = min(self.imp_long_min, diff)
                self.cnt_number()
            elif 34_000 <= diff < 48_000:
                #print(diff)
                #self.imp_short_min = min(self.imp_short_min, diff)
                #self.imp_short_max = max(self.imp_short_max, diff)
                self.continue_dialing()
            elif 20_000 < diff <= 34_000 or 80_000 <= diff < 100_000:
                print(diff)
        
        def cnt_number(self):
            self.data_en = False
            self.cnt += 1
            self.tim_end_dial.init(mode=Timer.ONE_SHOT, period=50, callback=self.end_dialing)

        def continue_dialing(self):
            self.data_en = False
            self.tim_end_dial.init(mode=Timer.ONE_SHOT, period=80, callback=self.end_dialing)
 
        def end_dialing(self, t):
            self.data_en = True
            self.pulse = self.cnt
            self.tim_data_en.init(mode=Timer.ONE_SHOT, period=40, callback=self.set_data_en)
            print(f'Number {self.pulse}')
                  #self.imp_short_min, '-', self.imp_short_max,
                  #self.imp_long_min, '-', self.imp_long_max)
            self.cnt = 0
        
        def set_data_en(self, t):
            self.data_en = False
                    
'''
def timer_callback(t):
    global flag_tim, tim_period
    out_timer.toggle()
    tim_period = 60 if out_timer.value() else 40
    flag_tim = True
'''

if __name__ == '__main__':
    
    in_1 = Pin(7, Pin.IN, Pin.PULL_UP)
    imp_1 = Pulse_measure(in_1)
        
    while True:
        pass