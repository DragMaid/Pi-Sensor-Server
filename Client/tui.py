from client       import Client
from threading    import Thread
from customModule import MultiLine
import npyscreen
import curses
import os

class logPrompt(npyscreen.BoxTitle):
    name = 'Log'
    _contained_widget = MultiLine

class commandPrompt(npyscreen.BoxTitle):
    name = 'Command'
    icon = ['>> ', '$ ', '=> ']
    _contained_widget = npyscreen.TitleText

class Form(npyscreen.FormBaseNew):
    name = 'TUI'
    valid_commands = ['start', 'stop', 'restart', 'exit', 'connect', 'disconnect', 'clear']

    def create(self):
        self.setupLog()
        self.setupPrompt()
        self.handlers.update({'^Q': self.handleError})

    def setupLog(self):
        self.log = self.add(logPrompt, max_height=self.DEFAULT_LINES-3)

    def setupPrompt(self):
        self.prompt = self.add(commandPrompt, max_height=3)
        self.prompt.entry_widget.label_widget.value = self.prompt.icon[0]
        self.prompt.entry_widget.text_field_begin_at = 3
        self.prompt.entry_widget.resize()
        self.prompt.entry_widget.entry_widget.handlers.update({curses.ascii.NL: self.promptCallback})

    def handleError(self, _input):
        self.notify('Client', 'Please use /exit to quit')

    def promptCallback(self, _input):
        self.processCommand(self.prompt.entry_widget.get_value())
        self.prompt.entry_widget.entry_widget.value = ''

    def createThread(self, func, *args):
        thread = Thread(target=func, args=args, daemon=True)
        thread.start()

    def clearLog(self, cache=False):
        if cache:
            self.log.entry_widget.clearLogFile()
        self.log.entry_widget.clearValues()

    def notify(self, name, msg):
        message = f'{name}: {msg}'
        if len(self.log.values) * self.log.entry_widget._contained_widget_height == self.log.entry_widget.height:
            self.clearLog()
            self.log.entry_widget._total_pages += 1
            self.log.entry_widget._current_page+= 1
        self.log.entry_widget._total_lines += 1
        self.log.values.append(message)
        self.log.entry_widget.writeLogFile(message)
        self.log.display()

    def send(self, command):
        controller.client.send(command)

    def processCommand(self, command):
        fullcmd = command
        if len(command) > 0:
            if command[0] == '/':
                command = command[1:]
                if command == 'exit':
                    exit(0)

                elif command == 'connect':
                    controller.clientConnect()

                elif command == 'disconnect':
                    controller.clientDisconnect()

                elif command == 'clear':
                    self.clearLog(cache=True)

                elif command == 'start':
                    self.send(command)

                elif command in self.valid_commands:
                    self.send(command)

                else:
                    self.notify('Client', "Not a valid command!")
            else:
                self.notify('Client', "This is not a command!")

class App(npyscreen.NPSApp):
    def main(self):
        self.mainForm = Form()
        controller.clientConnect()
        self.mainForm.edit()

class Controller:
    def __init__(self):
        self.app = App()
        self.client = Client(self.app)

    def clientConnect(self):
        if self.client.RUNNING:
            self.client.notify('Client', 'Please wait for last command to execute')
        else:
            self.client.terminate()
            self.client = Client(self.app)
            self.client.start()

    def clientDisconnect(self):
        self.client.stop() 

    def start(self):
        self.app.run()

if __name__ == '__main__':
    controller = Controller()
    controller.start()
