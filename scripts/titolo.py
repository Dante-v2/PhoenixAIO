import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from datetime import datetime
import helheim
from os import urandom
from autosolveclient.autosolve import AutoSolve
from mods.errorHandler import errorHandler
import traceback
import time

HANDLER = errorHandler(__file__)
helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

UNIQUE_ID = int(time.time() * 1000) * 2**random.randint(10,16)
AUTO_SOLVE = None
CAPTCHA_TOKENS = []
CAPTCHA = None

checkoutnum = 0
carted = 0
failed = 0
def perform_request(self, method, url, *args, **kwargs):
    if "proxies" in kwargs or "proxy"  in kwargs:
        return super(cloudscraper.CloudScraper, self).request(method, url, *args, **kwargs)
    else:
        return super(cloudscraper.CloudScraper, self).request(method, url, *args, **kwargs,proxies=self.proxies)
cloudscraper.CloudScraper.perform_request = perform_request


@staticmethod
def is_New_Captcha_Challenge(resp):
    try:
        return (
                cloudscraper.CloudScraper.is_Captcha_Challenge(resp)
                and re.search(
                    r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/?\w?/?\w?/orchestrate/captcha/v1',
                    resp.text,
                    re.M | re.S
                )
                and re.search(r'window._cf_chl_opt', resp.text, re.M | re.S)
        )
    except AttributeError:
        pass

    return False
cloudscraper.CloudScraper.is_New_Captcha_Challenge = is_New_Captcha_Challenge

#normal challenge
@staticmethod
def is_New_IUAM_Challenge(resp):
    try:
        return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code in [429, 503]
                and re.search(
                    r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/?\w?/?\w?/orchestrate/jsch/v1',
                    resp.text,
                    re.M | re.S
                )
                and re.search(r'window._cf_chl_opt', resp.text, re.M | re.S)
        )
    except AttributeError:
        pass

    return False
cloudscraper.CloudScraper.is_New_IUAM_Challenge = is_New_IUAM_Challenge

## fingerprint challenge
def is_fingerprint_challenge(resp):
    try:
        if resp.status_code == 429:
            if "/fingerprint/script/" in resp.text:
                return True
        return False
    except:
        pass

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

    error("FAILED TO READ CONFIG FILE")
    pass

class AutoSolveInitialize():
    def __init__(self):

        global AUTO_SOLVE
        global CAPTCHA

        try:
            if CAPTCHA == 'autosolve':
                if any(x == '' for x in [config['autosolve']['access-token'], config['autosolve']['api-key']]):
                    error('You have chosen AutoSolve for captcha solving but didn\'t enter all credentials.')
                    CAPTCHA = next((x for x in ['2captcha', 'anticaptcha', 'capmonster'] if config[x] != ''), None)
                    if not CAPTCHA:
                        error('Please enter at least one captcha provider.')
                        sys.exit()
                    else:
                        warn(f'Using {CAPTCHA}...')
                        return
            else:
                return
            warn('[AUTOSOLVE] - Connecting...')
            auto_solve_factory = AutoSolve({
                "access_token": config['autosolve']['access-token'],
                "api_key": config['autosolve']['api-key'],
                "client_key": "PheonixAIO-cdfbdc31-ca45-4fc7-9989-0dbbcd6c691b",
                "debug": True,
                "should_alert_on_cancel": True
            })
            AUTO_SOLVE = auto_solve_factory.get_instance()
            AUTO_SOLVE.init()
            AUTO_SOLVE.initialized()
            AUTO_SOLVE.emitter.on('AutoSolveResponse', self.handle_token)
            AUTO_SOLVE.emitter.on('AutoSolveResponse_Cancel', self.handle_token_cancel)
            AUTO_SOLVE.emitter.on('AutoSolveError', self.handle_exception)
            info('[AUTOSOLVE] - Successfully connected!')
        except Exception as e:
            error(f'[AUTOSOLVE] - Error connecting: {e}')
    
    def handle_token(self, message):
        CAPTCHA_TOKENS.append(json.loads(message))
    def handle_token_cancel(self, message):
        CAPTCHA_TOKENS.append({"taskId": json.loads(message)["taskId"], "token": "failed"})
    def handle_exception(self, message):
        error(f'[AUTOSOLVE] - Error connecting: {message}')
        
try:
    CAPTCHA = config['captcha']['titolo']
    config['2captcha']
    config['capmonster']
    config['anticaptcha']
except:
    error('Your config file isn\'t updated. Please download the latest one.')
    sys.exit()
