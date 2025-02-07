import json, requests, threading, certifi, ssl, socket, hashlib, psutil, tempfile, csv, urllib3, sys, random, base64, platform, hashlib, random, atexit, ctypes, logging, webbrowser, signal, os, uuid, string
import websocket
import asyncio
import os
from mods.logger import info, warn, error
import time
import subprocess

machineOS = platform.system()
version = '1.3.0' 

actived = 0

def configWriter(json_obj, w_file):

    if machineOS == "Darwin":
        path = os.path.dirname(__file__).rsplit('/', 1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), w_file)
    elif machineOS == "Windows":
        path = os.path.dirname(__file__).rsplit('\\', 1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), w_file)

    path = os.path.dirname(__file__).rsplit('/', 1)[0]

    with open(f'{path}', 'w') as f:
        json.dump(json_obj, f, indent=4)
        f.close()

try:
    if machineOS == "Darwin":
        path = os.path.dirname(__file__).rsplit('/', 1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), "config.json")
    elif machineOS == "Windows":
        path = os.path.dirname(__file__).rsplit('\\', 1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), "config.json")
    with open(f'{path}', 'r') as f:
        config = json.load(f)
        f.close()
        
except Exception as e:

    error("FAILED TO READ CONFIG")
    pass


class customThread(threading.Thread):
    global actived
    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        threading.Thread.start(self)

    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


devostopparecazzo = True

