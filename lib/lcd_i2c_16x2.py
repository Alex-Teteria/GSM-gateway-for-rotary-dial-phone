# This code was generated in part with the assistance of artificial intelligence (GitHub Copilot).
# Reviewed, adapted and tested on Pi Pico with RP2040 by Olexandr Teteria.
# 05.10.2025
# Released under the MIT license

# Reviewed and adapted by .
from machine import I2C, Pin
import time

class LCDI2C16x2:
    # LCD commands
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80

    # Flags for display entry mode
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTDECREMENT = 0x00

    # Flags for display on/off control
    LCD_DISPLAYON = 0x04
    LCD_CURSOROFF = 0x00
    LCD_BLINKOFF = 0x00

    # Flags for function set
    LCD_2LINE = 0x08
    LCD_5x8DOTS = 0x00
    LCD_4BITMODE = 0x00

    # Backlight control
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00

    En = 0b00000100 # Enable bit
    Rw = 0b00000010 # Read/Write bit
    Rs = 0b00000001 # Register select bit

    def __init__(self, i2c, addr=0x27, num_lines=2, num_columns=16):
        self.i2c = i2c
        self.addr = addr
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.backlight = self.LCD_BACKLIGHT

        # Initialization sequence
        self._write(0x03 << 4)
        time.sleep_ms(5)
        self._write(0x03 << 4)
        time.sleep_ms(5)
        self._write(0x03 << 4)
        time.sleep_ms(1)
        self._write(0x02 << 4)

        self._command(self.LCD_FUNCTIONSET | self.LCD_4BITMODE | self.LCD_2LINE | self.LCD_5x8DOTS)
        self._command(self.LCD_DISPLAYCONTROL | self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF)
        self._command(self.LCD_CLEARDISPLAY)
        time.sleep_ms(2)
        self._command(self.LCD_ENTRYMODESET | self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT)
        time.sleep_ms(2)

    def _write(self, data):
        self.i2c.writeto(self.addr, bytes([data | self.backlight]))

    def _strobe(self, data):
        self._write(data | self.En)
        time.sleep_us(500)
        self._write(data & ~self.En)
        time.sleep_us(100)

    def _command(self, cmd):
        self._send(cmd, 0)

    def _send(self, data, mode):
        highnib = data & 0xF0
        lownib = (data << 4) & 0xF0
        self._write4bits(highnib | mode)
        self._write4bits(lownib | mode)

    def _write4bits(self, data):
        self._write(data)
        self._strobe(data)

    def clear(self):
        self._command(self.LCD_CLEARDISPLAY)
        time.sleep_ms(2)

    def home(self):
        self._command(self.LCD_RETURNHOME)
        time.sleep_ms(2)

    def set_cursor(self, col, row):
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        if row > self.num_lines:
            row = self.num_lines - 1
        self._command(self.LCD_SETDDRAMADDR | (col + row_offsets[row]))

    def write(self, string):
        for char in string:
            self._send(ord(char), self.Rs)

    def backlight_on(self):
        self.backlight = self.LCD_BACKLIGHT
        self._write(0)

    def backlight_off(self):
        self.backlight = self.LCD_NOBACKLIGHT
        self._write(0)

        
