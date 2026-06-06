#饱和水汽压：E(t)=611.2exp(17.67t/(243.5+t))
#干空气比焓：g(t)=1.01t    1.01为干空气的定压比热，kJ/(kg℃)。
#水蒸气比焓：v(t)=2501+1.85t   2501是水在0℃时变成水蒸气的汽化潜热，kJ/kg；1.85是水蒸气的定压比热，kJ/(kg℃)
#湿空气的含湿量：d(t,rh)=0.622rhE(t)/(p-rh*E(t))     rh为相对湿度；p为标准大气压101325，单位为Pa
#湿空气的比焓：h(t,rh)=g(t)+d(t,rh)v(t)
#rh(t_g,t_s)=p[g(t_s)-g(t_g)+d(t_s,100%)v(t_s)]/[E(t_g)[g(t_s)-g(t_g)+d(t_s,100%)v(t_s)+0.622v(t_g)]]
#'''
import math
class AAC(object):
    def __init__(self):
        self.p = 101325  # unit Pa

    def E(self, t):
        # 饱和水汽压：E(t)=611.2exp(17.67t/(243.5+t))
        val = 611.2 * math.exp(17.67 * t / (243.5 + t))
        return val

    def g(self, t):
        # 干空气比焓：g(t)=1.01t    1.01为干空气的定压比热，kJ/(kg℃)。
        val = 1.01 * t
        return val

    def v(self, t):
        # 水蒸气比焓：v(t)=2501+1.85t   2501是水在0℃时变成水蒸气的汽化潜热，kJ/kg；1.85是水蒸气的定压比热，kJ/(kg℃)
        val = 2501 + 1.85 * t
        return val
    
    def d(self, t, rh):
        # 湿空气的含湿量：d(t,rh)=0.622rhE(t)/(p-rh*E(t))     rh为相对湿度；p为标准大气压101325，单位为Pa
        val = 0.622 * rh * self.E(t) / (self.p - rh * self.E(t))
        return val

    def d2(self, tg, ts, ds):
        # tw为湿空气湿球温度，℃；t为干球温度，℃；ds为湿空气等焓加湿到饱和状态时含湿量（简称饱和含湿量），kg / kg(a)
        # ds查表 (kg/kg)
        if ts >= 0:
            val = ((2530 - 2.326 * ts) * ds - 1.006 * (tg - ts)) / \
                  (2501 + 1.86 * tg - 4.186 * ts)
        else:
            val = ((2830 - 0.24 * ts) * ds - 1.006 * (tg - ts)) / \
                  (2830 + 1.86 * tg - 2.1 * ts)
        return val

    def h(self, t, rh):
        # 湿空气的比焓：h(t,rh)=g(t)+d(t,rh)v(t)
        val = self.g(t) + self.d(t, rh) * self.v(t)
        return val

    def calcDiff(self,a,b):
        if abs(a) < abs(b):
            return 100*(1.0 - abs(a) / abs(b))
        else:
            return 100*(1.0 - abs(b) / abs(a))
        
    def rh(self, tg, ts):
        # rh为相对湿度, tg为干球温度，ts为湿球温度
        val = self.p * (self.g(ts) - self.g(tg) + self.d(ts, 1) * self.v(ts)) / \
              (self.E(tg) * (self.g(ts) - self.g(tg) + self.d(ts, 1) * self.v(ts) + 0.622 * self.v(tg)))
        return val
    
    
    def ts(self, tg, rh, diff):
        count = 0
        tsTemp = tg - 5 #起始湿度为干球温度-5摄氏度
        tsFitStep = 0.01 #ts调整步长 单位:摄氏度
        MAX_CALC_TIMES = 10000 #最多计算10000次
    
        while (self.calcDiff(self.rh(tg,tsTemp), rh) > diff):
            count+=1
            if (self.rh(tg, tsTemp) >rh):
                tsTemp -= tsFitStep
            else:
                tsTemp += tsFitStep

            if count > MAX_CALC_TIMES:
                print("calc ts failed.")
                return -9999 #无效值
        
        return round(tsTemp,2)
    



