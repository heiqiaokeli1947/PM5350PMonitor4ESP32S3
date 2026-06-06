import math
import struct
class MathTool:
    @staticmethod
    def from32bitToFloat32BigEdition(temp):
        if isinstance(temp,(list,tuple)) and len(temp) ==2:
            res = struct.unpack('>f', temp[0].to_bytes(2,'big')+temp[1].to_bytes(2,'big'))[0]
        
            if math.isnan(res):
                return "NaN"
            else:
                return res
        else:
            return 0
            #raise ValueError('input is not list or len is not 2')

    @staticmethod
    def from64bitToInt64BigEdition(temp):
        if isinstance(temp,(list,tuple)) and len(temp) ==4:
            return struct.unpack('>q', temp[0].to_bytes(2,'big')+temp[1].to_bytes(2,'big')+temp[2].to_bytes(2,'big')+temp[3].to_bytes(2,'big'))[0]
        else:
            return 0
            #raise ValueError('input is not list or len is not 2')
