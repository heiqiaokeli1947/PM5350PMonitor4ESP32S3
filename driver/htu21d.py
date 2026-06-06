import utime

class HTU21D(object):
    ADDRESS = 0x40
    ISSUE_TEMP_ADDRESS = 0xE3
    ISSUE_HU_ADDRESS = 0xE5

    def __init__(self, i2c):
        self.i2c = i2c
        self.hardWareReady=False

    def initHardware(self):
        i2c_devices = self.i2c.scan()
        #print(i2c_devices)
        
        if self.ADDRESS not in i2c_devices:
            self.hardWareReady = False
        else:
            self.hardWareReady = True

    def _crc_check(self, value):
        """CRC check data
        Notes:
            stolen from https://github.com/sparkfun/HTU21D_Breakout

        Args:
            value (bytearray): data to be checked for validity
        Returns:
            True if valid, False otherwise
        """
        remainder = ((value[0] << 8) + value[1]) << 8
        remainder |= value[2]
        divsor = 0x988000

        for i in range(0, 16):
            if remainder & 1 << (23 - i):
                remainder ^= divsor
            divsor >>= 1

        if remainder == 0:
            return True
        else:
            print("HTU21D CRC invalid.")
            return False

    def _issue_measurement(self, write_address):

        self.i2c.writeto_mem(int(self.ADDRESS), int(write_address), '')
        utime.sleep_ms(50)
        data = bytearray(3)
        self.i2c.readfrom_into(self.ADDRESS, data)
        if not self._crc_check(data):
            raise ValueError()
        raw = (data[0] << 8) + data[1]
        raw &= 0xFFFC
        return raw

    @property
    def temperature(self):
        try:
            if not self.hardWareReady:
                self.initHardware()
                
            raw = self._issue_measurement(self.ISSUE_TEMP_ADDRESS)
            return round((-46.85 + (175.72 * raw / 65536)),2)
        except (OSError,TypeError):
            self.hardWareReady = False
            return -9999

    @property
    def humidity(self):
        try:
            if not self.hardWareReady:
                self.initHardware()
                
            raw =  self._issue_measurement(self.ISSUE_HU_ADDRESS)
            value = -6 + (125.0 * raw / 65536)
            return round(value,2)
        except (OSError,TypeError):
            self.hardWareReady = False
            return -9999
            
