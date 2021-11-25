from iputils   import getIP
from time      import sleep
from threading import Thread
from aiohttp   import web
from socketio  import AsyncServer

class Server:
    server = AsyncServer(async_mode='aiohttp')
    app    = web.Application()
    count  = int(0)
    PORT   = int(8080)
    IP     = str()

    def __init__ (self, util, *args):
        self.sensor = util

    def run(self):
        self.setup()

    def setup(self):
        self.server.attach(self.app)
        self.callbacks()
        while True:
            try:
                self.IP = getIP()
                web.run_app(self.app)
                break
            except:
                sleep(5)
                continue

    def subThread(self, func, *args):
        self.server.start_background_task(target=func)

    async def send(self, msg):
        await self.server.emit('message', msg)
        print("Server: Message has been sent")

    async def sleep(self):
        await self.server.sleep(0)

    def callbacks(self):
        @self.server.event
        def connect(sid, environ):
            print(f"Server: Connected by {sid}")

        @self.server.event
        def disconnect(sid):
            print(f"Server: User {sid} has disconnected")
            self.subThread(self.sensor.stopSensor)

        @self.server.event
        def start(sid):
            self.subThread(self.sensor.startSensor)

        @self.server.event
        def stop(sid):
            print("Server: Sensor has stopped!")
            self.subThread(self.sensor.stopSensor)

        @self.server.event
        def restart(sid):
            self.subThread(self.sensor.restartSensor)
