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
import html
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

html = '''document.write("<!DOCTYPE html><html><body><form action='{}' method='POST'><input type='hidden' name='PaReq' value='{}'><input type='hidden' name='TermUrl' value='{}'><input type='hidden' name='MD' value='{}'></form><script>document.forms[0].submit()</script></body></html>")'''

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
    CAPTCHA = config['captcha']['courir']
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

class COURIR():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'Courir/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "Courir/proxies.txt")
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
                doubleDown=False,
                requestPostHook=self.injection
        )

        self.sku = row['SKU']
        self.size = row['SIZE']
        self.email = row['MAIL']
        self.password = row['PASSWORD']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.housenumber = row['HOUSENUMBER']
        self.region = row['REGION']
        self.zipcode = row['ZIPCODE']
        self.city = row['CITY']
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.card = row["CARDNUMBER"]
        self.month = row['MONTH']
        self.year = row['YEAR']
        self.cvv = row['CVV']

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

        self.linkgiafatto = False

        self.balance = balancefunc()
        self.threadID = '%03d' % i
        self.webhook_url = webhook
        self.version = version
        self.build_proxy()
        self.monster = config['capmonster']

        if self.country == 'FR':
            self.domain = "https://www.courir.com/"

        elif self.country == 'BE':
            self.domain = "https://www.courir.be/"

        elif self.country == 'ES':
            self.domain = "https://www.courir.es/"

        self.bar()

        self.warn('Task started!')
        self.getprod()

    def error(self, text):
        message = f'[TASK {self.threadID}] - [COURIR] [{self.sku}] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [COURIR] [{self.sku}] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [COURIR] [{self.sku}] - {text}'
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

    def solve_v3(self, url):
        self.warn('Solving captcha...')
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.recaptcha(sitekey='6Lf7htIZAAAAAKVu_e4Hyg3nhCXfVh2tlQbOjzYT', url=url)
                code = result['code']
                self.success('Captcha solved!')
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
                    "siteKey" : "6LdzlrYUAAAAADQyrcdOSHUtC5eeiSrWCVP2el0s", 
                    "version" : '2',
                    "minScore": '0.9'
                })
                while True:
                    print('a')
                    for token in CAPTCHA_TOKENS:
                        if token['taskId'] == f'{self.threadID}-{UNIQUE_ID}':
                            if token['token'] != 'failed':
                                CAPTCHA_TOKENS.remove(token)
                                self.success('Captcha solved!')
                                return token['token']
                            else:
                                self.error('Autosolve captcha solve failed')
                                return self.solve_v2(url)
                    time.sleep(1)
            except Exception as e:
                self.error(f'An error occured solving captcha with Autosolve: {e}')
                return self.solve_v3(url)

    def solve(self, timeout=10, verbose = False, responseLog = True):

        COOKIE_TOKEN = 'FOZon2MBI9RDO2nDrcF'
        ENDPOINT = 'https://geetest.stranck.ovh'
        try:
            s = requests.Session()
            s.cookies.set_cookie(requests.cookies.create_cookie('token', COOKIE_TOKEN))
            payload = {'gt': self.gt, 'challenge': self.challenge}
            if(verbose):
                print('Submitting challenge...')
            r = s.post(ENDPOINT+'/submit', json=payload)
            if(responseLog):
                print(r.text)
            r_json = json.loads(r.text.strip())
            if not r_json["success"]:        
                return None
            else:
                rid = r_json['id']
                payload = {'id': rid}    
            
            i = 0
            while i < timeout:
                #print(payload)
                r = s.post(ENDPOINT+'/check', json=payload)
                if(responseLog):
                    print(r.text.strip())
                r_json = json.loads(r.text)
                if r_json["success"]:
                    if r_json['ready']:
                        break
                    else:
                        i+=1
                        time.sleep(1)
                else:
                    #time.sleep(1)
                    #pass
                    return None
            if(verbose):
                print("Retryving results...")
            if i < timeout:
                r = s.post(ENDPOINT+'/fetch', json=payload)
                if(responseLog):
                    print(r.text.strip())
                if r_json["success"]:
                    r_json = json.loads(r.text)
                    return r_json['result']
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(e)

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

        except:
            pass

    def genkey(self):

        self.publickey = "fQXiz4wCHXdXRa434XC4gg=="
        self.privatekey = "as7rlcwKB5ZzRSva9E6ZtUKDmZShuEUPHaULQ47mGtmeRBfX4A/u8i57gPBwAVLw"
        self.companyname = "phoenix"
        result = []
        t = f'{self.publickey}:phoenix:{int(time.time() * 1000)}:{self.privatekey}'
        for i in range(0, len(t), 4):
            result.append((base64.b64encode((t[i : i + 4]).encode("utf-8"))).decode("utf-8"))
        key = (base64.b64encode(("".join(result)).encode("utf-8"))).decode("utf-8")
        return key

    def connection2(self):

        try:
            
            if self.linkgiafatto:
                captchalink = self.captchalink
            else:
                captchalink = f"https://geo.captcha-delivery.com/captcha/?initialCid={self.initialcid}&hash={self.hsh}&cid={self.cid}&t=fe&referer=https://www.courir.com/&s={self.sss}"

            headers = {
                'accept-encoding': 'gzip, deflate, br',
                'pragma': 'no-cache',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-US,en;q=0.9,sr;q=0.8'
            }

            s = requests.Session()
            r = s.get(captchalink, proxies = self.s.proxies, headers = headers)   
            if r.status_code == 200:
                ciao = r.text
                self.challenge = ciao.split("challenge: '")[1].split("',")[0]
                self.gt = ciao.split("gt: '")[1].split("',")[0]
                self.ip = ciao.split("'&x-forwarded-for=' + encodeURIComponent('")[1].split("'")[0]
                self.initialcid = ciao.split("&icid=' + encodeURIComponent('")[1].split("'")[0]
                self.hsh = ciao.split("&hash=' + encodeURIComponent('")[1].split("'")[0]
                self.ip = ciao.split("(IP ")[1].split(")")[0]

                body = {
                    "key": str(self.genkey()),
                    "gt": self.gt,
                    "challenge": self.challenge
                }
                print(body)

                headers2 = {
                    f"x-{self.companyname}-key": f'{self.privatekey}'
                }

                r = requests.post(f'https://curvesolutions.dev/{self.publickey}/geetest', headers=headers2, data=body)

                jsonresp = json.loads(r.text)
                self.geetest_challenge = jsonresp['data']['challenge']
                self.geetest_validate = jsonresp['data']['validate']
                self.geetest_seccode = jsonresp['data']['seccode']

                self.proxi2 = self.s.proxies['http'].split("http://")[1]

                headers = {
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                    'Cache-Control': 'no-cache',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Referer': 'https://geo.captcha-delivery.com/',
                    'Pragma': 'no-cache',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
                }


                dd_url = 'https://geo.captcha-delivery.com/captcha/check?cid=' + self.cid + '&icid=' + self.initialcid +'&ccid=' + 'null' +'&geetest-response-challenge=' + str(self.geetest_challenge) +'&geetest-response-validate=' + str(self.geetest_validate)  +'&geetest-response-seccode=' + str(self.geetest_seccode) +'&hash=' + self.hsh +'&ua=' + 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' +'&referer=' + self.dataurl +'&parent_url=' + f'https://www.slamjam.com/' + '&s=' + str(self.sss)

                r = self.s.get(dd_url, headers=headers)

                if r.status_code == 200:
                
                    jsondd = json.loads(r.text)
                    dd = jsondd['cookie']

                    dd = dd.split('datadome=')[1].split('"')[0]

                    self.cookie_obj = requests.cookies.create_cookie(domain='.courir.com',name='datadome',value=dd)
                    self.s.cookies.set_cookie(self.cookie_obj)

                    return self.success('Datadome done, proceding...')

                else:
                    return self.error('Datadome failed, retrying...')

            else:
                self.build_proxy()
                return self.error('Datadome failed, restarting...')

        except Exception as e:
            self.build_proxy()
            return self.error(f'Datadome failed {e}, retrying...')

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

    def ddsolve(self):
        try:
            
            captchalink = f"https://geo.captcha-delivery.com/captcha/?initialCid={self.initialcid}&hash={self.hsh}&cid={self.cid}&t=fe&referer={self.dataurl}&s={self.sss}"
            headers = {
                'accept-encoding': 'gzip, deflate, br',
                'pragma': 'no-cache',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-US,en;q=0.9,sr;q=0.8'
            }
            s = requests.Session()
            r = s.get(captchalink, proxies = self.s.proxies, headers = headers)   
            if r.status_code == 200:
                ciao = r.text
                print('ciao')
                self.challenge = ciao.split("challenge: '")[1].split("',")[0]
                self.gt = ciao.split("gt: '")[1].split("',")[0]
                self.ip = ciao.split("'&x-forwarded-for=' + encodeURIComponent('")[1].split("'")[0]
                self.initialcid = ciao.split("&icid=' + encodeURIComponent('")[1].split("'")[0]
                self.hsh = ciao.split("&hash=' + encodeURIComponent('")[1].split("'")[0]
                self.ip = ciao.split("(IP ")[1].split(")")[0]
                self.warn('Solving captcha...')
                x = self.solve()
                if x == None:
                    print('a')
                    x = self.solve()
                else:
                    print(x)
                #self.get_ddCaptchaChallenge()
                #dd_url = 'https://geo.captcha-delivery.com/captcha/check?cid=' + self.cid + '&icid=' + self.initialcid +'&ccid=' + 'null' +'&g-recaptcha-response=' + self.captcha +'&hash=' + self.hsh +'&ua=' + 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' +'&referer=' + f'https://{self.domain}/' +'&parent_url=' + f'https://{self.domain}/' + '&x-forwarded-for=' + '&captchaChallenge=' + str(self.result) + '&s=' + str(self.sss)
                #r = requests.get(dd_url, headers = headers)
                #if r.status_code == 200:
                #    jsondd = json.loads(r.text)
                #    dd = jsondd['cookie']
                #    dd = dd.split('datadome=')[1].split(';')[0]
                #    self.cookie_obj = requests.cookies.create_cookie(domain=f".aw-lab.com",name='datadome',value=dd)
                #    self.s.cookies.set_cookie(self.cookie_obj)
                #    return self.success('Datadome done, proceding...')
                #else:
                #    self.s.cookies.clear()
                #    self.build_proxy()
                #    return self.error('Datadome failed, retrying...')
            elif r.status_code == 403:
                self.s.cookies.clear()
                self.build_proxy()
                return self.error('Proxy banned, restarting...')
            else:
                self.error('Datadome failed, restarting...')
                self.s.cookies.clear()
                self.build_proxy()
                return self.error('Datadome failed, restarting...')
        except Exception as e:
            self.s.cookies.clear()
            self.build_proxy()
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

    def tokenn(self):
        i = 0
        self.warn('Getting token...')
        while True:
            try:
                r = self.s.get(
                    f'{self.domain}on/demandware.store/Sites-Courir-FR-Site/fr_FR/Login-Show',
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if r.status_code == 200:
                    self.csrf = r.text.split('csrf_token" value="')[1].split('"')[0]
                    self.loginx = r.text.split('for="dwfrm_login_username_')[1].split('"')[0]
                    self.passwx = r.text.split('for="dwfrm_login_password_')[1].split('"')[0]
                    self.success('Succesfully got token!')
                    break
                else:
                    self.error(f'Failed getting token: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting token: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.login()

    def login(self):
        i = 0
        self.stop = False
        self.warn('Logging in...')
        code = self.solve_v3('https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/Login-Show')
        payload = {
            'g-recaptcha-response': code,
            'dwfrm_login_username_d0xnltwofxue': self.email,
            'dwfrm_login_password_d0lyxzqxoxnz': self.password,
            'dwfrm_login_login': 'Login',
            'csrf_token': self.csrf
        }
        print(payload)
        while True:
            try:
                r = self.s.post(
                    f'{self.domain}on/demandware.store/Sites-Courir-FR-Site/en_FR/Login-LoginForm?scope=',
                    data = payload,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if r.status_code == 302 and '/account' in r.headers['location']:
                    self.success('Succesfully logged in!')
                    break
                elif r.status_code == 302 and '/DDUser-Challenge' in r.headers['location']:
                    self.error(f'Datadome found while logging in, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 302:
                    print(r.headers)
                    self.error('Failed logging in: wrong credentials')
                    self.stop = True
                    break
                else:
                    self.error(f'Failed logging in: {r.status_code}, retrying...')
                    print(r.headers)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        if self.stop:
            sys.exit()
        else:
            self.getprod()

    def getprod(self):
        i = 0
        self.warn('Getting product page...')
        while True:
            try:
                r = self.s.get(
                    f'{self.domain}on/demandware.store/Sites-Courir-FR-Site/en_FR/Product-Variation?pid={self.sku}&format=ajax',
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if r.status_code == 200:
                    continue
                    soup = bs(r.text, features='lxml')
                    self.title = soup.find("span", {"itemprop":"name"}).text
                    xxx = soup.find('form',{'method':'post'})
                    produc = xxx.find('div',{'class':'product-variations size-variation js-product-size-variations'})
                    vic = produc.find('ul',{'class':'swatches clearfix size'}).find_all('li')
                    instock = []
                    var = []
                    for n in vic:
                        if 'unselectable' not in n['class']:
                            var.append(n.find('a',{'class':'swatchanchor'})['href'])
                            instock.append(n.find('a',{'class':'swatchanchor'})['href'].split('_size=')[1])
                    connect = zip(instock, var)
                    self.connect = list(connect)
                    if self.size == "RANDOM":
                        self.success(f'{self.title} in stock!')
                        self.connetto = random.choice(self.connect)
                        self.sizeprint = self.connetto[0]
                        self.varlink = self.connetto[1]
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
                            if str(self.size1) <= str(x[0]) <= str(self.size2):
                                self.sizerange.append(x[0])
                        if len(self.sizerange) < 1:
                            self.warn(f'{self.title} size {self.size} OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        else:
                            self.sizerandom = random.choice(self.sizerange)
                            self.success(f'{self.title} size {self.sizerandom} in stock!')
                            for i in self.connect:
                                if self.sizerandom in i[0]:
                                    self.sizeprint = self.connetto[0]
                                    self.varlink = self.connetto[1]
                            break
                    else:
                        for element in self.connect:
                            if self.size == element[0]:
                                self.success(f'{self.title} size {self.size} in stock!')
                                self.sizeprint = self.connetto[0]
                                self.varlink = self.connetto[1]
                        break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                print(traceback.format_exc())
                self.error(f'Exception while getting product page: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.variant()

    def variant(self):
        self.warn('Getting variant...')
        i = 0
        while True:
            try:
                r = self.s.get(
                    f'{self.varlink}&format=ajax',
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if r.status_code == 200:
                    self.variantx = r.text.split("id: '")[1].split("'")[0]
                    self.success('Succesfully got variant!')
                    break
                else:
                    self.error(f'Failed logging in: {r.status_code}, retrying...')
                    print(r.headers)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.atc()
    def atc(self):
        global carted
        self.fail = False   
        head = {
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer':f'https://www.courir.com/fr/p/phoenix-{self.sku}.html',
            'x-requested-with': 'XMLHttpRequest'
        }
        self.s.headers.update(head)
        self.warn('Adding to cart...')
        i = 0
        payload = {
            'cartAction': 'add',
            'pid': self.variantx
        }
        while True:
            try:
                r = self.s.post(
                    f'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/Cart-AddProduct?format=ajax',
                    data = payload,
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if 'datadome/user_challenge' in r.text:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                if r.status_code == 200:
                    self.check = (r.text.split('minicart-quantity">')[1].split('<')[0]).strip()
                    if self.check == '1':
                        self.success('Succesfully added to cart!')
                        carted = carted + 1
                        self.bar()
                        break
                    else:
                        self.error('Failed adding to cart, retrying...')
                        print(r.text)
                        self.fail = True
                        break
                else:
                    self.error(f'Failed logging in: {r.status_code}, retrying...')
                    print(r.headers)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        if self.fail:
            self.getprod()
        self.checkout()

    def checkout(self):
        self.warn('Getting checkout page...')
        i = 0
        while True:
            try:
                r = self.s.get(
                    'https://www.courir.com/fr/shipping',
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if r.status_code == 200 and r.url == 'https://www.courir.com/fr/shipping':
                    self.csrf2 = r.text.split('csrf_token" value="')[1].split('"')[0]
                    self.success('Succesfully got checkout page!')
                    break
                else:
                    self.error(f'Failed logging in: {r.status_code}, retrying...')
                    print(r.headers)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.ship()

    def ship(self):
        self.warn('Submitting ship...')
        payload = {
            'dwfrm_singleshipping_shippingAddress_shippingMethodID': 'Livraison_Domicile',
            'dwfrm_singleshipping_addressList': 'Defaut',
            'dwfrm_singleshipping_shippingAddress_addressFields_addressType': 'CUSTOMER',
            'dwfrm_singleshipping_shippingAddress_addressFields_addressID': 'Defaut',
            'dwfrm_singleshipping_shippingAddress_keepShippingAddressInput': 'true',
            'dwfrm_billing_save': 'true',
            'dwfrm_billing_addressList': 'Defaut',
            'dwfrm_billing_billingAddress_addressID': 'Defaut',
            'dwfrm_singleshipping_shippingAddress_save': 'Valider',
            'csrf_token':self.csrf2
        }
        head = {
            'content-type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.courir.com/fr/shipping',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        }
        self.s.headers.update(head)
        i = 0
        while True:
            try:
                r = self.s.post(
                    f'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/COShipping-SingleShipping',
                    data = payload,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                print(r.url)
                print(r.text)
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if r.status_code == 302 and r.headers['Location'] == 'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/COPayment-Start':
                    self.success('Succesfully submitted ship!')
                    break
                elif r.status_code == 302:
                    self.error('Failed submitting ship, rotating proxies...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Failed logging in: {r.status_code}, retrying...')
                    print(r.headers)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.paymentstart()
    
    def paymentstart(self):
        self.warn('Getting payment page...')
        i = 0
        while True:
            try:
                r = self.s.get(
                    'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/COPayment-Start',
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if r.status_code == 200:
                    self.csrf3 = r.text.split('csrf_token" value="')[1].split('"')[0]
                    self.success('Succesfully got payment page!')
                    break
                else:
                    self.error(f'Failed logging in: {r.status_code}, retrying...')
                    print(r.headers)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.payment()

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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
        return encryptedAesData

    def payment(self):
        self.warn('Submitting payment...')
        self.declined = False
        cardnu = self.card[-4:]
        cardnum = f'************{cardnu}'
        ua = self.s.headers['User-Agent']
        #10001|E348EBBFF1F0C3FCD819E9433A29D1ED7218D5C48EAFF60F58CE3ADD10F34A3D2FA7FEF3248BFED219534DCC83D45578F24BA9FA870FC4DE900CBCB92E4AB1988F9DCBA93B7392D77E7550B1A9E91F66C79358EAF8808230414A9F3ECB9129F7369E95A462EA99DB52167E4583D06975DE1C28100355B1CEA372B83EDD19DBBFA1A4F1566F656DC8F9D93D4FA5341B4F3D8CA94F56CDF8F666C1D6F4AA077BC998FC3A3F74BED84B34CD6B9888D831B0546272A185F9DA9CF8C09CCDA8344A0F7CE5291D13FE6DF24E5C51FA8E35A0885E7113DB45DB121A54E367E7C9695CE24FE7FCBCA305363B57CFEA8B70DBA192CCD9BC68B2328D3465DD9C2960AEA93F
        cardtype = identify_card_type(self.card)
        if cardtype == "MasterCard":
            card_type = "mc"
        elif cardtype == "Visa":
            card_type = "visa"
        clientdata = {"version":"1.0.0","deviceFingerprint":"ryEGX8eZpJ0030000000000000KZbIQj6kzs0050271576cVB94iKzBGAfeuwDADoz5S16Goh5Mk0045zgp4q8JSa00000qZkTE00000q6IQbnyNfpEC4FlSABmQ:40","persistentCookie":[],"components":{"userAgent":"a251d26aeb7e05ea8eee1c1318ef94d5","webdriver":0,"language":"en","colorDepth":24,"deviceMemory":8,"pixelRatio":1,"hardwareConcurrency":16,"screenWidth":1920,"screenHeight":1080,"availableScreenWidth":1920,"availableScreenHeight":1040,"timezoneOffset":-120,"timezone":"Europe/Rome","sessionStorage":1,"localStorage":1,"indexedDb":1,"addBehavior":0,"openDatabase":1,"platform":"Win32","plugins":"c08e978ab02e3595bfb9cb7ebefef333","canvas":"77f1c5b57a6e2d7894baddf6b3586631","webgl":"4f8102d43550787d458be24e0b543e30","webglVendorAndRenderer":"Google Inc. (NVIDIA)~ANGLE (NVIDIA, NVIDIA GeForce RTX 3090 Direct3D11 vs_5_0 ps_5_0, D3D11-27.21.14.6089)","adBlock":0,"hasLiedLanguages":0,"hasLiedResolution":0,"hasLiedOs":0,"hasLiedBrowser":0,"fonts":"bc08e11f73721bd53372bd37483d4589","audio":"902f0fe98719b779ea37f27528dfb0aa","enumerateDevices":"320ebbd4ee5e2532c9aa55c27a15ae8b"}}
        riskdata = clientdata.encode(encoding='UTF-8')
        risk = {"riskData":{"clientData":riskdata},"paymentMethod":{"type":"scheme","holderName":f"{self.name} {self.surname}","encryptedCardNumber":self.maincard(pan = self.card, key = "10001|E348EBBFF1F0C3FCD819E9433A29D1ED7218D5C48EAFF60F58CE3ADD10F34A3D2FA7FEF3248BFED219534DCC83D45578F24BA9FA870FC4DE900CBCB92E4AB1988F9DCBA93B7392D77E7550B1A9E91F66C79358EAF8808230414A9F3ECB9129F7369E95A462EA99DB52167E4583D06975DE1C28100355B1CEA372B83EDD19DBBFA1A4F1566F656DC8F9D93D4FA5341B4F3D8CA94F56CDF8F666C1D6F4AA077BC998FC3A3F74BED84B34CD6B9888D831B0546272A185F9DA9CF8C09CCDA8344A0F7CE5291D13FE6DF24E5C51FA8E35A0885E7113DB45DB121A54E367E7C9695CE24FE7FCBCA305363B57CFEA8B70DBA192CCD9BC68B2328D3465DD9C2960AEA93F"),"encryptedExpiryMonth":self.mainmonth(expiry_month = self.month, key = "10001|E348EBBFF1F0C3FCD819E9433A29D1ED7218D5C48EAFF60F58CE3ADD10F34A3D2FA7FEF3248BFED219534DCC83D45578F24BA9FA870FC4DE900CBCB92E4AB1988F9DCBA93B7392D77E7550B1A9E91F66C79358EAF8808230414A9F3ECB9129F7369E95A462EA99DB52167E4583D06975DE1C28100355B1CEA372B83EDD19DBBFA1A4F1566F656DC8F9D93D4FA5341B4F3D8CA94F56CDF8F666C1D6F4AA077BC998FC3A3F74BED84B34CD6B9888D831B0546272A185F9DA9CF8C09CCDA8344A0F7CE5291D13FE6DF24E5C51FA8E35A0885E7113DB45DB121A54E367E7C9695CE24FE7FCBCA305363B57CFEA8B70DBA192CCD9BC68B2328D3465DD9C2960AEA93F"),"encryptedExpiryYear":self.mainyear(expiry_year = self.year, key = "10001|E348EBBFF1F0C3FCD819E9433A29D1ED7218D5C48EAFF60F58CE3ADD10F34A3D2FA7FEF3248BFED219534DCC83D45578F24BA9FA870FC4DE900CBCB92E4AB1988F9DCBA93B7392D77E7550B1A9E91F66C79358EAF8808230414A9F3ECB9129F7369E95A462EA99DB52167E4583D06975DE1C28100355B1CEA372B83EDD19DBBFA1A4F1566F656DC8F9D93D4FA5341B4F3D8CA94F56CDF8F666C1D6F4AA077BC998FC3A3F74BED84B34CD6B9888D831B0546272A185F9DA9CF8C09CCDA8344A0F7CE5291D13FE6DF24E5C51FA8E35A0885E7113DB45DB121A54E367E7C9695CE24FE7FCBCA305363B57CFEA8B70DBA192CCD9BC68B2328D3465DD9C2960AEA93F"),"encryptedSecurityCode":self.maincvv(cvc = self.cvv, key = "10001|E348EBBFF1F0C3FCD819E9433A29D1ED7218D5C48EAFF60F58CE3ADD10F34A3D2FA7FEF3248BFED219534DCC83D45578F24BA9FA870FC4DE900CBCB92E4AB1988F9DCBA93B7392D77E7550B1A9E91F66C79358EAF8808230414A9F3ECB9129F7369E95A462EA99DB52167E4583D06975DE1C28100355B1CEA372B83EDD19DBBFA1A4F1566F656DC8F9D93D4FA5341B4F3D8CA94F56CDF8F666C1D6F4AA077BC998FC3A3F74BED84B34CD6B9888D831B0546272A185F9DA9CF8C09CCDA8344A0F7CE5291D13FE6DF24E5C51FA8E35A0885E7113DB45DB121A54E367E7C9695CE24FE7FCBCA305363B57CFEA8B70DBA192CCD9BC68B2328D3465DD9C2960AEA93F"),},"browserInfo":{"acceptHeader":"*/*","colorDepth":24,"language":"en","javaEnabled":False,"screenHeight":1080,"screenWidth":1920,"userAgent":ua,"timeZoneOffset":-120}}
        print(risk)
        payload = {
            'dwfrm_adyPaydata_adyenStateData': risk,
            'dwfrm_adyPaydata_paypalStateData': '',
            'dwfrm_billing_paymentMethods_creditCard_number': f'************{cardnum}',
            'dwfrm_billing_paymentMethods_creditCard_type': card_type,
            'adyenPaymentMethod': '<input name="brandCode" type="radio" value="scheme" id="rb_scheme"><span class="paymentMethod__adyen__radio-option"></span><span class="paymentMethod__adyen__label">Carte bancaire</span>',
            'adyenIssuerName': '',
            'brandCode': 'scheme',
            'dwfrm_payment_save': '',
            'dwfrm_adyPaydata_adyenFingerprint': '',
            'csrf_token': self.csrf3
        }
        print(payload)
        head = {
            'Referer': 'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/COPayment-Start',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        }
        self.s.headers.update(head)
        print(self.s.headers)
        i = 0
        while True:
            try:
                r = self.s.post(
                    f'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/COPayment-Payment',
                    data = payload,
                    timeout = self.timeout
                )
                print(r.text)
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    self.warn('Datadome found, proceding...')
                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]
                    self.connection2()
                    i = i + 1
                    continue
                if r.status_code == 200:
                    self.result = r.text.split('resultCode" value="')[1].split('"')[0]
                    print(self.result)
                    self.token3d = r.text.split('token3ds2" value="')[1].split('"')[0]
                    self.postURL = 'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/Adyen-Redirect3DS2?utm_nooverride=1'
                    self.Pareq = 'null'
                    break
                elif r.status_code == 400:
                    print(r.text)
                    continue
                #if r.status_code == 302 and r.headers['Location'] == 'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/COPayment-Start':
                #    self.error('Card declined/Something wrong with your card while submitting payment!')
                #    self.declined = True
                #    break
                else:
                    self.error(f'Failed logging in: {r.status_code}, retrying...')
                    print(r.text)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        #if self.decline:
        #    self.declined()
        #asyncio.run(self.main3d())
    
    async def main3d(self):

        self.warn("Waiting for 3D secure..")

        try:

            chrome = await launch(
                handleSIGINT=False,
                handleSIGTERM=False,
                handleSIGHUP=False,
                headless=False,
                logLevel='WARNING',
                args=[
                    f'--window-size={750},{750}',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
                ]
            )

            page = (await chrome.pages())[0]
            self.dumped = json.loads(self.dumped)
            await page.setCookie(*self.dumped)
            await page.setRequestInterception(True)
            self._3dsAccepted = False
            self._3dsCancelled = False

            #webhook = await send_3ds_webhook(
            #    f'New Balance {self.country.upper()}',
            #    self.pid,
            #    self.chosenSize['displaySize'],
            #    self.webhookPrice,
            #    self._email,
            #    self.task_name,
            #    mode=self.mode,
            #    description=f'Solve 3DS on browser',
            #    thumbnail=self.image
            #)

            async def intercept(request):
                if 'ciao' in request.url:
                    self._3dsAccepted = True
                    self.threeddata = request._postData
                    self.threedheaders = request._headers
                    self.threedurl = request.url
                    await request.abort()
                    await chrome.close()
                    return True
                else:
                    self._3dsAccepted = False
                    await request.continue_()

            page.on('request', lambda req: asyncio.ensure_future(intercept(req)))
            script = html.format(self.postURL, self.pareq, self.termurl, self.MD)
            await page.evaluate(script)

            while self._3dsAccepted == False:
                try:
                    dimensions = await page.evaluate('''() => {
                        return {
                            width: document.documentElement.clientWidth,
                            height: document.documentElement.clientHeight,
                            deviceScaleFactor: window.devicePixelRatio,
                        }
                    }''')
                except Exception as e:
                    if 'page has been closed' in str(e) and self._3dsAccepted != True:
                        self.warn('3DS Window closed.')
                        return False
                await asyncio.sleep(storage.delay)

        except Exception as e:
            self.error(f"Exception while handling 3DS: {e}")
            return False

    
     