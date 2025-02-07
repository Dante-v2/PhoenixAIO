from threading import Lock
from colorama import Fore, init
from datetime import datetime
import sys, os
init(autoreset=True)

class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

lock = Lock()
unbuffered = Unbuffered(sys.stdout)

def info(s, end='\n'):
    now = str(datetime.now())[:-3]
    string = f'[{now}] {Fore.GREEN}{s}{end}'
    with lock:
        unbuffered.write(string)

def warn(s, end='\n'):
    now = str(datetime.now())[:-3]
    string = f'[{now}] {Fore.YELLOW}{s}{end}'
    with lock:
        unbuffered.write(string)

def error(s, end='\n'):
    now = str(datetime.now())[:-3]
    string = f'[{now}] {Fore.RED}{s}{end}'
    with lock:
        unbuffered.write(string)

def cyan(s, end='\n'):
    now = str(datetime.now())[:-3]
    string = f'[{now}] {Fore.CYAN}{s}{end}'
    with lock:
        unbuffered.write(string)