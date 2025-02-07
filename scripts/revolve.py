import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from autosolveclient.autosolve import AutoSolve
import copy
from datetime import datetime
import traceback
from mods.errorHandler import errorHandler
import traceback
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

HANDLER = errorHandler(__file__)
urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

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

carted = 0
checkoutnum = 0
failed = 0

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

UNIQUE_ID = int(time.time() * 1000) * 2**random.randint(10,16)
AUTO_SOLVE = None
CAPTCHA_TOKENS = []
CAPTCHA = None

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
    CAPTCHA = config['captcha']['revolve']
    config['2captcha']
    config['capmonster']
    config['anticaptcha']
except:
    error(f'Your config file isn\'t updated. Please download the latest one.')
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

class REVOLVE():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
        

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'revolve/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "revolve/proxies.txt")
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
            sys.exit(1)

        self.s = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
                },
                captcha=self.captcha,
                doubleDown=False,
                requestPostHook=self.injection
        )
        
        self.link = row['PID']
        self.size = row['SIZE']
        self.mail = row['EMAIL']
        self.password = row['PASSWORD']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.country = row['COUNTRY']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.zipcode = row['ZIP']
        self.city = row['CITY']
        self.region = row['STATE']
        self.phone = row['PHONE NUMBER']
        self.card = row['CARD NUMBER']
        self.month = row["EXP MONTH"]
        self.year = row['EXP YEAR']
        self.cvc = row['CVC']
        self.discount = row['DISCOUNT']
        self.payment = row['PAYMENT']

        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.delay = int(config["delay"])
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        self.discord = DISCORD_ID
        self.timeout = 120
        self.build_proxy()
        self.bar()

        if self.country == 'United States':
            self.nation = 'US'
        self.nation = self.country
        self.islogin = False

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

        self.warn('Starting tasks...')
        
        if self.password != '':
            self.login()
        else:
            self.getprod() 


