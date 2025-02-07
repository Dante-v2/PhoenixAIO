import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, pytz, copy, traceback
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from os import urandom
from urllib import parse
from autosolveclient.autosolve import AutoSolve
import helheim

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

failed = 0
checkoutnum = 0
carted = 0

def perform_request(self, method, url, *args, **kwargs):
    if "proxies" in kwargs or "proxy"  in kwargs:
        return super(cloudscraper.CloudScraper, self).request(method, url, *args, **kwargs)
    else:
        return super(cloudscraper.CloudScraper, self).request(method, url, *args, **kwargs,proxies=self.proxies)
cloudscraper.CloudScraper.perform_request = perform_request

API_URL = 'https://api.tls.expert/v1/chrome/'

auth = '6EjsxvuY5vMa5dtKwyU4AzyryWUXVLD5pcbj2g3wtXRSVv36'

@staticmethod
def is_New_Captcha_Challenge(resp):
    try:
        return (
                cloudscraper.CloudScraper.is_Captcha_Challenge(resp)
                and re.search(
                    r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/?\w?/?\w?/orchestrate/captcha/v1"',
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
                    r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/?\w?/?\w?/orchestrate/jsch/v1"',
                    resp.text,
                    re.M | re.S
                )
                and re.search(r'window._cf_chl_opt', resp.text, re.M | re.S)
        )
    except AttributeError:
        pass

    return False
cloudscraper.CloudScraper.is_New_IUAM_Challenge = is_New_IUAM_Challenge

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
    CAPTCHA = config['captcha']['sns']
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

