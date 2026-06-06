class SensorData():
    def __init__(self):
        self.__temp = -9999
        self.__humi = -9999
        self.__wetBulbTemp = -9999
        self.__presure = -9999
        self.__altitude = -9999
        self.__luminance = -9999
        self.__pm25 = -9999
        self.__tempBMP280 = -9999
        self.__tempLM75_1 = -9999
        self.__tempLM75_2 = -9999
        self.__tempLM75_3 = -9999


    @property
    def wetBulbTemp(self):
        return self.__wetBulbTemp

    @wetBulbTemp.setter
    def wetBulbTemp(self, wetBulbTemp):
        self.__wetBulbTemp = wetBulbTemp

    @property
    def temp(self):
        return self.__temp

    @temp.setter
    def temp(self, temp):
        self.__temp = temp

    @property
    def humi(self):
        return self.__humi

    @humi.setter
    def humi(self, humi):
        self.__humi = humi

    @property
    def presure(self):
        return self.__presure

    @presure.setter
    def presure(self, presure):
        self.__presure = presure

    @property
    def altitude(self):
        return self.__altitude

    @altitude.setter
    def altitude(self, altitude):
        self.__altitude = altitude

    @property
    def luminance(self):
        return self.__luminance

    @luminance.setter
    def luminance(self, luminance):
        self.__luminance = luminance

    @property
    def pm25(self):
        return self.__pm25

    @pm25.setter
    def pm25(self, pm25):
        self.__pm25 = pm25

    @property
    def tempBMP280(self):
        return self.__tempBMP280

    @tempBMP280.setter
    def tempBMP280(self, temp):
        self.__tempBMP280 = temp



    @property
    def __dict__(self):
        return {"temp": self.__temp, "humi": self.__humi, "presure": self.__presure, "altitude": self.__altitude,
                "luminance": self.__luminance, "pm25": self.__pm25, "tempBMP280": self.__tempBMP280,
                "tempLM75_1": self.__tempLM75_1, "tempLM75_2": self.__tempLM75_2, "tempLM75_3": self.__tempLM75_3}
