import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from selenium import webdriver
from autosolveclient.autosolve import AutoSolve
import copy
import traceback, numpy
from urllib.parse import unquote
from pyppeteer import launch
import asyncio
from mods.errorHandler import errorHandler
import traceback
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

HANDLER = errorHandler(__file__)
html = '''document.write("<!DOCTYPE html><html><body><form action='{}' method='POST'><input type='hidden' name='PaReq' value='{}'><input type='hidden' name='TermUrl' value='{}'><input type='hidden' name='MD' value='{}'></form><script>document.forms[0].submit()</script></body></html>")'''

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
            r'cpo.src\s*=\s*"/cdn-cgi/challenge-platform/?\w?/?\w?/orchestrate/captcha/v1"',
            resp.text,
            re.M | re.S
        )
                and re.search(r'window._cf_chl_enter\(', resp.text, re.M | re.S)
        )
    except AttributeError:
        pass

    return False
cloudscraper.CloudScraper.is_New_Captcha_Challenge = is_New_Captcha_Challenge


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
                and re.search(r'window._cf_chl_enter\(', resp.text, re.M | re.S)
        )
    except AttributeError:
        pass

    return False
cloudscraper.CloudScraper.is_New_IUAM_Challenge = is_New_IUAM_Challenge
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
    CAPTCHA = config['captcha']['b4b']
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

class ChallengeSolver():
    def __init__(self, s):
        self.s = s

    def getCookieByName(self, name):
        for c in self.s.cookies:
            if c.name == name:
                return c.value
        return None

    def addCookie(self, name, value, domain):
        cookie_obj = requests.cookies.create_cookie(domain = domain, name = name, value = value)
        self.s.cookies.set_cookie(cookie_obj)

    def xorKeyValueASeparator(self, keyStr, sourceStr):
        keyLength = len(keyStr)
        sourceLen = len(sourceStr)
        targetStr = ""
        for i in range(sourceLen):
            rPos = i % keyLength
            a = ord(sourceStr[i])
            b = ord(keyStr[rPos])
            c = a ^ b
            d = str(c) + "a"
            targetStr += d
        return targetStr

    def solve_normal_challenge(self, r):
        in1 = r.text.split('"vii="+m2vr("')[1].split('"')[0]
        sbtsckCookie = r.text.split('document.cookie="sbtsck=')[1].split(';')[0]
        self.addCookie("sbtsck", sbtsckCookie, "www.basket4ballers.com")

        sp = r.text.split('function genPid() {return String.fromCharCode(')[1]
        prid = chr(int(sp.split(')')[0])) + chr(int(sp.split(')+String.fromCharCode(')[1].split(')')[0]))
        gprid = prid
        
        prlst = self.getCookieByName("PRLST")
        if (prlst == None or (not (prid in prlst) and len(prlst.split('/')) < 5)):
            if prlst and prlst != '':
                prlst += "/"
            elif not prlst:
                prlst = ''
            self.addCookie("PRLST", prlst + prid, "www.basket4ballers.com"    )

        cookieUTGv2 = self.getCookieByName("UTGv2")
        cookieUTGv2Splitted = cookieUTGv2
        if cookieUTGv2 != None and "-" in cookieUTGv2Splitted:
            cookieUTGv2Splitted = cookieUTGv2Splitted.split("-")[1]
        if cookieUTGv2 == None or cookieUTGv2 != cookieUTGv2Splitted:
            if(cookieUTGv2 == None):
                cookieUTGv2 = r.text.split('this.sbbsv("')[1].split('"')[0]
                self.addCookie("UTGv2", cookieUTGv2, "www.basket4ballers.com")
            else:
                cookieUTGv2 = cookieUTGv2Splitted
                self.s.cookies.set('UTGv2', cookieUTGv2, domain='www.basket4ballers.com', path='/')

        ts = int(time.time()) - int(r.text.split('/1000)-')[1].split(")")[0])
        r2 = self.s.get(f'https://basket4ballers.com/sbbi/?sbbpg=sbbShell&gprid={gprid}&sbbgs={cookieUTGv2}&ddl={ts}')
        
        if "sbrmpIO=start()" in r2.text:
            return 3

        if not "D-" in cookieUTGv2:
            cookieUTGv2 = "D-" + cookieUTGv2
            self.s.cookies.set('UTGv2', cookieUTGv2, domain='www.basket4ballers.com', path='/')

        trstr = r2.text.split('{sbbdep("')[1].split('"')[0].strip()
        trstrup = trstr.upper()
        data = {
            "cdmsg": self.xorKeyValueASeparator(trstrup, "v0phj7cahz-41-zezw4iqrr-w7mccahwofo-egdctq9g4nf-noieo-90.3095389639745667"),
            "femsg": 1,
            "bhvmsg": self.xorKeyValueASeparator(trstrup, "0pvc0b7oa39j-iws9o"),
            "futgs": "",
            "jsdk": trstr,
            "glv": self.xorKeyValueASeparator(trstrup, "N"),
            "lext": self.xorKeyValueASeparator(trstrup, "[0,0]"),
            "sdrv": 0
        }
        r3 = self.s.post(f'https://basket4ballers.com/sbbi/?sbbpg=sbbShell&gprid={gprid}&sbbgs={cookieUTGv2}&ddl={ts}', data = data)
        if 'smbtFrm()' in r3.text:
            return 2
        else:
            return 0

    def solve_captcha_challenge(self, r):
        html = r.text.split("data:image/png;base64,")[1].split('"')[0]
        captchaID = r.text.split('SBM.captchaInput.id="')[1].split('"')[0]
        sbtsckCookie = r.text.split('doc.cookie="sbtsck=')[1].split(';')[0]
        self.addCookie('sbtsck', sbtsckCookie, 'www.basket4ballers.com')
        captchaIDlen = len(captchaID)
        totalTime = 0
        output = ""
        for i in range(3):
            t = random.randint(0,2)
            if i == 0:
                t += random.randint(5,15)
            c = t if t < captchaIDlen else captchaIDlen - 1
            output += captchaID[c]
            totalTime += t
        output = str(totalTime) + "/" + output
        pvstr = output
        solver = TwoCaptcha(config['2captcha'])
        result = solver.normal(html, caseSensitive=1)
        self.addCookie('pvstr', pvstr, 'www.basket4ballers.com')
        self.addCookie('cnfc', result['code'], 'www.basket4ballers.com')
        return 1
    
