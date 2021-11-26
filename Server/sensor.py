from busio  import I2C
from board  import SCL, SDA
from time   import sleep
from server import Server
from adafruit_amg88xx import AMG88XX
import asyncio

class Sensor:
    i2c    = I2C(SCL, SDA)
    amg    = AMG88XX(i2c)
    Delta  = float(0.8)
    AvTemp = int(0)
    active = bool(False)

    def __init__ (self):
        self.server = Server(self)

    def startServer(self):
        self.server.run()

    def setupEnvTemp(self):
        sum = 0
        for x in range(15):
            cal = self.amg.pixels[4][4]
            if x > 5:
                sum += cal 
                sleep(0.1)
        self.AvTemp = sum / 9 

    def detect(self):
        if self.amg.pixels[4][4] > self.AvTemp + self.Delta:
            return True

    async def setup(self):
        print("Server: Initializing sensor ...", flush=True, end='')
        self.setupEnvTemp()
        print("Done!")
        await self.server.send('Sensor booted up successfully!')
        while self.active:
            await self.server.sleep()
            if self.detect():
                await self.server.send('Intruder detected!')
                await self.stopSensor()
                break

    async def startSensor(self):
        if not self.active:
            self.active = True
            await self.server.send('Setting up sensor...')
            await asyncio.sleep(0.5)
            await self.setup()
        else:
            print("Server: Sensor is already running!")
            await self.server.send('Sensor is already running!')

    async def stopSensor(self):
        self.active = False
        await self.server.send('Sensor has stopped!')

    async def restartSensor(self):
        await self.stopSensor()
        await self.startSensor()

if __name__ == '__main__':
    Sensor().startServer()
