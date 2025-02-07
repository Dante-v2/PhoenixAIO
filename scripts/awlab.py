import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, string, pytz, js2py
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from cryptography.hazmat.backends import default_backend
from os import urandom
from autosolveclient.autosolve import AutoSolve
import traceback
from helheim.exceptions import HelheimRuntimeError
from mods.errorHandler import errorHandler
import traceback
import helheim
import copy

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

HANDLER = errorHandler(__file__)
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
    CAPTCHA = config['captcha']['awlab']
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

class AWLAB():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'awlab/exceptions.log')
        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'Awlab/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "Awlab/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()

        except:
            error("Failed To Read Proxies File - using no proxies")
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
                requestPostHook=self.injection
        )

        helheim.wokou(self.s)

        self.name = row['FIRST NAME']
        self.surname = row['LAST NAME']
        self.email = row['EMAIL']
        self.address = row['ADDRESS LINE 1']
        self.prefix = row['PREFIX']
        self.phone = row['PHONE NUMBER']
        self.city = row['CITY']
        self.zip = row['ZIP']
        self.state = row['STATE']
        self.country = row['COUNTRY']
        self.pidmonitor = row['PID']
        self.payment = row['PAYMENT']
        self.mode = row['MODE']
        self.card = row['CARD NUMBER']
        self.month = row["EXP MONTH"]
        self.year = row['EXP YEAR']
        self.cvc = row['CVC']
        self.discount = row['DISCOUNT']

        self.discord = DISCORD_ID
    
        self.twoCaptcha = str(config['2captcha'])

        try:
            if self.name.upper() == "RANDOM":
                self.name = names.get_first_name(gender='male')
            if self.surname.upper() == "RANDOM":
                self.surname = names.get_last_name()
            if self.phone.upper() == "RANDOM":
                self.phone = str("0"+str(random.randint(7400000000,7999990000)))
            if self.email[:6].upper() == "RANDOM":
                self.email = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.email.split("@")[1]).lower()
        except Exception as e:
            error(e)
        
        self.delay = int(config['delay'])
        self.timeout = 120
          
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.balance = balancefunc()
        self.threadID = '%03d' % i
        self.webhook_url = webhook
        self.version = version
        self.monster = config['capmonster']

        if self.country == 'IT':
            self.domain = "www.aw-lab.com"
            self.lang = "en_IT"
            self.site_region = "Sites-awlab-it-Site"
            self.guest_text = "Checkout come ospite"
            self.proced = 'Procedi al pagamento'
            self.ref1 = 'spedizione'
            self.fatt = 'fatturazione'
            self.applico = "APPLICA"
            self.cart = 'carrello'
            self.checklink = 'https://www.aw-lab.com/fatturazione'

        elif self.country == 'ES':
            self.domain = "es.aw-lab.com"
            self.lang = "en_ES"
            self.site_region = "Sites-awlab-es-Site"
            self.guest_text = "Realiza el pedido sin registrarte"
            self.proced = 'Ir a la caja'
            self.fatt = 'billing'
            self.ref1 = 'shipping'
            self.applico = "aplicar"
            self.cart = 'cart'
            self.checklink = 'https://es.aw-lab.com/billing'

        elif self.country in ('GB', 'UK', 'DE', 'NL', 'FR', 'PT', 'AT', 'BE', 'CZ', 'DK', 'HU', 'LU', 'PL', 'SK', 'SL'):
            self.domain = "en.aw-lab.com"
            self.lang = "en_GB"
            self.ref1 = 'shipping'
            self.site_region = "Sites-awlab-en-Site"
            self.guest_text = "Checkout as guest"
            self.proced = 'Proceed to Checkout'
            self.fatt = 'billing'
            self.applico = "Apply"
            self.cart = 'cart'
            self.checklink = 'https://en.aw-lab.com/billing'

        self.build_proxy()
        
        if self.payment == 'CAD' or self.payment == 'COD':
            self.payment = 'CASH_ON_DELIVERY'
        elif self.payment == 'PP':
            self.payment = 'PayPal'
        elif self.payment == 'CC':
            self.payment = 'CREDIT_CARD'
        else:
            self.error('Payment not valid, check csv!')
            time.sleep(10)
            sys.exit(1)

        self.atc_url = f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/Cart-AddProduct?format=ajaxd'
        self.token_url = f'https://{self.domain}/login?original=%2Faccount'
        self.guestmode_url = f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/COCustomer-LoginForm'
        self.ship_url = f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/COShipping-SingleShipping'
        self.checkout_url = f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/COBilling-Billing'
        self.clearcart_url = f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/Cart-SubmitForm?format=ajax'

        self.bar()

        self.warn('Task started!')
        self.tokenn()

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [AWLAB] [{self.pidmonitor}] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [AWLAB] [{self.pidmonitor}] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [AWLAB] [{self.pidmonitor}] - {text}'
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
        self.headers = {
            'Host': f'{self.domain}',
            'Referer': f'https://www.{self.domain}/'
        }

        self.s.headers.update(self.headers)
        self.s.cookies = cookies
        del self.s.cookies['datadome']
        if self.all_proxies == [] or not self.all_proxies:
            return None
        else:
            self.px = random.choice(self.all_proxies)
            splitted = self.px.split(':')
            self.porta = splitted[1]
            self.logan = splitted[2]
            self.possward = splitted[3]
            self.addbvbv = splitted[0]
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

    def solve_v2(self, url):
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.recaptcha(sitekey='6Lf7htIZAAAAAKVu_e4Hyg3nhCXfVh2tlQbOjzYT', url=url)
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
                        "websiteKey": "6Lf7htIZAAAAAKVu_e4Hyg3nhCXfVh2tlQbOjzYT"
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
                    "siteKey" : "6Lf7htIZAAAAAKVu_e4Hyg3nhCXfVh2tlQbOjzYT", 
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

    def get_ddCaptchaChallenge(self):

        try:

            self.warn('Parsing challenge...')

            js_script = """
            const navigator = {
                userAgent: 'user_agent',
                language: 'singleLangHere',
                languages: 'langListHere'
            }

            ddExecuteCaptchaChallenge = function(r, t) {
                function e(r, t, e) {
                    this.seed = r, this.currentNumber = r % t, this.offsetParameter = t, this.multiplier = e, this.currentNumber <= 0 && (this.currentNumber += t)
                }
                e.prototype.getNext = function() {
                    return this.currentNumber = this.multiplier * this.currentNumber % this.offsetParameter, this.currentNumber
                };
                for (var n = [function(r, t) {
                        var e = 26157,
                            n = 0;
                        if (s = "VEc5dmEybHVaeUJtYjNJZ1lTQnFiMkkvSUVOdmJuUmhZM1FnZFhNZ1lYUWdZWEJ3YkhsQVpHRjBZV1J2YldVdVkyOGdkMmwwYUNCMGFHVWdabTlzYkc5M2FXNW5JR052WkdVNklERTJOMlJ6YUdSb01ITnVhSE0", navigator.userAgent) {
                            for (var a = 0; a < s.length; a += 1 % Math.ceil(1 + 3.1425172 / navigator.userAgent.length)) n += s.charCodeAt(a).toString(2) | e ^ t;
                            return n
                        }
                        return s ^ t
                    }, function(r, t) {
                        for (var e = (navigator.userAgent.length << Math.max(r, 3)).toString(2), n = -42, a = 0; a < e.length; a++) n += e.charCodeAt(a) ^ t << a % 3;
                        return n
                    }, function(r, t) {
                        for (var e = 0, n = (navigator.language ? navigator.language.substr(0, 2) : void 0 !== navigator.languages ? navigator.languages[0].substr(0, 2) : "default").toLocaleLowerCase() + t, a = 0; a < n.length; a++) e = ((e = ((e += n.charCodeAt(a) << Math.min((a + t) % (1 + r), 2)) << 3) - e + n.charCodeAt(a)) & e) >> a;
                        return e
                    }], a = new e(function(r) {
                        for (var t = 126 ^ r.charCodeAt(0), e = 1; e < r.length; e++) t += (r.charCodeAt(e) * e ^ r.charCodeAt(e - 1)) >> e % 2;
                        return t
                    }(r), 1723, 7532), o = a.seed, u = 0; u < t; u++) {
                    o ^= (0, n[a.getNext() % n.length])(u, a.seed)
                }
                ddCaptchaChallenge = o
                return ddCaptchaChallenge
            }
            ddExecuteCaptchaChallenge("putCidHere", 10);
            """.replace("putCidHere",self.cid).replace("user_agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36") \
                .replace("singleLangHere", "en-US").replace("langListHere", "en-US,en;q=0.9,sr;q=0.8")

            self.result = js2py.eval_js(js_script)
            self.warn('Got challenge...')
            return self.result

        except Exception as e:
            print(e)

    def solvedd(self):
        try:
            captchalink = f"https://geo.captcha-delivery.com/captcha/?initialCid={self.initialcid}&hash={self.hsh}&t={self.t}&s={self.sss}&cid={self.cid}&referer={self.referer}"
            s = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            helheim.wokou(s)
            h = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fi;q=0.6',
                'Connection': 'keep-alive',
                'dnt': '1',
                'Host': 'geo.captcha-delivery.com',
                'Referer': 'https://www.aw-lab.com/',
                'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
                'sec-ch-ua-mobile': '?0',
                'Sec-Fetch-Dest': 'iframe',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Upgrade-Insecure-Requests': '1'
            }
            s.proxies = self.s.proxies
            r = s.get(captchalink, headers=h)
            open(f'awlab{int(time.time() * 1000)}.html', 'w+', encoding='utf-8').write(r.text)
            if r.status_code == 200:
                ciao = r.text
                try:
                    self.initialcid = ciao.split("&icid=' + encodeURIComponent('")[1].split("'")[0]
                    self.hsh = ciao.split("&hash=' + encodeURIComponent('")[1].split("'")[0]
                    self.ip = ciao.split("(IP ")[1].split(")")[0]
                except:
                    self.initialcid = ciao.split("initialCid=")[1].split('&')[0]
                    self.hsh = ciao.split("hash=")[1].split('&')[0]
                    self.ip = ciao.split("(IP ")[1].split(")")[0]
                self.warn('Solving captcha...')
                captchaurl = "https://api.capmonster.cloud/createTask"
                payload = {
                    "clientKey": self.monster,
                    "task":
                    {
                        "type":"NoCaptchaTask",
                        "websiteURL":f'https://{self.domain}/',
                        "websiteKey":"6LcSzk8bAAAAAOTkPCjprgWDMPzo_kgGC3E5Vn-T",
                        "proxyType":"http",
                        "proxyAddress":self.addbvbv,
                        "proxyPort":self.porta,
                        "proxyLogin":self.logan,
                        "proxyPassword":self.possward,
                        "userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
                    }
                }
                r = requests.post(captchaurl, json = payload)
                taskid = r.text.split('"taskId":')[1].split('}')[0]
                data = {
                    "clientKey": self.monster,
                    "taskId": taskid
                }
                r = requests.post("https://api.capmonster.cloud/getTaskResult", json = data)
                while not "ready" in r.text:
                    time.sleep(5)
                    r = requests.post("https://api.capmonster.cloud/getTaskResult", json = data)
                if "ready" in r.text:
                    self.success('Captcha solved!')
                    self.captcha = r.text.split('"gRecaptchaResponse":"')[1].split('"')[0]
                    h = {
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fi;q=0.6',
                        'Connection': 'keep-alive',
                        'dnt': '1',
                        'Host': 'geo.captcha-delivery.com',
                        'Referer': captchalink,
                        'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
                        'sec-ch-ua-mobile': '?0',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin',
                    }
                    self.get_ddCaptchaChallenge()
                    dd_url = 'https://geo.captcha-delivery.com/captcha/check?cid=' + self.cid + '&icid=' + self.initialcid +'&ccid=null&g-recaptcha-response=' + self.captcha +'&hash=' + self.hsh +'&ua=' + s.headers['User-Agent'] +'&referer=' + f'https://{self.domain}/on/demandware.store/{self.site_region}' +'&parent_url=' + f'https://{self.domain}/' + '&x-forwarded-for=&captchaChallenge=' + str(self.result) + '&s=' + str(self.sss)
                    r = s.get(dd_url, headers = h)
                    if r.status_code == 200:
                        jsondd = json.loads(r.text)
                        dd = jsondd['cookie']
                        dd = dd.split('datadome=')[1].split(';')[0]
                        self.cookie_obj = requests.cookies.create_cookie(domain=f".aw-lab.com",name='datadome',value=dd)
                        self.s.cookies.set_cookie(self.cookie_obj)
                        return self.success('Datadome done, proceeding...')
                    else:
                        self.build_proxy()
                        return self.error('Datadome failed, retrying...')
            elif r.status_code == 403:
                self.build_proxy()
                return self.error('Proxy banned, restarting...')
            else:
                self.error('Datadome failed, restarting...')
                self.build_proxy()
                return self.error('Datadome failed, restarting...')
        except Exception as e:
            self.build_proxy()
            open(self.logs_path, 'a+').write(f'{e}\n')
            return self.error(f'Datadome failed: {e}, retrying...')
            
    def random_char(self, y):
        return ''.join(random.choice(string.ascii_letters) for x in range(y))

    def bar(self):
        if machineOS.lower() == 'windows':
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running AW LAB | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running AW LAB | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

    def injection(self, session, response):
        self.bar()
        #try:
        if helheim.isChallenge(session, response):
            self.warn('Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response
        #except:
        #    if session.is_New_IUAM_Challenge(response):
        #        self.warn('Solving Cloudflare v2 api 2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
        #    elif session.is_New_Captcha_Challenge(response):
        #        self.warn('Solving Cloudflare v2 api 2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
        #    else:
        #        return response
        
    def tokenn(self):
        self.restockmode = False
        self.warn('Getting token...')
        try:
            r = self.s.get(
                self.token_url,
                timeout = self.timeout
            )
            if "geo.captcha" in r.text:
                self.warn('Datadome found, solving...')
                self.referer = r.url
                if "t':'fe" in r.text:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()           
                    time.sleep(self.delay)
                    self.tokenn()
            if r.status_code == 200:
                cftokenhtml = bs(r.text, features='lxml')
                self.cftoken = cftokenhtml.find(attrs={'name': 'csrf_token'})['value']
                self.success('Successfully got token!')
                if self.mode == 'RESTOCK':
                    self.restockmode = True
                    self.preparing()
                else:
                    self.monitor()
            else:
                self.error('Error getting token, retrying...')
                self.build_proxy()
                self.tokenn()
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            self.error('Connection error, retrying...')
            self.build_proxy()
            self.tokenn()
        except Exception as e:
            self.error(f'Unknown error while getting token: {e.__class__.__name__}, retrying...')
            open(self.logs_path, 'a+').write(f'{e}\n')
            self.build_proxy()
            self.tokenn()
            
    def preparing(self):
        self.warn('Preparing session...') 
        while True:
            try:
                r = self.s.get(
                    f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/Product-GetAvailability?pid=AW_22121RBC&format=ajax', 
                    timeout = self.timeout
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.t = r.text.split("t':'")[1].split("'")[0]
                        self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                        self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                        self.sss = r.text.split("s':")[1].split(",'")[0]
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.solvedd()
                        continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                if r.status_code == 200:
                    pr = r.json()
                    count = 0
                    instockpids = []
                    for i in pr:
                        count+=1               
                        self.available = pr[i]['available']
                        selectedsku = i
                        self.status = pr[i]['status']
                        if self.available == False:
                            continue
                        else:
                            instockpids.append(selectedsku)
                    if instockpids:
                        self.sku2 = random.choice(instockpids)
                        break
                    else:
                        time.sleep(self.delay)
                        continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while preparing session, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception preparing session 1 : {e.__class__.__name__}, retrying...')
                continue
        self.atcprep()

    def atcprep(self):
        while True:
            try:
                payload = {
                    'Quantity': '1',
                    'sizeTable': '',
                    'cartAction': 'add',
                    'pid': self.sku2,
                    'productSetID': self.sku2,
                    'redirect': 'true'
                }
                r = self.s.post(
                    self.atc_url, 
                    data = payload,
                    headers={
                        'Referer': f'https://{self.domain}/{self.sku2}.html',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    timeout = self.timeout
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                if r.status_code == 200 and 'b-cart__subtitle">1' in r.text:
                    break
                elif '<span class="b-utility-menu__quantity">0</span>' in r.text:
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception error while preparing session 2: {e.__class__.__name__}, restarting...')
                self.build_proxy()
                continue
        self.shippingprep()

    def shippingprep(self):
        self.discountfailed = False
        payload = {
            'dwfrm_billing_billingAddress_email_emailAddress': self.email,
            'dwfrm_singleshipping_shippingAddress_addressFields_phonecountrycode_codes':f'{self.prefix}',
            'dwfrm_singleshipping_shippingAddress_addressFields_phonewithoutcode': self.phone,
            'dwfrm_singleshipping_shippingAddress_addressFields_phone': f'{self.prefix}{self.phone}',
            'dwfrm_singleshipping_shippingAddress_addressFields_isValidated':'true',
            'dwfrm_singleshipping_shippingAddress_addressFields_firstName': self.name,
            'dwfrm_singleshipping_shippingAddress_addressFields_lastName': self.surname,
            'dwfrm_singleshipping_shippingAddress_addressFields_title':'Mr',
            'dwfrm_singleshipping_shippingAddress_addressFields_birthdayfields_day':'02',
            'dwfrm_singleshipping_shippingAddress_addressFields_birthdayfields_month':'04',
            'dwfrm_singleshipping_shippingAddress_addressFields_birthdayfields_year':random.randint(1990, 2003),
            'dwfrm_singleshipping_shippingAddress_addressFields_birthday':'1990-04-02',
            'dwfrm_singleshipping_shippingAddress_addressFields_address1': self.address,
            'dwfrm_singleshipping_shippingAddress_addressFields_postal': self.zip,
            'dwfrm_singleshipping_shippingAddress_addressFields_city': self.city,
            'dwfrm_singleshipping_shippingAddress_addressFields_states_state': self.state,
            'dwfrm_singleshipping_shippingAddress_addressFields_country': self.country,
            'dwfrm_singleshipping_shippingAddress_useAsBillingAddress':'true',
            'dwfrm_singleshipping_shippingAddress_shippingMethodID':'ANY_STD',
            'dwfrm_singleshipping_shippingAddress_save':self.proced,
            'csrf_token': self.cftoken
        }
        while True:
            try:
                r = self.s.post(
                    self.ship_url, 
                    data = payload,
                    headers={'Referer': f'https://{self.domain}/{self.ref1}'},
                    timeout = self.timeout,
                    allow_redirects=False
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.t = r.text.split("t':'")[1].split("'")[0]
                        self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                        self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                        self.sss = r.text.split("s':")[1].split(",'")[0]
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.solvedd()
                        continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 302 and 'DDUser-Challenge' in r.headers['Location']:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                if r.status_code == 302 and self.fatt in r.headers['Location']:
                    self.captcha_url = r.url
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue       
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception while preparing session 3: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.tiredisc = "NO"
        if self.discount != "":
            self.tiredisc = self.discount
            self.appdiscountprep()
        if self.discountfailed:
            sys.exit(1)
        else:
            self.clearcart()

    def appdiscountprep(self):
        self.discountfailed = False
        try:
            payload = {
                'dwfrm_billing_save':'true',
                'dwfrm_billing_billingAddress_addressId':'guest-shipping',
                'dwfrm_billing_billingAddress_addressFields_isValidated':'true',
                'dwfrm_billing_billingAddress_addressFields_firstName': self.name,
                'dwfrm_billing_billingAddress_addressFields_lastName': self.surname,
                'dwfrm_billing_billingAddress_addressFields_address1': self.address,
                'dwfrm_billing_billingAddress_addressFields_postal': self.zip,
                'dwfrm_billing_billingAddress_addressFields_city': self.city,
                'dwfrm_billing_billingAddress_addressFields_states_state': self.state,
                'dwfrm_billing_billingAddress_addressFields_country': self.country,
                'dwfrm_billing_billingAddress_invoice_accountType': 'private',
                'dwfrm_billing_billingAddress_invoice_companyName': '',
                'dwfrm_billing_billingAddress_invoice_taxNumber': '',
                'dwfrm_billing_billingAddress_invoice_vatNumber': '',
                'dwfrm_billing_billingAddress_invoice_sdlCode': '',
                'dwfrm_billing_couponCode': self.discount,
                'dwfrm_billing_applyCoupon': self.applico,
                'dwfrm_billing_paymentMethods_creditCard_encrypteddata':'',	
                'dwfrm_billing_paymentMethods_creditCard_type':'',	
                'dwfrm_adyPaydata_brandCode':'',
                'noPaymentNeeded':'true',
                'dwfrm_billing_paymentMethods_creditCard_selectedCardID':'',
                'csrf_token': self.cftoken
            }
            r = self.s.post(
                self.checkout_url, 
                data = payload,
                timeout = self.timeout
            )
            if "geo.captcha" in r.text:
                self.warn('Datadome found, solving...')
                self.referer = r.url
                if "t':'fe" in r.text:
                    self.t = r.text.split("t':'")[1].split("'")[0]
                    self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                    self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                    self.sss = r.text.split("s':")[1].split(",'")[0]
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.solvedd()
                    self.appdiscountprep()
                else:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()           
                    time.sleep(self.delay)
                    self.appdiscountprep()
            if "stata applicata" in r.text:
                return self.success('Session almost ready, proceeding...')
            elif "se ha aplicado" in r.text:
                return self.success('Session almost ready, proceeding...')
            elif "has been applied" in r.text:
                return self.success('Session almost ready, proceeding...')
            elif r.status_code >= 500 and r.status_code <= 600:
                self.warn('Site dead, retrying...')
                time.sleep(self.delay)
                self.appdiscountprep()   
            elif r.status_code == 403:
                self.error('Proxy banned, rotating proxies...')
                self.build_proxy()
                self.appdiscountprep()   
            elif r.status_code == 429:
                self.error('Rate limit, rotating proxies...')
                self.build_proxy()
                self.appdiscount()   
            else:
                self.discountfailed = True
                return self.error('Discount failed, stopping task')
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            self.error('Connection error, retrying...')
            self.build_proxy()
            self.appdiscountprep()
        except Exception as e: 
            open(self.logs_path, 'a+').write(f'{e}\n')
            self.error(f'Exception while preparing session 4: {e.__class__.__name__}, retrying...')
            self.build_proxy()
            self.appdiscountprep()

    def clearcart(self):
        payload = {
            'dwfrm_cart_shipments_i0_items_i0_quantity': '1',
            'dwfrm_cart_couponCode': '',
            'csrf_token': self.cftoken,
            'dwfrm_cart_shipments_i0_items_i0_deleteProduct': True
        }
        while True:
            try:
                r = self.s.post(
                    self.clearcart_url, 
                    data = payload,
                    timeout = self.timeout
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.t = r.text.split("t':'")[1].split("'")[0]
                        self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                        self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                        self.sss = r.text.split("s':")[1].split(",'")[0]
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.solvedd()
                        continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                if r.status_code == 200:
                    if 'Il tuo carrello' and 'vuoto' in r.text:
                        r = self.s.post(
                            f'https://{self.domain}/{self.cart}', 
                            timeout = self.timeout
                        )
                        if r.status_code == 200:
                            if 'Il tuo carrello' and 'vuoto' in r.text:
                                self.success('Session ready!') 
                                break
                            elif 'Your shopping cart is empty' in r.text:
                                self.success('Session ready!') 
                                break
                            else:
                                continue
                        elif r.status_code >= 500 and r.status_code <= 600:
                            self.warn('Site dead, retrying...')
                            time.sleep(self.delay)
                            continue   
                        elif r.status_code == 403:
                            self.error('Proxy banned, rotating proxies...')
                            self.build_proxy()
                            continue   
                        elif r.status_code == 429:
                            self.error('Rate limit, rotating proxies...')
                            self.build_proxy()
                            continue
                        else:
                            self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                            self.build_proxy()
                            continue       
                    elif 'Your shopping cart is empty' in r.text:
                        r = self.s.post(
                            f'https://{self.domain}/{self.cart}',
                            timeout = self.timeout
                        )
                        if r.status_code == 200:
                            if 'Il tuo carrello' and 'vuoto' in r.text:
                                self.success('Session ready!') 
                                break
                            elif 'Your shopping cart is empty' in r.text:
                                self.success('Session ready!') 
                                break
                            else:
                                continue
                        elif r.status_code >= 500 and r.status_code <= 600:
                            self.warn('Site dead, retrying...')
                            time.sleep(self.delay)
                            continue   
                        elif r.status_code == 403:
                            self.error('Proxy banned, rotating proxies...')
                            self.build_proxy()
                            continue   
                        elif r.status_code == 429:
                            self.error('Rate limit, rotating proxies...')
                            self.build_proxy()
                            continue
                        else:
                            self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                            self.build_proxy()
                            continue       
                    else:
                        continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue       
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'{e}\n') 
                self.error(f'Exception while preparing session 4: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.monitor()

    def monitor(self):
        try:
            self.lung = len(self.pidmonitor)
            if self.lung >= 22:
                self.sku = self.pidmonitor
                self.atc()
            elif self.lung >= 19:
                self.islung = True
                self.stockCheck()
            elif self.lung >= 11:
                self.islung = False
                self.stockCheck()
            else:
                self.error('Failed reading PID, check CSV')
                sys.exit(1)
        except Exception as e:
            open(self.logs_path, 'a+').write(f'{e}\n')
            self.error(f'Unknown error while getting sizes: {e.__class__.__name__}, retrying...')
            self.build_proxy()
            self.tokenn()

    def stockCheck(self):
        while True: 
            try:
                r = self.s.get(
                    f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/Product-GetAvailability?pid={self.pidmonitor}&format=ajax', 
                    timeout = self.timeout
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.t = r.text.split("t':'")[1].split("'")[0]
                        self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                        self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                        self.sss = r.text.split("s':")[1].split(",'")[0]
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.solvedd()
                        continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                if r.status_code == 200:
                    pr = r.json()
                    count = 0
                    instockpids = []
                    for i in pr:
                        if self.islung:
                            if self.pidmonitor in i:
                                count+=1               
                                self.available = pr[i]['available']
                                selectedsku = i
                                self.status = pr[i]['status']
                                if self.available == False:
                                    continue
                                else:
                                    instockpids.append(selectedsku)
                        else:
                            count+=1               
                            self.available = pr[i]['available']
                            selectedsku = i
                            self.status = pr[i]['status']
                            if self.available == False:
                                continue
                            else:
                                instockpids.append(selectedsku)
                    if instockpids:
                        self.success('Product in stock!')           
                        self.sku = random.choice(instockpids)
                        break
                    else:
                        self.warn('Product OOS, monitoring...') 
                        time.sleep(self.delay)
                        continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue       
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Unable to fetch sizes {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.atc()

    def atc(self): 
        global carted, checkoutnum, failed
        self.warn('Adding to cart...')
        while True:
            try:
                payload = {
                    'Quantity': '1',
                    'sizeTable': '',
                    'cartAction': 'add',
                    'pid': self.sku,
                    'productSetID': self.sku,
                    'redirect': 'true'
                }
                r = self.s.post(
                    self.atc_url,
                    data = payload,
                    headers={
                        'Referer': f'https://{self.domain}/{self.sku}.html',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    timeout = self.timeout
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                if r.status_code == 200 and 'b-cart__subtitle">1' in r.text:
                    self.success('Successfully added to cart!')
                    carted = carted + 1
                    self.bar()
                    self.riparto = False
                    if self.restockmode:
                        try:
                            color = r.text.split('data-product-details="')[1].split('"')[0].replace('&quot;', '').split('dimension2:')[1].split(',')[0]                            
                            soup = bs(r.text, features='lxml')
                            self.sizegiusta = soup.find('div',{'class':'b-minicart__product-info'}).find('div',{'data-attribute':'size'}).find('span',{'class':'b-product__value b-product-list__value'}).text
                            self.img = f'https://www.aw-lab.com/dw/image/v2/BCLG_PRD/on/demandware.static/-/Sites-awlab-master-catalog/default/dwe3c277df/images/large/{color}_0.jpg?sw=300'
                            break
                        except:
                            self.sizegiusta = 'Unkown'
                            self.img = 'https://es.aw-lab.com/on/demandware.static/-/Library-Sites-awlab-content-global/default/dwc53ffc0b/awlab/blp/blp-premium-logo.png'
                            self.captcha_url = r.url
                            break
                    else:
                        break
                elif '<span class="b-utility-menu__quantity">0</span>' in r.text:
                    self.warn('Product OOS, retrying...') 
                    time.sleep(self.delay)
                    self.riparto = True
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue     
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except HelheimRuntimeError as e:
                self.atcerror()
                continue
            except Exception as e: 
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception error while adding to cart:{e.__class__.__name__}, restarting...')
                self.build_proxy()
                continue
        if self.riparto:
            self.monitor()
        else:
            if self.restockmode:
                self.checkcart()
            else:
                self.shipping()

    def atcerror(self):
        self.warn('Getting cookies...')
        while True:
            try:
                r = self.s.get(
                    f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/Product-GetAvailability?format=ajax',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue     
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception error while getting cookies:{e.__class__.__name__}, restarting...')
                self.build_proxy()
                continue
        return self.success('Succesfully got cookies')

    def shipping(self):
        self.discountfailed = False
        self.warn('Submitting shipping info...')
        year = random.randint(1990, 2003)
        payload = {
            'dwfrm_billing_billingAddress_email_emailAddress': self.email,
            'dwfrm_singleshipping_shippingAddress_addressFields_phonecountrycode_codes':f'{self.prefix}',
            'dwfrm_singleshipping_shippingAddress_addressFields_phonewithoutcode': self.phone,
            'dwfrm_singleshipping_shippingAddress_addressFields_phone': f'{self.prefix}{self.phone}',
            'dwfrm_singleshipping_shippingAddress_addressFields_isValidated':'true',
            'dwfrm_singleshipping_shippingAddress_addressFields_firstName': self.name,
            'dwfrm_singleshipping_shippingAddress_addressFields_lastName': self.surname,
            'dwfrm_singleshipping_shippingAddress_addressFields_title':'Mr',
            'dwfrm_singleshipping_shippingAddress_addressFields_birthdayfields_day':'02',
            'dwfrm_singleshipping_shippingAddress_addressFields_birthdayfields_month':'04',
            'dwfrm_singleshipping_shippingAddress_addressFields_birthdayfields_year':year,
            'dwfrm_singleshipping_shippingAddress_addressFields_birthday':f'{year}-04-02',
            'dwfrm_singleshipping_shippingAddress_addressFields_address1': self.address,
            'dwfrm_singleshipping_shippingAddress_addressFields_postal': self.zip,
            'dwfrm_singleshipping_shippingAddress_addressFields_city': self.city,
            'dwfrm_singleshipping_shippingAddress_addressFields_states_state': self.state,
            'dwfrm_singleshipping_shippingAddress_addressFields_country': self.country,
            'dwfrm_singleshipping_shippingAddress_useAsBillingAddress':'true',
            'dwfrm_singleshipping_shippingAddress_shippingMethodID':'ANY_STD',
            'dwfrm_singleshipping_shippingAddress_save':self.proced,
            'csrf_token': self.cftoken
        }
        while True:
            try:
                r = self.s.post(
                    self.ship_url,
                    data = payload,
                    headers={'Referer': f'https://{self.domain}/{self.ref1}'},
                    timeout = self.timeout,
                    allow_redirects=False
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.t = r.text.split("t':'")[1].split("'")[0]
                        self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                        self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                        self.sss = r.text.split("s':")[1].split(",'")[0]
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.solvedd()
                        continue
                    else:
                        #open(f'awlab{int(time.time() * 1000)}.html', 'w+', encoding='utf-8').write(r.text)
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 302 and 'DDUser-Challenge' in r.headers['Location']:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                if r.status_code == 302 and self.fatt in r.headers['Location']:
                    try:
                        r = self.s.get('https://www.aw-lab.com/fatturazione')
                        soup = bs(r.text, features='lxml')
                        minicart = soup.find('div',{'class':'b-minicart__product-info'})
                        attr = minicart.find('div',{'class':'b-product__attribute b-product-list__attribute'})
                        self.sizegiusta = attr.find('span',{'class':'b-product__value b-product-list__value'}).text
                        mini = soup.find('div',{'class':'b-minicart__products'})
                        ulm = mini.find('div',{'class':'b-minicart__product-image'})
                        self.img = ulm.find('img',{'class':'b-lazyload'})['data-lazy']
                        self.success('Successfully submitted shipping info!')
                        self.captcha_url = r.url
                        break
                    except:
                        self.sizegiusta = 'Unkown'
                        self.img = 'https://es.aw-lab.com/on/demandware.static/-/Library-Sites-awlab-content-global/default/dwc53ffc0b/awlab/blp/blp-premium-logo.png'
                        self.success('Successfully submitted shipping info!')
                        self.captcha_url = r.url
                        break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue     
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception while submitting shipping:{e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.tiredisc = "NO"
        if self.discount != "":
            self.tiredisc = self.discount
            self.appdiscount()
        if self.discountfailed:
            sys.exit(1)
        self.checkoutCaptcha = 'captchaLabel' in r.text
        if self.payment =='CREDIT_CARD':
            self.adyen()
        else:
            self.checkout()

    def appdiscount(self):
        self.discountfailed = False
        self.warn('Submitting discount...')
        payload = {
            'dwfrm_billing_save':'true',
            'dwfrm_billing_billingAddress_addressId':'guest-shipping',
            'dwfrm_billing_billingAddress_addressFields_isValidated':'true',
            'dwfrm_billing_billingAddress_addressFields_firstName': self.name,
            'dwfrm_billing_billingAddress_addressFields_lastName': self.surname,
            'dwfrm_billing_billingAddress_addressFields_address1': self.address,
            'dwfrm_billing_billingAddress_addressFields_postal': self.zip,
            'dwfrm_billing_billingAddress_addressFields_city': self.city,
            'dwfrm_billing_billingAddress_addressFields_states_state': self.state,
            'dwfrm_billing_billingAddress_addressFields_country': self.country,
            'dwfrm_billing_billingAddress_invoice_accountType': 'private',
            'dwfrm_billing_billingAddress_invoice_companyName': '',
            'dwfrm_billing_billingAddress_invoice_taxNumber': '',
            'dwfrm_billing_billingAddress_invoice_vatNumber': '',
            'dwfrm_billing_billingAddress_invoice_sdlCode': '',
            'dwfrm_billing_billingAddress_invoice_pec': '',
            'dwfrm_billing_couponCode': self.discount,
            'dwfrm_billing_applyCoupon': self.applico,
            'dwfrm_billing_paymentMethods_selectedPaymentMethodID': self.payment,
            'dwfrm_billing_paymentMethods_creditCard_encrypteddata':'',	
            'dwfrm_billing_paymentMethods_creditCard_type':'',	
            'dwfrm_adyPaydata_brandCode':'',
            'noPaymentNeeded':'true',
            'dwfrm_billing_paymentMethods_creditCard_selectedCardID':'',
            'csrf_token': self.cftoken
        }
        try:
            r = self.s.post(
                self.checkout_url,
                data = payload,
                headers={'Referer': f'https://{self.domain}/{self.fatt}'},
                timeout = self.timeout,
                allow_redirects=False
            )
            if "geo.captcha" in r.text:
                self.warn('Datadome found, solving...')
                self.referer = r.url
                if "t':'fe" in r.text:
                    self.t = r.text.split("t':'")[1].split("'")[0]
                    self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                    self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                    self.sss = r.text.split("s':")[1].split(",'")[0]
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.solvedd()
                    self.appdiscount()
                else:
                    #open(f'awlab{int(time.time() * 1000)}.html', 'w+', encoding='utf-8').write(r.text)
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()           
                    time.sleep(self.delay)
                    self.appdiscount()
            if "stata applicata" in r.text:
                return self.success('Discount Submitted, proceeding...')
            elif "se ha aplicado" in r.text:
                return self.success('Discount Submitted, proceeding...')
            elif "has been applied" in r.text:
                return self.success('Discount Submitted, proceeding...')
            elif r.status_code >= 500 and r.status_code <= 600:
                self.warn('Site dead, retrying...')
                time.sleep(self.delay)
                self.appdiscount()   
            elif r.status_code == 403:
                self.error('Proxy banned, rotating proxies...')
                self.build_proxy()
                self.appdiscount()   
            elif r.status_code == 429:
                self.error('Rate limit, rotating proxies...')
                self.build_proxy()
                self.appdiscount() 
            else:
                self.discountfailed = True
                return self.error('Discount failed, stopping task')
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            self.error('Connection error, retrying...')
            self.build_proxy()
            self.appdiscount()
        except Exception as e: 
            open(self.logs_path, 'a+').write(f'{e}\n')
            self.error(f'Exception while submitting discount:{e.__class__.__name__}, retrying...')
            self.build_proxy()
            self.appdiscount()

    def checkcart(self):
        self.warn('Getting checkout page...')
        while True:
            try:
                r = self.s.get(
                    self.checklink,
                    timeout = self.timeout
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.t = r.text.split("t':'")[1].split("'")[0]
                        self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                        self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                        self.sss = r.text.split("s':")[1].split(",'")[0]
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.solvedd()
                        continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                if r.status_code == 200:
                    self.success('Succesfully got checkout page!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue   
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating proxies...')
                    self.build_proxy()
                    continue   
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                #elif r.status_code == 302:
                #    print(r.text)
                #    time.sleep(5000)
                #    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, rotating proxies...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception while getting checkout page:{e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.checkoutCaptcha = 'captchaLabel' in r.text
        if self.payment =='CREDIT_CARD':
            self.adyen()
        else:
            self.checkout()
        
    def checkout(self):
        self.stop = False
        global checkoutnum, failed, carted
        if self.checkoutCaptcha:
            self.warn('Solving checkout captcha...')
            code = self.solve_v2(self.checklink)
        self.warn('Submitting payment...') 
        payload = {
            'dwfrm_billing_save':'true',
            'dwfrm_billing_billingAddress_addressId':'guest-shipping',
            'dwfrm_billing_billingAddress_addressFields_isValidated':'true',
            'dwfrm_billing_billingAddress_addressFields_firstName': self.name,
            'dwfrm_billing_billingAddress_addressFields_lastName': self.surname,
            'dwfrm_billing_billingAddress_addressFields_address1': self.address,
            'dwfrm_billing_billingAddress_addressFields_postal': self.zip,
            'dwfrm_billing_billingAddress_addressFields_city': self.city,
            'dwfrm_billing_billingAddress_addressFields_states_state': self.state,
            'dwfrm_billing_billingAddress_addressFields_country': self.country,
            'dwfrm_billing_billingAddress_invoice_accountType': 'private',
            'dwfrm_billing_billingAddress_invoice_companyName': '',
            'dwfrm_billing_billingAddress_invoice_taxNumber': '',
            'dwfrm_billing_billingAddress_invoice_vatNumber': '',
            'dwfrm_billing_billingAddress_invoice_sdlCode': '',
            'dwfrm_billing_billingAddress_invoice_pec': '',
            'dwfrm_billing_couponCode': self.discount,
            'dwfrm_billing_paymentMethods_creditCard_encrypteddata':'',	
            'dwfrm_billing_paymentMethods_creditCard_type':'',	
            'dwfrm_adyPaydata_brandCode':'',
            'noPaymentNeeded':'true',
            'dwfrm_billing_paymentMethods_creditCard_selectedCardID':'',
            'dwfrm_billing_paymentMethods_selectedPaymentMethodID':self.payment,
            'dwfrm_billing_billingAddress_personalData':'true',
            'dwfrm_billing_billingAddress_tersmsOfSale':'true',
            'csrf_token': self.cftoken
        }
        if self.checkoutCaptcha:
            payload['g-recaptcha-response'] = code
        while True:
            try:
                r = self.s.post(
                    self.checkout_url,
                    headers={
                        'Referer': f'https://{self.domain}/{self.fatt}',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    data = payload,
                    timeout = self.timeout,
                    allow_redirects=False
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.t = r.text.split("t':'")[1].split("'")[0]
                        self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                        self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                        self.sss = r.text.split("s':")[1].split(",'")[0]
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.solvedd()
                        continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 302 and 'DDUser-Challenge' in r.headers['Location']:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                if r.status_code == 302:
                    if "ordine" in r.headers['Location']:
                        try:
                            soup = bs(r.text, features='lxml') 
                            numero = soup.find("span",{"class":"b-checkout-confirmation__order-number"}).text
                            self.numero = numero.split('Numero ordine: ')[1]
                            self.success('Successfully checked out!')
                            checkoutnum = checkoutnum + 1
                            self.bar()
                            break
                        except Exception as e: 
                            open(self.logs_path, 'a+').write(f'{e}\n')
                            self.error(f'Cad not available, {e} switching to PP...')
                            self.payment = 'PayPal' 
                            continue
                    elif "riepilogoordine" in r.headers['Location']:
                        try:
                            soup = bs(r.text, features='lxml') 
                            numero = soup.find("span",{"class":"b-checkout-confirmation__order-number"}).text
                            self.numero = numero.split('Numero ordine: ')[1]
                            self.success('Successfully checked out!')
                            checkoutnum = checkoutnum + 1
                            self.bar()
                            break
                        except:
                            self.error('Cad not available, switching to PP...')
                            self.payment = 'PayPal' 
                            continue
                    elif "token=EC" in r.headers['Location']:
                        self.success('Successfully checked out')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        xx = r.headers['Location'].split("token=EC")[1]
                        pp = xx.split('&')[0]
                        self.adyen_url = f'https://www.paypal.com/webscr&cmd=_express-checkout&token=EC{pp}'
                        break
                    else:
                        self.error('Failed submitting payment, retrying...')
                        failed = failed + 1
                        self.bar()
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error('Failed submitting payment, retrying...')
                    failed = failed + 1
                    self.bar()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception while submitting payment:{e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        if self.stop:
            sys.exit(1)
        if self.payment == 'PayPal':
            self.passCookies()
        else:
            self.SuccessCAD()

    def gnerateCardDataJson(self, name, pan, cvc, expiry_month, expiry_year):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "holderName": name,
            "number": pan,
            "cvc": cvc,
            "expiryMonth": expiry_month,
            "expiryYear": expiry_year,
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

    def main(self, name, pan, cvc, expiry_month, expiry_year, key):
        plainCardData = self.gnerateCardDataJson(
            name=name,
            pan=pan,
            cvc=cvc,
            expiry_month=expiry_month,
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


    def adyen(self):

        self.tred = False
        self.dconfermato = False
        global checkoutnum, failed, carted
        if self.checkoutCaptcha:
            self.warn('Solving checkout captcha...')
            code = self.solve_v2(self.checklink)
        self.warn('Submitting order...')

        cardtype = identify_card_type(self.card)
        if cardtype == "MasterCard":
            card_type = "mc"
        elif cardtype == "Visa":
            card_type = "visa"

        payload = {
            'dwfrm_billing_save':'true',
            'dwfrm_billing_billingAddress_addressId':'guest-shipping',
            'dwfrm_billing_billingAddress_addressFields_isValidated':'true',
            'dwfrm_billing_billingAddress_addressFields_firstName':self.name,
            'dwfrm_billing_billingAddress_addressFields_lastName':self.surname,
            'dwfrm_billing_billingAddress_addressFields_address1':self.address,
            'dwfrm_billing_billingAddress_addressFields_postal':self.zip,
            'dwfrm_billing_billingAddress_addressFields_city':self.city,
            'dwfrm_billing_billingAddress_addressFields_states_state':self.state,
            'dwfrm_billing_billingAddress_addressFields_country':self.country,
            'dwfrm_billing_couponCode': self.discount,
            'dwfrm_billing_paymentMethods_selectedPaymentMethodID':self.payment,
            'dwfrm_billing_paymentMethods_creditCard_encrypteddata': self.main(name = f"{self.name} {self.surname}",pan = self.card,cvc = self.cvc,expiry_month = self.month,expiry_year = self.year ,key = "10001|A58F2F0D8A4A08232DD1903F00A3F99E99BB89D5DEDF7A9612A3C0DC9FA9D8BDB2A20A233B663B0A48D47A0A1DDF164B3206985EFF19686E3EF75ADECF77BA10013B349C9F95CEBB5A66C48E3AD564410DB77A5E0798923E849E48A6274A80CBE1ACAA886FF3F91C40C6F2038D90FABC9AEE395D4872E24183E8B2ACB28025964C5EAE8058CB06288CDA80D44F69A7DFD3392F5899886094DB23F703DAD458586338BF21CF84288C22020CD2AB539A35BF1D98582BE5F79184C84BE877DB30C3C2DE81E394012511BFE9749E35C3E40D28EE3338DE7CBB1EDD253951A7B66A85E9CC920CA2A40CAD48ACD8BD1AE681997D1655E59005F1887B872A7A873EDBD1"),
            'dwfrm_billing_paymentMethods_creditCard_type':card_type,
            'dwfrm_adyPaydata_brandCode':'',
            'noPaymentNeeded':'true',
            'dwfrm_billing_paymentMethods_creditCard_selectedCardID':'',
            'dwfrm_billing_billingAddress_personalData':'true',
            'dwfrm_billing_billingAddress_tersmsOfSale':'true',
            'csrf_token': self.cftoken
        }
        if self.checkoutCaptcha:
            payload['g-recaptcha-response'] = code
        while True:
            try:
                r = self.s.post(
                    f'https://{self.domain}/on/demandware.store/{self.site_region}/{self.lang}/COBilling-Billing',
                    data = payload, 
                    allow_redirects = True,
                    headers={'Referer': f'https://{self.domain}/{self.fatt}'},
                    timeout = self.timeout
                )
                if "geo.captcha" in r.text:
                    self.warn('Datadome found, solving...')
                    self.referer = r.url
                    if "t':'fe" in r.text:
                        self.t = r.text.split("t':'")[1].split("'")[0]
                        self.initialcid = r.text.split("cid':'")[1].split("'")[0]
                        self.hsh = r.text.split("hsh':'")[1].split("'")[0]
                        self.sss = r.text.split("s':")[1].split(",'")[0]
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.solvedd()
                        continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()           
                        time.sleep(self.delay)
                        continue
                if 'https://en.aw-lab.com/cart' == r.url:
                    self.error(f'Failed checking out, product went oos...')
                    failed = failed + 1
                    self.bar()
                    self.tokenn()
                    break
                elif 'https://www.aw-lab.com/carrello' == r.url:
                    self.error('Failed checking out, product went oos...')
                    failed = failed + 1
                    self.bar()
                    self.tokenn()
                    break
                elif 'Controlla le impostazioni di pagamento e riprova' in r.text:
                    self.error('Something went wrong while checking out, check your CC information')
                    failed = failed + 1
                    self.bar()
                    continue
                elif 'https://www.aw-lab.com/riepilogoordine' == r.url and 'Numero ordine' in r.text or 'Grazie per il tuo ordine' in r.text:
                    self.success('Successfully checked out!')
                    self.adyen_url = r.url
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break
                elif 'https://en.aw-lab.com/revieworder' == r.url and 'products ordered' in r.text or 'Order Number' in r.text:
                    self.success('Successfully checked out!')
                    self.adyen_url = r.url
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break
                elif 'https://es.aw-lab.com/cart' == r.url:
                    self.error('Failed checking out, product went oos...')
                    failed = failed + 1
                    self.bar()
                    self.tokenn()
                    break
                elif 'Compruebe la configuración de pago y vuelve a intentarlo' in r.url:
                    self.error('Failed checking out, wrong card infomation')
                    failed = failed + 1
                    self.bar()
                    self.tokenn()
                    break
                elif 'https://www.aw-lab.com/spedizione' == r.url:
                    self.error('Failed checking out, product went oos...')
                    failed = failed + 1
                    self.bar()
                    self.build_proxy()
                    self.tokenn()
                    break
                elif r.status_code == 429:
                    self.error('Rate limit, rotating proxies...')
                    self.build_proxy()
                    continue
                elif 'Billing' in r.url:
                    self.error('Failed checking out, product went oos...')
                    failed = failed + 1
                    self.bar()
                    self.tokenn()
                    break
                elif 'Adyen-Redirect3ds' in r.url:
                    self.success(f'Successfully checked out!')
                    self.tred = True
                    self.dconfermato = True
                    self.adyen_url = r.url
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break
                elif 'menu__quantity">0' in r.text:
                    self.error('Failed checking out, product went oos...')
                    failed = failed + 1
                    self.bar()
                    self.build_proxy()
                    self.tokenn()
                    break
                else:
                    self.error('Failed checking out, product went oos...')
                    failed = failed + 1
                    self.bar()
                    self.build_proxy()
                    self.tokenn()
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.error(f'Exception while submitting order:{e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        if self.tred:
            self.passCookies()
        else:
            self.SuccessCCnotred()

    def passCookies(self):
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
            url = urllib.parse.quote(base64.b64encode(bytes(self.adyen_url, 'utf-8')).decode())
            self.token = f"https://api.phoenixbot.io/exploits/?cookie={cookieStr}&redirect={url}"
            self.token2 = f"https://api.phoenixbot.io/mobile/?cookie={cookieStr}&redirect={url}"
            apiurl2 = "http://tinyurl.com/api-create.php?url="
            tinyasdurl2 = urllib.request.urlopen(apiurl2 + self.token2).read()
            if self.sizegiusta == '':
                self.sizegiusta == 'Unkown size'
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
                    writer.writerow({'SITE':'AWLAB','SIZE':f'{self.sizegiusta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.sku}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'AWLAB','SIZE':f'{self.sizegiusta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.sku}'})         
            if self.payment =='CREDIT_CARD':
                if self.dconfermato:
                    self.Success3d()
                else:
                    self.SuccessCC()
            else:
                self.SuccessPP()
        except Exception as e: 
            open(self.logs_path, 'a+').write(f'{e}\n')
            self.error('Exception sending webhook, retrying...') 
            self.SuccessPP()

    def SuccessCAD(self):
        try:
            if self.mode == "":
                self.mode = "NORMAL"
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Cooked!', color = 0x715aff)
            embed.add_embed_field(name=f'**AWLAB {self.country}**', value = f'{self.sku}', inline = True)
            embed.add_embed_field(name='**Size**', value = f'{self.sizegiusta}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='Mode', value = self.mode, inline = True)
            embed.add_embed_field(name='**Email**', value = f'||{self.email}||', inline = False)
            embed.add_embed_field(name='**Discount**', value = f'{self.tiredisc}', inline = False)
            embed.add_embed_field(name='**Numero ordine**', value = f'||{self.numero}||', inline = False)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.set_thumbnail(url = self.img) 
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass


    def Pubblic_Webhook(self):
        try:
            if self.mode == "":
                self.mode = "NORMAL"
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Success', color = 40703)
            embed.add_embed_field(name=f'**AWLAB {self.country}**', value = f'{self.sku}', inline = True)
            embed.add_embed_field(name='**Size**', value = f'{self.sizegiusta}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='Mode', value = self.mode, inline = True)
            embed.add_embed_field(name='**Discount**', value = f'{self.tiredisc}', inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.img)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.s.cookies.clear()
            if self.mode == 'ONCE':
                sys.exit(1)
            else:
                self.tokenn()
        except:
            pass


    def SuccessPP(self):
        try:
            if self.mode == "":
                self.mode = "NORMAL"
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Success!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**AWLAB {self.country}**', value = f'{self.sku}', inline = True)
            embed.add_embed_field(name='**Size**', value = f'{self.sizegiusta}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='Mode', value = self.mode, inline = True)
            embed.add_embed_field(name='**Email**', value = f'||{self.email}||', inline = False)
            embed.add_embed_field(name='**Discount**', value = f'{self.tiredisc}', inline = False)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.img)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook_PP()
        except:
            pass
        

    def Pubblic_Webhook_PP(self):
        try:
            if self.mode == "":
                self.mode = "NORMAL"
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**AWLAB {self.country}**', value = f'{self.sku}', inline = True)
            embed.add_embed_field(name='**Size**', value = f'{self.sizegiusta}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = False)
            embed.add_embed_field(name='Mode', value = self.mode, inline = True)
            embed.add_embed_field(name='**Discount**', value = f'{self.tiredisc}', inline = True)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.img)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.s.cookies.clear()
            if self.mode == 'ONCE':
                try:
                    playsound('checkout.wav')
                    sys.exit(1)
                except:
                    sys.exit(1)
            else:
                try:
                    playsound('checkout.wav')
                    self.tokenn()
                except:
                    self.tokenn()
        except:
            pass

    def SuccessCC(self):
        try:
            if self.mode == "":
                self.mode = "NORMAL"
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Success!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**AWLAB {self.country}**', value = f'{self.sku}', inline = True)
            embed.add_embed_field(name='**Size**', value = f'{self.sizegiusta}', inline = True)
            embed.add_embed_field(name='Payment method', value = 'CC', inline = True)
            embed.add_embed_field(name='Mode', value = self.mode, inline = True)
            embed.add_embed_field(name='**Email**', value = f'||{self.email}||', inline = False)
            embed.add_embed_field(name='**Discount**', value = f'{self.tiredisc}', inline = False)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.img)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook_CC()
        except:
            pass

    def Success3d(self):
        try:
            if self.mode == "":
                self.mode = "NORMAL"
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - 3D is waiting for you! Click here', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**AWLAB {self.country}**', value = f'{self.sku}', inline = True)
            embed.add_embed_field(name='**Size**', value = f'{self.sizegiusta}', inline = True)
            embed.add_embed_field(name='Payment method', value = 'CC', inline = True)
            embed.add_embed_field(name='Mode', value = self.mode, inline = True)
            embed.add_embed_field(name='**Email**', value = f'||{self.email}||', inline = False)
            embed.add_embed_field(name='**Discount**', value = f'{self.tiredisc}', inline = False)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.img)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook_CC()
        except:
            pass


    def Pubblic_Webhook_CC(self):
        try:
            if self.mode == "":
                self.mode = "NORMAL"
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**AWLAB {self.country}**', value = f'{self.sku}', inline = True)
            embed.add_embed_field(name='**Size**', value = f'{self.sizegiusta}', inline = True)
            embed.add_embed_field(name='Payment method', value = 'CC', inline = False)
            embed.add_embed_field(name='Mode', value = self.mode, inline = True)
            embed.add_embed_field(name='**Discount**', value = f'{self.tiredisc}', inline = True)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.img)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.s.cookies.clear()
            if self.mode == 'ONCE':
                try:
                    playsound('checkout.wav')
                    sys.exit(1)
                except:
                    sys.exit(1)
            else:
                try:
                    playsound('checkout.wav')
                    self.tokenn()
                except:
                    self.tokenn()
        except:
            pass

    def SuccessCCnotred(self):
        try:
            if self.mode == "":
                self.mode = "NORMAL"
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Succesfully checked out!', color = 4437377)
            embed.add_embed_field(name=f'**AWLAB {self.country}**', value = f'{self.sku}', inline = True)
            embed.add_embed_field(name='**Size**', value = f'{self.sizegiusta}', inline = True)
            embed.add_embed_field(name='Payment method', value = 'CC', inline = True)
            embed.add_embed_field(name='Mode', value = self.mode, inline = True)
            embed.add_embed_field(name='**Email**', value = f'||{self.email}||', inline = False)
            embed.add_embed_field(name='**Discount**', value = f'{self.tiredisc}', inline = False)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.set_thumbnail(url = self.img)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook_CC()
        except:
            pass