#####################################################################################################################  - CHOOSE PROXY


    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [REVOLVE] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [REVOLVE] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [REVOLVE] - {text}'
        warn(message)

    def build_proxy(self):
        cookies = self.s.cookies
        self.s = cloudscraper.create_scraper(
            captcha=self.captcha,
            browser={
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
            },
            requestPostHook=self.injection
        )
        self.s.cookies = cookies
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

    def bar(self):
        if machineOS.lower() == 'windows':
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running REVOLVE | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running REVOLVE | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')



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
                return CF_2(session,response,key="a6077c8d-a15f-4293-93b7-c854d3a2a3e6",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.warn('Solving Cloudflare v2')
                return CF_2(session,response,key="a6077c8d-a15f-4293-93b7-c854d3a2a3e6",captcha=True,debug=False).solve() 
            else:
                return response

    def solve_v2(self, url):
        self.warn('Solving captcha...')
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.recaptcha(sitekey='6LcHm8MUAAAAAMJUJOsQjIApHVu3LSajpGJ7DW3M', url=url)
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
                        "websiteKey": "6LcHm8MUAAAAAMJUJOsQjIApHVu3LSajpGJ7DW3M"
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
                    self.success('Captcha solved!')
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
                    "siteKey" : "6LcHm8MUAAAAAMJUJOsQjIApHVu3LSajpGJ7DW3M", 
                    "version" : '0'
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

    def captchax(self):
        self.warn('Challenge found, solving...')
        
        headers = {
            'Accept':'*/*',
            'X-Requested-With':'XMLHttpRequest',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.s.headers.update(headers)
        while True:
            try:
                url = self.captcha_url
                captcha = self.solve_v2(url)
                payload = {
                    'source':'BROWSING_BY_IP',
                    'siteType': 'VISIBLE_FOR_BOTS',
                    'key':self.valuekey,
                    'response':captcha
                }
                r = self.s.post(
                    'https://www.revolve.com/r/ajax/VerifyHuman.jsp',
                    data =payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    if r_json['success'] == True:
                        break
                    else:
                        self.error('Captcha Failed, retrying...')
                        continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while solving challenge: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while solving challenge: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        return self.success('Succesfully solved challenge!')
            
    def checkcart(self):
        self.warn('Checking cart...')
        ischecked = False
        hhh = {
            'Accept':'*/*',
            'X-Requested-With':'XMLHttpRequest',
        }
        self.s.headers.update(hhh)
        while True:
            try:
                r = self.s.post(
                    'https://www.revolve.com/r/ajax/GetCartRailContent.jsp', 
                    data = '',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    r_json = json.loads(b.text)
                    if r_json['success'] == True:
                        if r_json['data']['itemsCount'] == 1:
                            ischecked = True
                            break 

                        else:
                            self.error('Cart empty, restarting')
                            break

                    else:
                        self.error('Cart check failed, retrying...')
                        time.sleep(self.delay)
                        self.build_proxy()
                        continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while checking cart: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while checking cart: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        if ischecked:
            return self.warn('Succesfully checked cart, proceding...')
        else:
            self.s.cookies.clear()
            if self.password != '':
                self.login()
            else:
                self.getprod() 

    def checkcart2(self):
        self.warn('Checking cart...')
        porcodiooo = {
            'Accept':'*/*',
            'X-Requested-With':'XMLHttpRequest',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.s.headers.update(porcodiooo)
        while True:
            try:
                b = self.s.post(
                    'https://www.revolve.com/r/ajax/GetCartRailContent.jsp', 
                    data = '', 
                    timeout = self.timeout
                )
                if b.status_code == 200:
                    r_json = json.loads(b.text)
                    if r_json['success'] == True:
                        if r_json['data']['itemsCount'] != 0:
                            ciao = r_json['data']['cartRailItems']
                            self.warn('Clearing cart...')
                            for i in ciao:
                                a = i['code']
                                b = i['size']
                                head = {
                                    'Referer':'https://www.revolve.com/r/ShoppingBag.jsp?navsrc=header'
                                }
                                self.s.headers.update(head)
                                payload = {
                                    'code':a,
                                    'size':b
                                }
                                t = self.s.post(
                                    'https://www.revolve.com/r/ajax/RemoveFromBag.jsp', 
                                    data = payload, 
                                    timeout = self.timeout
                                )
                                clearc = json.loads(t.text)
                                if clearc['success'] != True:
                                    continue
                            break
                        else:
                            return self.warn('Cart is empty, starting...')
                    else:
                        self.error('Cart check failed, restarting...')
                        time.sleep(self.delay)
                        continue
                elif b.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif b.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif b.status_code >= 500 and b.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while checking cart: {b.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while checking cart: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        return self.success('Cart cleared!')

    def login(self):
        self.warn('Attempting login...')
        payload = {
            'email':self.mail,
            'pw':self.password,
            'd':'Womens',
            'favcode':'',
            'favbrand':'',
            'g_recaptcha_response':'',
            'karmir_luys':True,
            'rememberMe':True,
            'isCheckout':False,
            'saveForLater':False
        }
        headers = {
            'Accept':'*/*',
            'X-Requested-With':'XMLHttpRequest',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.s.headers.update(headers)
        while True:
            try:
                o = self.s.get(
                    'https://www.revolve.com/r/ShoppingBag.jsp', 
                    timeout = self.timtout
                )
                if o.status_code == 200:
                    r = self.s.post(
                        'https://www.revolve.com/r/ajax/SignIn.jsp',
                        data = payload,
                        timeout = self.timeout
                    )
                    if r.status_code == 200:
                        r_json = json.loads(r.text)
                        if r_json['success'] == True:
                            self.success('Succesfully logged in!')
                            self.islogin = True
                            break
                        else:
                            self.error('Login failed, check your account')
                            sys.exit(1)
                            break
                    elif r.status_code == 403:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 429:
                        self.error('Rate limit, retryng...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    elif r.status_code >= 500 and r.status_code <= 600:
                        self.warn('Site dead, retrying...')
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error(f'Error while attempting login: {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        self.build_proxy()
                        continue
                elif o.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif o.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif o.status_code >= 500 and o.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while attempting login: {o.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while attempting login: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.checkcart2()
        self.getprod()

    def getprod(self):
        self.warn('Getting product page...')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        }
        self.s.headers.update(headers)
        now = datetime.now()
        timestamp = str(datetime.timestamp(now)).split('.')[0]
        while True:
            try:
                r = self.s.get(
                    f'https://www.revolveclothing.com/phoenix/dp/{self.link}/?ph={timestamp}', 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'sitekey' in r.text:
                        self.captcha_url = r.url
                        self.valuekey = r.text.split(" key: '")[1].split("'")[0]
                        self.captchax()
                        continue
                    soup = bs(r.text, features='lxml')
                    try:
                        self.title = soup.find('meta',{'property':'wanelo:product:name'})['content']
                    except:
                        self.warn('Product is OOS, retrying...')
                        time.sleep(self.delay)
                        continue
                    try:
                        b = soup.find("div", {"class":"u-inline-block"})
                        self.price = b.find("span", {"class":"price__retail"}).text
                        pass
                    except:
                        self.warn('Product is OOS, retrying...')
                        time.sleep(self.delay)
                        continue
                    c = soup.find("div", {"id":"js-primary-slideshow__pager"})
                    self.image = c.find("a", {"href":"#js-primary-slideshow__image"})["data-image"]
                    size1 = soup.find("div", {"class":"product-sizes product-sections"})
                    size2 = size1.find("ul", {"id":"size-ul"})
                    size3 = size2.find_all("input", {"class":"js-size-option size-options__radio size-clickable"})
                    if "isWomens" in r.text:
                        self.sesso = "Womens"
                        self.ismens = "false"
                    else:
                        self.sesso = "Mens"
                        self.ismens = "true"
                    self.csfr = r.text.split("csrfHash = '")[1].split("'")[0]
                    self.sizes = []
                    for element in size3:
                        if element['data-qty'] != "0":
                            self.sizes.append(element['value'])
                    if len(self.sizes) < 1:
                        self.warn(f'{self.title} is OOS, retrying...')
                        time.sleep(self.delay)
                        continue
                    if self.size != "RANDOM":
                        if self.size not in self.sizes:
                            self.warn(f'{self.title} size {self.size} is OOS, retrying...')
                            time.sleep(self.delay)
                            continue
                        else:
                            self.warn(f'{self.title} size {self.size} in stock!')
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
                            if str(self.size1) <= str(self.sizes) <= str(self.size2):
                                self.sizerange.append(self.sizes)
                        if len(self.sizerange) < 1:
                            self.warn(f'{self.title} size {self.size} OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        else:
                            break
                    else:
                        self.success(f'{self.title} in stock! Sizes: {self.sizes}')
                        break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting product page: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting product page: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.atc()

    def atc(self):
        global failed , carted, checkoutnum
        self.warn('Adding to cart...')
        headers = {
            'Accept': '*/*',
            'Referer': self.link,
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.s.headers.update(headers)
        if self.size == "RANDOM":
            self.sizescelta = random.choice(self.sizes)
        elif "," in self.size or "-" in self.size:
            self.sizescelta = random.choice(self.sizerange)
        else:
            self.sizescelta = self.size
        while True:
            try:
                payload = {
                    'colorSelect': self.link,
                    'serialNumber': '',
                    'sizeSelect': self.sizescelta,
                    'sectionURL': 'https://www.revolve.com/shoes/br/3f40a9/?navsrc=main',
                    'sessionID': '',
                    'count': '',
                    'csrfHash': self.csfr,
                    'isMens': self.ismens,
                    'd': self.sesso,
                    'src': 'addtobag',
                    'srcType': '',
                    'qvclick': '-1',
                    'contextReferrer': 'https://www.revolve.com/shoes/br/3f40a9/?navsrc=main',
                    'addedFromFavorite': False,
                    'fitItemSizes': ''
                }
                r = self.s.post(
                    "https://www.revolve.com/r/ajax/AddItemToBag.jsp", 
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:   
                    if 'sitekey' in r.text:
                        self.captcha_url = r.url
                        self.valuekey = r.text.split(" key: '")[1].split("'")[0]
                        self.captcha()
                        continue
                    else:
                        r_json = json.loads(r.text)
                        if r_json['success'] == True:
                            self.success('Successfully added to cart!')
                            carted = carted + 1
                            self.bar()
                            break
                        else:
                            self.checkcart()
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while adding to cart: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        if self.discount != '':
            self.promo()
        if self.islogin == True:
            self.creditcard()
        else:
            self.ship()

    def promo(self):
        self.warn('Applying discount code...')
        headers = {
            'Accept':'*/*',
            'X-Requested-With':'XMLHttpRequest',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.s.headers.update(headers)
        payload = {
            'promo':self.discount,
            'scope':''
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.revolve.com/r/ajax/ApplyPromoCode.jsp',
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'sitekey' in r.text:
                        self.captcha_url = r.url
                        self.valuekey = r.text.split(" key: '")[1].split("'")[0]
                        self.captcha()
                        continue
                    else:
                        r_json = json.loads(r.text)
                        if r_json['success'] == True:
                            break
                        else:
                            self.error('Invalid discount code, task stopped!')
                            sys.exit(1)
                            break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while applying discount code: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while applying discount code: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        return self.success('Succesfully applied discount code')

    def ship(self):
        self.warn('Submitting shipping...')
        headers = {
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'https://www.revolve.com/r/DeliveryOptions.jsp'
        }
        self.s.headers.update(headers)
        data = {
            'name': f'{self.name} {self.surname}',
            'street': self.address,
            'street2': self.address2,
            'city': self.city,
            'state': self.region,
            'zip': self.zipcode,
            'country': self.nation,
            'telephone': self.phone,
            'deliveryCode': '',
            'email': self.mail,
            'pw': '',
            'verifypw': '',
            'create': False,
            'news': False,
            'autofilled': '',
            'internationalID': '',
            'dateOfBirth': '',
            'karmir_luys': False,
            'g_recaptcha_response': ''
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.revolve.com/r/ajax/SaveDeliveryOptions.jsp", 
                    data = data, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'sitekey' in r.text:
                        self.captcha_url = r.url
                        self.valuekey = r.text.split(" key: '")[1].split("'")[0]
                        self.captcha()
                        continue
                    else:
                        r_json = json.loads(r.text)
                        if r_json['success'] == True:
                            self.success('Succesfully submitted shipping!')
                            break
                        else:
                            self.checkcart()
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting ship: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting ship: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.rates()

    def rates(self):  
        self.warn('Getting shipping rates...')
        headers = {
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'https://www.revolve.com/r/ShippingOptions.jsp?create=false'
        }
        self.s.headers.update(headers)
        data = {
            'wrapType': '',
            'to': '',
            'from': '',
            'msg': ''
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.revolve.com/r/ajax/SaveGiftOption.jsp", 
                    data = data, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'sitekey' in r.text:
                        self.captcha_url = r.url
                        self.valuekey = r.text.split(" key: '")[1].split("'")[0]
                        self.captcha()
                        continue
                    else:
                        r_json = json.loads(r.text)
                        if r_json['success'] == True:
                            self.success('Succesfully got shipping rates!')
                            break
                        else:
                            self.checkcart()
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting shipping rates: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting shipping rates: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        if self.payment == "CC":
            self.creditcard()
        else:
            self.pay()

    def pay(self):
        global failed , carted, checkoutnum
        self.warn('Getting paypal link...')
        headers = {
            'Accept': 'application/json',
            'Referer': 'https://www.revolve.com/r/PaymentOptions.jsp'
        }
        self.s.headers.update(headers)
        while True:
            try:
                r = self.s.post("https://www.revolve.com/r/expresscheckout.jsp?js=true&paymentType=PayPal|GB", headers = headers)
                if r.status_code == 200 and "token" in r.text:
                    token = r.text.split('token":"')[1].split('"')[0]
                    self.ppurl = f"https://www.paypal.com/webscr?cmd=_express-checkout&useraction=commit&token={token}"
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    self.success('Successfully checked out!')
                    break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting paypal: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting paypal: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.pass_cookies()

    def creditcard(self):
        self.warn('Submitting credit card...')
        headers = {
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'https://www.revolve.com/r/PaymentOptions.jsp'
        }
        self.s.headers.update(headers)
        cardnu1 = self.card[:4]
        cardnu2 = self.card[4:8]
        cardnu3 = self.card[8:12]
        cardnu4 = self.card[-4:]
        self.cardnumber = f'{cardnu1} {cardnu2} {cardnu3} {cardnu4}'
        self.year2 = self.year[-2:]
        data = {
            'credit': '',
            'id': '-1',
            'number': self.cardnumber,
            'code': self.cvc,
            'expMonth': self.month,
            'expYear': self.year2,
            'useShip': True,
            'name': '',
            'street': '',
            'street2': '',
            'city': '',
            'state': '',
            'zip': '',
            'country': 'Italy',
            'telephone': '',
            'dateOfBirth': '',
            'internationalID': '',
            'installmentOption': '',
            'installmentOptionText': '',
            'installmentOptionRate': '',
            'csrfHash': self.csfr
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.revolve.com/r/ajax/SavePaymentOptions.jsp", 
                    data = data, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'sitekey' in r.text:
                        self.captcha_url = r.url
                        self.valuekey = r.text.split(" key: '")[1].split("'")[0]
                        self.captcha()
                        continue
                    else:
                        r_json = json.loads(r.text)
                        if r_json['success'] == True:
                            self.success('Credit card submitted!')
                            break
                        else:
                            self.checkcart()
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting credit card: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting credit card: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.placeorder()

    def placeorder(self):
        self.declined = False
        global failed , carted, checkoutnum
        self.warn('Submitting order...')
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://www.revolve.com/r/ReviewConfirm.jsp'
        }
        self.s.headers.update(headers)
        data = {
            'csrfHash':  self.csfr,
            'cccode_value': '',
            'payType': 'std'
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.revolve.com/r/ProcessingOrder.jsp", 
                    data = data,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'Referer': 'https://www.revolve.com/r/ProcessingOrder.jsp'
                    }
                    self.s.headers.update(headers)
                    data = {
                    "cccode_value": ""
                    }
                    r = self.s.post(
                        "https://www.revolve.com/r/ajax/SubmitOrder.jsp", 
                        data = data, 
                        timeout = self.timeout
                    )
                    if r.status_code == 200:
                        if 'sitekey' in r.text:
                            self.captcha_url = r.url
                            self.valuekey = r.text.split(" key: '")[1].split("'")[0]
                            self.captcha()
                            continue
                        else:
                            r_json = json.loads(r.text)
                            if r_json['success'] == False:
                                self.declined = True
                                self.error('Payment declined!')
                                failed = failed + 1
                                self.bar()
                                break
                            if r_json['success'] == True:
                                msg0 = r_json['msg0']
                                msg1 = msg0.replace(',','')
                                payload = {
                                    'successful':True,
                                    'invoice':'',
                                    'invoice':msg1
                                }
                                heade = {
                                    'Content-Type':'application/x-www-form-urlencoded',
                                    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                                    'Referer':'https://www.revolve.com/r/ProcessingOrder.jsp',
                                }
                                self.s.headers.update(heade)
                                z = self.s.post(
                                    'https://www.revolve.com/r/OrderSummary.jsp', 
                                    data = payload, 
                                    timeout = self.timeout
                                )
                                if z.status_code == 200:
                                    if "Riepilogo dell'ordine" in z.text:
                                        self.success('Succesfully checked out!')
                                        checkoutnum = checkoutnum + 1
                                        self.bar()
                                        break
                                    elif 'your order has been placed' in z.text:
                                        self.success('Succesfully checked out!')
                                        checkoutnum = checkoutnum + 1
                                        self.bar()
                                        break
                                    elif 'Your order confirmation' in z.text:
                                        self.success('Succesfully checked out!')
                                        checkoutnum = checkoutnum + 1
                                        self.bar()
                                        break
                                    elif 'Your order is almost complete!' in z.text:
                                        self.warn('Processing order...')
                                        continue
                                    else:
                                        self.error('Checkout failed, while processing order')
                                        self.build_proxy()
                                        self.checkcart()
                                        break
                                elif z.status_code == 403:
                                    self.error('Proxy banned, retrying...')
                                    self.build_proxy()
                                    time.sleep(self.delay)
                                    continue
                                elif z.status_code == 429:
                                    self.error('Rate limit, retryng...')
                                    self.build_proxy()
                                    time.sleep(self.delay)
                                    continue
                                elif z.status_code >= 500 and z.status_code <= 600:
                                    self.warn('Site dead, retrying...')
                                    time.sleep(self.delay)
                                    continue
                                else:
                                    self.error(f'Error while submitting order: {z.status_code}, retrying...')
                                    time.sleep(self.delay)
                                    self.build_proxy()
                                    continue
                    elif r.status_code == 403:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 429:
                        self.error('Rate limit, retryng...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    elif r.status_code >= 500 and r.status_code <= 600:
                        self.warn('Site dead, retrying...')
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error(f'Error while submitting order: {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        self.build_proxy()
                        continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retryng...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting order: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting order: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        if self.declined:
            self.decline()
        self.SuccessCC()

    def pass_cookies(self):
        try:
            cookieStr = ""
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
                    writer.writerow({'SITE':'REVOLVE','SIZE':f'{self.sizescelta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'REVOLVE','SIZE':f'{self.sizescelta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            self.SuccessPP()
        except Exception as e: 
            self.error(f'Error passing cookies: {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.pass_cookies()


    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**REVOLVE**', value = self.title, inline = False)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"{self.link}", inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.image)  
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
                sys.exit(1)
            except:
                sys.exit(1)
        except:
            pass

    def SuccessPP(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**REVOLVE**', value = self.title, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
            embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass

    def SuccessCC(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', color = 0x715aff)
            embed.add_embed_field(name=f'**REVOLVE**', value = self.title, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
            embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass

    def decline(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Payment Declined', color = 15746887)
        embed.add_embed_field(name=f'**REVOLVE**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.set_thumbnail(url = self.image)   
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        sys.exit(1)
