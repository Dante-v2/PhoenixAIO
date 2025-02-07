import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, os, time, re, urllib, cloudscraper, names, lxml, pytz, copy
from mods.logger import info, warn, error
from random import randint
import cloudscraper
from discord_webhook import DiscordWebhook, DiscordEmbed
import lxml
from bs4 import BeautifulSoup as bs
import time, datetime
import re
import urllib.parse
import names
from twocaptcha import TwoCaptcha
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from cryptography.hazmat.backends import default_backend
from os import urandom
from autosolveclient.autosolve import AutoSolve
import traceback
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')
UNIQUE_ID = int(time.time() * 1000) * 2**random.randint(10,16)
AUTO_SOLVE = None
CAPTCHA_TOKENS = []
CAPTCHA = None


urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

cnum = 0

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

    error("FAILED TO READ CONFIG")
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


class GENCOURIR():

    def __init__(self, row, i):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'gencourir/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "gencourir/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()

        except:
            error("FAILED TO READ PROXIES, STARTING LOCAL HOST")
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

        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.mail = row['MAIL']
        self.password = row['PASSWORD'] 
        self.phone = row['PHONE']
        self.zip = row['ZIP']
        self.city = row['CITY']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.country = row['COUNTRY']
        self.threadID = '%03d' % i
        self.twoCaptcha = str(config['2captcha'])

        if self.name.upper() == "RANDOM":
            self.name = names.get_first_name(gender='male')
        if self.surname.upper() == "RANDOM":
            self.surname = names.get_last_name()
        if self.phone.upper() == "RANDOM":
            self.phone = str("0"+str(random.randint(600000000,699999999)))
        if self.mail[:6].upper() == "RANDOM":
            self.mail = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.mail.split("@")[1]).lower()

        self.prefix = ''
        
        if self.country == 'FR':
            self.prefix = '+33'
        self.build_proxy()
        self.bar()

        warn(f'[TASK {self.threadID}] [GEN_COURIR] - Starting tasks...')
        self.register()

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
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO - COURIR ACC Running | Generated: {cnum}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO - COURIR ACC Running | Generated: {cnum}\x07')


    def injection(self, session, response):
        try:
            if helheim.isChallenge(session, response):
                warn('Solving Cloudflare v2')
                return helheim.solve(session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                warn('Solving Cloudflare v2 api 2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                warn('Solving Cloudflare v2 api 2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True).solve() 
            else:
                return response

    def solve_v3(self, url):
        warn('Solving captcha...')
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
                            info('Captcha solved!')
                            return token['token']
                        else:
                            error('Autosolve captcha solve failed')
                            return self.solve_v2(url)
                time.sleep(1)
        except Exception as e:
            error(f'An error occured solving captcha with Autosolve: {e}')
            return self.solve_v3(url)
   
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

                    return info('Datadome done, proceding...')

                else:
                    return error('Datadome failed, retrying...')

            else:
                self.s.cookies.clear()
                self.build_proxy()
                return error('Datadome failed, restarting...')

        except Exception as e:
            return self.error(f'Datadome failed {e}, retrying...')

    def register(self):

        global cnum
        i = 0
        warn(f'[TASK {self.threadID}] [GEN_COURIR] - Getting account information...')
        try:
            while True:
                t = self.s.get("https://www.courir.com/fr/register?IsCheckout=false")
                print(t.status_code)
                if 'Please enable JS' in t.text:
                    self.dataurl = t.url                    
                    resp = t.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        error('Proxy banned, rotating...')
                        self.build_proxy()
                        i = 0
                        continue
                    warn('Datadome found, proceding...')
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
                if t.status_code == 200:
                    self.csrf = t.text.split('csrf_token" value="')[1].split('"')[0]
                    self.passwx = t.text.split('login_password_')[1].split('"')[0]
                    print(self.passwx)

                    try:
                        code = self.solve_v3('https://www.courir.com/fr/register?IsCheckout=false')

                        info(f'[TASK {self.threadID}] [GEN_COURIR] - Captcha solved')

                        try:
                            
                            day = str(random.randint(1,31))
                            month = str(random.randint(10,12))
                            year = str(random.randint(1990,2000))

                            warn(f'[TASK {self.threadID}] [GEN_COURIR] - Creating account...')
                            payload = {
                                'g-recaptcha-response':code,
                                'dwfrm_profile_loyaltycard_number':'',
                                'dwfrm_profile_customer_civility': 'M.',
                                'dwfrm_profile_customer_lastname': self.surname,
                                'dwfrm_profile_customer_firstname': self.name,
                                'dwfrm_profile_customer_email': self.mail,
                                f'dwfrm_profile_login_password_{self.passwx}': self.password,
                                'dwfrm_profile_customer_birthday': f'{year}-{month}-{day}',
                                'dwfrm_profile_customer_phoneMobile': self.phone,
                                'dwfrm_profile_customer_phoneCodeHome': self.prefix,
                                'dwfrm_profile_customer_phoneCountryCode': self.country,
                                'dwfrm_profile_address_qualityCode': '00',
                                'dwfrm_profile_address_countryCode': self.country,
                                'dwfrm_profile_address_postalCode': self.zip,
                                'dwfrm_profile_address_city': self.city,
                                'dwfrm_profile_address_address1': self.address,
                                'dwfrm_profile_address_address2': self.address2,
                                'dwfrm_profile_confirm': 'Je crée un compte',
                                'csrf_token': self.csrf
                            }

                            r = self.s.post("https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/Account-RegistrationForm", data = payload, allow_redirects = False)

                            if r.status_code == 302 and r.headers['Location'] == 'https://www.courir.com/fr/account?registration=true':
                                break

                            else:
                                print(r.headers)
                                print(r.text)
                                error(f'[TASK {self.threadID}] [GEN_COURIR] - Error creating account, check your information')
                                sys.exit()

                        except Exception as e:
                            error( f"[TASK {self.threadID}] [GEN_COURIR] - Error with cloudflare")  

                    except Exception as e:
                        error(f'[TASK {self.threadID}] [GEN_COURIR] - Captcha failed {e}')

                else:
                    error(f'[TASK {self.threadID}] [GEN_COURIR] - Failed getting information')
            self.SavingAccount()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [GEN_COURIR] - Connection error, retrying...')
            time.sleep(2)
            self.register()

        except TimeoutError:
            error(f'[TASK {self.threadID}] [GEN_COURIR] - Timeout reached, retrying...')
            time.sleep(2)
            self.register()
    
        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_COURIR] - Exception creating account {e}')
            time.sleep(2)
            self.register()



    def SavingAccount(self):

        global cnum
        txt = self.mail + ':' + self.password
        warn(f'[TASK {self.threadID}] [GEN_COURIR] - Saving account...')
        try:
            path = os.path.dirname(__file__).rsplit('/', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), "gencourir")
            file_to_open = os.path.join(path, "output.txt")
            with open(file_to_open, 'a') as output:
                output.writelines(f'{txt}\n')
                output.close()
                info(f'[TASK {self.threadID}] [GEN_COURIR] - Account saved in txt')
                cnum = cnum + 1
                self.bar()
        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_COURIR] - Failed saving account')
            input("")