else:
    if CAPTCHA == 'autosolve':
        AutoSolveInitialize()
    elif CAPTCHA == '2captcha' and config['2captcha'] == '':
        error('You have chosen 2captcha for captcha solving but didn\'t enter your API key.')
        CAPTCHA = next((x for x in ['anticaptcha', 'capmonster'] if config[x] != ''), None)
    elif CAPTCHA == 'anticaptcha' and config['anticaptcha'] == '':
        error('You have chosen AntiCaptcha for captcha solving but didn\'t enter your API key.')
        CAPTCHA = next((x for x in ['2captcha', 'capmonster'] if config[x] != ''), None)
    elif CAPTCHA == 'capmonster' and config['capmonster'] == '':
        error('You have chosen CapMonster for captcha solving but didn\'t enter your API key.')
        CAPTCHA = next((x for x in ['2captcha', 'anticaptcha'] if config[x] != ''), None)
    elif CAPTCHA not in ['autosolve', '2captcha', 'capmonster', 'anticaptcha']:
        error('Invalid captcha provider selected.')
        CAPTCHA = next((x for x in ['2captcha', 'anticaptcha', 'capmonster'] if config[x] != ''), None)
    if not CAPTCHA:
        error('Please enter at least one captcha provider.')
        sys.exit()
    else:
        warn(f'Using {CAPTCHA}...')

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

class TITOLO():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'titolo/exceptions.log')
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'titolo/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "titolo/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()

        except:
            error("Failed To Read Proxies File - using no proxies ")
            self.all_proxies = None

        if config['anticaptcha'] != "":
            self.captcha = {
                'provider': 'anticaptcha',
                'api_key': config['anticaptcha']
            }
        elif config['2captcha'] != "":
            self.captcha={
                'provider': '2captcha',
                'api_key':config['2captcha']
            }
        else:
            error('2Captcha or AntiCaptcha needed. Stopping task.')
            time.sleep(5)
            sys.exit(1)

        self.s = cloudscraper.create_scraper(
            browser= {
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
            },
            captcha=self.captcha,
            requestPostHook=self.injection
        )

        self.link = row['LINK']       
        self.size = row['SIZE']
        self.mail = row['MAIL']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.country = row['COUNTRY']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.housenumber = row['HOUSENUMBER']
        self.zipcode = row['ZIPCODE']
        self.city = row['CITY']
        self.region = row['REGION']
        self.phone = row['PHONE']
        self.payment = row['PAYMENT']
        
        self.twoCaptcha = config['2captcha']
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        try:
            if self.name.upper() == "RANDOM":
                self.name = names.get_first_name(gender='male')
            if self.surname.upper() == "RANDOM":
                self.surname = names.get_last_name()
            if self.phone.upper() == "RANDOM":
                self.phone = str("0"+str(random.randint(7400000000,7999990000)))
            if self.mail[:6].upper() == "RANDOM":
                self.mail = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.mail.split("@")[1]).lower()
        except Exception as e:
            error(e)

        if self.country == 'US':
            if self.region == 'Alabama':
                self.region = '1'
            if self.region == 'Alaska':
                self.region = '2'
            if self.region == 'American Samoa':
                self.region = '3'
            if self.region == 'Arizona':
                self.region = '4'
            if self.region == 'Arkansas':
                self.region = '5'
            if self.region == 'Armed Forces Africa':
                self.region = '6'
            if self.region == 'Armed Forces Americas':
                self.region = '7'
            if self.region == 'Armed Forces Canada':
                self.region = '8'
            if self.region == 'Armed Forces Europe':
                self.region = '9'
            if self.region == 'Armed Forces Middle East':
                self.region = '10'
            if self.region == 'Armed Forces Pacific':
                self.region = '11'
            if self.region == 'California':
                self.region = '12'
            if self.region == 'Colorado':
                self.region = '13'
            if self.region == 'Connecticut':
                self.region = '14'
            if self.region == 'Delaware':
                self.region = '15'
            if self.region == 'District of Columbia':
                self.region = '16'
            if self.region == 'Federated States Of Micronesia':
                self.region = '17'
            if self.region == 'Florida':
                self.region = '18'
            if self.region == 'Georgia':
                self.region = '19'
            if self.region == 'Guam':
                self.region = '20'
            if self.region == 'Hawaii':
                self.region = '21'
            if self.region == 'Idaho':
                self.region = '22'
            if self.region == 'Illinois':
                self.region = '23'
            if self.region == 'Indiana':
                self.region = '24'
            if self.region == 'Iowa':
                self.region = '25'
            if self.region == 'Kansas':
                self.region = '26'
            if self.region == 'Kentucky':
                self.region = '27'
            if self.region == 'Louisiana':
                self.region = '28'
            if self.region == 'Maine':
                self.region = '29'
            if self.region == 'Marshall Islands':
                self.region = '30'
            if self.region == 'Maryland':
                self.region = '31'
            if self.region == 'Massachusetts':
                self.region = '32'
            if self.region == 'Michigan':
                self.region = '33'
            if self.region == 'Minnesota':
                self.region = '34'
            if self.region == 'Mississippi':
                self.region = '35'
            if self.region == 'Missouri':
                self.region = '36'
            if self.region == 'Montana':
                self.region = '37'
            if self.region == 'Nebraska':
                self.region = '38'
            if self.region == 'Nevada':
                self.region = '39'
            if self.region == 'New Hampshire':
                self.region = '40'
            if self.region == 'New Jersey':
                self.region = '41'
            if self.region == 'New Mexico':
                self.region = '42'
            if self.region == 'New York':
                self.region = '43'
            if self.region == 'North Carolina':
                self.region = '44'
            if self.region == 'North Dakota':
                self.region = '45'
            if self.region == 'Northern Mariana Islands':
                self.region = '46'
            if self.region == 'Ohio':
                self.region = '47'
            if self.region == 'Oklahoma':
                self.region = '48'
            if self.region == 'Oregon':
                self.region = '49'
            if self.region == 'Palau':
                self.region = '50'
            if self.region == 'Pennsylvania':
                self.region = '51'
            if self.region == 'Puerto Rico':
                self.region = '52'
            if self.region == 'Rhode Island':
                self.region = '53'
            if self.region == 'South Carolina':
                self.region = '54'
            if self.region == 'South Dakota':
                self.region = '55'
            if self.region == 'Tennessee':
                self.region = '56'
            if self.region == 'Texas':
                self.region = '57'
            if self.region == 'Utah':
                self.region = '58'
            if self.region == 'Vermont':
                self.region = '59'
            if self.region == 'Virgin Islands':
                self.region = '60'
            if self.region == 'Virginia':
                self.region = '61'
            if self.region == 'Washington':
                self.region = '62'
            if self.region == 'West Virginia':
                self.region = '63'
            if self.region == 'Wisconsin':
                self.region = '64'
            if self.region == 'Wyoming':
                self.region = '65'

        self.webhook_url = webhook
        self.version = version
        self.threadID = '%03d' % i
        self.discord = DISCORD_ID

        self.timeout = 120
        self.delay = int(config['delay'])
        self.build_proxy()
        self.balance = balancefunc()
        self.bar()

        self.domain = self.link.split('titoloshop.com/')[1].split('/')[0]

        self.warn('Task started!')
        
        self.scrapeproduct()


