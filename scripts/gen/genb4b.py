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
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')
UNIQUE_ID = int(time.time() * 1000) * 2**random.randint(10,16)
AUTO_SOLVE = None
CAPTCHA_TOKENS = []
CAPTCHA = None

urllib3.disable_warnings()
version = '1.0.0'
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
    CAPTCHA = config['captcha']['b4b']
    config['2captcha']
    config['capmonster']
    config['anticaptcha']
except Exception as e:
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
        try:
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
        except Exception as e:
            self.error(e)

class GENB4B():

    def __init__(self, row, i):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'genb4b/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "genb4b/proxies.txt")
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

        self.mail = row['MAIL']
        self.password = row['PASSWORD']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.address1 = row['ADDRESS 1']
        self.address2 = row['ADDRESS 2']
        self.city = row['CITY']
        self.zipcode = row['ZIP']
        self.region = row['REGION']
        self.phone = row['PHONE']
        self.country = row ['COUNTRY']
        self.dni = row['DNI']
        
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

        self.bar()
        self.build_proxy()
        self.threadID = '%03d' % i
        self.twoCaptcha = str(config['2captcha'])

        if self.country == 'AR': #paesi
            self.country = '44'
        if self.country == 'AM':
            self.country = '45'
        if self.country == 'AT':
            self.country = '2'
        if self.country == 'BY':
            self.country = '52'
        if self.country == 'BE':
            self.country = '3'
        if self.country == 'BR':
            self.country = '58'
        if self.country == 'BG':
            self.country = '236'
        if self.country == 'CA':
            self.country = '4'
        if self.country == 'CN':
            self.country = '5'
        if self.country == 'HR':
            self.country = '74'
        if self.country == 'CZ':
            self.country = '16'
        if self.country == 'DK':
            self.country = '20'
        if self.country == 'EE':
            self.country = '86'
        if self.country == 'FI':
            self.country = '7'
        if self.country == 'FR':
            self.country = '8'
        if self.country == 'DE':
            self.country = '1'
        if self.country == 'GI':
            self.country = '97'
        if self.country == 'GR':
            self.country = '9'
        if self.country == 'HK':
            self.country = '22'
        if self.country == 'HU':
            self.country = '143'
        if self.country == 'IE':
            self.country = '26'
        if self.country == 'IT':
            self.country = '10'
        if self.country == 'JP':
            self.country = '11'
        if self.country == 'JE':
            self.country = '116'
        if self.country == 'LV':
            self.country = '125'
        if self.country == 'LI':
            self.country = '130'
        if self.country == 'LT':
            self.country = '131'
        if self.country == 'LU':
            self.country = '12'
        if self.country == 'MT':
            self.country = '139'
        if self.country == 'MC':
            self.country = '148'
        if self.country == 'NL':
            self.country = '13'
        if self.country == 'NO':
            self.country = '23'
        if self.country == 'PL':
            self.country = '14'
        if self.country == 'PT':
            self.country = '15'
        if self.country == 'RO':
            self.country = '36'
        if self.country == 'SM':
            self.country = '186'
        if self.country == 'SG':
            self.country = '25'
        if self.country == 'SK':
            self.country = '37'
        if self.country == 'SI':
            self.country = '193'
        if self.country == 'KR':
            self.country = '28'
        if self.country == 'ES':
            self.country = '6'
        if self.country == 'SE':
            self.country = '18'
        if self.country == 'CH':
            self.country = '19'
        if self.country == 'TW':
            self.country = '203'
        if self.country == 'UA':
            self.country = '216'
        if self.country == 'GB':
            self.country = '17'
        if self.country == 'US':
            self.country = '21'
        if self.country == 'VA':
            self.country = '107'

        if self.country == '8':
            if self.region == 'Corse':
                self.region = '314'
            else:
                self.region = '315'
            
        if self.country == '10': #regioni IT
            if self.region == 'AG':
                self.region = '123'
            if self.region == 'AL':
                self.region = '124'
            if self.region == 'AN':
                self.region = '125'
            if self.region == 'AO':
                self.region = '126'
            if self.region == 'AR':
                self.region = '127'
            if self.region == 'AP':
                self.region = '128'
            if self.region == 'AT':
                self.region = '129'
            if self.region == 'AV':
                self.region = '130'
            if self.region == 'BA':
                self.region = '131'
            if self.region == 'BT':
                self.region = '132'
            if self.region == 'BL':
                self.region = '133'
            if self.region == 'BN':
                self.region = '134'
            if self.region == 'BG':
                self.region = '135'
            if self.region == 'BI':
                self.region = '136'
            if self.region == 'BO':
                self.region = '137'
            if self.region == 'BZ':
                self.region = '138'
            if self.region == 'BS':
                self.region = '139'
            if self.region == 'BR':
                self.region = '140'
            if self.region == 'CA':
                self.region = '141'
            if self.region == 'CL':
                self.region = '142'
            if self.region == 'CB':
                self.region = '143'
            if self.region == 'CI':
                self.region = '144'
            if self.region == 'CE':
                self.region = '145'
            if self.region == 'CT':
                self.region = '146'
            if self.region == 'CZ':
                self.region = '147'
            if self.region == 'CH':
                self.region = '148'
            if self.region == 'CO':
                self.region = '149'
            if self.region == 'CS':
                self.region = '150'
            if self.region == 'CR':
                self.region = '151'
            if self.region == 'KR':
                self.region = '152'
            if self.region == 'CN':
                self.region = '153'
            if self.region == 'EN':
                self.region = '154'
            if self.region == 'FM':
                self.region = '155'
            if self.region == 'FE':
                self.region = '156'
            if self.region == 'FI':
                self.region = '157'
            if self.region == 'FG':
                self.region = '158'
            if self.region == 'FC':
                self.region = '159'
            if self.region == 'FR':
                self.region = '160'
            if self.region == 'GE':
                self.region = '161'
            if self.region == 'GO':
                self.region = '162'
            if self.region == 'GR':
                self.region = '163'
            if self.region == 'IM':
                self.region = '164'
            if self.region == 'IS':
                self.region = '165'
            if self.region == 'AQ':
                self.region = '166'
            if self.region == 'SP':
                self.region = '167'
            if self.region == 'LT':
                self.region = '168'
            if self.region == 'LE':
                self.region = '169'
            if self.region == 'LC':
                self.region = '170'
            if self.region == 'LI':
                self.region = '171'
            if self.region == 'LO':
                self.region = '172'
            if self.region == 'LU':
                self.region = '173'
            if self.region == 'MC':
                self.region = '174'
            if self.region == 'MN':
                self.region = '175'
            if self.region == 'MS':
                self.region = '176'
            if self.region == 'MT':
                self.region = '177'
            if self.region == 'VS':
                self.region = '178'
            if self.region == 'ME':
                self.region = '179'
            if self.region == 'MI':
                self.region = '180'
            if self.region == 'MO':
                self.region = '181'
            if self.region == 'MB':
                self.region = '182'
            if self.region == 'NA':
                self.region = '183'
            if self.region == 'NO':
                self.region = '184'
            if self.region == 'NU':
                self.region = '185'
            if self.region == 'OG':
                self.region = '186'
            if self.region == 'OT':
                self.region = '187'
            if self.region == 'OR':
                self.region = '188'
            if self.region == 'PD':
                self.region = '189'
            if self.region == 'PA':
                self.region = '190'
            if self.region == 'PR':
                self.region = '191'
            if self.region == 'PV':
                self.region = '192'
            if self.region == 'PG':
                self.region = '193'
            if self.region == 'PU':
                self.region = '194'
            if self.region == 'PE':
                self.region = '195'
            if self.region == 'PC':
                self.region = '196'
            if self.region == 'PI':
                self.region = '197'
            if self.region == 'PT':
                self.region = '198'
            if self.region == 'PN':
                self.region = '199'
            if self.region == 'PZ':
                self.region = '200'
            if self.region == 'PO':
                self.region = '201'
            if self.region == 'RG':
                self.region = '202'
            if self.region == 'RA':
                self.region = '203'
            if self.region == 'RC':
                self.region = '204'
            if self.region == 'RE':
                self.region = '205'
            if self.region == 'RI':
                self.region = '206'
            if self.region == 'RN':
                self.region = '207'
            if self.region == 'RM':
                self.region = '208'
            if self.region == 'RO':
                self.region = '209'
            if self.region == 'SA':
                self.region = '210'
            if self.region == 'SS':
                self.region = '211'
            if self.region == 'SV':
                self.region = '212'
            if self.region == 'VT':
                self.region = '232'
            if self.region == 'VI':
                self.region = '231'
            if self.region == 'VV':
                self.region = '230'
            if self.region == 'VR':
                self.region = '229'
            if self.region == 'VC':
                self.region = '228'
            if self.region == 'VB':
                self.region = '227'
            if self.region == 'VE':
                self.region = '226'
            if self.region == 'VA':
                self.region = '225'
            if self.region == 'UD':
                self.region = '224'
            if self.region == 'TS':
                self.region = '223'
            if self.region == 'TV':
                self.region = '222'
            if self.region == 'TN':
                self.region = '221'
            if self.region == 'TP':
                self.region = '220'
            if self.region == 'TO':
                self.region = '219'
            if self.region == 'TR':
                self.region = '218'
            if self.region == 'TE':
                self.region = '217'
            if self.region == 'TA':
                self.region = '216'
            if self.region == 'SO':
                self.region = '215'
            if self.region == 'SR':
                self.region = '214'
            if self.region == 'SI':
                self.region = '213'

        self.bar()

        self.warn('Starting task...')
        self.getchallenge()


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
                f'Phoenix AIO - B4B ACC Running | Generated: {cnum}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO - B4B ACC Running | Generated: {cnum}\x07')

    def error(self, text):
        message = f'[TASK {self.threadID}] - [GEN B4B] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [GEN B4B] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [GEN B4B] - {text}'
        warn(message)

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
                    timeout = 120
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
        self.register()

    def register(self):
        self.warn('Creating account...')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
            'Content-type': 'application/x-www-form-urlencoded',
        }
        self.s.headers.update(headers)
        self.warn('Solving captcha...')
        code = self.solve_v2('https://www.basket4ballers.com/fr/authentification')
        payload = {
            'id_gender':'2',
            'customer_lastname':self.surname,
            'customer_firstname':self.name,
            'email':self.mail,
            'passwd':self.password,
            'days':'',
            'months':'',
            'years':'',
            'firstname':self.name,
            'lastname':self.surname,
            'company':'',
            'vat_number':'',
            'address1':self.address1,
            'address2':self.address2,
            'postcode':self.zipcode,
            'city':self.city,
            'id_state':self.region,
            'id_country':self.country,
            'other':'',
            'phone':self.phone,
            'phone_mobile':self.phone,
            'alias':'My address',
            'dni':self.dni,
            'new_abo[subscriptions][]':'3',
            'new_abo[subscriptions][]':'5',
            'new_abo[subscriptions][]':'6',
            'new_abo[subscriptions][]':'4',
            'new_abo[id_country]':self.country,
            'new_abo[phone]':self.phone,
            'referralprogram':'',
            'g-recaptcha-response':code,
            'email_create':'1',
            'is_new_customer':'1',
            'back':'',
            'submitAccount':''
        }
        while True:
            try:
                r = self.s.post(
                    "https://www.basket4ballers.com/fr/authentification", 
                    data = payload, 
                    timeout = 120
                )
                if 'stackpath' in r.text and any([x in r.text for x in ['captchaImageInline', '"vii="']]):
                    self.handle_challenge(r)
                    continue
                if 'mon-compte' in r.url:
                    self.success('Account created!')
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
                    self.error(f'Error creatinga account: {r.status_code}, retrying...')
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
        self.SavingAccount()

    def SavingAccount(self):

        global cnum
        txt = self.mail + ':' + self.password
        self.warn('Saving account...')
        try:
            path = os.path.dirname(__file__).rsplit('/', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), "genb4b")
            file_to_open = os.path.join(path, "output.txt")
            with open(file_to_open, 'a') as output:
                output.writelines(f'{txt}\n')
                output.close()
                self.success('Account saved in txt')
                cnum = cnum + 1
                self.bar()
        except Exception as e:
            self.error(f'Failed saving account: {e}')
            input("")