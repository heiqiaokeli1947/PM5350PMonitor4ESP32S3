from machine import Pin, I2C
from struct import unpack as unp
from time import sleep_ms

# SHT20 default address
SHT20_I2CADDR = 0x40

# SHT20 Command
TRI_T_MEASURE_NO_HOLD = b'\xf3'
TRI_RH_MEASURE_NO_HOLD = b'\xf5'
READ_USER_REG = b'\xe7'
WRITE_USER_REG = b'\xe6'
SOFT_RESET = b'\xfe'


class SHT20(object):

    def __init__(self, i2c):
        self._address = SHT20_I2CADDR
        self.i2c = i2c

    def get_temperature(self):
        self.i2c.writeto(self._address, TRI_T_MEASURE_NO_HOLD)
        sleep_ms(150)
        origin_data = self.i2c.readfrom(self._address, 2)
        origin_value = unp('>h', origin_data)[0]
        value = -46.85 + 175.72 * (origin_value / 65536)
        return round(value,2)

    def get_relative_humidity(self):
        self.i2c.writeto(self._address, TRI_RH_MEASURE_NO_HOLD)
        sleep_ms(150)
        origin_data = self.i2c.readfrom(self._address, 2)
        origin_value = unp('>H', origin_data)[0]
        value = -6 + 125.0 * (origin_value / 65536)
        return round(value,2)