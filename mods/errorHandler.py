import os
import sys

class errorHandler():
    def __init__(self, site):
        try:
            self.site = site.split('.py')[0].split('\\')[-1]
            if not os.path.isdir('.\error-logs'):
                os.mkdir('error-logs')
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), f'./error-logs/{self.site}.log')
            try:
                self.file = open(f'{self.logs_path}', 'a+')
            except:
                self.file = None
        except:
            pass
    def log_exception(self, tb):
        try:
            if self.file:
                line = tb.split(",")[1]
                exc = tb.split('\n')[-2]
                text = f'Exception in {line}: {exc}\n'
                self.file.write(text)
            else:
                return
        except:
            pass