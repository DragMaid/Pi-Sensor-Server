import socket
import select
import subprocess
import os
import time
import busio
import board
import adafruit_amg88xx

i2c = busio.I2C(board.SCL, board.SDA)
amg = adafruit_amg88xx.AMG88XX(i2c)

class HostGate:
    COMMAND = "ifconfig | grep 192.168.0" #The ip will always start with 192.168.0.
    HOST = str("192.168.0.106")        # HOST ip assigned after initialization
    PORT = 8080        # Port to listen on (non-privileged ports are > 1023)
    DeltaTemp = 0.8
    AvTemp = 0
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while True:
            try:
                self.getIP()
                self.s.bind((self.HOST, self.PORT))
                break
            except Exception:
                time.sleep(10)

    def getIP(self):
        process = subprocess.Popen(self.COMMAND, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        output = process.stdout.readline().decode('utf-8')
        self.HOST = output.split()[1]
        
    def setupEnvTemp(self):
        sum = 0
        for x in range(10):
            if x > 1:
                sum += amg.pixels[3][3]
                time.sleep(0.1)
        self.AvTemp = sum / 8

    def detect(self, AvTemp):
        valid = 0
        if amg.pixels[3][3] > AvTemp + self.DeltaTemp:
            valid += 1 
            if amg.pixels[3][4] > AvTemp + self.DeltaTemp:
                valid += 1
            if amg.pixels[4][3] > AvTemp + self.DeltaTemp:
                valid += 1
            if amg.pixels[4][4] > AvTemp + self.DeltaTemp:
                valid += 1
        if valid >= 2:
            return True

    def cleanupPort(self):
        command = f"lsof -i tcp:{self.PORT}"
        os.system(command)

    def start(self, restart=False):
        if restart:
            self.s.listen()
            print("Waiting for connection...")
            self.conn, self.addr = self.s.accept()
        print('Connected by', self.addr)
        print('Initializing sensor...', flush=True, end=" ")
        self.setupEnvTemp()
        print("Done")
        print("Server is online!")
        while True:
            if self.detect(self.AvTemp):
                print("Human detected!")
                break
        self.conn.sendall(bytes("trigger", 'UTF-8'))
        answer = self.conn.recv(1024)
        local = str(answer)[2:-1]
        if local == "N":
            self.start(restart=True)
        self.start()
        
if __name__ == "__main__":
    HostGate().start(restart=True)