class START():

    def __init__(self, webhook_url, version):

        uri = "wss://eyesberglab.com:3143"
        self.webhook_url = webhook_url
        self.version = version
        self.mobilemode = config['mobilemode']

        try:
            self.ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
            self.ws.connect(uri)
            result = self.ws.recv()
            if result == "welcome":
                if config['mobilemode'] != "":
                    connessione = '''{
                        "type":"bot",
                        "action":"connection",
                        "mobilekey": "ilmiovalore"
                    }'''.replace('ilmiovalore', config['mobilemode'])
                    self.ws.send(connessione)

                    r = self.ws.recv()

                    if "Welcome" in r:

                        info('Successfully connected to mobile!')

                        self.connessione = True

                        pronto = '''{
                            "type":"bot", 
                            "action":"message", 
                            "message":"Bot ready!"
                        }'''

                        self.ws.send(pronto)
        
                    
                        self.listen()

                    elif "failed" in r:

                        error("Another instance already opened")
                        sys.exit(1)

                    else:
                        self.connessione = False


        except Exception as e:
            print(f"CANT CONNECT TO MOBILE")


    def listen(self):

        global actived 

        
        try:
            warn('Waiting for input...')
            while True:
                r = self.ws.recv()

                if r == "":
                    continue

                else:

                    rjson = json.loads(r)
                    if rjson['type'] == "mobile" and rjson['action'] == "start":

                        self.url = rjson['url']
                        self.site = rjson['site']
                        isstart = True
                        break

                    elif r['type'] == "bot":
                        continue
                    else:
                        continue

        except:
            self.listen()


        threading.Thread(target=self.listening).start()
        threading.Thread(target=self.getbar).start()
        self.starttask()


    def getbar(self):
        try:


            jsonevents = """{}"""

            

            if machineOS == "Windows":

                while True:

                    MAX_BUFFER = 260
                    title_text_buffer = (ctypes.c_char * MAX_BUFFER)()
                    res = ctypes.windll.kernel32.GetConsoleTitleA(title_text_buffer, MAX_BUFFER)
                    title = str(title_text_buffer.value)
                    try:
                        self.carted = title.split("Carted:")[1].split("|")[0]
                        self.checkoutnum = title.split("Checkout:")[1].split("|")[0]
                        self.failed = title.split("Failed:")[1].split("|")[0]
                        if "'" in self.failed:
                            self.failed = self.failed.replace("'","")
                    except Exception:
                        continue
                    aaa = '''{
                        "type":"bot",
                        "Checkout":"self.checkoutnum",
                        "Carted":"self.carted",
                        "Failed":"self.failed"
                    }'''.replace('self.checkoutnum', f"{str(self.checkoutnum)}").replace('self.carted', f"{str(self.carted)}").replace('self.failed', f"{str(self.failed)}")

                    jsonevents2 = aaa

                    if jsonevents != jsonevents2:
                        jsonevents = jsonevents2
                        self.ws.send(jsonevents2)
                        continue

                    else:
                        time.sleep(3)
                        continue

            else:
                
                aaa = '''{
                    "type":"bot", "action":"message", "message":"messaggio"
                }'''.replace('messaggio', f'{self.site} is running!')

                self.ws.send(aaa)


        except:
            pass


    def listening(self):

        global actived

        while True:

            r = self.ws.recv()            
            if r == "":
                continue
            else:
                rjson = json.loads(r)
                if rjson['type'] == "mobile" and rjson['action'] == "stop":
                    break
                elif rjson['type'] == "bot":                    
                    continue
                else:
                    continue
        
        actived = 1


    def starttask(self):

        global actived

        self.listathread = []

        if self.site == "AWLAB":      

            request = b'GET /S1T3S4EWKXU/ HTTP/1.0\r\nHost: api.phoenixbot.io\r\n\r\n'
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wrappedSocket = ssl.wrap_socket(client, ssl_version=ssl.PROTOCOL_TLSv1)
            target = "api.phoenixbot.io"
            port = 443
            wrappedSocket.connect((target,port))    
            wrappedSocket.sendall(request)
            result = wrappedSocket.recv(4096)
            while (len(result) < 1):
                result = wrappedSocket.recv(4096)  

            self.lock = str(result)

            if 'pid' in self.lock:
                self.preloadpid = self.lock.split('pid:')[1].split('<')[0]                


            if 'bypass' in self.lock:
                self.bypass = self.lock.split('bypass:')[1].split('<')[0]


            from scripts.awlabsingolo import AWLABSING

            try:
                if machineOS == 'Darwin':
                        path = os.path.dirname('__file__').rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'Awlab/tasks.csv')
                elif machineOS == 'Windows':
                        path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'Awlab/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                    
                    for row in csv_input:

                        if self.url != "":
                            pid = self.url
                        else:
                            pid = row['PID']     

                        fname = row['FIRST NAME']
                        lname = row['LAST NAME']
                        email = row['EMAIL']
                        address = row['ADDRESS LINE 1']
                        prefix = row['PREFIX']
                        phone = row['PHONE NUMBER']
                        city = row['CITY']
                        zip = row['ZIP']
                        state = row['STATE']
                        country = row['COUNTRY']
                        payment = row['PAYMENT']
                        mode = row['MODE']
                        card = row['CARD NUMBER']
                        month = row["EXP MONTH"]
                        year = row['EXP YEAR']
                        cvc = row['CVC']
                        discount = row['DISCOUNT']
                        i += 1
                        t = customThread(target=AWLABSING, args=(pid, fname, lname, email, address, prefix, phone, city, zip, state, country, payment, mode, card, month, year, cvc, discount, self.webhook_url, version, i, self.preloadpid, self.bypass))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}')

        elif self.site == 'SUSI':
            from scripts.susi import SUSI
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'susi/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'susi/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
            
                    for row in csv_input:
                        if self.url != "":
                            variantt = self.url
                        else:
                            variantt = row['VARIANT']  
                        fname = row['FIRST NAME'] 
                        lname = row['LAST NAME']
                        email = row['EMAIL']
                        password = row ['PASSWORD']
                        address = row['ADDRESS LINE 1']
                        address2 = row['ADDRESS LINE 2']
                        house_number = row['HOUSE NUMBER']
                        phone = row['PHONE NUMBER']
                        city = row['CITY']
                        postcode = row['ZIP']
                        state = row['STATE']

                        i += 1
                        t = customThread(target=SUSI, args=(variantt, fname, lname, email, password, address, address2, house_number, phone, city, postcode, state, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
                            
            except Exception as e:
                error(f'Failed To Read Task - {str(e)}')

        elif self.site == 'ALLIKE':
            from scripts.Allike2 import Allike
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'allike/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'allike/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0

                    for row in csv_input:
                        name = row['FIRST NAME']
                        surname = row['LAST NAME']
                        email = row['EMAIL']
                        street = row['ADDRESS LINE 1']
                        city = row['CITY']
                        postcode = row['ZIP']
                        country = row['COUNTRY']
                        phone = row['PHONE NUMBER']
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK'] 
                        size = row['SIZE']
                        payment = row['PAYMENT']
                        cardnumber = row['CARD NUMBER']
                        expmonth = row['EXP MONTH']
                        expyear = row['EXP YEAR']
                        cvc = row['CVC']

                        i += 1
                        t = customThread(target=Allike, args=(name, surname, email, street, city, postcode, region, country, phone, link, size, payment, cardnumber, expmonth, expyear, cvc, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}')

        elif self.site == 'SOTF':
            from scripts.Sotf import Sotf
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'Sotf/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'Sotf/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                    for row in csv_input:
                        account = row['ACCOUNT']
                        password = row['PASSWORD']

                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']   

                        size = row['SIZE']
                        mail = row['MAIL']
                        name = row['NAME']
                        surname = row['SURNAME']
                        address = row['ADDRESS']
                        num = row['NUM']
                        city = row['CITY']
                        country = row['COUNTRY']
                        region = row['REGION']
                        postcode = row['POSTCODE']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        i += 1
                        t = customThread(target=Sotf, args=(account, password, link, size, mail, name, surname, address, num, city, country, region, postcode, phone, payment, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}')   


        elif self.site == 'SUPPASTORE':
                from scripts.suppastore import SUPPASTORE
                try:
                    if machineOS == 'Darwin':
                        path = os.path.dirname('__file__').rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'suppa/tasks.csv')
                    elif machineOS == 'Windows':
                        path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'suppa/tasks.csv')
                    with open(f'{path}', 'r') as f:
                        csv_input = csv.DictReader(f)
                        i = 0
            
                        for row in csv_input:
                            if self.url != "":
                                link = self.url
                            else:
                                link = row['LINK']
                            name = row['NAME']
                            surname = row['SURNAME']
                            email = row['EMAIL']
                            street = row['STREET']
                            num = row['NUM']
                            city = row["CITY"]
                            postcode = row['POSTCODE']
                            region = row['REGION']
                            regionid = row["REGIONID"]
                            country = row['COUNTRY']
                            phone = row['PHONE']
                            size = row['SIZE']
                            payment = row["PAYMENT"]

                            i += 1
                            t = customThread(target=SUPPASTORE, args=(name, surname, email, street, num, city, postcode, region, regionid, country, phone, link, size, payment, self.webhook_url, self.version, i))
                            self.listathread.append(t)
                    
                        self.startoithread()

                except Exception as e:
                        error(f'Failed To Read Task - {str(e)}') 


        
        elif self.site == 'FOOTDISTRICT':
            from scripts.footdistrict import Footdistrict
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'footdistrict/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'footdistrict/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0

                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']
                        size = row['SIZE']
                        mail = row['MAIL']
                        name = row['NAME']
                        surname = row['SURNAME']
                        country = row['COUNTRY']
                        address = row['ADDRESS']
                        address2 = row['ADDRESS2']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        region = row['REGION']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        mode = row['MODE']
                        i += 1
                        t = customThread(target=Footdistrict, args=(link, size, mail, name, surname, country, address, address2, zipcode, city, region, phone, payment, mode, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 


        elif self.site == 'SNS':
            from scripts.sns import SNS
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'sns/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'sns/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0

                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']
                        size = row['SIZE']
                        country = row['COUNTRY']
                        mail = row['MAIL']									
                        name = row['NAME']
                        surname = row['SURNAME']
                        address = row['ADDRESS']
                        address2 = row['ADDRESS2']
                        city = row['CITY']
                        zipcode = row['ZIPCODE']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        cardnumber = row['CARDNUMBER']
                        expmonth = row['EXPMONTH']
                        expyear = row['EXPYEAR']
                        cvv = row['CVV']
                        promocode = row['PROMOCODE']
                        i += 1
                        t = customThread(target=SNS, args=(link, size, country, mail, name, surname, address, address2, city, zipcode, phone, payment, cardnumber, expmonth, expyear, cvv, promocode, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}')


        elif self.site == 'BSTN':
            from scripts.bstn import BSTN
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'bstn/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'bstn/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
            
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']
                        size = row['SIZE']
                        mail = row['MAIL']
                        name = row['NAME']
                        surname = row['SURNAME']
                        country = row['COUNTRY']
                        address = row['ADDRESS']
                        address2 = row['HOUSENUMBER']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        region = row['REGION']
                        phone = row['PHONE']
                        i += 1
                        t = customThread(target=BSTN, args=(link, size, mail, name, surname, country, address, address2, zipcode, city, region, phone, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 



        elif self.site == 'BASKET4BALLERS':
                      
                from scripts.b4b import B4B
                
                try:
                    if machineOS == 'Darwin':
                        path = os.path.dirname('__file__').rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'basket4ballers/tasks.csv')
                    elif machineOS == 'Windows':
                        path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'basket4ballers/tasks.csv')
                    with open(f'{path}', 'r') as f:
                        csv_input = csv.DictReader(f)
                        i = 0
                            
                        for row in csv_input:
                            if self.url != "":
                                link = self.url
                            else:
                                link = row['LINK']  
                            size = row['SIZE']
                            account = row['ACCOUNT']
                            password = row['PASSWORD']
                            zipcode = row['ZIPCODE']
                            payment = row['PAYMENT']
                            mode = row['MODE']
                            i += 1
                            t = customThread(target=B4B, args=(link, size, account, password, zipcode, payment, mode, self.webhook_url, self.version, i))     
                            self.listathread.append(t)
                    
                        self.startoithread()
                except Exception as e:
                    error(f'Failed To Read Task - {str(e)}') 

        elif self.site == 'STARCOW':
            from scripts.starcow import STARCOW
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'starcow/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'starcow/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                    
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK'] 
                        size = row['SIZE']
                        account = row['ACCOUNT']
                        password = row['PASSWORD']
                        mode = row['MODE']
                        country = row['COUNTRY']
                        i += 1
                        t = customThread(target=STARCOW, args=(link, size, account, password, mode, country, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 

        elif self.site == 'PRODIRECT':
            from scripts.prodirect import PRODIRECT
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'prodirect/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'prodirect/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0

                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK'] 
                        name = row['NAME']
                        surname = row['SURNAME']
                        address1 = row['ADDRESS 1']
                        address2 = row['ADDRESS 2']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        region = row['REGION']
                        country = row['COUNTRY']
                        phone = row['PHONE']
                        size = row['SIZE']
                        account = row['ACCOUNT']
                        password = row['PASSWORD']
                        mode = row['MODE']
                        i += 1
                        t = customThread(target=PRODIRECT, args=(name, surname, address1, address2, zipcode, city, region, country, phone, link, size, account, password, mode, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 
            
        elif self.site == 'CALIROOTS':
            from scripts.caliroots import CALI
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'caliroots/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'caliroots/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0

                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']  
                        size = row['SIZE']
                        i += 1
                        t = customThread(target=CALI, args=(link, size, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 

        
        elif self.site == 'TITOLO':
            from scripts.titolo import TITOLO
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'titolo/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'titolo/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                        
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK'] 
                        size = row['SIZE']
                        mail = row['MAIL']
                        name = row['NAME']
                        surname = row['SURNAME']
                        address = row['ADDRESS']
                        address2 = row['ADDRESS2']
                        housenumber = row['HOUSENUMBER']
                        postcode = row['ZIPCODE']
                        city = row['CITY']
                        region = row['REGION']
                        country = row['COUNTRY']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        i += 1
                        t = customThread(target=TITOLO, args=(link, size, mail, name, surname, country, address, address2, housenumber, postcode, city, region, phone, payment, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
#
            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 

        elif self.site == '43EINHALB':
            from scripts.einhalb import HEINLAB
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), '43einhalb/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), '43einhalb/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                        
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']
                        account = ""
                        password = ""
                        size = row['SIZE']
                        mail = row['MAIL']
                        name = row['NAME']
                        surname = row['SURNAME']
                        country = row['COUNTRY']
                        address = row['ADDRESS']
                        address2 = row['ADDRESS2']
                        housenumber = row['HOUSENUMBER']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        phone = row['PHONE']
                        password = password
                        account = account
                        i += 1
                        t = customThread(target=HEINLAB, args=(link, size, mail, name, surname, address, address2, housenumber, zipcode, city, country, phone, password, account, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
#
            except Exception as e:
                error(f'Failed To Read Task - {str(e)}')


        elif self.site == 'CONSORTIUM':
            from scripts.consortium import CONSORTIUM
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'consortium/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'consortium/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                        
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']   
                        size = row['SIZE']
                        account = row['ACCOUNT']
                        password = row['PASSWORD']
                        name = row['NAME']
                        surname = row['SURNAME']
                        payment = row['PAYMENT']
                        cardnumber = row['CARDNUMBER']
                        expmonth = row['EXPMONTH']
                        expyear = row['EXPYEAR']
                        cvc = row['CVC']
                        mode = row['MODE']
                        i += 1
                        t = customThread(target=CONSORTIUM, args=(link, size, account, password, name, surname, payment, cardnumber, expmonth, expyear, cvc, mode, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
#
            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 
                
        elif self.site == 'SUGAR':
            from scripts.sugar import Sugar
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'sugar/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'sugar/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                    
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']   
                        size = row['SIZE']						
                        name = row['NAME']
                        surname = row['SURNAME']
                        mail = row['MAIL']
                        country = row['COUNTRY']
                        address = row['ADDRESS']
                        regionid = row['REGIONID']
                        region = row['REGION']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        cardnumber = row['CARD NUMBER']
                        month = row['EXP MONTH']
                        year = row['EXP YEAR']
                        cvv = row['CVV']
                        i += 1
                        t = customThread(target=Sugar, args=(link, size, mail, name, surname, country, address, regionid, region, zipcode, city, phone, payment, cardnumber, month, year, cvv, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
#
            except Exception as e:
                error(f'Failed To Read Task - {str(e)}')


        elif self.site == 'SNEAKAVENUE':
            from scripts.sav import SAV
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'sneakavenue/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'sneakavenue/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                        
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']   
                        pid = row['PID']
                        bsid = row['BSID']
                        size = row['SIZE']
                        mail = row['MAIL']
                        name = row['NAME']
                        surname = row['SURNAME']
                        country = row['COUNTRY']
                        address = row['ADDRESS']
                        address2 = row['ADDRESS2']
                        housenumber = row['HOUSENUMBER']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        region = row['REGION']
                        phone = row['PHONE']
                        i += 1
                        t = customThread(target=SAV, args=(link, pid, bsid, size, mail, name, surname, country, address, address2, housenumber, zipcode, city, region, phone, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
#
            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 


        elif self.site == 'SNEAKERS76':
            from scripts.sneakers76 import Sneakers76
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'sneakers76/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'sneakers76/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                        
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']  
                        size = row['SIZE']						
                        name = row['NAME']
                        surname = row['SURNAME']
                        mail = row['MAIL']
                        country = row['COUNTRY']
                        address = row['ADDRESS']
                        region = row['REGION']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        mode = row['MODE']
                        i += 1
                        t = customThread(target=Sneakers76, args=(link, size, name, surname, mail, country, address, region, zipcode, city, phone, payment, mode, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 


        elif self.site == 'WORKINGCLASSHEROES':
            from scripts.workingclassheroes import WCH
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'workingclassheroes/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'workingclassheroes/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                        
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']   
                        size = row['SIZE']						
                        name = row['NAME']
                        surname = row['SURNAME']
                        mail = row['MAIL']
                        country = row['COUNTRY']
                        zipcode = row['ZIPCODE']
                        address = row['ADDRESS']
                        address2 = row['ADDRESS2']
                        city = row['CITY']
                        phone = row['PHONE']
                        cardnumber = row['CARDNUMBER']
                        expmonth = row['EXPMONTH']
                        expyear = row['EXPYEAR']
                        cvc = row['CVC']
                        i += 1
                        t = customThread(target=WCH, args=(link, size, name, surname, mail, country, zipcode, address, address2, city, phone, cardnumber, expmonth, expyear, cvc, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
#
            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 

        elif self.site == 'CORNERSTREET':
            from scripts.cornerstreet import Corner
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'cornerstreet/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'cornerstreet/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                        
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']  
                        size = row['SIZE']		
                        user = row['MAIL']
                        password = row['PASSWORD']				
                        name = row['NAME']
                        surname = row['SURNAME']
                        country = row['COUNTRY']
                        address = row['ADDRESS']
                        add2 = row['ADDRESS 2']
                        region = row['REGION']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        i += 1
                        t = customThread(target=Corner, args=(link, size, user, password, name, surname, country, address, add2, region, zipcode, city, phone, payment, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}')

        elif self.site == 'SLAMJAM':
            from scripts.slamjam import Slamjam
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'slamjam/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'slamjam/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0

                    for row in csv_input:

                        variant = row['VARIANT']   
                        preload = row['PRELOAD']
                        size = row['SIZE']
                        mail = row['MAIL']
                        name = row['NAME']
                        surname = row['SURNAME']
                        address = row['ADDRESS']
                        address2 = row['ADDRESS2']
                        housenumber = row['HOUSENUMBER']
                        region = row['REGION']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        country = row['COUNTRY']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        cardnumber = row['CARDNUMBER']
                        expmonth = row['EXPMONTH']
                        expyear = row['EXPYEAR']
                        cvv = row['CVV']
                        i += 1
                        t = customThread(target=Slamjam, args=(variant, preload, size, mail, name, surname, address, address2, housenumber, region, zipcode, city, country, phone, payment, cardnumber, expmonth, expyear, cvv, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
#
#
            except Exception as e:
                    error(f'Failed To Read Task - {str(e)}') 

#
#
        elif self.site == 'OFF-WHITE':
            from scripts.offwhite import OffWhite
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'offwhite/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'offwhite/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                    
                    for row in csv_input:
                        if self.url != "":
                            sku = self.url
                        else:
                            sku = row['LINK']      
                        size = row['SIZE']
                        mail = row['MAIL']
                        password = row['PASSWORD']
                        name = row['NAME']
                        surname = row['SURNAME']
                        address = row['ADDRESS']
                        address2 = row['ADDRESS2']
                        housenumber = row['HOUSENUMBER']
                        region = row['REGION']
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        country = row['COUNTRY']
                        phone = row['PHONE']
                        vat = row['VAT']
                        payment = row['PAYMENT']
                        cardnumber = row['CARDNUMBER']
                        expmonth = row['EXPMONTH']
                        expyear = row['EXPYEAR']
                        cvv = row['CVV']
                        cardowner = row['CARDOWNER']
                        i += 1
                        t = customThread(target=OffWhite, args=(sku, size, mail, password, name, surname, address, address2, housenumber, region, zipcode, city, country, phone, vat, payment, cardnumber, expmonth, expyear, cvv, cardowner, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()
            

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 
                

        elif self.site == 'CROCS':                
            from scripts.crocs import CROCS
            try:
                    if machineOS == 'Darwin':
                            path = os.path.dirname('__file__').rsplit('/', 1)[0]
                            path = os.path.join(os.path.dirname(sys.argv[0]), 'Crocs/tasks.csv')
                    elif machineOS == 'Windows':
                            path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                            path = os.path.join(os.path.dirname(sys.argv[0]), 'Crocs/tasks.csv')
                    with open(f'{path}', 'r') as f:
                            csv_input = csv.DictReader(f)
                            i = 0
                            active = []
                            

                            for row in csv_input:
                                if self.url != "":
                                    pid = self.url
                                else:
                                    pid = row['LINK']      
                                size = row['SIZE']
                                fname = row['FIRST NAME']
                                lname = row['LAST NAME']
                                email = row['EMAIL']
                                address = row['ADDRESS LINE 1']
                                phone = row['PHONE NUMBER']
                                city = row['CITY']
                                zipp = row['ZIP']
                                country = row['COUNTRY']
                                payment = row['PAYMENT']
                                state = row['STATE']
                                card = row['CARD NUMBER']
                                month = row["EXP MONTH"]
                                year = row['EXP YEAR']
                                cvc = row['CVC']
                                discount = row['DISCOUNT']
                                i += 1
                                t = customThread(target=CROCS, args=(pid, size, fname, lname, email, address, phone, city, zipp, country, state, payment, card, month, year, cvc, discount, self.webhook_url, self.version, i))
                                self.listathread.append(t)
                    
                            self.startoithread()
            except Exception as e:
                    error(f'Failed To Read Task - {str(e)}')

        elif self.site == 'REVOLVE':
      
            from scripts.revolve import REVOLVE
            try:
                    if machineOS == 'Darwin':
                            path = os.path.dirname('__file__').rsplit('/', 1)[0]
                            path = os.path.join(os.path.dirname(sys.argv[0]), 'revolve/tasks.csv')
                    elif machineOS == 'Windows':
                            path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                            path = os.path.join(os.path.dirname(sys.argv[0]), 'revolve/tasks.csv')
                    with open(f'{path}', 'r') as f:
                            csv_input = csv.DictReader(f)
                            i = 0

                            for row in csv_input:
                                if self.url != "":
                                    link = self.url
                                else:
                                    link = row['LINK']     
                                size = row['SIZE']
                                fname = row['NAME']
                                lname = row['SURNAME']
                                email = row['EMAIL']
                                password = row['PASSWORD']
                                address = row['ADDRESS']
                                address2 = row['ADDRESS2']
                                phone = row['PHONE NUMBER']
                                city = row['CITY']
                                zipp = row['ZIP']
                                country = row['COUNTRY']
                                payment = row['PAYMENT']
                                state = row['STATE']
                                card = row['CARD NUMBER']
                                month = row["EXP MONTH"]
                                year = row['EXP YEAR']
                                cvc = row['CVC']
                                discount = row['DISCOUNT']
                                i += 1
                                t = customThread(target=REVOLVE, args=(link, size, fname, lname, email, password, address, address2, city, zipp, state, country, phone, payment, card, month, year, cvc, discount, self.webhook_url, self.version, i))
                                active.append(t)
                                self.listathread.append(t)
                    
                            self.startoithread()

            except Exception as e:
                    error(f'Failed To Read Task - {str(e)}')

        elif self.site == 'SOLEBOX':                        
                from scripts.solebox import SOLEBOX
                try:
                    if machineOS == 'Darwin':
                            path = os.path.dirname('__file__').rsplit('/', 1)[0]
                            path = os.path.join(os.path.dirname(sys.argv[0]), 'solebox/tasks.csv')
                    elif machineOS == 'Windows':
                            path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                            path = os.path.join(os.path.dirname(sys.argv[0]), 'solebox/tasks.csv')
                    with open(f'{path}', 'r') as f:
                            csv_input = csv.DictReader(f)
                            i = 0
                            active = []
                            for row in csv_input:
                                variant = row['VARIANT']
                                preload = row['PRELOAD']
                                mail = row['MAIL']
                                password = row['PASSWORD']
                                name = row['NAME']
                                surname = row['SURNAME']
                                address = row['ADDRESS']
                                address2 = row['ADDRESS2']
                                housenumber = row['HOUSENUMBER']
                                region = row['REGION']
                                zipcode = row['ZIPCODE']
                                city = row['CITY']
                                country = row['COUNTRY']
                                phone = row['PHONE']
                                i += 1
                                t = customThread(target=SOLEBOX, args=(variant, preload, mail, password, name, surname, address, address2, housenumber, region, zipcode, city, country, phone, self.webhook_url, self.version, i))
                                self.listathread.append(t)
                    
                            self.startoithread()
                except Exception as e:
                        error(f'Failed To Read Task - {str(e)}')   


        elif self.site == 'SNIPES':
                            
            from scripts.snipes import SNIPES
            try:
                if machineOS == 'Darwin':
                        path = os.path.dirname('__file__').rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'snipes/tasks.csv')
                elif machineOS == 'Windows':
                        path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'snipes/tasks.csv')
                with open(f'{path}', 'r') as f:
                        csv_input = csv.DictReader(f)
                        i = 0
                        active = []
                        for row in csv_input:
                            variant = row['VARIANT']
                            preload = row['PRELOAD']
                            mail = row['MAIL']
                            password = row['PASSWORD']
                            name = row['NAME']
                            surname = row['SURNAME']
                            address = row['ADDRESS']
                            address2 = row['ADDRESS2']
                            housenumber = row['HOUSENUMBER']
                            region = row['REGION']
                            zipcode = row['ZIPCODE']
                            city = row['CITY']
                            country = row['COUNTRY']
                            phone = row['PHONE']
                            discount = row['DISCOUNT']
                            i += 1
                            t = customThread(target=SNIPES, args=(variant, preload, mail, password, name, surname, address, address2, housenumber, region, zipcode, city, country, phone, discount, self.webhook_url, self.version, i))
                            self.listathread.append(t)
                    
                        self.startoithread()
            except Exception as e:
                    error(f'Failed To Read Task - {str(e)}')


        elif self.site == 'GALERIES':
            from scripts.galeries import Galeries
            try:
                if machineOS == 'Darwin':
                    path = os.path.dirname('__file__').rsplit('/', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'galeries/tasks.csv')
                elif machineOS == 'Windows':
                    path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                    path = os.path.join(os.path.dirname(sys.argv[0]), 'galeries/tasks.csv')
                with open(f'{path}', 'r') as f:
                    csv_input = csv.DictReader(f)
                    i = 0
                    for row in csv_input:
                        if self.url != "":
                            link = self.url
                        else:
                            link = row['LINK']     
                        size = row['SIZE']		
                        user = row['MAIL']
                        password = row['PASSWORD']
                        name = row['NAME']
                        surname = row['SURNAME']
                        country = row['COUNTRY']
                        address = row['ADDRESS']
                        add2 = row['ADDRESS 2']  
                        zipcode = row['ZIPCODE']
                        city = row['CITY']
                        prefix = row['PREFIX']
                        phone = row['PHONE']
                        payment = row['PAYMENT']
                        i += 1
                        t = customThread(target=Galeries, args=(link, size, user, password, name, surname, country, address, add2, zipcode, city, prefix, phone, payment, self.webhook_url, self.version, i))
                        self.listathread.append(t)
                    
                    self.startoithread()

            except Exception as e:
                error(f'Failed To Read Task - {str(e)}') 




        elif self.site == 'BASKET4BALLERS':
                      
                from scripts.b4b import B4B
                
                try:
                    if machineOS == 'Darwin':
                        path = os.path.dirname('__file__').rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'basket4ballers/tasks.csv')
                    elif machineOS == 'Windows':
                        path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'basket4ballers/tasks.csv')
                    with open(f'{path}', 'r') as f:
                        csv_input = csv.DictReader(f)
                        i = 0
                            
                        for row in csv_input:
                            if self.url != "":
                                link = self.url
                            else:
                                link = row['LINK']  
                            size = row['SIZE']
                            account = row['ACCOUNT']
                            password = row['PASSWORD']
                            zipcode = row['ZIPCODE']
                            payment = row['PAYMENT']
                            mode = row['MODE']
                            i += 1
                            t = customThread(target=B4B, args=(link, size, account, password, zipcode, payment, mode, self.webhook_url, self.version, i))     
                            self.listathread.append(t)
                    
                        self.startoithread()
                except Exception as e:
                    error(f'Failed To Read Task - {str(e)}') 



        elif self.site == 'FOOTLOCKER NEW':
                from scripts.footlocker2 import Footlocker
                try:
                    if machineOS == 'Darwin':
                        path = os.path.dirname('__file__').rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'footlocker/tasks.csv')
                    elif machineOS == 'Windows':
                        path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), 'footlocker/tasks.csv')
                    with open(f'{path}', 'r') as f:
                        csv_input = csv.DictReader(f)
                        i = 0
                        for row in csv_input:
                            if self.url != "":
                                sku = self.url
                            else:
                                sku = row['SKU']     
                            size = row['SIZE']		
                            mail = row['MAIL']
                            name = row['NAME']
                            surname = row['SURNAME']
                            address = row['ADDRESS']
                            address2 = row['ADDRESS2']  
                            housenumber = row['HOUSENUMBER']
                            region = row['REGION']
                            zipcode = row['ZIPCODE']
                            city = row['CITY']
                            country = row['COUNTRY']
                            phone = row['PHONE']
                            cardnumber = row['CARDNUMBER']
                            month = row['MONTH']
                            year = row['YEAR']
                            ccv = row['CCV']
                            i += 1
                            t = customThread(target=Footlocker, args=(sku, size, mail, name, surname, address, address2, housenumber, region, zipcode, city, country, phone, cardnumber, month, year, ccv, self.webhook_url, self.version, i))
                            self.listathread.append(t)

                    self.startoithread()

                except Exception as e:
                    error(f'Failed To Read Task - {str(e)}') 
        
        if self.site == 'THEBROKENARM':
                                            
                        from scripts.tba import TBA
                        try:
                                if machineOS == 'Darwin':
                                        path = os.path.dirname('__file__').rsplit('/', 1)[0]
                                        path = os.path.join(os.path.dirname(sys.argv[0]), 'thebrokenarm/tasks.csv')
                                elif machineOS == 'Windows':
                                        path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                                        path = os.path.join(os.path.dirname(sys.argv[0]), 'thebrokenarm/tasks.csv')
                                with open(f'{path}', 'r') as f:
                                        csv_input = csv.DictReader(f)
                                        i = 0
                                        
                                        for row in csv_input:
                                                if self.url != "":
                                                    pid = self.url
                                                else:
                                                    pid = row['LINK']     
                                                size = row['SIZE']
                                                fname = row['FIRST NAME']
                                                lname = row['LAST NAME']
                                                email = row['EMAIL']
                                                password = row['PASSWORD']
                                                address = row['ADDRESS LINE 1']
                                                address2 = row['ADDRESS LINE 2']
                                                phone = row['PHONE NUMBER']
                                                city = row['CITY']
                                                zip = row['ZIP']
                                                state = row['STATE']
                                                country = row['COUNTRY']
                                                i += 1
                                                t = customThread(target=TBA, args=(pid, size, fname, lname, email, password, address, address2, phone, city, zip, state, country, self.webhook_url, self.version, i))
                                                self.listathread.append(t)
                                        self.startoithread()
                        except Exception as e:
                                error(f'Failed To Read Task - {str(e)}')


        elif self.site == 'AMBUSH':
                    from scripts.ambush import Ambush
                    try:
                        if machineOS == 'Darwin':
                            path = os.path.dirname('__file__').rsplit('/', 1)[0]
                            path = os.path.join(os.path.dirname(sys.argv[0]), 'ambush/tasks.csv')
                        elif machineOS == 'Windows':
                            path = os.path.dirname('__file__').rsplit('\\', 1)[0]
                            path = os.path.join(os.path.dirname(sys.argv[0]), 'ambush/tasks.csv')
                        with open(f'{path}', 'r') as f:
                            csv_input = csv.DictReader(f)
                            i = 0
                            for row in csv_input:
                                if self.url != "":
                                    link = self.url
                                else:
                                    link = row['PID']    
                                size = row['SIZE'] 
                                name = row['FIRST NAME']
                                surname = row['LAST NAME']
                                email = row['EMAIL']
                                street = row['ADDRESS LINE 1']
                                street2 = row['ADDRESS 2']
                                city = row['CITY']
                                postcode = row['ZIP']
                                phone = row['PHONE NUMBER']                                   
                                state = row['STATE']
                                country = row['COUNTRY']
                                payment = row['PAYMENT']
                                cardnumber = row['CARD NUMBER']
                                expmonth = row['EXP MONTH']
                                expyear = row['EXP YEAR']
                                cvc = row['CVC']
                                cardholder = row['CARDHOLDER']
                                i += 1
                                t = customThread(target=Ambush, args=(link, size, name, surname, email, street, street2, city, postcode, phone, state, country, payment, cardnumber, expmonth, expyear, cvc, cardholder, self.webhook_url, self.version, i))
                                self.listathread.append(t)
                            self.startoithread()

                    except Exception as e:
                        error(f'Failed To Read Task - {str(e)}')




    def startoithread(self):

        global actived

        for element in self.listathread:
            element.start()

        while actived != 1:
            continue
        

        arr = os.listdir()
        try:
            for f in arr:
                if machineOS == "Windows":
                    if ".exe" in f and "Phoenix" in f:
                        os.startfile(f)
                else:
                    if "Phoenix AIO" in f:
                        subprocess.call(["open", f])
        except:
            pass
        parent_pid = os.getpid()
        parent = psutil.Process(parent_pid)
        print(f"{parent} killed - updateChecker()")
        pronto = '''{
            "type":"bot", 
            "action":"message", 
            "message":"Bot stopped, preparing session!"
        }'''

        self.ws.send(pronto)
        parent.kill()

        