#####################################################################################################################  - CHOOSE PROXY


    def bar(self):
        if machineOS.lower() == 'windows':
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - TITOLO Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - TITOLO Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [TITOLO] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [TITOLO] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [TITOLO] - {text}'
        warn(message)

    def build_proxy(self):
        cookies = self.s.cookies
        try:
            kasada = self.s.kasada
        except:
            pass
        self.s = cloudscraper.create_scraper(
            captcha=self.captcha,
            browser={
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
            },
            requestPostHook=self.injection
        )
        helheim.wokou(self.s)
        self.s.cookies = cookies
        try:
            self.s.kasada = kasada
        except:
            pass
        if self.all_proxies == [] or not self.all_proxies:
            return None
        else:
            self.px = random.choice(self.all_proxies)
            splitted = self.px.split(':')
            if len(splitted) == 2:
                self.s.proxies = {
                    'http': 'http://{}'.format(self.px),
                    'https': 'http://{}'.format(self.px)
                }
                return None
            
            elif len(splitted) == 4:
                self.s.proxies = {
                    'http': 'http://{}:{}@{}:{}'.format(splitted[2], splitted[3], splitted[0], splitted[1]),
                    'https': 'http://{}:{}@{}:{}'.format(splitted[2], splitted[3], splitted[0], splitted[1])
                }
                return None
            else:
                self.error('Invalid proxy: "{}", rotating'.format(self.px))
                return None

    def injection(self, session, response):
        try:
            if helheim.isChallenge(session, response):
                self.warn('Solving Cloudflare v2')
                return helheim.solve(session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                self.warn('Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.warn('Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True).solve() 
            else:
                return response

    def solve_v2(self, url):
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.recaptcha(sitekey='6Ldy9cAUAAAAABNI8b7_ruZzyUbxawAlvLJpTiJJ', url=url, invisible=True)
                code = result['code']
                return code
            except Exception as e:
                self.error(f'Exception solving captcha: {e}')
                return self.solve_v2(url)
        elif CAPTCHA == 'capmonster':
            try:
                captchaurl = "https://api.capmonster.cloud/createTask"
                payload = {
                    "clientKey": config['capmonster'],
                    "task": {
                        "type": "NoCaptchaTaskProxyless",
                        "websiteURL": url,
                        "websiteKey": "6Ldy9cAUAAAAABNI8b7_ruZzyUbxawAlvLJpTiJJ"
                    }
                }
                r = requests.post(captchaurl, json = payload)
                taskid = r.text.split('"taskId":')[1].split('}')[0]
                data = {
                    "clientKey": config['capmonster'],
                    "taskId": taskid
                }
                r = requests.post("https://api.capmonster.cloud/getTaskResult", json = data)
                i = 0
                while not "ready" in r.text and i < 30:
                    time.sleep(5)
                    i += 1
                    r = requests.post("https://api.capmonster.cloud/getTaskResult", json = data)
                if "ready" in r.text:
                    code = r.text.split('"gRecaptchaResponse":"')[1].split('"')[0]
                    return code
                else:
                    self.error('Failed solving captcha!')
                    return self.solve_v2(url)
            except Exception as e:
                self.error(f'Exception solving captcha: {e}')
                return self.solve_v2(url)
        elif CAPTCHA == 'autosolve':
            try:
                AUTO_SOLVE.send_token_request({
                    "taskId"  : f'{self.threadID}-{UNIQUE_ID}', 
                    "url"     : url, 
                    "siteKey" : "6Ldy9cAUAAAAABNI8b7_ruZzyUbxawAlvLJpTiJJ", 
                    "version" : '1'
                })
                while True:
                    for token in CAPTCHA_TOKENS:
                        if token['taskId'] == f'{self.threadID}-{UNIQUE_ID}':
                            if token['token'] != 'failed':
                                CAPTCHA_TOKENS.remove(token)
                                return token['token']
                            else:
                                self.error('Autosolve captcha solve failed')
                                return self.solve_v2(url)
                    time.sleep(1)
            except Exception as e:
                self.error(f'An error occured solving captcha with Autosolve: {e}')
                return self.solve_v2(url)

################################################################################################################################# - GET AL PRODOTTO

    def scrapeproduct(self):
        self.warn("Getting product...")
        while True:
            try:
                r = self.s.get(
                    self.link, 
                    timeout=self.timeout
                )
                if r.status_code == 200 or r.status_code == 201:
                    try:
                        if 'titoloCountdown' in r.text:
                            dataprod = int(r.text.split('titoloCountdown": { "timestamp": "')[1].split('"')[0])
                            current = int(time.time())
                            delta = dataprod - current
                            if delta > 20:
                                self.time_to_sleep = delta - 15
                                self.warn(f'Timer found, sleeping for {self.time_to_sleep} seconds...')
                                time.sleep(self.time_to_sleep)
                                continue
                        if 'recaptcha' in r.text:
                            self.captcha = True
                        else:
                            self.captcha = False
                        soup = bs(r.text, 'lxml')
                        form = soup.find('form', {'id': 'product_addtocart_form'})
                        self.atc_url = form['action']
                        self.pid = soup.find('input', {'name': 'product'})['value']
                        self.formkey = soup.find('input', {'name': 'form_key'})['value']
                        self.title = soup.find('span', {'itemprop': 'name'}).text.strip()
                        try:
                            self.image = r.text.split('type="image/jpeg" srcset="')[1].split('"')[0]
                        except:
                            self.image = "https://en.titoloshop.com/skin/frontend/waterlee-boilerplate/newtitolo/images/logo.gif"
                        soup = bs(r.text, features='lxml')
                        taglieu = soup.find('div',{'id':'tab-size_eu'})
                        supatt = []
                        sizeval = []
                        sizedascegl = []
                        self.supatt = taglieu('div')[0]['aria-describedby'].split('size-')[1].split(']')[0]
                        for i in taglieu('div'):
                            try:
                                oos = i['data-option-empty']
                            except:
                                supatt.append(i['data-option-id'])
                                sizeval.append(i['data-option-label'])
                                if 'EU' in i['data-option-label']:
                                    sizedascegl.append(i['data-option-label'].split(' (EU)')[0])
                        if not supatt:
                            self.warn('Product OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        connect = zip(supatt, sizeval, sizedascegl)
                        self.connect = list(connect)
                        if len(self.connect) < 1:
                            self.warn('Product OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        else:
                            if self.size == "RANDOM":
                                self.success(f'{self.title} in stock!')
                                self.connetto = random.choice(self.connect)
                                self.variante = self.connetto[0]
                                self.sizescelta = self.connetto[1]
                                self.sizeprint = self.connetto[2]
                                break
                            elif "," in self.size or "-" in self.size:
                                self.sizerange = []
                                try:
                                    self.size1 = str(self.size.split(',')[0])
                                    self.size2 = str(self.size.split(',')[1])
                                except:
                                    self.size1 = str(self.size.split('-')[0])
                                    self.size2 = str(self.size.split('-')[1])
                                for x in self.connect:
                                    if str(self.size1) <= str(x[2]) <= str(self.size2):
                                        self.sizerange.append(x[2])
                                if len(self.sizerange) < 1:
                                    self.warn(f'{self.title} size {self.size} OOS, monitoring...')
                                    time.sleep(self.delay)
                                    continue
                                else:
                                    self.sizerandom = random.choice(self.sizerange)
                                    self.success(f'{self.title} size {self.sizerandom} in stock!')
                                    for i in self.connect:
                                        if self.sizerandom in i[2]:
                                            self.variante = i[0]
                                            self.sizescelta = i[1]
                                            self.sizeprint = i[2]
                                    break
                            else:
                                for element in self.connect:
                                    if self.size == element[2]:
                                        self.success(f'{self.title} size {self.size} in stock!')
                                        self.variante = element[0]
                                        self.sizescelta = element[1]
                                        self.sizeprint = element[2]
                                break                                          
                    except Exception as e:
                        self.warn(f'Size not loaded {e.__class__.__name__}, retrying...')
                        open(self.logs_path, 'a+').write(f'Size not loaded: {e}\n')
                        time.sleep(self.delay)
                        continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                else:
                    self.error(f'Error getting product: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting product: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.ATC()

    def ATC(self):
        global carted, failed, checkoutnum
        headers ={
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': self.link,
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.cookie_obj = requests.cookies.create_cookie(domain="www.titoloshop.com",name='form_key',value=self.formkey)
        self.s.cookies.set_cookie(self.cookie_obj)
        now = datetime.now()
        timestamp = (str(datetime.timestamp(now)).split('.')[0])*13
        signature = base64.b64encode(timestamp.encode())
        if self.captcha:
            captcha = self.solve_v2(self.link)
            payload = {
                'product':self.pid,
                'selected_configurable_option':'',			
                'related_product':'',		
                'item':self.pid,
                'form_key':self.formkey,
                f'super_attribute[{self.supatt}]':self.variante,
                'qty':'1',
                f'formatted_size_value[{self.supatt}]':self.sizescelta,
                'g-recaptcha-response':captcha,
                'token':captcha,
                'signature':signature
            }
        else:
            payload = {
                'product':self.pid,
                'selected_configurable_option':'',			
                'related_product':'',		
                'item':self.pid,
                'form_key':self.formkey,
                f'super_attribute[{self.supatt}]':self.variante,
                'qty':'1',
                f'formatted_size_value[{self.supatt}]':self.sizescelta,
                'signature':signature
            }
        self.warn("Adding to cart...")
        self.oos = False
        while True:
            try:
                r = self.s.post(
                    self.atc_url, 
                    headers=headers,
                    data=payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    try:
                        l = r.json()
                        if type(l) == list and len(l) == 0:
                            self.success(f"{self.title} size {self.sizescelta} added to cart!")
                            carted = carted + 1
                            self.bar()
                            break
                        else:
                            self.warn("Size wasn't added, probably OOS")
                            self.oos = True
                            break
                    except:
                        self.warn("Size wasn't added, probably OOS")
                        self.oos = True
                        break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                else:
                    self.error(f'Error adding to cart: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception adding to cart: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception adding to cart: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue 
        if self.oos:
            self.s.cookies.clear()
            self.build_proxy()
            self.scrapeproduct()
        else:
            self.guest()

    def guest(self):
        self.warn("Getting checkout page...")
        while True:
            try:
                r = self.s.get(
                    f'https://www.titoloshop.com/{self.domain}/checkout/',
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.entity = r.text.split('a":{"entity_id":"')[1].split('"')[0]
                    self.success("Succesfully got checkout page!")
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                else:
                    self.error(f'Error getting checkout page: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting checkout page: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting checkout page: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue 
        self.billing()

    def billing(self):
        self.warn("Getting shipping rates...")
        headers = {
            'Accept':'*/*',
            'content-type': 'application/json',
            'x-requested-with': 'XMLHttpRequest',
            'referer': f'https://www.titoloshop.com/{self.domain}/checkout/'
        }
        self.s.headers.update(headers)
        payload = {
            "address": {
                "street": [self.address, self.housenumber],
                "city": self.city,
                "region": self.region,
                "country_id": self.country,
                "postcode": self.zipcode,
                "firstname": self.name,
                "lastname": self.surname,
                "telephone": self.phone
            }
        }
        while True:
            try:
                r = self.s.post(
                    f"https://www.titoloshop.com/{self.domain}/rest/{self.domain}/V1/guest-carts/{self.entity}/estimate-shipping-methods", 
                    json=payload, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.carrier_code = r.text.split('carrier_code":"')[1].split('"')[0]
                    self.method_code = r.text.split('method_code":"')[1].split('"')[0]
                    self.success("Succesfully got shipping rates!")
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                else:
                    self.error(f'Error getting shipping rates: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting shipping rates: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting shipping rates: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue 
        self.shipping()

    def shipping(self):
        self.warn("Submitting shipping info...")    
        payload = {
            "addressInformation": {
                "shipping_address": {
                    "countryId": self.country,
                    "regionCode": "",
                    "region": self.region,
                    "street": [self.address, self.housenumber],
                    "telephone": self.phone,
                    "postcode": self.zipcode,
                    "city": self.city,
                    "firstname": self.name,
                    "lastname": self.surname
                },
                "billing_address": {
                    "countryId": self.country,
                    "regionCode": "",
                    "region": self.region,
                    "street": [self.address, self.housenumber],
                    "telephone": self.phone,
                    "postcode": self.zipcode,
                    "city": self.city,
                    "firstname": self.name,
                    "lastname": self.surname,
                    "saveInAddressBook": None
                },
                "shipping_method_code": self.method_code,
                "shipping_carrier_code": self.carrier_code,
                "extension_attributes": {}
            }
        }
        while True:
            try:
                r = self.s.post(
                    f"https://www.titoloshop.com/{self.domain}/rest/{self.domain}/V1/guest-carts/{self.entity}/shipping-information", 
                    json=payload, 
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    self.success("Succesfully submitted ship!")
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                else:
                    self.error(f'Error submitting ship: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception submitting ship: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting ship: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue 
        self.paypal()

    def paypal(self):
        self.warn("Submitting payment...")
        payload = {
            "cartId": self.entity,
            "billingAddress": {
                "countryId": self.country,
                "regionCode": "",
                "region": self.region,
                "street": [self.address, self.housenumber],
                "telephone": self.phone,
                "postcode": self.zipcode,
                "city": self.city,
                "firstname": self.name,
                "lastname": self.surname,
                "saveInAddressBook": None
            },
            "paymentMethod": {
                "method": "datatranscw_paypal",
                "po_number": None,
                "additional_data": {}
            },
            "email": self.mail
        }
        while True:
            try:
                r = self.s.post(
                    f"https://www.titoloshop.com/{self.domain}/rest/{self.domain}/V1/guest-carts/{self.entity}/payment-information", 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.numeroboh = r.text.split('"')[1]
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                elif r.status_code == 400:
                    self.error(f"Product went oos while checking out {r.text}, restarting...")
                    open(self.logs_path, 'a+').write(f'Product went oos while checking out: {r.text}\n')
                    failed = failed + 1
                    self.bar()
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.scrapeproduct()
                    break
                else:
                    self.error(f'Error submitting payment: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception submitting payment: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting payment: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.paypal2()

    def paypal2(self):
        global carted, checkoutnum, failed
        while True:
            try:
                x = self.s.post(
                    f'https://www.titoloshop.com/{self.domain}/rest/{self.domain}/V1/guest-carts/{self.entity}/datatranscw/checkout/authorize',
                    json={"orderId": self.numeroboh},
                    timeout = self.timeout
                )
                if x.status_code == 200:
                    l = x.text.replace('\\n','').replace('\\t','').replace('\\','').replace('-','').replace('_','')
                    self.modulename = l.split('datauppmodulename", "')[1].split('"')[0]
                    self.uppmoduleversion = l.split('datauppmoduleversion", "')[1].split('"')[0]
                    self.merchantid = l.split('datamerchantid", "')[1].split('"')[0]
                    self.amount = l.split('dataamount", "')[1].split('"')[0]
                    self.currency = l.split('datacurrency", "')[1].split('"')[0]
                    self.refno = l.split('datarefno", "')[1].split('"')[0]
                    self.successurl = l.split('datasuccessurl", "')[1].split('"')[0]
                    self.errorurl = l.split('dataerrorurl", "')[1].split('"')[0]
                    self.cancelurl = l.split('datacancelurl", "')[1].split('"')[0]
                    self.upreturn = l.split('datauppreturnmaskedcc", "')[1].split('"')[0]
                    self.languagee = l.split('datalanguage", "')[1].split('"')[0]
                    self.reqtype = l.split('datareqtype", "')[1].split('"')[0]
                    self.customerdetails = l.split('datauppcustomerdetails", "')[1].split('"')[0]
                    self.paytmentmethod = l.split('datapaymentmethod", "')[1].split('"')[0]
                    self.amto = l.split('datalamt0", "')[1].split('"')[0]
                    self.taxamto = l.split('dataltaxamt0", "')[1].split('"')[0]
                    self.nameo = l.split('datalname0", "')[1].split('"')[0]
                    self.numberoo = l.split('datalnumber0", "')[1].split('"')[0]
                    self.desco = l.split('dataldesc0", "')[1].split('"')[0]
                    self.shippingamt = l.split('datashippingamt", "')[1].split('"')[0]
                    self.itemamt = l.split('dataitemamt", "')[1].split('"')[0]
                    self.taxmat = l.split('datataxamt", "')[1].split('"')[0]
                    self.cwtransid = l.split('datacwdatatransid", "')[1].split('"')[0]
                    self.theme = l.split('datatheme", "')[1].split('"')[0]
                    self.sign = l.split('datasign", "')[1].split('"')[0]
                    break
                elif x.status_code >= 500 and x.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif x.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif x.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif x.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                elif x.status_code == 400:
                    self.error(f"Product went oos while checking out 2 {x.text}, restarting...")
                    open(self.logs_path, 'a+').write(f'Product went oos while checking out 2: {x.text}\n')
                    failed = failed + 1
                    self.bar()
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.scrapeproduct()
                    break
                else:
                    self.error(f'Error submitting payment 2: {x.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception submitting payment 2: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting payment 2: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.paypal3()

    def paypal3(self):
        self.warn("Getting paypal info...")
        hnew = {
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer':'https://www.titoloshop.com/'
        }
        self.s.headers.update(hnew)
        while True:
            try:
                r = self.s.get(
                    f'https://pay.datatrans.com/upp/jsp/upStart.jsp?uppModuleName={self.modulename}&uppModuleVersion={self.uppmoduleversion}&merchantId={self.merchantid}&amount={self.amount}&currency={self.currency}&refno={self.refno}&successUrl={self.successurl}&errorUrl={self.errorurl}&cancelUrl={self.cancelurl}&uppReturnMaskedCC={self.upreturn}&language={self.languagee}&reqtype={self.reqtype}&uppCustomerName={self.name} {self.surname}&uppCustomerFirstName={self.name}&uppCustomerLastName={self.surname}&uppCustomerStreet={self.address} {self.housenumber}&uppCustomerCity={self.city}&uppCustomerCountry={self.country}&uppCustomerZipCode={self.zipcode}&uppCustomerEmail={self.mail}&uppCustomerDetails={self.customerdetails}&paymentmethod={self.paytmentmethod}&L_AMT0={self.amto}&L_TAXAMT0={self.taxamto}&L_NAME0={self.nameo}&L_Number0={self.numberoo}&L_Desc0={self.desco}&SHIPPINGAMT={self.shippingamt}&ITEMAMT={self.itemamt}&TAXAMT={self.taxmat}&cwDataTransId={self.cwtransid}&theme={self.theme}&sign={self.sign}&version=2.0.0',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.datatranstrxid = r.text.split('datatransTrxId" value="')[1].split('"')[0]
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                elif r.status_code == 400:
                    self.error(f"Product went oos while checking out 3 {r.text}, restarting...")
                    open(self.logs_path, 'a+').write(f'Product went oos while checking out 3: {r.text}\n')
                    failed = failed + 1
                    self.bar()
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.scrapeproduct()
                    break
                else:
                    self.error(f'Error submitting payment 3: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception submitting payment 3: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting payment 3: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.paypal4()

    def paypal4(self):
        global carted, failed, checkoutnum 
        payloadfinale = {
            'datatransTrxId':self.datatranstrxid,
            'hiddenFrame':False,
            'uppScreenWidth':'999',
            'iframed':'',
            'browserUserAgent':self.s.headers['User-Agent'],
            'browserJavaEnabled':False,
            'browserLanguage':'en',
            'browserColorDepth':'24',
            'browserScreenHeight':'1080'
        }
        hfin = {
            'content-type': 'application/x-www-form-urlencoded',
            'Referer':f'https://pay.datatrans.com/upp/jsp/upStart.jsp?uppModuleName={self.modulename}&uppModuleVersion={self.uppmoduleversion}&merchantId={self.merchantid}&amount={self.amount}&currency={self.currency}&refno={self.refno}&successUrl={self.successurl}&errorUrl={self.errorurl}&cancelUrl={self.cancelurl}&uppReturnMaskedCC={self.upreturn}&language={self.languagee}&reqtype={self.reqtype}&uppCustomerName={self.name} {self.surname}&uppCustomerFirstName={self.name}&uppCustomerLastName={self.surname}&uppCustomerStreet={self.address} {self.housenumber}&uppCustomerCity={self.city}&uppCustomerCountry={self.country}&uppCustomerZipCode={self.zipcode}&uppCustomerEmail={self.mail}&uppCustomerDetails={self.customerdetails}&paymentmethod={self.paytmentmethod}&L_AMT0={self.amto}&L_TAXAMT0={self.taxamto}&L_NAME0={self.nameo}&L_Number0={self.numberoo}&L_Desc0={self.desco}&SHIPPINGAMT={self.shippingamt}&ITEMAMT={self.itemamt}&TAXAMT={self.taxmat}&cwDataTransId={self.cwtransid}&theme={self.theme}&sign={self.sign}&version=2.0.0'
        }
        self.s.headers.update(hfin)
        self.warn("Opening paypal...")
        while True:
            try:
                r = self.s.post(
                    'https://pay.datatrans.com/upp/jsp/upStart_1.jsp',
                    data = payloadfinale,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    tok = r.text.split("name='token' value='")[1].split("'")[0]
                    self.ppurl = f'https://www.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token={tok}&useraction=commit'
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    self.success("Succesfully checked out!")
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error("Proxy banned, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 429:
                    self.error("Rate limit, retrying...")
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  
                elif r.status_code == 400:
                    self.error(f"Product went oos while opening paypal {r.text}, restarting...")
                    open(self.logs_path, 'a+').write(f'Product went oos while opening paypal: {r.text}\n')
                    failed = failed + 1
                    self.bar()
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.scrapeproduct()
                    break
                else:
                    self.error(f'Error opening paypal: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception opening paypal: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception opening paypal: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.pass_cookies()

    def pass_cookies(self):
        try:
            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]     
            try:
                for element in cookies:
                    if 'cf_chl' in element['name']:
                        cookies.remove(element)
            except:
                pass
            try:
                for cookie in cookies:
                    if cookie['domain'][0] == ".":
                        cookie['url'] = cookie['domain'][1:]
                    else:
                        cookie['url'] = cookie['domain']
                    cookie['url'] = "https://"+cookie['url']
            except:
                pass
            cookies = json.dumps(cookies)
            cookieStr = urllib.parse.quote(base64.b64encode(bytes(cookies, 'utf-8')).decode())
            if not cookieStr: return
            url = urllib.parse.quote(base64.b64encode(bytes(self.ppurl, 'utf-8')).decode())
            self.token = f"https://api.phoenixbot.io/exploits/?cookie={cookieStr}&redirect={url}"     
            self.token2 = f"https://api.phoenixbot.io/mobile/?cookie={cookieStr}&redirect={url}"
            apiurl2 = "http://tinyurl.com/api-create.php?url="
            tinyasdurl2 = urllib.request.urlopen(apiurl2 + self.token2).read()
            self.expToken2 = str(tinyasdurl2.decode("utf-8"))
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
            else:
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), "success.csv")   
            if len(self.token) > 1999:
                try:
                    apiurl = "http://tinyurl.com/api-create.php?url="
                    tinyasdurl = urllib.request.urlopen(apiurl + self.token).read()
                    self.expToken = str(tinyasdurl.decode("utf-8"))
                except:
                    self.expToken = "https://twitter.com/PhoenixAI0"
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'TITOLO','SIZE':f'{self.sizeprint}','PAYLINK':f'{self.token}','PRODUCT':f'{self.pid}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'TITOLO','SIZE':f'{self.sizeprint}','PAYLINK':f'{self.token}','PRODUCT':f'{self.pid}'})
            self.webhook()
        except Exception as e: 
            self.error(f'Exception error while passing cookies {e.__class__.__name__}, retrying...') 
            open(self.logs_path, 'a+').write(f'Exception passing cookies {e}\n')
            sys.exit(1)
            return None

    def webhook(self):
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**TITOLO**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizeprint, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'PAYPAL', inline = False)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False) 
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.pubblic()

    def pubblic(self):
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**TITOLO**', value = f"[LINK]({self.link})", inline = True)     
            embed.add_embed_field(name='**SIZE**', value = self.sizeprint, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'PAYPAL', inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
            except:
                pass