from lib.modbus.uModBusSerial import uModBusSerial
import lib.modbus.uModBusConst as Const
import domain.MathTool as MathTool
import utime


class PM5350P:
    def __init__(self,address=1, badud=38400):
        self.modbusAddr = address
        self.badud = badud
        #初始化modbus串口UART1，16=Rx,17=Tx是我接的引脚号
        self.modubsrtu=uModBusSerial(1,self.badud,8,1,None,[18,17])
        print("PM5350P init:modbus addr={},badud={}".format(self.modbusAddr,self.badud))
    def read(self):
        try:
            pm5350Data={}
            #施耐德PM5350P Modbus RTU 寄存器信息

            #地址3000，2寄存器=4字节=float32=A相电流A
            #地址3002，2寄存器=4字节=float32=B相电流A
            #地址3004，2寄存器=4字节=float32=C相电流A
            #地址3006，2寄存器=4字节=float32=N相电流A
            #地址3008，2寄存器=4字节=float32=G相电流A
            #地址3010，2寄存器=4字节=float32=AVG相电流A

            #地址3020，2寄存器=4字节=float32=A-B相电压V
            #地址3022，2寄存器=4字节=float32=B-C相电压V
            #地址3024，2寄存器=4字节=float32=C-A相电压V
            #地址3026，2寄存器=4字节=float32=L-L AVG相电压V
            #地址3028，2寄存器=4字节=float32=A-N相电压V
            #地址3030，2寄存器=4字节=float32=B-N相电压V
            #地址3032，2寄存器=4字节=float32=C-N相电压V
            #地址3036，2寄存器=4字节=float32=L-N AVG相电压V

            #地址3054，2寄存器=4字节=float32=功率A kW
            #地址3056，2寄存器=4字节=float32=功率B
            #地址3058，2寄存器=4字节=float32=功率C
            #地址3060，2寄存器=4字节=float32=总功率


            #地址3200，4寄存器=8字节=DATATIME=累计电能复位日期时间
            #地址3204，4寄存器=8字节=INT64=Active energy delevered(into load) Wh
            #地址3208，4寄存器=8字节=INT64=Active energy received(out of load) Wh
            #地址3212，4寄存器=8字节=INT64=Active energy delevered + received Wh
            #地址3216，4寄存器=8字节=INT64=Active energy delevered - received Wh
            #地址3220，4寄存器=8字节=INT64=Reactive energy delevered
            #地址3224，4寄存器=8字节=INT64=Reactive energy received

            #地址3078，2寄存器=4字节=float32=功率因数A
            #地址3080，2寄存器=4字节=float32=功率因数B
            #地址3082，2寄存器=4字节=float32=功率因数C
            #地址3084，2寄存器=4字节=float32=总功率因数

            #地址3110，2寄存器=4字节=float32=频率
    
            temp = self.modubsrtu.read_holding_registers(self.modbusAddr,3000-1, 12)  # 读电流
            #print("I result:{}".format(temp))
            pm5350Data['Ia'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[0:2])
            pm5350Data['Ib'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[2:4])
            pm5350Data['Ic'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[4:6])
            pm5350Data['In'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[6:8])
            pm5350Data['Ig'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[8:10])
            pm5350Data['Iavg'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[10:12])

            temp = self.modubsrtu.read_holding_registers(self.modbusAddr,3020-1, 18)  # 读电压
            #print("V result:{}".format(temp))
            pm5350Data['Vab'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[0:2])
            pm5350Data['Vbc'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[2:4])
            pm5350Data['Vca'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[4:6])
            pm5350Data['Vll'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[6:8])
            pm5350Data['Van'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[8:10])
            pm5350Data['Vbn'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[10:12])
            pm5350Data['Vcn'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[14:18])
            pm5350Data['Vln_avg'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[0:2])

            temp = self.modubsrtu.read_holding_registers(self.modbusAddr,3054-1, 8)  # 读功率
            #print("P result:{}".format(temp))
            pm5350Data['Pa'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[0:2])
            pm5350Data['Pb'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[2:4])
            pm5350Data['Pc'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[4:6])
            pm5350Data['Ptotal'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[6:8])

            temp = self.modubsrtu.read_holding_registers(self.modbusAddr,3078-1, 8)  # 读功率因数
            #print("PF result:{}".format(temp))
            pm5350Data['PFa'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[0:2])
            pm5350Data['PFb'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[2:4])
            pm5350Data['PFc'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[4:6])
            pm5350Data['PFtotal'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[6:8])
            

            temp = self.modubsrtu.read_holding_registers(self.modbusAddr,3200-1, 28)  # 读电能
            #print("Energy result:{}".format(temp))
            pm5350Data['ErestTime'] = MathTool.MathTool.from64bitToInt64BigEdition(temp[0:4])
            pm5350Data['Eaed'] = MathTool.MathTool.from64bitToInt64BigEdition(temp[4:8])

            temp = self.modubsrtu.read_holding_registers(self.modbusAddr,3110-1, 2)  # 读功率因数
            #print("Freq result:{}".format(temp))
            pm5350Data['Freq'] = MathTool.MathTool.from32bitToFloat32BigEdition(temp[0:2])
            return pm5350Data
        except OSError:
            print("no data recived.")
            return {}
        except ValueError as e:
            print("ValueError exception:{}".format(e))
            return {}
            