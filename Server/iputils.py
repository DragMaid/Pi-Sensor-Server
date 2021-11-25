from subprocess import Popen, PIPE

COMMAND = ("ifconfig | grep 192.168.0") #The ip will always start with 192.168.0.

def getIP():
    process = Popen(COMMAND, shell=True, stdout=PIPE, stderr=PIPE)
    process.wait()
    output = process.stdout.readline().decode('utf-8')
    output = output.split()[1]
    return output