class NAKED():

    def __init__(self, row, webhook, version, threadID, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'naked/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "naked/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()

        except Exception as e:
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
            self.error('2Captcha or AntiCaptcha needed. Stopping task.')
            time.sleep(5)
            sys.exit(1)

        self.s = cloudscraper.create_scraper(
            browser= {
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
            },
            captcha='vanaheim',
            doubleDown=False,
            requestPostHook=self.injection
        )
        
        self.link = row['LINK'] 
        self.linkweb = self.link
        self.size = row['SIZE']
        self.country = row['COUNTRY']
        self.mail = row['MAIL']
        self.password = row['PASSWORD']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.city = row['CITY']
        self.zipcode = row['ZIPCODE']
        self.phone = row['PHONE']
        self.payment = row['PAYMENT']
        self.mode = row['MODE']
        self.cardnumber = row['CARDNUMBER']
        self.expmonth = row['EXPMONTH']
        self.expyear = row['EXPYEAR']
        self.cvv = row['CVV']
        self.discountcode = row['PROMOCODE']
        self.version = version
        self.webhook_url = webhook
        self.discord = DISCORD_ID
        if self.mode == 'FAST':
            self.warn('Setting up FAST mode...')
            self.harvestedTokens = []
            threading.Thread(target=self.handleHarvester).start()
            for i in range(8):
                threading.Thread(target=self.harvest_v3, args=([self.link, i])).start()

        #self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        self.listsuccess = ["https://discord.com/api/webhooks/773665832554987550/o6FJp62HUV5p7DzMGyMg1B1fVG9ADfpgu-OU6Ztm89DWefNQHc_ei2D44RoN2479WjHZ"]

        self.timeout = 120
        self.balance = balancefunc()
        self.threadID = '%03d' % threadID
        self.bar()
        self.build_proxy()
        self.delay = int(config["delay"])

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

        self.warn('Task started!')
        if self.password != '':
            self.loginget()
        else:
            self.Monitor()

    def error(self, text):
        message = f'[TASK {self.threadID}] - [NAKED] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [NAKED] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [NAKED] - {text}'
        warn(message)

    def build_proxy(self):
        cookies = self.s.cookies
        self.s = cloudscraper.create_scraper(
            captcha='vanaheim',
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
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - NAKED Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - NAKED Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')

    def injection(self, session, response):
        try:
            if helheim.isChallenge(session, response):
                self.warn('Solving Cloudflare v2')
                return helheim.solve(session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                self.warn('Solving Cloudflare v2 api 2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.warn('Solving Cloudflare v2 api 2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
            else:
                return response

    def handleHarvester(self):
        while True:
            for token in copy.deepcopy(self.harvestedTokens):
                if int(time.time()) + 5 > token['expiry']:
                    self.harvestedTokens.remove(token)
                    threading.Thread(target=self.harvest_v3, args=([self.link, 0]))
            time.sleep(5)

    def solve_v3(self, url):
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.recaptcha(sitekey='6LeNqBUUAAAAAFbhC-CS22rwzkZjr_g4vMmqD_qo', url=url)
                code = result['code']
                return code
            except Exception as e:
                self.error(f' Exception solving captcha: {e}')
                return self.solve_v3(url)
        elif CAPTCHA == 'capmonster':
            try:
                captchaurl = "https://api.capmonster.cloud/createTask"
                payload = {
                    "clientKey": config['capmonster'],
                    "task": {
                        "type":"NoCaptchaTaskProxyless",
                        "websiteURL": url,
                        "websiteKey":"6LeNqBUUAAAAAFbhC-CS22rwzkZjr_g4vMmqD_qo"
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
                    return self.solve_v3(url)
            except Exception as e:
                self.error(f'Exception solving captcha: {e}')
                return self.solve_v3(url)
        elif CAPTCHA == 'autosolve':
            try:
                AUTO_SOLVE.send_token_request({
                    "taskId"  : f'{self.threadID}-{UNIQUE_ID}', 
                    "url"     : url, 
                    "siteKey" : "6LeNqBUUAAAAAFbhC-CS22rwzkZjr_g4vMmqD_qo", 
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
                                return self.solve_v3(url)
                    time.sleep(1)
            except Exception as e:
                self.error(f'An error occured solving captcha with Autosolve: {e}')
                return self.solve_v3(url)

    def harvest_v3(self, url, i):
        time.sleep(5 * i)
        code = self.solve_v3(url)
        self.success(f'Token harvested. Available tokens: {len(self.harvestedTokens) + 1}')
        return self.harvestedTokens.append({'token': code, 'expiry': int(time.time()) + 90})

    def loginget(self):
        self.warn('Getting login page...')
        while True:
            try:
                r = self.s.get(
                    'https://www.nakedcph.com/en/auth/view',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.logintoken = r.text.split('_AntiCsrfToken" value="')[1].split('"')[0]
                    self.success('Succesfully got login page!')
                    break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    if self.dk == False:
                        self.cookies()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error while getting login page:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting login page: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.loginpost()

    def loginpost(self):
        self.warn('Solving captcha...')
        code = self.solve_v3('https://www.nakedcph.com/en/auth/view')
        payload = {
            '_AntiCsrfToken':self.logintoken,
            'email':self.mail,
            'password':self.password,
            'g-recaptcha-response':code,
            'action':'login'
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.nakedcph.com/en/auth/submit',
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    if r_json['Response']['Success'] == True:
                        self.success('Succesfully logged in!')
                        break
                    else:
                        print(r_json)
                        time.sleep(5000)
                        break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    if self.dk == False:
                        self.cookies()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error while logging in:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while logging in: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.Monitor()

    def cookies(self):
        self.fail = False
        self.warn('Setting up cookies...')
        payload = {
            'countryCode': 'DK',
            'redirectUrl': 'https://www.nakedcph.com/en/settings'
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.nakedcph.com/en/customer/setregion?countryCode=DK&redirectUrl=https%3a%2f%2fwww.nakedcph.com%2fen%2fsettings',
                    data = payload,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 302 and r.headers['location'] == 'https://www.nakedcph.com/en/settings':
                    self.dk = True
                    break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    self.fail = True
                    break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.fail = True
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    self.fail = True
                    break
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.fail = True
                    break
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.fail = True
                    break
                else:
                    self.error(f'Unkown Error getting cookies:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.fail = True
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.fail = True
                break
            except Exception as e:
                self.error(f'Exception while getting cookies: {e}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                self.fail = True
                break
        if self.fail:
            return self.error('Failed getting cookies, restarting...')
        else:
            return self.success('Succesfully got cookies!')

    def Monitor(self):
        self.dk = False
        self.warn('Getting product page...')
        while True:
            try:     
                r = self.s.get(
                    self.link,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.text = r.text
                    soup = bs(r.text, features='lxml')
                    self.title = r.text.split("product.name = '")[1].split("'")[0]
                    try:
                        check = r.text.split('class="countdown countdown-lg" data-date="countdown')[1]
                        self.warn(f'{self.title} not dropped yet, monitoring...')
                        time.sleep(self.delay)
                        continue
                    except:
                        pass 
                    try:
                        self.csfr = self.s.cookies["AntiCsrfToken"]
                    except:
                        self.csfr = r.text.split('AntiCsrfToken" value="')[1].split('"')[0]
                    self.price = r.text.split('<meta itemprop="price" content="')[1].split('"')[0]
                    self.stockcheck = r.text.split("product.inStock = '")[1].split("'")[0]
                    if self.stockcheck == 'no':
                        check = r.text.split('role="alert">')[1]
                        self.warn(f'{self.title} oos, monitoring...')
                        time.sleep(self.delay)
                        continue
                    elif self.stockcheck == 'yes':
                        self.success(f'{self.title} in stock, Getting sizes...')
                        chs = soup.find('select',{'id':'product-form-select'})('option')
                        variant = []
                        size = []
                        for i in chs:
                            if 'Choose size' not in i.text:
                                if 'disabled=""' not in str(i):
                                    variant.append(i['value'])
                                    size.append(i.text.strip().replace(',','.'))
                        tot = zip(size, variant)
                        connect = list(tot)
                        self.sizerange = []
                        if self.size == "RANDOM":
                            scelta = random.choice(connect)
                            ciao0 = scelta[0]
                            self.sizeinstock = "".join(ciao0)
                            ciao1 = scelta[1]
                            self.idreal = "".join(ciao1)
                            self.warn(f'Adding to cart size {self.sizeinstock}')
                            break
                        elif '-' in self.size:
                            self.size1 = float(self.size.split('-')[0])
                            self.size2 = float(self.size.split('-')[1])
                            for x in connect:
                                if self.size1 <= float(x[0]) <= self.size2:
                                    self.sizerange.append(x[0])        
                            self.sizerandom = random.choice(self.sizerange)
                            self.warn(f'Adding to cart size {self.sizerandom}')
                            self.sizeinstock = self.sizerandom
                            for x in connect:
                                if self.sizerandom == x[0]:
                                    ciao1 = x[1]
                                    self.idreal = "".join(ciao1)
                            break
                        elif ',' in self.size:
                            self.size1 = float(self.size.split(',')[0])
                            self.size2 = float(self.size.split(',')[1])
                            for x in connect:
                                if self.size1 <= float(x[0]) <= self.size2:
                                    self.sizerange.append(x)        
                            self.sizerandom = random.choice(self.sizerange)
                            self.warn(f'Adding to cart size {self.sizerandom}')
                            self.sizeinstock = self.sizerandom
                            for x in connect:
                                if self.sizerandom == x[0]:
                                    ciao1 = x[1]
                                    self.idreal = "".join(ciao1)
                            break
                        else:
                            for Traian in connect:
                                if self.size not in size:
                                    self.warn('Size unavailable, retrying...')
                                    time.sleep(self.delay)
                                    continue
                                elif self.size == Traian[0]:
                                    ciao0 = Traian[0]
                                    self.sizeinstock = "".join(ciao0)
                                    ciao1 = Traian[1]
                                    self.idreal = "".join(ciao1)
                            self.warn(f'Adding to cart size {ciao0}')
                            break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    if self.dk == False:
                        self.cookies()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error getting product page:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting product page: {e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.Atc()            

    #def getimage(self):
    #    self.warn('Getting session...')
    #    headers = {
    #        'Accept':'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    #        'referer':self.link
    #    }
    #    self.s.headers.update(headers)
    #    while True:
    #        try:
    #            r = self.s.get(
    #                f'https://www.sneakersnstuff.com/productimages/{self.zio}.png',
    #                timeout = self.timeout
    #            )
    #            if r.status_code == 200:
    #                break
    #            elif r.status_code == 429:
    #                self.s.cookies.clear()
    #                self.build_proxy()
    #                self.error('Rate limit, retrying...')
    #                continue
    #            elif r.status_code == 403:
    #                self.error('Proxy banned, retrying...')
    #                self.s.cookies.clear()
    #                self.build_proxy()
    #                continue
    #            elif r.status_code >= 500 and r.status_code <= 600:
    #                self.warn('Site down, retrying...')
    #                time.sleep(self.delay)
    #                continue
    #            elif r.status_code == 404:
    #                self.warn('Page not loaded, retrying...')
    #                time.sleep(self.delay)
    #                continue
    #            elif r.status_code == 1020:
    #                self.warn('Cf error 1020, rotating...')
    #                self.s.cookies.clear()
    #                self.build_proxy()
    #                continue
    #            else:
    #                self.error(f'Unkown Error getting session:{r.status_code}, retrying...')
    #                self.s.cookies.clear()
    #                self.build_proxy()
    #                continue
    #        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    #            self.error('Connection error, retrying...')
    #            self.build_proxy()
    #            continue
    #        except Exception as e:
    #            self.error(f'Exception while getting session: {e.__class__.__name__}, retrying...')
    #            time.sleep(self.delay)
    #            continue
    #    return self.success('Succesfully got session!')

    def Atc(self):
        global carted, failed, checkoutnum
        self.recursive = True
        headers = {
            'Accept':'*/*',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest'
        }
        self.s.headers.update(headers)
        while True:
            try:
                if 'g-recaptcha' in self.text:
                    self.warn('Captcha found...')
                    if self.mode == 'FAST':
                        if len(self.harvestedTokens) == 0:
                            self.warn('Solving captcha...')
                            code = self.solve_v3(self.link)
                        else:
                            self.success('Using harvested token')
                            code = self.harvestedTokens.pop(0)['token']
                    else:
                        self.warn('Solving captcha...')
                        code = self.solve_v3(self.link)
                    self.success('Captcha solved!')
                    payload = {'_AntiCsrfToken':self.csfr,'g-recaptcha-response': code,'id':self.idreal,'partial':'ajax-cart'}
                    r = self.s.post(
                        'https://www.nakedcph.com/en/cart/add', 
                        data = payload, 
                        timeout = self.timeout
                    )
                    if r.status_code == 200:
                        if "empty" in r.text:
                            self.warn('Cart empty, retrying...')
                            time.sleep(self.delay)
                            self.recursive = False
                            break
                        self.success('Successfully added to cart!')
                        carted = carted + 1
                        self.bar()
                        self.pngstate = self.s.cookies["png.state"]
                        break
                    elif r.status_code == 409:
                        self.warn(f'{self.title} OOS during atc, retrying...')
                        time.sleep(self.delay)
                        self.recursive = False
                        break
                    elif r.status_code == 500:
                        self.warn(f'{self.title} OOS during atc, retrying...')
                        time.sleep(self.delay)
                        self.recursive = False
                        break
                    elif r.status_code == 429:
                        self.s.cookies.clear()
                        self.build_proxy()
                        self.error('Rate limit, retrying...')
                        continue
                    elif r.status_code == 403:
                        self.error('Proxy banned, retrying...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        continue
                    elif r.status_code >= 500 and r.status_code <= 600:
                        self.warn('Site down, retrying...')
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 404:
                        self.warn('Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 1020:
                        self.warn('Cf error 1020, rotating...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        continue
                    else:
                        self.error(f'Unkown Error adding to cart:{r.status_code}, retrying...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        continue
                else:
                    self.warn('No captcha found...')
                    payload = {'_AntiCsrfToken':self.csfr,'id':self.idreal,'partial':'ajax-cart'}
                    payload  = parse.urlencode(payload)
                    r = self.s.post(
                        'https://www.nakedcph.com/en/cart/add',
                        data = payload,
                        timeout = self.timeout
                    )
                    if r.status_code == 200:
                        if "empty" in r.text:
                            self.warn('Cart empty, retrying...')
                            time.sleep(self.delay)
                            self.recursive = False
                            break
                        self.success('Successfully added to cart!')
                        carted = carted + 1
                        self.bar()
                        self.pngstate = self.s.cookies["png.state"]
                        break
                    elif r.status_code == 409:
                        self.warn(f'{self.title} OOS during atc, retrying...')
                        time.sleep(self.delay)
                        self.recursive = False
                        break
                    elif r.status_code == 500:
                        self.warn(f'{self.title} OOS during atc, retrying...')
                        time.sleep(self.delay)
                        self.recursive = False
                        break
                    elif r.status_code == 429:
                        self.s.cookies.clear()
                        self.build_proxy()
                        self.error('Rate limit, retrying...')
                        continue
                    elif r.status_code == 403:
                        self.error('Proxy banned, retrying...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        continue
                    elif r.status_code >= 500 and r.status_code <= 600:
                        self.warn('Site down, retrying...')
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 404:
                        self.warn('Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 1020:
                        self.warn('Cf error 1020, rotating...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        continue
                    else:
                        self.error(f'Unkown Error adding to cart:{r.status_code}, retrying...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while adding to cart: {e}, retrying...')
                time.sleep(self.delay)
                self.recursive = False
                break
        if self.recursive:
            self.passcookies2()
            self.checkout1()
        else:
            self.Monitor()

    def checkout1(self):
        headers = {
            'referer':'https://www.nakedcph.com/en/cart/view'
        }
        self.s.headers.update(headers)
        self.warn('Getting checkout page...')
        while True:
            try:       
                r = self.s.get(
                    f"https://www.nakedcph.com/en/customer/setregion?countryCode={self.country}&redirectUrl=/en/cart/view", 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:        
                        if cookie['name'] == 'AntiCsrfToken':
                            self.csfrtoken = cookie['value']
                    self.success('Successfully got checkout page!')
                    break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error getting checkout page:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting checkout page: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.rates()

    def rates(self):
        self.warn('Getting shipping rates...')
        while True:
            try:       
                r = self.s.get(
                    f"https://www.nakedcph.com/en/webshipper/render?partial=shipping-quotes&zip=&countryCode={self.country}&address=&skip_layout=1", 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.shippingmethod = r.text.split('value="')[1].split('"')[0]
                    self.success('Successfully got shipping rates!')
                    break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error getting shipping rates:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting shipping rates: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.checkout2()

    def checkout2(self):
        headerz = {
            'x-anticsrftoken':self.csfr
        }
        self.s.headers.update(headerz)
        self.warn('Submitting email...')
        payload = {
            'emailAddress': self.mail
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.nakedcph.com/en/customer/checkemailavailability", 
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.success('Email submitted!')
                    break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error submitting email:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting email: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        if self.discountcode != "":
            self.discount()
        else:
            self.checkout3()

    def discount(self):
        self.warn('Submitting discount...')
        payload = {
            'checkoutcode':self.discountcode,
            'partial':'ajax-cart'
        }
        try:
            r = self.s.post(
                f"https://www.nakedcph.com/en/cart/setcheckoutcode", 
                data = payload, 
                timeout = self.timeout
            )
            if r.status_code == 200:
                discount = r.text.split('"discountPercent":')[1].split(',')[0]
                if discount != "0.0":
                    self.success('Promocode submitted, proceding...')  
                    self.pngstate = self.s.cookies["png.state"]
                    self.checkout3()
                else:
                    self.warn('Promo code not available, proceding...')
                    self.checkout3()
            else:
                self.error(f'Error submitting promo code: {r.status_code}, proceding anyway...')
                self.checkout3()
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            self.error('Connection error, retrying...')
            self.build_proxy()
            self.checkout3()
        except Exception as e:
            self.error(f'Exception while submitting promo code: {e.__class__.__name__}, retrying...')
            time.sleep(self.delay)
            self.checkout3()

    def checkout3(self):
        self.warn('Submitting payment...')
        if self.payment == "CC":
            self.paynum = "7"
        else:
            self.paynum = "5"
        payload = {
            'id':self.paynum,
            'partial':'ajax-cart'
        }
        while True:
            try:            
                r = self.s.post(
                    'https://www.nakedcph.com/en/cart/setpaymentmethod', 
                    data = payload, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'Your shopping bag is empty' in r.text:
                        self.warn('Bag empty. restarting...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        self.Monitor()
                        break
                    elif 'This item is no longer available' in r.text:
                        self.warn('Item no longer reserved, restarting...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        self.Monitor()
                        break
                    else:
                        self.success('Succesfully submitted payment!')    
                        break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error submitting payment:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting payment: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        if self.payment == "PP":
            self.pp()
        elif self.payment == "CC":
            self.cc()
        else:
            self.error('Wrong payment on csv, using paypal...')
            self.pp()

    def pp(self):
        self.warn('Placing order...')
        payload = {
            '_AntiCsrfToken':self.csfrtoken,
            'country':self.country,
            'emailAddress':self.mail,
            'postalCodeQuery':'',
            'firstName':self.name,
            'lastName':self.surname,
            'addressLine2':self.address,
            'addressLine3':self.address2,
            'postalCode':self.zipcode,
            'city':self.city,
            'phoneNumber':self.phone,
            'toggle-billing-address':'on',
            'billingProvince':'-1',
            'billingProvince':'-1',
            'webshipperQuoteMethod':self.shippingmethod,
            'txvariant':'card',
            'termsAccepted':'true'
        }
        while True:
            try:         
                r = self.s.post(
                    "https://www.nakedcph.com/en/cart/process", 
                    data = payload, 
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 302:
                    self.success('Successfully checked out!')
                    self.ppurl = r.headers['Location']
                    break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error submitting order:{r.status_code}, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting order: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.passcookies()



    def gnerateCardDataJsoncard(self, pan):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "number": pan,
            "generationtime": generation_time
        }

    def encryptWithAesKey(self, aes_key, nonce, plaintext):
        cipher = AESCCM(aes_key, tag_length=8)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        return ciphertext

    def decodeAdyenPublicKey(self, encoded_public_key):
        backend = default_backend()
        key_components = encoded_public_key.split("|")
        public_number = rsa.RSAPublicNumbers(int(key_components[0], 16), int(key_components[1], 16))
        return backend.load_rsa_public_numbers(public_number)

    def encryptWithPublicKey(self, public_key, plaintext):
        ciphertext = public_key.encrypt(plaintext, padding.PKCS1v15())
        return ciphertext

    def maincard(self, pan, key):

        plainCardData = self.gnerateCardDataJsoncard(
            pan=pan
        )

        cardDataJsonString = json.dumps(plainCardData, sort_keys=True)
        aesKey = AESCCM.generate_key(256)
        nonce = urandom(12)
        encryptedCardData = self.encryptWithAesKey(aesKey, nonce, bytes(cardDataJsonString, encoding='utf8'))
        encryptedCardComponent = nonce + encryptedCardData
        adyenPublicKey = key
        publicKey = self.decodeAdyenPublicKey(adyenPublicKey)
        encryptedAesKey = self.encryptWithPublicKey(publicKey, aesKey)
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_18", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))

        return encryptedAesData

    def gnerateCardDataJsonmonth(self, expiry_month):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "expiryMonth": expiry_month,
            "generationtime": generation_time
        }

    def mainmonth(self, expiry_month, key):

        plainCardData = self.gnerateCardDataJsonmonth(
            expiry_month=expiry_month
        )

        cardDataJsonString = json.dumps(plainCardData, sort_keys=True)
        aesKey = AESCCM.generate_key(256)
        nonce = urandom(12)
        encryptedCardData = self.encryptWithAesKey(aesKey, nonce, bytes(cardDataJsonString, encoding='utf8'))
        encryptedCardComponent = nonce + encryptedCardData
        adyenPublicKey = key
        publicKey = self.decodeAdyenPublicKey(adyenPublicKey)
        encryptedAesKey = self.encryptWithPublicKey(publicKey, aesKey)
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_18", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))

        return encryptedAesData


    def gnerateCardDataJsonyear(self, expiry_year):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "expiryYear": expiry_year,
            "generationtime": generation_time
        }


    def mainyear(self, expiry_year, key):

        plainCardData = self.gnerateCardDataJsonyear(
            expiry_year=expiry_year
        )

        cardDataJsonString = json.dumps(plainCardData, sort_keys=True)
        aesKey = AESCCM.generate_key(256)
        nonce = urandom(12)
        encryptedCardData = self.encryptWithAesKey(aesKey, nonce, bytes(cardDataJsonString, encoding='utf8'))
        encryptedCardComponent = nonce + encryptedCardData
        adyenPublicKey = key
        publicKey = self.decodeAdyenPublicKey(adyenPublicKey)
        encryptedAesKey = self.encryptWithPublicKey(publicKey, aesKey)
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_18", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))

        return encryptedAesData

    def gnerateCardDataJsoncvv(self, cvc):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "generationtime": generation_time,
            "cvc": cvc
        }


    def maincvv(self, cvc, key):

        plainCardData = self.gnerateCardDataJsoncvv(
            cvc=cvc,
        )

        cardDataJsonString = json.dumps(plainCardData, sort_keys=True)
        aesKey = AESCCM.generate_key(256)
        nonce = urandom(12)
        encryptedCardData = self.encryptWithAesKey(aesKey, nonce, bytes(cardDataJsonString, encoding='utf8'))
        encryptedCardComponent = nonce + encryptedCardData
        adyenPublicKey = key
        publicKey = self.decodeAdyenPublicKey(adyenPublicKey)
        encryptedAesKey = self.encryptWithPublicKey(publicKey, aesKey)
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_18", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))

        return encryptedAesData


    def cc(self):
        self.warn('Placing order with creditcard...')
        payload = {
            '_AntiCsrfToken':self.csfrtoken,
            'country':self.country,
            'emailAddress':self.mail,
            'postalCodeQuery':'',
            'firstName':self.name,
            'lastName':self.surname,
            'addressLine2':self.address,
            'addressLine3':self.address2,
            'postalCode':self.zipcode,
            'city':self.city,
            'phoneNumber':self.phone,
            'toggle-billing-address':'on',
            'webshipperQuoteMethod':self.shippingmethod,
            'txvariant':'card',
            'termsAccepted':'true',
            'encryptedExpiryMonth': self.mainmonth(expiry_month = self.expmonth,key = "10001|83D0E61238A154C5DE9E5369811B9BAC4E9D34027C981041A016A9607E028D30A225DFD7E2DA1BA405C403A6DD26DBCDC1E6FC086FAF584230B4A9BE29100C9B70B1BAE2AD470DE3CD70E11C2D0A5901F593EC2ED3D20993E5FDED27ED09303E3CACA3575DAB50290896ABD0504370B6764E3B25C7B84B2B455A6522E052E6A81E19FF95D3E230698D57D38EE93100EFB1276C1713345D126B74C2553E828B02C77FEA618EB14AD1FDF8B2CA208BD8FF1A233ACAE0F26BF46DC661AE62C3C7AC831DB1FE77678753BE372B101B2B01E77A4FAE07C3A48A3ECD8AAC0274C2565F85551AD8313277C29CEA1C7B60F9F09CA37308097ABCE5735A66AE0DA66B13CB"),
            'encryptedExpiryYear': self.mainyear(expiry_year = self.expyear,key = "10001|83D0E61238A154C5DE9E5369811B9BAC4E9D34027C981041A016A9607E028D30A225DFD7E2DA1BA405C403A6DD26DBCDC1E6FC086FAF584230B4A9BE29100C9B70B1BAE2AD470DE3CD70E11C2D0A5901F593EC2ED3D20993E5FDED27ED09303E3CACA3575DAB50290896ABD0504370B6764E3B25C7B84B2B455A6522E052E6A81E19FF95D3E230698D57D38EE93100EFB1276C1713345D126B74C2553E828B02C77FEA618EB14AD1FDF8B2CA208BD8FF1A233ACAE0F26BF46DC661AE62C3C7AC831DB1FE77678753BE372B101B2B01E77A4FAE07C3A48A3ECD8AAC0274C2565F85551AD8313277C29CEA1C7B60F9F09CA37308097ABCE5735A66AE0DA66B13CB"),
            'encryptedSecurityCode': self.maincvv(cvc = self.cvv,key = "10001|83D0E61238A154C5DE9E5369811B9BAC4E9D34027C981041A016A9607E028D30A225DFD7E2DA1BA405C403A6DD26DBCDC1E6FC086FAF584230B4A9BE29100C9B70B1BAE2AD470DE3CD70E11C2D0A5901F593EC2ED3D20993E5FDED27ED09303E3CACA3575DAB50290896ABD0504370B6764E3B25C7B84B2B455A6522E052E6A81E19FF95D3E230698D57D38EE93100EFB1276C1713345D126B74C2553E828B02C77FEA618EB14AD1FDF8B2CA208BD8FF1A233ACAE0F26BF46DC661AE62C3C7AC831DB1FE77678753BE372B101B2B01E77A4FAE07C3A48A3ECD8AAC0274C2565F85551AD8313277C29CEA1C7B60F9F09CA37308097ABCE5735A66AE0DA66B13CB"),
            'encryptedCardNumber': self.maincard(pan = self.cardnumber,key = "10001|83D0E61238A154C5DE9E5369811B9BAC4E9D34027C981041A016A9607E028D30A225DFD7E2DA1BA405C403A6DD26DBCDC1E6FC086FAF584230B4A9BE29100C9B70B1BAE2AD470DE3CD70E11C2D0A5901F593EC2ED3D20993E5FDED27ED09303E3CACA3575DAB50290896ABD0504370B6764E3B25C7B84B2B455A6522E052E6A81E19FF95D3E230698D57D38EE93100EFB1276C1713345D126B74C2553E828B02C77FEA618EB14AD1FDF8B2CA208BD8FF1A233ACAE0F26BF46DC661AE62C3C7AC831DB1FE77678753BE372B101B2B01E77A4FAE07C3A48A3ECD8AAC0274C2565F85551AD8313277C29CEA1C7B60F9F09CA37308097ABCE5735A66AE0DA66B13CB")
        }
        while True:
            try:            
                r = self.s.post(
                    "https://www.nakedcph.com/en/cart/process", 
                    data = payload, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'Your shopping bag is empty' in r.text:
                        self.warn('Bag empty. restarting...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        self.Monitor()
                        break
                    elif 'This item is no longer available' in r.text:
                        self.warn('Item no longer reserved, restarting...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        self.Monitor()
                        break
                    elif r.url == "https://www.nakedcph.com/en/cart/view":   
                        self.declined()
                        sys.exit()
                        break
                    else:
                        self.success('Successfully checked out!')
                        self.ppurl = r.url
                        break
                elif r.status_code == 400:
                    self.error(f'Payment declined: {r.text}')
                    self.declined()
                    break
                elif r.status_code == 429:
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.error('Rate limit, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 1020:
                    self.warn('Cf error 1020, rotating...')
                    self.s.cookies.clear()
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown Error submitting order:{r.status_code}, retrying...')
                    self.declined()
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting order: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.passcookies()

    def passcookies(self):
        try:
            cookieStr = ""
            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
            try:
                for element in cookies:
                    if 'cf_chl' in element['name']:
                        cookies.remove(element)
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
                    if len(self.sizeinstock) > 2:
                        self.sizeinstock = f'{self.sizeinstock[:2]}+'
                    writer.writerow({'SITE':'NAKED','SIZE':f'{self.sizeinstock}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    if len(self.sizeinstock) > 2:
                        self.sizeinstock = f'{self.sizeinstock[:2]}+'
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'NAKED','SIZE':f'{self.sizeinstock}','PAYLINK':f'{self.token}','PRODUCT':str(f'{self.title}')})
            if self.payment == "CC":
                self.webhookcard()
            else:
                self.SuccessPP()
        except Exception as e: 
            self.error(f'Exception while passing checkout cookies: {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.passcookies()

    def passcookies2(self):
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
            url = urllib.parse.quote(base64.b64encode(bytes("https://www.nakedcph.com//", 'utf-8')).decode())
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
                    if len(self.sizeinstock) > 2:
                        self.sizeinstock = f'{self.sizeinstock[:2]}+'
                    writer.writerow({'SITE':'NAKED','SIZE':f'{self.sizeinstock}','PAYLINK':f'{self.token}','PRODUCT':str(f'{self.title}')})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    if len(self.sizeinstock) > 2:
                        self.sizeinstock = f'{self.sizeinstock[:2]}+'
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'NAKED','SIZE':f'{self.sizeinstock}','PAYLINK':f'{self.token}','PRODUCT':str(f'{self.title}')})
            self.webhook()

        except Exception as e:
            self.error(f'Exception while passing cart cookies: {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.passcookies2()

    def webhook(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Cart waiting for you! Click here', url = self.expToken, color = 16426522)
        embed.add_embed_field(name='**NAKED**', value = f'{self.title}', inline = True)
        embed.add_embed_field(name='**SIZE**', value = f'{self.sizeinstock}', inline = True)
        embed.add_embed_field(name='**PRICE**', value = f'{self.price}', inline = False)
        embed.add_embed_field(name='**TOKEN**', value = f'||{self.pngstate}||', inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook()
    
    def Pubblic_Webhook(self):
        webhook = DiscordWebhook(url= random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name='**NAKED**', value = f'{self.title}', inline = False)
        embed.add_embed_field(name='**PRODUCT**', value = f'[LINK]({self.linkweb})', inline = True)
        embed.add_embed_field(name='**SIZE**', value = f'{self.sizeinstock}', inline = False)
        embed.add_embed_field(name='Delay', value = self.delay, inline = True)
        embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        return self.success('Cart sent, proceding with aco...') 

    def SuccessPP(self):
        global carted, failed, checkoutnum
        checkoutnum = checkoutnum + 1
        self.bar()
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**NAKED**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizeinstock, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = True)
        embed.add_embed_field(name='**PRICE**', value = f'{self.price}', inline = False)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = True)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook2()

    def Pubblic_Webhook2(self):
        webhook = DiscordWebhook(url= random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name='**NAKED**', value = f'{self.title}', inline = False)
        embed.add_embed_field(name='**PRODUCT**', value = f'[LINK]({self.linkweb})', inline = True)
        embed.add_embed_field(name='**SIZE**', value = f'{self.sizeinstock}', inline = False)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
        embed.add_embed_field(name='Delay', value = self.delay, inline = True)
        embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        try:
            playsound('checkout.wav')
            sys.exit(1)
        except:
            sys.exit(1)

    def webhookcard(self):
        global carted, failed, checkoutnum
        checkoutnum = checkoutnum + 1
        self.bar()
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Checked out!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**NAKED**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizeinstock, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = True)
        embed.add_embed_field(name='**PRICE**', value = f'{self.price}', inline = False)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = True)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook2()


    def declined(self):
        global carted, failed, checkoutnum
        failed = failed + 1
        self.bar()
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Card declined!', color = 15746887)
        embed.add_embed_field(name=f'**NAKED**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizeinstock, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = True)
        embed.add_embed_field(name='**PRICE**', value = f'{self.price}', inline = False)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        sys.exit()