from machine import UART, Pin, Timer
import time
import sys


class SIM800L:
    '''
    '''
    def __init__(self, uart, baudrate, tx, rx):
        self.uart = UART(uart, baudrate=baudrate, tx=Pin(tx), rx=Pin(rx))
        
    def send_command(self, command, timeout=1000):
        """
        Sends an AT command to the SIM800 module.
        """
        self.uart.write(command + '\r')
        time.sleep_ms(100)  # Delay to allow command processing
        return self.read_response(timeout)

    def read_response(self, timeout=1000):
        """
        Reads the response from the SIM800 module over UART.
        """
        start_time = time.ticks_ms()
        response = b''
        while (time.ticks_diff(time.ticks_ms(), start_time) < timeout):
            if self.uart.any():
                response += self.uart.read(self.uart.any())
        return response

    def send_ata(self):
        self.uart.write('ATA' + '\r\n')
        time.sleep_ms(100)
        start = time.ticks_ms()
        response = b''
        while time.ticks_diff(time.ticks_ms(), start) < 2000:
            if self.uart.any():
                response += self.uart.read(self.uart.any())
        return response
    
    def init_module(self):
        response = self.send_command('AT')
        if b"OK" not in response:
            print('Module error!')
            return False
        response = self.send_command('AT+CCALR?')
        if b"1" not in response:
            print('Module is not ready for phone call!')
            return False
        else:
            print('Module Ok!')
        # перевіряємо якість зв'язку
        if not self.signal_quality()[0]:
            return False
        # вкл.АОН
        response = self.send_command('AT+CLIP=1').decode()
        print(response)
        return True

    def signal_quality(self):
        quality_band = {'0': 'BER < 0.2%',
                    '1': '0.2% < BER < 0.4%',
                    '2': '0.4% < BER < 0.8%',
                    '3': '0.8% < BER < 1.6%',
                    '4': '1.6% < BER < 3.2%',
                    '5': '3.2% < BER < 6.4%',
                    '6': '6.4% < BER < 12.8%',
                    '7': 'BER > 12.8%'}
        # returns received signal strength indication <rssi> 
        # and channel bit error rate <ber>
        response = self.send_command('AT+CSQ').decode().replace('\n', '').replace('\r', '')
        for ch in response:
            if ch in 'ATCSQ+:OK ':
                response = response.replace(ch, '')
        rssi, ber = response.split(',')
        if 5 < int(rssi) < 25:
            rssi_str = '-90...-50 dBm, norm signal level'
        elif 1 <= int(rssi) <= 5:
            rssi_str = '-111...-90 dBm, low signal level'
        elif int(rssi) == 0:
            rssi_str = '-115 dBm or less, bad signal level'
            print(f'{rssi}, rssi = {rssi_str}')
            print(quality_band[ber])
            return False, rssi_str, quality_band[ber] 
        elif 25 <= int(rssi) <= 30:
            rssi_str = '-50...-54 dBm, good signal level'
        elif int(rssi) == 31:
            rssi_str = '-52 dBm or greater, excellent signal level'
        else:
            rssi_str = '?, not known or not detectable signal'
        
        print(f'{rssi}, rssi = {rssi_str}')
        print(quality_band[ber])
        return True, rssi_str, quality_band[ber]
            
    def init_sim800(self):
        for i in range(10):
            if self.init_module():
                break
            time.sleep(2)
        else:
            print("Exit program via error module or bad signal level")
            sys.exit()


