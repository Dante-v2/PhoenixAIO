import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
import traceback
from autosolveclient.autosolve import AutoSolve
import copy
import dns.resolver
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
    CAPTCHA = config['captcha']['galeries']
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

class GALERIES():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'galeries/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "galeries/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()

        except:
            error("Failed reading proxies, running localhost")
            self.all_proxies = None

        
        if config['2captcha'] != "":
            self.captcha={
                'provider': '2captcha',
                'api_key':config['2captcha']
            }
        elif config['anticaptcha'] != "":
            self.captcha = {
                'provider': 'anticaptcha',
                'api_key': config['anticaptcha']
            }
        else:
            error('2Captcha or AntiCaptcha needed. Stopping task.')
            sys.exit(1)

        self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha=self.captcha,doubleDown=False,requestPostHook=self.injection)
        self.user = row['MAIL']
        self.password = row['PASSWORD']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.address1 = row['ADDRESS']
        self.address2 = row['ADDRESS 2'] 
        self.zip = row['ZIPCODE']
        self.country = row['COUNTRY']
        self.prefix = row['PREFIX']
        self.phone = row['PHONE']
        self.city = row['CITY']
        self.link = row['LINK'] 
        self.size = row['SIZE']
        self.payment = row['PAYMENT']

        self.balance = balancefunc()
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.delay = int(config["delay"])
        self.build_proxy()
        self.discord = DISCORD_ID

        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        self.timeout = 120
        self.bar()

        try:
            if self.name.upper() == "RANDOM":
                self.name = names.get_first_name(gender='male')
            if self.surname.upper() == "RANDOM":
                self.surname = names.get_last_name()
            if self.phone.upper() == "RANDOM":
                self.phone = str("0"+str(random.randint(7400000000,7999990000)))
            if self.user[:6].upper() == "RANDOM":
                self.user2 = "{}{}{}@{}".format(self.name, self.surname.split(' ')[0], str(random.randint(1000,9999)), self.user.split("@")[1]).lower()
        except Exception as e:
            error(e)

        self.warn('Starting tasks...')
        self.login()
        #self.getprod()

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [GALERIES] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [GALERIES] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [GALERIES] - {text}'
        warn(message)

    def build_proxy(self):
        cookies = self.s.cookies
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
                f = random.choice([_.to_text() for _ in dns.resolver.query(splitted[0], 'A')])
                self.s.proxies = {
                    'http': 'http://{}:{}@{}:{}'.format(splitted[2], splitted[3], f, splitted[1]),
                    'https': 'http://{}:{}@{}:{}'.format(splitted[2], splitted[3], f, splitted[1])
                }
                return None
            else:
                self.error('Invalid proxy: "{}", rotating'.format(self.px))
                return None

    def bar(self):
        if machineOS.lower() == 'windows':
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} -  Running GALERIES | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running GALERIES | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

    def injection(self, session, response):
        self.bar()
        #try:
        if helheim.isChallenge(session, response):
            self.warn('Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response
        #except:
        #if session.is_New_IUAM_Challenge(response):
        #    self.warn('Solving Cloudflare v2 api 2')
        #    return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=True).solve() 
        #elif session.is_New_Captcha_Challenge(response):
        #    self.warn('Solving Cloudflare v2 api 2')
        #    return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
        #else:
        #    return response

    def solve_v2(self, url):
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.recaptcha(sitekey='6LezI7AUAAAAAAzEiviPwx1gNVPcH2TMVsOMxxbd', url=url)
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
                        "websiteKey": "6LezI7AUAAAAAAzEiviPwx1gNVPcH2TMVsOMxxbd"
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
                    "siteKey" : "6LezI7AUAAAAAAzEiviPwx1gNVPcH2TMVsOMxxbd", 
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

    def login(self):
        self.warn('Getting login info...')
        while True:
            try:                    
                r = self.s.get(
                    'https://www.galerieslafayette.com/login', 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    soup = bs(r.text, features='lxml')
                    ci = soup.find('div',{'class':'content-wrapper'})
                    forms = ci.find('form',{'id':'login-form'})
                    self.login_url = forms['action']
                    self.register_url = forms['action'].split('tab_id=')[1]
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while getting login info: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while getting login info, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting login info: {e.__class__.__name__}, retrying...')
                continue
        if 'RANDOM' in self.user:
            self.register()
        else:
            self.login2()

    def register(self):
        while True:
            try:
                x = self.s.get(
                    f'https://secure.galerieslafayette.com/auth/realms/gl/login-actions/registration?client_id=ecom-front&tab_id={self.register_url}', 
                    timeout = self.timeout
                )
                if x.status_code == 200:
                    soup = bs(x.text, features='lxml')
                    ci = soup.find('div',{'class':'content-wrapper'})
                    forms = ci.find('form',{'id':'create-new-account-form'})
                    self.registration = forms['action']
                    day = str(random.randint(10,31))
                    month = str(random.randint(10,12))
                    year = str(random.randint(1990,2000))
                    self.warn('Solving captcha...')
                    code = self.solve_v2(x.url)
                    payload = {
                        'rememberMe': 'on',
                        'user.attributes.brand': 'GL',
                        'siteUrl': 'https://www.galerieslafayette.com',
                        'isGC': 'false',
                        'isFid': 'false',
                        'user.attributes.title': 'MR',
                        'lastName': self.surname,
                        'firstName': self.name,
                        'email': self.user2,
                        'user.attributes.phoneNumber': '',
                        'user.attributes.birthDate': f'{day}-{month}-{year}',
                        'password': self.password,
                        'password-confirm': self.password,
                        'g-recaptcha-response':code,
                        'gl-soft-cs': 'd021bbf0-735d-438f-a272-fa638ac1d2fa'
                    }
                    s = self.s.post(
                        self.registration, 
                        data = payload, 
                        timeout = self.timeout
                    ) 
                    if s.status_code == 200 and 'Votre compte est' in s.text and not 'Une erreur est survenue' in s.text:
                        self.user = self.user2
                        self.success('Account Successfully registered')
                        self.s.cookies.clear()
                        break
                    elif s.status_code >= 500 and s.status_code <= 600:
                        self.warn('Site dead, retrying...')
                        time.sleep(self.delay)
                        continue
                    elif s.status_code == 403:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    elif s.status_code == 404:
                        self.error('Page not loaded, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    elif s.status_code == 429:
                        self.error('Rate limit, retrying...')
                        self.build_proxy()
                        continue
                    else:
                        error(f'Unkown error creating account: {s.status_code}, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue   
                elif x.status_code >= 500 and x.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif x.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif x.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif x.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while creating account: {x.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection while creating account, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while creating account: {e.__class__.__name__}, retrying...')
                continue
        self.login()

    def login2(self):
        self.warn('Logging in...')
        self.warn('Solving captcha...')
        code = self.solve_v2(self.login_url)
        payload = {
            'rememberMe': 'on',
            'nbAttempt': '1',
            'isGC': True,
            'isFid': False,
            'username': self.user,
            'password': self.password,
            'g-recaptcha-response': code
        }
        while True:
            try:
                s = self.s.post(
                    self.login_url, 
                    data = payload, 
                    timeout = self.timeout
                ) 
                if s.status_code == 200:
                    if s.url != self.login_url:
                        self.success('Successfully logged in!')
                        break
                    elif "L'adresse email et/ou votre mot de passe ne sont pas valides" in s.text:
                        self.error('Invalid email or password, stopping')
                        sys.exit(1)
                        break
                    elif 'Captcha invalide' in s.text:
                        self.error('Captcha failed, retrying')
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Unkown error while logging in, retrying')
                        time.sleep(self.delay)
                        continue
                elif s.status_code >= 500 and s.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif s.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif s.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif s.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while logging in: {s.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection while logging in, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while logging in: {e.__class__.__name__}, retrying...')
                continue
        self.getprod()

    def getprod(self):
        self.warn('Getting product page...')
        while True:
            try:
                r = self.s.get(self.link,proxies = self.s.proxies,timeout = self.timeout)
                if r.status_code == 200:
                    soup = bs(r.text, features='lxml')
                    self.success('Successfully got product page')
                    titinfo = soup.find('div',{'class':'product-page__content__information--title'})
                    self.title = titinfo.find('span',{'class':'product-title'}).text
                    img = soup.find('meta',{'property':'og:image'})['content']
                    self.img = f'https:{img}'
                    self.pid = self.img.split('G_')[1].split('_')[0]
                    rowpage = soup.find('section',{'class':'row product-page__content--margin'})
                    self.color = rowpage.find('section',{'class':'columns small-24 xmedium-24 large-24 product-page__content__toolbox'})['data-color-code']
                    try:
                        sizesprod = soup.find('div',{'class':'row sizeBlock'})
                        sizeblock = sizesprod.find('select',{'class':'sizeBlock__select sizeBlock__select--size'})
                        optionval = sizeblock.find_all('option')
                    except:
                        self.warn('Product OOS, monitoring...')
                        time.sleep(self.delay)
                        continue
                    sizevalue = []
                    sizetext = []
                    for x in optionval:
                        sizevalue.append(x['value'])
                        sizetext.append(x.text)
                    self.element = zip(sizevalue, sizetext)
                    self.all_sizes = list(self.element)
                    if len(self.all_sizes) < 1:
                        self.warn('Product OOS, monitoring...')
                        time.sleep(self.delay)
                        continue
                    self.instock = []
                    for element in self.all_sizes:
                        if element[0] != "":
                            self.instock.append(element)
                    if len(self.instock) < 1:
                        warn(f'Product OOS, monitoring...')
                        time.sleep(self.delay)
                        continue
                    else:
                        self.sizeinstock = []
                        for h in self.instock:
                            if 'taille' not in h[1]:
                                self.sizeinstock.append(h)
                        self.print = []
                        for x in self.sizeinstock:
                            if 'FR' in x[1]:
                                self.print.append(x[1].split(' -')[0])
                            else:
                                self.print.append(x[1])
                        self.sizerange = []
                        if len(self.print) < 1:
                            self.warn('Product OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        if self.size == "RANDOM":
                            if self.sizeinstock != '':
                                self.success(f'Size available! {self.print}')
                                break
                            else:
                                self.warn('Product OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                        elif '-' in self.size:
                            self.size1 = str(self.size.split('-')[0])
                            self.size2 = str(self.size.split('-')[1])
                            for x in self.print:
                                if self.size1 <= str(x) <= self.size2:
                                    self.sizerange.append(x)     
                            self.success(f'Size available! {self.sizerange}')
                            break
                        elif ',' in self.size:
                            self.size1 = str(self.size.split(',')[0])
                            self.size2 = str(self.size.split(',')[1])
                            for x in self.print:
                                if self.size1 <= str(x) <= self.size2:
                                    self.sizerange.append(x)     
                            self.success(f'Size available! {self.sizerange}')
                            break
                        else:
                            if self.sizeinstock != '':
                                if self.size in self.print:
                                    self.success(f'Size {self.size} available!')
                                    break
                                else:
                                    self.warn(f'Size chosen {self.size} not available, monitoring...')
                                    time.sleep(self.delay)
                                    continue
                            else:
                                self.warn('Product OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while getting product page: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while getting product page, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting product page: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.atc() 

    def atc(self):
        global carted, failed, checkoutnum
        if self.size == 'RANDOM':
            self.scelto = random.choice(self.sizeinstock)
            self.value = self.scelto[0]
            self.printa = self.scelto[1]
            if 'FR' in self.printa:
                self.printa = self.printa.split(' -')[0]
            self.warn(f'Adding to cart size {self.printa}...')
        elif '-' in self.size:
            self.sizerandom = random.choice(self.sizerange)
            self.choice = []
            for x in self.sizeinstock:
                if self.sizerandom == x[1]:
                    self.choice.append(x)
            self.value = self.choice[0][0]
            self.printa = self.choice[0][1]
            if 'FR' in self.printa:
                self.printa = self.printa.split(' -')[0]
            self.warn(f'Adding to cart size {self.printa}...')
        elif ',' in self.size:
            self.sizerandom = random.choice(self.sizerange)
            self.choice = []
            for x in self.sizeinstock:
                if self.sizerandom == x[1]:
                    self.choice.append(x)
            self.value = self.choice[0][0]
            self.printa = self.choice[0][1]
            if 'FR' in self.printa:
                self.printa = self.printa.split(' -')[0]
            self.warn(f'Adding to cart size {self.printa}...')
        else:
            if self.size in self.print:
                self.choice = []
                for x in self.sizeinstock:
                    if self.size == x[1]:
                        self.choice.append(x)
                self.value = self.choice[0][0]
                self.printa = self.choice[0][1]
                if 'FR' in self.printa:
                    self.printa = self.printa.split(' -')[0]
                self.warn(f'Adding to cart size {self.printa}...')
            else:
                self.warn('Product OOS, monitoring...')
                time.sleep(self.delay)
                self.getprod()
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]
                t =self.s.get(
                    f"https://www.galerieslafayette.com/ajax/p/{self.pid}/{self.color}?sizeCode={self.value}&version=v2",
                    timeout = self.timeout
                )
                if t.status_code == 200:
                    r = self.s.get(
                        f'https://www.galerieslafayette.com/product/add/{self.value}/1?sc=pr&ts={timestamp}',
                        timeout = self.timeout
                    )
                    if r.status_code == 200:
                        if "ajouter" in r.text:
                            carted = carted + 1
                            self.bar()
                            self.success('Successfully added to cart')
                            break
                        else:
                            self.error('Failed adding to cart, retrying')
                            time.sleep(self.delay)
                            continue
                    elif r.status_code >= 500 and r.status_code <= 600:
                        self.warn('Site dead, retrying...')
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 403:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    elif r.status_code == 404:
                        self.error('Page not loaded, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 429:
                        self.error('Rate limit, retrying...')
                        self.build_proxy()
                        continue
                    else:
                        error(f'Unkown error while adding to cart: {r.status_code}, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif t.status_code >= 500 and t.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif t.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif t.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif t.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while adding to cart: {t.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection while adding to cart, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                continue
        self.ship1()

    def ship1(self):
        self.warn('Checking cart info...')
        while True:
            try:
                r = self.s.get(
                    'https://www.galerieslafayette.com/deliveries/1', 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    c = r.text
                    self.cartcode = c.split('data-logistic-cart-code="')[1].split('"')[0]
                    self.success('Successfully got cart info')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while checking cart info: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection while checking cart info, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while checking cart info: {e.__class__.__name__}, retrying...')
                continue
        self.ship2()

    def ship2(self):
        self.warn('Getting shipping info...')
        self.country = self.country.lower()
        while True:
            try:
                r = self.s.get(
                    f'https://www.galerieslafayette.com/deliveries/1/{self.cartcode}/country/{self.country}', 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.success('Successfully got shipping info')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while getting shipping info: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection while getting shipping info, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting shipping info: {e.__class__.__name__}, retrying...')
                continue
        self.ship3()

    def ship3(self):
        self.warn('Submitting shipping...')
        payload = {
            "title":"MR",
            "firstName":self.name,
            "lastName":self.surname,
            "companyName":"",
            "alias":"",
            "streetNameAndNumber":f"{self.address1} {self.address2}",
            "supplement":"",
            "supplementMore":"",
            "zipCode":self.zip,
            "city":self.city,
            "countryCode":self.country,
            "phoneMobile":f"{self.prefix}{self.phone}",
            "expatPackageNumber":"",
            "qualityCode":"",
            "extendedQualityCode":""
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.galerieslafayette.com/ajax/deliveries/redress-custom-address/shipping', 
                    json = payload, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.numero = '16'
                    if self.country == 'fr':
                        self.numero = '21'
                    else:
                        self.numero = '16'
                    x = self.s.post(
                        f'https://www.galerieslafayette.com/ajax/deliveries/custom-address/create/address/redirect/{self.cartcode}/{self.numero}', 
                        json = payload, 
                        timeout = self.timeout
                    )
                    if x.status_code == 200:
                        r_json = json.loads(x.text)
                        if r_json['success'] == True:
                            self.success('Successfully submitted ship')
                            break
                        else:
                            self.error('Failed submitting ship')
                            time.sleep(self.delay)
                            continue
                    elif x.status_code >= 500 and x.status_code <= 600:
                        self.warn('Site dead, retrying...')
                        time.sleep(self.delay)
                        continue
                    elif x.status_code == 403:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    elif x.status_code == 404:
                        self.error('Page not loaded, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    elif x.status_code == 429:
                        self.error('Rate limit, retrying...')
                        self.build_proxy()
                        continue
                    else:
                        error(f'Unkown error while submitting shipping: {x.status_code}, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while submitting shipping: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection while submitting shipping, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting shipping: {e.__class__.__name__}, retrying...')
                continue
        if self.payment == 'PP':
            self.payment1()
        else:
            self.error('Invalid payment method, using PP...')
            self.payment1()

    def payment1(self):
        self.warn('Submitting payment...')
        payload = {"paymentInfoPaypalRequest":{}}
        while True:
            try:
                r = self.s.post(
                    'https://www.galerieslafayette.com/ajax/payment/multimodes/hosted_page', 
                    json = payload, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    x = r.text
                    self.pay_url = x.split('action="')[1].split('"')[0]
                    soup = bs(r.text, features='lxml')
                    self.bsid = soup.find('input',{'name':'PSPID'})['value']
                    self.orderid = soup.find('input',{'name':'ORDERID'})['value']
                    self.amount = soup.find('input',{'name':'AMOUNT'})['value']
                    self.ordershipcost = soup.find('input',{'name':'ORDERSHIPCOST'})['value']
                    self.currency = soup.find('input',{'name':'CURRENCY'})['value']
                    self.language = soup.find('input',{'name':'LANGUAGE'})['value']
                    self.cn = soup.find('input',{'name':'CN'})['value']
                    self.emaill = soup.find('input',{'name':'EMAIL'})['value']
                    self.ownerzip = soup.find('input',{'name':'OWNERZIP'})['value']
                    self.owneraddress = soup.find('input',{'name':'OWNERADDRESS'})['value']
                    self.ownercty = soup.find('input',{'name':'OWNERCTY'})['value']
                    self.ownertown = soup.find('input',{'name':'OWNERTOWN'})['value']
                    self.ecom_namefirst = soup.find('input',{'name':'ECOM_SHIPTO_POSTAL_NAME_FIRST'})['value']
                    self.ecom_namelast = soup.find('input',{'name':'ECOM_SHIPTO_POSTAL_NAME_LAST'})['value']
                    self.ecom_state = soup.find('input',{'name':'ECOM_SHIPTO_POSTAL_STATE'})['value']
                    self.ecom_street1 = soup.find('input',{'name':'ECOM_SHIPTO_POSTAL_STREET_LINE1'})['value']
                    self.ecom_countrycode = soup.find('input',{'name':'ECOM_SHIPTO_POSTAL_COUNTRYCODE'})['value']
                    self.ecom_postalcity = soup.find('input',{'name':'ECOM_SHIPTO_POSTAL_CITY'})['value']
                    self.ecom_postalcode = soup.find('input',{'name':'ECOM_SHIPTO_POSTAL_POSTALCODE'})['value']
                    self.SHASIGN = soup.find('input',{'name':'SHASIGN'})['value']
                    self.backurl = soup.find('input',{'name':'BACKURL'})['value']
                    self.accepturl = soup.find('input',{'name':'ACCEPTURL'})['value']
                    self.declineurl = soup.find('input',{'name':'DECLINEURL'})['value']
                    self.exceotptionurl = soup.find('input',{'name':'EXCEPTIONURL'})['value']
                    self.cancellurl = soup.find('input',{'name':'CANCELURL'})['value']
                    self.pm = soup.find('input',{'name':'PM'})['value']
                    self.brand = soup.find('input',{'name':'BRAND'})['value']
                    self.aliasusage = soup.find('input',{'name':'ALIASUSAGE'})['value']
                    self.aliasoperation = soup.find('input',{'name':'ALIASOPERATION'})['value']
                    self.success('Payment info submitted')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while submitting payment: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection while submitting payment, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting payment: {e.__class__.__name__}, retrying...')
                continue
        self.finalize()

    def finalize(self):
        global carted, failed, checkoutnum
        payload = {
            'PSPID':self.bsid,
            'ORDERID':self.orderid,
            'AMOUNT':self.amount,
            'ORDERSHIPCOST':self.ordershipcost,
            'CURRENCY':self.currency,
            'LANGUAGE':self.language,
            'CN':self.cn,
            'EMAIL':self.emaill,
            'OWNERZIP':self.ownerzip,
            'OWNERADDRESS':self.owneraddress,
            'OWNERCTY':self.ownercty,
            'OWNERTOWN':self.ownertown,
            'ECOM_BILLTO_POSTAL_CITY':self.ownertown,
            'ECOM_BILLTO_POSTAL_COUNTRYCODE':self.ecom_countrycode,
            'ECOM_BILLTO_POSTAL_STREET_LINE1':self.ecom_street1,
            'ECOM_BILLTO_POSTAL_POSTALCODE':self.ecom_postalcode,
            'ECOM_SHIPTO_POSTAL_NAME_FIRST':self.ecom_namefirst,
            'ECOM_SHIPTO_POSTAL_NAME_LAST':self.ecom_namelast,
            'ECOM_SHIPTO_POSTAL_STATE':self.ecom_state,
            'ECOM_SHIPTO_POSTAL_STREET_LINE1':self.ecom_street1,
            'ECOM_SHIPTO_POSTAL_COUNTRYCODE':self.ecom_countrycode,
            'ECOM_SHIPTO_POSTAL_CITY':self.ecom_postalcity,
            'ECOM_SHIPTO_POSTAL_POSTALCODE':self.ecom_postalcode,
            'SHASIGN':self.SHASIGN,
            'BACKURL':self.backurl,
            'ACCEPTURL':self.accepturl,
            'DECLINEURL':self.declineurl,
            'EXCEPTIONURL':self.exceotptionurl,
            'CANCELURL':self.cancellurl,
            'PM':self.pm,
            'BRAND':self.brand,
            'ALIASUSAGE':self.aliasusage,
            'ALIASOPERATION':self.aliasoperation
        }
        self.warn('Opening paypal...')
        while True:
            try:
                r = self.s.post(
                    self.pay_url, 
                    data = payload, 
                    timeout = self.timeout, 
                    allow_redirects = False
                )
                if r.status_code == 200:
                    soup = bs(r.text, features='lxml')
                    pp_tok = soup.find('input',{'name':'token'})['value']
                    self.pp_url = f'https://www.paypal.com/FR/cgi-bin/webscr?cmd=_express-checkout&token={pp_tok}&useraction=commit'
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    self.success('Successfully checked out!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while opening paypal: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection while opening paypal, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while opening paypal: {e.__class__.__name__}, retrying...')
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
                for element in cookies:
                    if 'KEYCLOAK_ADAPTER_STATE' in element['name']:
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
            cookies.pop(0)
            cookies.pop(0)
            cookies = json.dumps(cookies)
            cookieStr = urllib.parse.quote(base64.b64encode(bytes(cookies, 'utf-8')).decode())
            if not cookieStr: return
            url = urllib.parse.quote(base64.b64encode(bytes(self.pp_url, 'utf-8')).decode())
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
                    writer.writerow({'SITE':'GALERIES','SIZE':f'{self.printa}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'GALERIES','SIZE':f'{self.printa}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            self.SuccessPP()
        except Exception as e: 
            self.error(f'Exception error while passing cookies: {e.__class__.__name__}, retrying...') 
            sys.exit(1)
            return None

    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name='**GALERIES LA FAYETTE**', value = self.title, inline = True)
            embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = True)
            embed.add_embed_field(name='**SIZE**', value = str(self.printa), inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.pm, inline = False)    
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.img) 
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
            embed.add_embed_field(name='**GALERIES LA FAYETTE**', value = self.title, inline = True)
            embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = True)
            embed.add_embed_field(name='**SIZE**', value = str(self.printa), inline = True)
            embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.emaill}||", inline = False)
            embed.add_embed_field(name='**ORDER ID**', value = f"||{self.orderid}||", inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.pm, inline = False) 
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.img) 
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg") 
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass