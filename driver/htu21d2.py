from machine import I2C

class HTU21D:
    def __init__(self,i2c):
        self.HTDU21D_ADDRESS           = 0x40
        self.TRIGGER_TEMP_MEASURE_HOLD = 0xE3
        self.TRIGGER_HUMD_MEASURE_HOLD = 0xE5
        self.SHIFTED_DIVISOR           = (2**8 + 2**5 + 2**4 + 1)<<15
        self.READ_USER_REG             = 0xE7
        self.WRITE_USER_REG            = 0xE6
        self.SOFT_RESET                = 0xFE
        
        self.RH12_TEMP14 = 0b00000000
        self.RH08_TEMP12 = 0b00000001
        self.RH10_TEMP13 = 0b10000000
        self.RH11_TEMP11 = 0b10000001
        self.i2c=i2c
        
    def readTemp(self):
        buf = bytes([self.TRIGGER_TEMP_MEASURE_HOLD])
        self.i2c.writeto(self.HTDU21D_ADDRESS, buf) 
        data = bytearray(3)           
        self.i2c.readfrom_into(self.HTDU21D_ADDRESS, data)
        crcResult     = self.__check_crc(data[0], data[1], data[2])
        raw           = (data[0]<<8 | data[1]) & 0xfffc
        temp          = -46.85 + 175.72 * raw / 65536.0
        temp = round(temp,2)
        #print("crc:{}".format(crcResult))
        return # if crcResult == 0 else crcResult
        
    def readHumid(self):
        buf = bytes([self.TRIGGER_HUMD_MEASURE_HOLD])
        self.i2c.writeto(self.HTDU21D_ADDRESS, buf) 
        data = bytearray(3)          
        self.i2c.readfrom_into(self.HTDU21D_ADDRESS, data)
        crcResult     = self.__check_crc(data[0], data[1], data[2])
        raw           = (data[0]<<8 | data[1]) & 0xfffc
        humid         = -6.0 + 125.0 * raw / 65536.0
        humid = round(humid,2)
        #print("crc:{}".format(crcResult))
        return humid if crcResult == 0 else crcResult
        
    def __check_crc(self, msb, lsb, crc):
        divisor   = self.SHIFTED_DIVISOR
        remainder = msb<<16 | lsb<<8 | crc
        
        for i in range(23, 7, -1):
            if remainder & 1<<i:
                remainder ^= divisor
             
            divisor >>= 1
            
        return 0 if remainder == 0 else 999
    
    def readUserRegister(self):
        buf = bytes([self.READ_USER_REG])
        self.i2c.writeto(self.HTDU21D_ADDRESS, buf)
        data = bytearray(1)
        self.i2c.readfrom_into(self.HTDU21D_ADDRESS, data)
        return data
        
    def setResolution(self, resolution):
        userRegister = self.readUserRegister()[0]
        userRegister &= 0b01111110
        resolution   &= 0b10000001
        userRegister |= resolution
        
        buf = bytes([self.WRITE_USER_REG, userRegister])
        self.i2c.writeto(self.HTDU21D_ADDRESS, buf)
        
    def softReset(self):
        buf = bytes([self.SOFT_RESET])
        self.i2c.writeto(self.HTDU21D_ADDRESS, buf)