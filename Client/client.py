# Client modules
from socketio  import Client
from time      import sleep
from threading import Thread

# Notification modules
import os
import webbrowser
from pydub import AudioSegment
from pydub.playback import play

# Preloaded static files 
DIRECTORY = os.path.dirname(os.path.abspath(__file__)) 
SOUND = AudioSegment.from_mp3(os.path.join(DIRECTORY, "static/yahello.mp3"))
NOTIFICATION = os.path.join(DIRECTORY, "static/index.html")
BROWSER = 'firefox'

class Client(Thread):
    client    = Client()
    ADDR      = str('http://')
    IP        = str('192.168.0.113') # This is my server's tatic IP
    PORT      = int(8080)
    URL       = str(f'{ADDR}{IP}:{PORT}')
    CONNECTED = False
    RUNNING   = False

    def __init__(self, app): 
        Thread.__init__(self)
        self.daemon = True
        self.app    = app

    def start(self):
        if not self.CONNECTED:
            self.notify('Client', 'Attempting to connect...')
            Thread.start(self)
        else:
            self.notify('Client', 'Already connected to server')

    def stop(self):
        if not self.CONNECTED:
            self.notify('Client', 'Daemon currently not running!')
        else:   
            self.notify('Client', 'Disconnecting...')
            self.client.disconnect()

    def run(self):
        self.RUNNING = True
        self.callbacks()
        self.setup()
        self.RUNNING = False

    def setup(self):
            try:
                self.client.connect(self.URL)
                self.CONNECTED = True
                self.client.wait()
            except:
                self.notify('Client', 'Unable to connect to server!')

    def send(self, mode):
        if not self.CONNECTED:
            self.notify('Client', 'Daemon currently not running!')
        else:
            try:
                self.client.emit(mode)
            except:
                self.notify('Client', 'Problem occured while trying to execute command!')

    def showNotification(self, *args):
        play(SOUND)
        webbrowser.get(BROWSER).open(NOTIFICATION)

    def createThread(self, func, *args):
        thread = Thread(target=func, args=(args,))
        thread.start()

    def notify(self, name, msg):
        self.app.mainForm.notify(name, msg)

    def terminate(self):
        self.client.disconnect()

    def callbacks(self):
        @self.client.event
        def connect():
            self.notify('Client', 'Connection established')

        @self.client.event
        def disconnect():
            self.CONNECTED = False
            self.notify('Client', 'Disconnected from server')
            self.client.disconnect()

        @self.client.event
        def message(data):
            self.notify('Server', data)
            if data == "Intruder detected!":
                self.createThread(self.showNotification)