class B4B():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
        
        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'basket4ballers/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "basket4ballers/proxies.txt")
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
                requestPostHook=self.injection
        )
        
        self.link = row['LINK']
        self.size = row['SIZE']
        self.account = row['ACCOUNT']
        self.password = row['PASSWORD']
        self.zipcode = row['ZIPCODE']
        self.payment = row['PAYMENT']
        self.mode = row['MODE']
        self.card = row['CARD NUMBER']
        self.month = row['EXP MONTH']
        self.year = row['EXP YEAR']
        self.cvv = row['CVV']

        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.timeout = 120
        self.balance = balancefunc()
        self.version = version
        self.bar()
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.delay = int(config['delay'])
        self.build_proxy()
        self.discord = DISCORD_ID

        #if "/en/" in self.link:
        #    self.link = self.link.replace("/en/","/fr/")

        if self.link == 'METALLICPURPLE':
            self.link = 'https://www.basket4ballers.com/fr/baskets-lifestyle/27029-air-jordan-1-high-og-court-purple-wmns-cd0461-151.html?ph=3728647213'

        self.warn('Task started!')
        
        if self.mode == "FAST":
            self.getprod()
        else:
            self.getchallenge()

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [BASKET4BALLERS] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [BASKET4BALLERS] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [BASKET4BALLERS] - {text}'
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
                f'Phoenix AIO {self.version} - Running BASKET4BALLERS | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running BASKET4BALLERS | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

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
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.recaptcha(sitekey='6LcpBD0UAAAAALwqETJkSSuQZYcavdDKu1sy_XPN', url=url)
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
                        "websiteKey": "6LcpBD0UAAAAALwqETJkSSuQZYcavdDKu1sy_XPN"
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
                    "siteKey" : "6LcpBD0UAAAAALwqETJkSSuQZYcavdDKu1sy_XPN", 
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

    def handle_challenge(self, r):
        challenge_solver = ChallengeSolver(self.s)
        if '"vii="' in r.text:
            self.warn('Solving challenge...')
            try:
                result = challenge_solver.solve_normal_challenge(r)
                if result in [1,2]:
                    self.success(f'Successfully solved challenge! [{result}]')
                    return True
                elif result == 3:
                    self.success(f'Successfully solved challenge! [1]')
                    return False
                else:
                    self.error('Error solving challenge...')
                    return False
            except Exception as e:
                self.error(f'Exception solving challenge: {e.__class__.__name__}')
                return False
        elif 'captchaImageInline' in r.text:
            self.warn('Solving captcha challenge...')
            try:
                result = challenge_solver.solve_captcha_challenge(r)
                if result in [1,2]:
                    self.success(f'Successfully solved challenge! [{result}]')
                    return True
                elif result == 3:
                    return False
                else:
                    self.error('Error solving challenge...')
                    return False
            except Exception as e:
                self.error(f'Exception solving challenge: {e.__class__.__name__}')
                return False

    def getchallenge(self):
        self.warn('Getting login page...')
        while True:
            try:
                r = self.s.get(
                    'https://www.basket4ballers.com/fr/authentification',
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    result = self.handle_challenge(r)
                    if not result:
                        continue
                    else:
                        break
                if r.status_code == 200:
                    self.success('Succesfully got login page...')
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
                    self.error(f'Error while loggin in: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.login()

    def login(self):
        self.stop2 = False
        self.warn('Attempting login...')
        while True:
            try:
                self.warn('Solving captcha...')
                code = self.solve_v2('https://www.basket4ballers.com/fr/authentification?back=my-account')
                self.success('Captcha solved!')
                payload = {
                    'email': self.account,
                    'passwd': self.password,
                    'g-recaptcha-response':code,
                    'back': 'my-account',
                    'SubmitLogin': 'Se connecter'
                }
                r = self.s.post(
                    "https://www.basket4ballers.com/fr/authentification", 
                    data = payload, 
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if r.status_code == 302 and 'mon-compte' in r.headers['Location']:
                    self.success('Successfully logged in!')
                    break
                if r.status_code == 200:
                    self.success('Wrong credentials, stopping')
                    self.stop2 = True
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
                    self.error(f'Error while loggin in: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while logging in: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        if self.stop2:
            sys.exit()
        if self.mode == "FAST":
            self.shipping()
        else:
            self.clear()
            self.getprod()

    def clear(self):
        self.warn('Checking cart...')
        while True:
            try:
                r = self.s.get(
                    "https://www.basket4ballers.com/fr/commande", 
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                if r.status_code == 200:
                    try:
                        soup = bs(r.text, features='lxml')
                        cartdel = soup.find('a',{'class':'ajax_cart_block_remove_link block-cart__remove-product'})['href']
                        self.delete = cartdel
                        self.warn('Clearing cart...')
                        x = self.s.get(
                            self.delete, 
                            timeout = self.timeout
                        )
                        if x.status_code == 200:
                            self.error('Cart not empty yet, retrying...')
                            continue
                        elif x.status_code == 403:
                            self.error('Proxy banned, retrying...')
                            self.build_proxy()
                            time.sleep(self.delay)
                            continue
                        elif x.status_code == 429:
                            self.error('Rate limit, retryng...')
                            self.build_proxy()
                            time.sleep(self.delay)
                            continue
                        elif x.status_code >= 500 and x.status_code <= 600:
                            self.warn('Site dead, retrying...')
                            time.sleep(self.delay)
                            continue
                        else:
                            self.error(f'Error while clearing cart: {x.status_code}, retrying...')
                            time.sleep(self.delay)
                            self.build_proxy()
                            continue
                    except:
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
                self.s.cookies.clear()
                self.build_proxy()
                continue
        return self.success('Cart is empty, proceeding...')

    def checkcart(self):
        self.warn('Checking cart...')
        self.cartempty = True
        while True: 
            try:
                r = self.s.get(
                    "https://www.basket4ballers.com/fr/commande", 
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                if r.status_code == 200:
                    if "var txtProduct = 'product';" in r.text:
                        self.cartempty = False
                        break
                    else:
                        self.error('Cart is empty, restarting...')
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
                self.s.cookies.clear()
                self.build_proxy()
                continue
        if self.cartempty:
            self.getprod()
        else:
            self.shipping()

    def getprod(self):
        self.warn('Getting product page...')
        while True:
            try:
                r = self.s.get(
                    self.link, 
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if '<em class="caps">sold out</em>' in r.text.lower():
                    self.warn('Prodcut OOS, monitoring...')
                    time.sleep(self.delay)
                    continue
                if 'countdown' in r.text:
                    self.warn('Product not released yet, monitoring...')
                    time.sleep(self.delay)
                    continue
                if r.status_code == 200:
                    self.check = r.text
                    soup = bs(r.text, features='lxml')
                    self.title = soup.find("span", {"itemprop": "name"}).text
                    self.tokennn = r.text.split("static_token='")[1].split("';")[0]
                    try:
                        self.img = r.text.split('rel="gal1" href="')[1].split('"')[0]
                    except:
                        self.img = "https://cdn2.basket4ballers.com/img/logo.jpg"
                    var = r.text.split("var combinations=")[1].split("var combinationsFromController")[0]
                    var2 = var[:-1]
                    self.prodid = var.split('"reference":"IDP')[1].split('--')[0]                      
                    r_json = json.loads(var2)
                    variant = list(r_json.keys())
                    quantity = []
                    size = []
                    for i in variant:
                        quant = r_json[i]
                        quantity.append(quant['quantity'])
                        sizee = quant['attributes_values']
                        size.append(sizee['15'])
                    connect = zip(variant, size, quantity)
                    self.connect = list(connect)
                    if "Disponible dans" in r.text:
                        self.warn(f'{self.title} not dropped yet, monitoring...')
                        time.sleep(self.delay)
                        continue
                    self.listaxatc = []
                    if self.mode == "ATC":
                        for element in self.connect:
                            self.listaxatc.append(element)
                    else:
                        for element in self.connect:
                            if element[2] != 0:
                                self.listaxatc.append(element)
                    if len(self.listaxatc) < 1:
                        open(f'b4bOOSlog{int(time.time() * 1000)}.html', 'w+', encoding='utf-8').write(r.text)
                        self.warn(f'{self.title} OOS, monitoring...')
                        time.sleep(self.delay)
                        continue
                    else:
                        if self.mode == "ATC":
                            self.warn('ATC mode chosen, proceeding')
                        else:
                            self.success(f'{self.title} is in stock...')                       
                        break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Product page not loaded, retrying...')
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
                self.error(f'Exception while getting product page: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.atc()

    def atc(self):
        global carted
        self.warn('Adding to cart...')
        headers = {
            'Accept' : 'application/json, text/javascript, */*; q=0.01',
            'Referer' : self.link,
            'X-Requested-With' : 'XMLHttpRequest',
            'x-mod-sbb-ctype': 'xhr'
        }
        self.isfailed = False
        if 'grecaptcha-container' in self.check:
            self.warn('Solving ATC captcha...')
            captcha = self.solve_v2(self.link)
            self.success('Captcha solved!')
        else:
            captcha = ''
        sizes = []
        variants = []
        for element in self.listaxatc:
            sizes.append(element[1])
            variants.append(element[0])
        if self.size == "RANDOM":
            self.listascelta = random.choice(self.listaxatc)
            self.sizescelta = self.listascelta[1]
            self.variantescelta = self.listascelta[0]
        elif '-' in self.size:
            self.size1 = float(self.size.split(',')[0])
            self.size2 = float(self.size.split(',')[1])
            self.sizerange = []
            self.variantrange = []
            for i in self.listaxatc:
                if self.size1 <= float(i[1]) <= self.size2:
                    self.sizerange.append(i[1])
                    self.variantrange.append(i[0])
            scelto = zip(self.variantrange, self.sizerange)
            scelto = list(scelto)
            scelta = random.choice(scelto)
            self.sizescelta = scelta[1]
            self.variantescelta = scelta[0]
        elif ',' in self.size:
            self.size1 = float(self.size.split(',')[0])
            self.size2 = float(self.size.split(',')[1])
            self.sizerange = []
            self.variantrange = []
            for i in self.listaxatc:
                if self.size1 <= float(i[1]) <= self.size2:
                    self.sizerange.append(i[1])
                    self.variantrange.append(i[0])
            scelto = zip(self.variantrange, self.sizerange)
            scelto = list(scelto)
            scelta = random.choice(scelto)
            self.sizescelta = scelta[1]
            self.variantescelta = scelta[0]
        else:
            for i in self.listaxatc:
                if self.size == i[1]:
                    self.variantescelta = i[0]
                    self.sizescelta = i[1]
        payload = {
            'controller' : 'cart',
            'token' : self.tokennn,
            'ajax' : 'true',
            'add' : '1',
            'id_product' : self.prodid,
            'ipa' : self.variantescelta,
            'id_customization' : '',
            'qty' : '1',
            'g-recaptcha-response': captcha
        }
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]
                r = self.s.post(
                    f"https://www.basket4ballers.com/?rand={timestamp}", 
                    data = payload, 
                    headers=headers,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if r.status_code == 200:
                    if f'idCombination":{self.variantescelta}' in r.text:
                        self.idaddress = r.text.split('idAddressDelivery":')[1].split(',')[0]
                        self.cartid = r.text.split('idCombination":')[1].split(',')[0]
                        self.success(f'Added to cart size {self.sizescelta}')
                        carted = carted + 1
                        self.bar()
                        break
                    elif 'not enough products in stock' in r.text:
                        self.warn(f'Failed adding to cart, size {self.sizescelta} is oos, retrying...')
                        self.isfailed = True
                        break
                    elif 'assez de produits en stock' in r.text:
                        self.warn(f'Failed adding to cart, size {self.sizescelta} is oos, retrying...')
                        self.isfailed = True
                        break
                    else:
                        if self.mode == "ATC":
                            self.warn(f'Failed adding to cart size {self.sizescelta}, retrying...')
                            time.sleep(self.delay)
                            continue
                        else:
                            self.warn(f'Failed adding to cart size {self.sizescelta}, retrying...')
                            self.isfailed = True
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
                self.s.cookies.clear()
                self.build_proxy()
                continue
        if self.isfailed:
            #self.warn(f'Failed adding to cart size {self.sizescelta}, retrying...')
            time.sleep(self.delay)
            self.getprod()
        else:
            if self.mode == "FAST":
                self.getchallenge()
            else:
                self.shipping()

    def shipping(self):
        self.warn('Submitting shipping...')
        headers = {
            'Referer' : 'https://www.basket4ballers.com/fr/commande?step=1'
        }
        payload = {
            "d_address_delivery": self.idaddress,
            "same": "1",
            "step": "2",
            "back": "",
            "processAddress": "Suivant"
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.basket4ballers.com/fr/commande", 
                    data = payload, 
                    headers=headers,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if r.status_code == 200:
                    self.success('Succesfully submitted shipping!')
                    self.datakey = "126"
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
                    self.error(f'Error while submitting shipping: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting shipping: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.shiprate()

    def shiprate(self):
        self.warn('Fetching shipping rates...')
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.basket4ballers.com/fr/commande',
        }
        payload = {
            'ajax' : True,
            'method':'updateExtraCarrier',
            'id_address':self.idaddress,
            'id_delivery_option':'126,',
            'token':self.tokennn,
            'allow_refresh':"1"
        }
        while True:
            try:
                num = int(''.join([str(random.randint(0,10)) for _ in range(13)]))
                r = self.s.post(
                    f"https://www.basket4ballers.com/fr/commande?rand={num}",
                    data = payload,
                    headers=headers,
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if r.status_code == 200:
                    self.success(f'Succesfully got shipping rates!') 
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
                    self.error(f'Error while fetching shipping rate: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while fetching shipping rates: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.shippingrates()

    def shippingrates(self):
        self.warn(f'Submitting shipping rates...')
        headers = {
            'Referer' : 'https://www.basket4ballers.com/fr/commande?step=1'
        }
        payload = {
            'delivery_option[337414]' : '126,',
            'relais_codePostal' : self.zipcode,
            'cgv' : '1',
            'step' : '3',
            'back' : '',
            'processCarrier' : 'Suivant'
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.basket4ballers.com/fr/commande", 
                    data = payload, 
                    headers=headers,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if r.status_code == 200:
                    self.success('Succesfully submitted shipping rates!') 
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
                    self.error(f'Error while submitting shipping rate: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting shipping rates: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        if self.payment == "PP":
            self.ppweb = "Paypal"
            self.pagamento()
        else:
            self.ppweb = "CreditCard"
            self.pagamento2()

    def pagamento(self):
        global checkoutnum, failed
        self.warn('Submitting order...')
        payload = {
            'ajax' : '1',
            'onlytoken' : '1',
            'express_checkout' : 'payment_cart',
            'current_shop_url' : 'https://www.basket4ballers.com/fr/commande',
            'bn' : 'PRESTASHOP_EC'
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.basket4ballers.com/modules/paypal/express_checkout/payment.php?&ajax=1&onlytoken=1&express_checkout=payment_cart&current_shop_url=https://www.basket4ballers.com/en/commande&bn=PRESTASHOP_EC", 
                    data = payload,
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if r.status_code == 200:
                    if "EC-" in r.text:
                        token = r.text
                        self.urlfinale =  f"https://www.paypal.com/webscr?cmd=_express-checkout&useraction=commit&token={token}"
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        self.success('Successfully checked out!')
                        break
                    else:
                        self.error('Checkout failed, retrying...')
                        failed = failed + 1
                        self.bar()
                        self.checkcart()
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
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.passcookies()

    def pagamento2(self):
        self.check = False
        global checkoutnum, failed
        self.warn('Submitting order...')
        payload = {
            'systempay_payment_type': 'standard'
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.basket4ballers.com/fr/module/systempay/redirect", 
                    json = payload, 
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if r.status_code == 200:
                    soup = bs(r.text, features='lxml')
                    xx = soup.find('form',{'action':'https://paiement.systempay.fr/vads-payment/'})
                    self.signature = xx.find('input',{'name':'signature'})['value']
                    self.vads_action_mode = xx.find('input',{'name':'vads_action_mode'})['value']
                    self.vads_amount = xx.find('input',{'name':'vads_amount'})['value']
                    self.vads_contrib = xx.find('input',{'name':'vads_contrib'})['value']
                    self.vads_ctx_mode = xx.find('input',{'name':'vads_ctx_mode'})['value']
                    self.vads_currency = xx.find('input',{'name':'vads_currency'})['value']
                    self.vads_cust_address = xx.find('input',{'name':'vads_cust_address'})['value']
                    self.vads_cust_cell_phone = xx.find('input',{'name':'vads_cust_cell_phone'})['value']
                    self.vads_cust_city = xx.find('input',{'name':'vads_cust_city'})['value']
                    self.vads_cust_country = xx.find('input',{'name':'vads_cust_country'})['value']
                    self.vads_cust_email = xx.find('input',{'name':'vads_cust_email'})['value']
                    self.vads_cust_first_name = xx.find('input',{'name':'vads_cust_first_name'})['value']
                    self.vads_cust_id = xx.find('input',{'name':'vads_cust_id'})['value']
                    self.vads_cust_last_name = xx.find('input',{'name':'vads_cust_last_name'})['value']
                    self.vads_cust_phone = xx.find('input',{'name':'vads_cust_phone'})['value']
                    self.vads_cust_state = xx.find('input',{'name':'vads_cust_state'})['value']
                    self.vads_language = xx.find('input',{'name':'vads_language'})['value']
                    self.vads_nb_products = xx.find('input',{'name':'vads_nb_products'})['value']
                    self.vads_order_id = xx.find('input',{'name':'vads_order_id'})['value']
                    self.vads_cust_title = xx.find('input',{'name':'vads_cust_title'})['value']
                    self.vads_order_info = xx.find('input',{'name':'vads_order_info'})['value']
                    self.vads_page_action = xx.find('input',{'name':'vads_page_action'})['value']
                    self.vads_payment_config = xx.find('input',{'name':'vads_payment_config'})['value']
                    self.vads_redirect_error_message = xx.find('input',{'name':'vads_redirect_error_message'})['value']
                    self.vads_redirect_error_timeout = xx.find('input',{'name':'vads_redirect_error_timeout'})['value']
                    self.vads_redirect_success_message = xx.find('input',{'name':'vads_redirect_success_message'})['value']
                    self.vads_redirect_success_timeout = xx.find('input',{'name':'vads_redirect_success_timeout'})['value']
                    self.vads_return_mode = xx.find('input',{'name':'vads_return_mode'})['value']
                    self.vads_ship_to_city = xx.find('input',{'name':'vads_ship_to_city'})['value']
                    self.vads_ship_to_country = xx.find('input',{'name':'vads_ship_to_country'})['value']
                    self.vads_cust_zip = xx.find('input',{'name':'vads_cust_zip'})['value']
                    self.vads_ship_to_first_name = xx.find('input',{'name':'vads_ship_to_first_name'})['value']
                    self.vads_ship_to_last_name = xx.find('input',{'name':'vads_ship_to_last_name'})['value']
                    self.vads_ship_to_phone_num = xx.find('input',{'name':'vads_ship_to_phone_num'})['value']
                    self.vads_ship_to_state = xx.find('input',{'name':'vads_ship_to_state'})['value']
                    self.vads_ship_to_street = xx.find('input',{'name':'vads_ship_to_street'})['value']
                    self.vads_ship_to_street2 = xx.find('input',{'name':'vads_ship_to_street2'})['value']
                    self.vads_ship_to_zip = xx.find('input',{'name':'vads_ship_to_zip'})['value']
                    self.vads_shipping_amount = xx.find('input',{'name':'vads_shipping_amount'})['value']
                    self.vads_site_id = xx.find('input',{'name':'vads_site_id'})['value']
                    self.vads_tax_amount = xx.find('input',{'name':'vads_tax_amount'})['value']
                    self.vads_totalamount_vat = xx.find('input',{'name':'vads_totalamount_vat'})['value']
                    self.vads_trans_date = xx.find('input',{'name':'vads_trans_date'})['value']
                    self.vads_trans_id = xx.find('input',{'name':'vads_trans_id'})['value']
                    self.vads_url_return = xx.find('input',{'name':'vads_url_return'})['value']
                    self.vads_version = xx.find('input',{'name':'vads_version'})['value']
                    self.vads_product_label0 = xx.find('input',{'name':'vads_product_label0'})['value']
                    self.vads_product_amount0 = xx.find('input',{'name':'vads_product_amount0'})['value']
                    self.vads_product_qty0 = xx.find('input',{'name':'vads_product_qty0'})['value']
                    self.vads_product_ref0 = xx.find('input',{'name':'vads_product_ref0'})['value']
                    self.vads_product_type0 = xx.find('input',{'name':'vads_product_type0'})['value']
                    self.vads_product_vat0 = xx.find('input',{'name':'vads_product_vat0'})['value']
                    self.success('Order succesfully submitted!')
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
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.submitcc()

    def submitcc(self):
        self.warn('Opening credit card page...')
        payload = {
            'signature':self.signature,
            'vads_action_mode':self.vads_action_mode,
            'vads_amount':self.vads_amount,
            'vads_contrib':self.vads_contrib,
            'vads_ctx_mode':self.vads_ctx_mode,
            'vads_currency':self.vads_currency,
            'vads_cust_address':self.vads_cust_address,
            'vads_cust_cell_phone':self.vads_cust_cell_phone,
            'vads_cust_city':self.vads_cust_city,
            'vads_cust_country':self.vads_cust_country,
            'vads_cust_email':self.vads_cust_email,
            'vads_cust_first_name':self.vads_cust_first_name,
            'vads_cust_id':self.vads_cust_id,
            'vads_cust_last_name':self.vads_cust_last_name,
            'vads_cust_phone':self.vads_cust_phone,
            'vads_cust_state':self.vads_cust_state,
            'vads_cust_title':self.vads_cust_title,
            'vads_cust_zip':self.vads_cust_zip,
            'vads_language':self.vads_language,
            'vads_nb_products':self.vads_nb_products,
            'vads_order_id':self.vads_order_id,
            'vads_order_info':self.vads_order_info,
            'vads_page_action':self.vads_page_action,
            'vads_payment_config':self.vads_payment_config,
            'vads_redirect_error_message':self.vads_redirect_error_message,
            'vads_redirect_error_timeout':self.vads_redirect_error_timeout,
            'vads_redirect_success_message':self.vads_redirect_success_message,
            'vads_redirect_success_timeout':self.vads_redirect_success_timeout,
            'vads_return_mode':self.vads_return_mode,
            'vads_ship_to_city':self.vads_ship_to_city,
            'vads_ship_to_country':self.vads_ship_to_country,
            'vads_ship_to_first_name':self.vads_ship_to_first_name,
            'vads_ship_to_last_name':self.vads_ship_to_last_name,
            'vads_ship_to_phone_num':self.vads_ship_to_phone_num,
            'vads_ship_to_state':self.vads_ship_to_state,
            'vads_ship_to_street':self.vads_ship_to_street,
            'vads_ship_to_street2':self.vads_ship_to_street2,
            'vads_ship_to_zip':self.vads_ship_to_zip,
            'vads_shipping_amount':self.vads_shipping_amount,
            'vads_site_id':self.vads_site_id,
            'vads_tax_amount':self.vads_tax_amount,
            'vads_totalamount_vat':self.vads_totalamount_vat,
            'vads_trans_date':self.vads_trans_date,
            'vads_trans_id':self.vads_trans_id,
            'vads_url_return':self.vads_url_return,
            'vads_version':self.vads_version,
            'vads_product_label0':self.vads_product_label0,
            'vads_product_amount0':self.vads_product_amount0,
            'vads_product_qty0':self.vads_product_qty0,
            'vads_product_ref0':self.vads_product_ref0,
            'vads_product_type0':self.vads_product_type0,
            'vads_product_vat0':self.vads_product_vat0
        }
        headers = {
            'Referer':'https://www.basket4ballers.com/',
        }
        while True:
            try:
                r = self.s.post(
                    'https://paiement.systempay.fr/vads-payment/',
                    headers = headers,
                    data = payload,
                    timeout = self.timeout
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if r.status_code == 200:
                    self.cahcheid = r.text.split('cacheId" value="')[1].split('"')[0]
                    self.success('Succesfully got credit card page!')
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
                    self.error(f'Error while opening credit card page: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while opening credit card page: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.choice()

    def choice(self):
        self.warn('Getting card information...')
        cardtype = identify_card_type(self.card)
        if cardtype == "MasterCard":
            self.type = 'MASTERCARD'
        elif cardtype == "Visa":
            self.type = 'VISA'
        payload = {
            'sequenceNumber':'1',
            'cacheId':self.cahcheid,
            'cardType':self.type
        }
        while True:
            try:
                r = self.s.post(
                    'https://paiement.systempay.fr/vads-payment/exec.paymentChoice.a',
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.cacheid2 = r.text.split('cacheId" value="')[1].split('"')[0]
                    self.success('Succesfully got card information!')
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
                    self.error(f'Error while getting card information: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting card information: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.final()

    def final(self):
        self.refuse = False
        self.warn('Submitting cc...')
        payload = {
            'cacheId':self.cacheid2,
            'browserScreenHeight':'937',
            'browserScreenWidth':'1920',
            'timeZone':'-120',
            'colorDepth':'24',
            'vads_card_info_form':'generic',
            'vads_card_number':self.card,
            'vads_payment_brand_choice_selected':'',
            'vads_payment_brand_choice_list':self.type,
            'vads_payment_brand_choice':self.type,
            'vads_expiry_month':self.month,
            'vads_expiry_year':self.year,
            'vads_cvv':self.cvv
        }
        while True:
            try:
                r = self.s.post(
                    'https://paiement.systempay.fr/vads-payment/exec.card_input.a',
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'name="status" content="REFUSED' in r.text:
                        self.error('Your card got refused, check your csv/card...')
                        self.refuse = True
                        break
                    else:
                        self.posturl = r.text.split('"url":"')[1].split('"')[0]
                        self.MD = r.text.split('"MD":"')[1].split('"')[0]
                        self.pareq = r.text.split('"PaReq":"')[1].split('"')[0]
                        self.termurl = r.text.split('"TermUrl":"')[1].split('"')[0]
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
                    self.error(f'Error while submitting cc: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting cc: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        if self.refuse:
            sys.exit()
        self.webhook3d()
        asyncio.run(self.main3d())
        self.term3d()

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
            await page.setRequestInterception(True)
            self._3dsAccepted = False
            self._3dsCancelled = False

            async def intercept(request):
                if 'bdx-pass.payzen.eu' in request.url:
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
            script = html.format(self.posturl, self.pareq, self.termurl, self.MD)
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
                await asyncio.sleep(self.delay)

        except Exception as e:
            self.error(f"Exception while handling 3DS: {e.__class__.__name__}")
            return False

    def term3d(self):
        while True:
            try:
                r = self.s.post(
                    self.termurl,
                    data = self.threeddata,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.result = r.text.split('"value":"')[1].split('"')[0]
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
                    self.error(f'Error while term3d: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while term3d: {e}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.complete3d()

    def complete3d(self):
        self.warn('Completing checkout...')
        payload = {
            'cacheId':self.cacheid2,
            'authenticationInstructionResult':self.result
        }
        while True:
            try:
                r = self.s.post(
                    'https://paiement.systempay.fr/vads-payment/vads.authenticationResult.a',
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.orderid = r.text.split('orderId" content="')[1].split('"')[0]
                    self.statuss = r.text.split('status" content="')[1].split('"')[0]
                    if self.statuss == 'REFUSED':
                        self.error('Payment declined!')
                    else:
                        self.success('Succesfully checked out!')
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
                    self.error(f'Error while completing checkout: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while completing checkout: {e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        if self.statuss == 'REFUSED':
            self.declined()
        else:
            self.webhookcc()

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
            url = urllib.parse.quote(base64.b64encode(bytes(self.urlfinale, 'utf-8')).decode())
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
                    writer.writerow({'SITE':'BASKET4BALLERS','SIZE':f'{self.sizescelta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'BASKET4BALLERS','SIZE':f'{self.sizescelta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            self.SuccessPP()
        except Exception as e: 
            self.error(f'Exception passing cookies: {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.passcookies()

    def clearcart(self):

        try:

            try:

                warn(f'[TASK {self.threadID}] [BASKET4BALLERS] - Clearing cart...')

                headers = {
                    'Accept' : 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Encoding' : 'gzip, deflate, br',
                    'Accept-Language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'Connection' : 'keep-alive',
                    'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Host' : 'www.basket4ballers.com',
                    'Sec-Fetch-Dest' : 'empty',
                    'Sec-Fetch-Mode' : 'cors',
                    'Sec-Fetch-Site' : 'same-origin',
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
                    'X-Requested-With' : 'XMLHttpRequest'

                }


                while True:

                    payload = {
                        'controller': 'cart',
                        'qty' : '1',
                        'id_product' : self.prodid,
                        'ipa' : self.variantescelta,
                        'id_address_delivery': self.idaddress,
                        'token' : self.tokennn,
                        'ajax': True
                    }


                    now = datetime.now()

                    timestamp = str(datetime.timestamp(now))

                    self.timestamp = timestamp.split('.')[0]

                    if self.mom:
                        r = self.s.post(f"https://www.basket4ballers.com/?rand={self.timestamp}", data = payload, proxies = self.selected_proxies, allow_redirects = False)
                    else:
                        r = self.s.post(f"https://www.basket4ballers.com/?rand={self.timestamp}", data = payload, headers = headers, proxies = self.selected_proxies, allow_redirects = False)

                    if r.status_code == 200:
                        
                        jsoncart = json.loads(r.text)

                        if '0,00' in str(jsoncart['productTotal']):
                            info(f'[TASK {self.threadID}] [BASKET4BALLERS] - Cart cleared!')
                            break

                        else:
                            warn(f'[TASK {self.threadID}] [BASKET4BALLERS] - Cart not cleared, retrying...')
                            time.sleep(self.delay)
                            continue


                    elif r.status_code == 400:
                        error(f'[TASK {self.threadID}] [BASKET4BALLERS] - {r.status_code} Bad request, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [BASKET4BALLERS] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 404:
                        error(f'[TASK {self.threadID}] [BASKET4BALLERS] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        error(f'[TASK {self.threadID}] [BASKET4BALLERS] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [BASKET4BALLERS] - Site dead, retrying...')
                        time.sleep(self.delay)
                        continue


                    else:
                        error(f'[TASK {self.threadID}] [BASKET4BALLERS] - {r.status_code} while clearing cart, retrying...')
                        time.sleep(self.delay)
                        continue


                self.getprod()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [BASKET4BALLERS] - Connection error, retrying...')
                time.sleep(self.delay)
                self.clearcart()

            except TimeoutError:
                error(f'[TASK {self.threadID}] [BASKET4BALLERS] - Timeout reached, retrying...')
                time.sleep(self.delay)
                self.clearcart()

            except Exception as e:
                error(f'[TASK {self.threadID}] [BASKET4BALLERS] - Exception while adding to cart, retrying...')
                time.sleep(self.delay)

                self.clearcart()

        except:
            pass

    def SuccessPP(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**BASKET4BALLERS**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.ppweb, inline = True) 
        embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.account}||", inline = False)
        embed.add_embed_field(name='**PASSWORD**', value = f"||{self.password}||", inline = True)     
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False) 
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url=self.img)
        embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook()


    def webhook3d(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - 3d is waiting for you!', color = 16426522)
        embed.add_embed_field(name=f'**BASKET4BALLERS**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.ppweb, inline = True) 
        embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.account}||", inline = False)
        embed.add_embed_field(name='**PASSWORD**', value = f"||{self.password}||", inline = True)  
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)    
        embed.set_thumbnail(url=self.img)
        embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook3d()

    def Pubblic_Webhook3d(self):
        if self.mode == "":
            self.mode = "SAFE"
        webhook = DiscordWebhook(url =random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'**BASKET4BALLERS**', value = self.title, inline = False)
        embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = False)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.ppweb, inline = True)
        embed.add_embed_field(name='MODE', value = self.mode, inline = True)
        embed.add_embed_field(name='Delay', value = self.delay, inline = False)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_thumbnail(url=self.img)
        embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        try:
            return playsound('checkout.wav')
        except:
            return True

    def webhookcc(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Succesfully checked out!', color = 4437377)
        embed.add_embed_field(name=f'**BASKET4BALLERS**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.ppweb, inline = True) 
        embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.account}||", inline = False)
        embed.add_embed_field(name='**PASSWORD**', value = f"||{self.password}||", inline = True) 
        embed.add_embed_field(name='**ORDER NUMBER**', value = f"||{self.orderid}||", inline = True) 
        embed.add_embed_field(name='**PAYMENT STATUS**', value = f"||{self.statuss}||", inline = True) 
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)    
        embed.set_thumbnail(url=self.img)
        embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()

    def declined(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Payment declined!', color = 15746887)
        embed.add_embed_field(name=f'**BASKET4BALLERS**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.ppweb, inline = True) 
        embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.account}||", inline = False)
        embed.add_embed_field(name='**PASSWORD**', value = f"||{self.password}||", inline = True)  
        embed.add_embed_field(name='**ORDER NUMBER**', value = f"||{self.orderid}||", inline = True) 
        embed.add_embed_field(name='**PAYMENT STATUS**', value = f"||{self.statuss}||", inline = True) 
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)    
        embed.set_thumbnail(url=self.img)  
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        sys.exit()

    def Pubblic_Webhook(self):
        if self.mode == "":
            self.mode = "SAFE"
        webhook = DiscordWebhook(url =random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'**BASKET4BALLERS**', value = self.title, inline = False)
        embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = False)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.ppweb, inline = True)
        embed.add_embed_field(name='MODE', value = self.mode, inline = True)
        embed.add_embed_field(name='Delay', value = self.delay, inline = False)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_thumbnail(url=self.img)
        embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        try:
            playsound('checkout.wav')
            time.sleep(500)
            sys.exit(1)
        except:
            time.sleep(500)
            sys.exit(1)

