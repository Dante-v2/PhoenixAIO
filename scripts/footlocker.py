import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, pytz
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
import traceback
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

def balancefunc():
    try:
        payload = {
            "clientKey": config['capmonster']
        }
        data = requests.post("https://api.capmonster.cloud/getBalance", json = payload)
        jsona = json.loads(data.text)
        balance = jsona['balance']
        return balance
    except:
        balance = 'Unkown'
        return balance

class FOOTLOCKER():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
        
        try:
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'footlocker/exceptions.log')
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'footlocker/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "footlocker/proxies.txt")
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

        self.sku = row['SKU']
        self.size = row['SIZE']
        self.mail = row['MAIL']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.country = row['COUNTRY']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2'] 
        self.zipcode = row['ZIPCODE']
        self.city = row['CITY']
        self.region = row['REGION']
        self.phone = row['PHONE']
        self.cardnumber = row['CARDNUMBER']
        self.housenumber = row['HOUSENUMBER']
        self.month = row['MONTH']
        self.year = row['YEAR']
        self.ccv = row['CCV']
        self.mode = row['MODE']

        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        
        self.monster = config['capmonster']
        self.build_proxy()
        self.lang = self.country.lower()
        self.discord = DISCORD_ID
        self.timeout = 120
        self.balance = balancefunc()
        self.bar()
        self.delay = int(config['delay'])

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

        self.domain = ''
        self.countryname = ''

        if self.country == "DK":
            self.domain = "https://www.footlocker.dk"
            self.countryname = "Denmark"

        elif self.country == "BE":
            self.domain = "https://www.footlocker.be"
            self.countryname = "Belgium"

        elif self.country == "GR":
            self.domain = "https://www.footlocker.gr"
            self.countryname = "Greece"

        elif self.country == "HU":
            self.domain = "https://www.footlocker.hu"
            self.countryname = "Hungary"

        elif self.country == "IE":
            self.domain = "https://www.footlocker.ie"
            self.countryname = "Ireland"

        elif self.country == "IT":
            self.domain = "https://www.footlocker.it"
            self.countryname = "Italy"

        elif self.country == "LU":
            self.domain = "https://www.footlocker.lu"
            self.countryname = "Luxemburg"

        elif self.country == "NO":
            self.domain = "https://www.footlocker.no"
            self.countryname = "Norway"

        elif self.country == "AT":
            self.domain = "https://www.footlocker.at" 
            self.countryname = "Austria"

        elif self.country == "CZ":
            self.domain = "https://www.footlocker.cz"     
            self.countryname = "Czech Republic" 

        elif self.country == "PL":
            self.domain = "https://www.footlocker.pl"
            self.countryname = "Poland"

        elif self.country == "PT":
            self.domain = "https://www.footlocker.pt"
            self.countryname = "Portugal"

        elif self.country == "SE":
            self.domain = "https://www.footlocker.se"
            self.countryname = "Sweden"

        elif self.country == "ES":
            self.domain = "https://www.footlocker.es"
            self.countryname = "Spain"

        elif self.country == "DE":
            self.domain = 'https://www.footlocker.de'
            self.countryname = 'Deutschland'

        elif self.country == 'FR':
            self.domain = 'https://www.footlocker.fr'
            self.countryname = 'France'
        
        elif self.country == 'UK' or 'GB':
            self.domain = 'https://www.footlocker.co.uk'
            self.countryname = 'United Kingdom'
            self.country = 'GB'

        elif self.country == 'NL':
            self.domain = 'https://www.footlocker.nl'
            self.countryname = 'Netherlands'

        self.warn('Starting tasks...')

        self.gettoken()

        if self.mode == 'SPECIAL':
            self.getprodapi()
        else:
            self.getprod()

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [FOOTLOCKER] [{self.sku}] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [FOOTLOCKER] [{self.sku}] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [FOOTLOCKER] [{self.sku}] - {text}'
        warn(message)


#####################################################################################################################  - CHOOSE PROXY


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
                f'Phoenix AIO {self.version} - Running FOOTLOCKER | Capmonster Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running FOOTLOCKER | Capmonster Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')



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




################################################################################################################################# - GET AL PRODOTTO


    def datadomesolve(self):

        try:

            captchalink = f"https://geo.captcha-delivery.com/captcha/?initialCid={self.initialcid}&referer=www.footlocker.it&hash={self.hsh}&t=fe&s={self.sss}&cid={self.cid}&referer={self.referer}"
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
                warn(ciao)
                self.initialcid = ciao.split("&icid=' + encodeURIComponent('")[1].split("'")[0]
                self.hsh = ciao.split("&hash=' + encodeURIComponent('")[1].split("'")[0]
                self.ip = ciao.split("(IP ")[1].split(")")[0]
                self.warn('Solving captcha...')
                captchaurl = "https://api.capmonster.cloud/createTask"
                payload = {
                    "clientKey": self.monster,
                    "task":
                    {
                        "type":"NoCaptchaTaskProxyless",
                        "websiteURL":self.domain,
                        "websiteKey":"6LccSjEUAAAAANCPhaM2c-WiRxCZ5CzsjR_vd8uX",
                    }
                }
                r = self.s.post(captchaurl, json = payload)
                taskid = r.text.split('"taskId":')[1].split('}')[0]
                data = {
                    "clientKey": self.monster,
                    "taskId": taskid
                }
                r = self.s.post("https://api.capmonster.cloud/getTaskResult", json = data)
                while not "ready" in r.text:
                    time.sleep(5)
                    r = requests.post("https://api.capmonster.cloud/getTaskResult", json = data)
                if "ready" in r.text:
                    self.success('Captcha solved!')
                    self.captcha = r.text.split('"gRecaptchaResponse":"')[1].split('"')[0]
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
                    dd_url = 'https://geo.captcha-delivery.com/captcha/check?cid=' + self.cid + '&icid=' + self.initialcid +'&ccid=' + 'null' +'&g-recaptcha-response=' + self.captcha +'&hash=' + self.hsh +'&ua=' + 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' +'&referer=' + f'{self.domain}' +'&parent_url=' + f'{self.domain}' + '&s=' + str(self.sss)
                    r = requests.get(dd_url, headers = headers)
                    if r.status_code == 200:
                        jsondd = json.loads(r.text)
                        dd = jsondd['cookie']
                        dd = dd.split('datadome=')[1].split('"')[0]
                        self.cookie_obj = requests.cookies.create_cookie(domain=f"{self.domain.split('https://www')[1]}",name='datadome',value=dd)
                        self.s.cookies.set_cookie(self.cookie_obj)
                        return self.success('Datadome done, proceding...')
                    else:
                        return self.error('Datadome failed, retrying...')
            else:
                self.build_proxy()
                return self.error('Datadome failed, restarting...')
        except Exception as e:
            self.build_proxy()
            open(self.logs_path, 'a+').write(f'Exception solving datadome: {e}\n\n')
            return self.error('Datadome failed, retrying...')

    def gettoken(self):
        self.inqueue = False
        self.warn('Getting cookies...')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': '*/*',
            'Origin': self.domain,
            'Referer': self.domain,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en'
        }
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]
                if self.inqueue:
                    r = self.s.head(
                        f"{self.domain}/api/session?timestamp={timestamp}", 
                        headers = headers,
                        timeout = self.timeout
                    )
                else:
                    r = self.s.get(
                        f"{self.domain}/api/session?timestamp={timestamp}", 
                        headers = headers,
                        timeout = self.timeout
                    )
                if r.status_code == 200:
                    if self.inqueue:
                        self.inqueue = False
                        continue
                    csrf = json.loads(r.text)
                    self.csrf = csrf['data']['csrfToken']
                    break            
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()  
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 529:
                    self.inqueue = True
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed getting cookies: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed getting cookies: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting cookies: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting cookies: {e}\n\n')
                self.s.cookies.clear()
                self.build_proxy()
                continue
        return self.success('Succesfully got cookies...')  

    def getprodapi(self):
        self.inqueue = False
        self.warn('Getting product...')
        headers = {
            'Accept': 'application/ld+json',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6'
        }
        self.s.headers.update(headers)
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]
                if self.inqueue:
                    r = self.s.head(
                        f'{self.domain}/./api/products/pdp/{self.sku}?format=json&_v=7515&timestamp={timestamp}',
                        timeout = self.timeout
                    )
                else:
                    r = self.s.get(
                        f'{self.domain}/./api/products/pdp/{self.sku}?format=json&_v=7515&timestamp={timestamp}',
                        timeout = self.timeout
                    )
                if r.status_code == 200:
                    if self.inqueue:
                        self.inqueue = False
                        continue
                    r_json = json.loads(r.text)
                    self.title = r_json['name']
                    self.price = r_json['sellableUnits'][0]['price']['value']
                    self.image = f"https://images.footlocker.com/is/image/FLEU/{self.sku}_01?wid=640&hei=640&fmt=png-phoenix"
                    try:
                        self.date = r_json['variantAttributes'][0]['skuLaunchDate']
                        if "Jan" in self.date:
                            mese = "Gen"
                            month = "01"
                        elif "Feb" in self.date:
                            mese = "Feb"
                            month = "02"
                        elif "Mar" in self.date:
                            mese = "Mar"
                            month = "03"
                        elif "Apr" in self.date:
                            mese = "Apr"
                            month = "04"
                        elif "May" in self.date:
                            mese = "May"
                            month = "05"
                        elif "Jun" in self.date:
                            mese = "Jun"
                            month = "06"
                        elif "Jul" in self.date:
                            mese = "Jul"
                            month = "07"
                        elif "Aug" in self.date:
                            mese = "Aug"
                            month = "08"
                        elif "Sep" in self.date:
                            mese = "Sep"
                            month = "09"
                        elif "Oct" in self.date:
                            mese = "Oct"
                            month = "10"
                        elif "Nov" in self.date:
                            mese = "Nov"
                            month = "11"
                        elif "Dec" in self.date:
                            mese = "Dec"
                            month = "12"
                        day = self.date.split(f"{mese} ")[1].split(" ")[0]
                        year = self.date.split(f"{day} ")[1].split(" ")[0]
                        ora = self.date.split(f"{year} ")[1].split(" ")[0]
                        dataprod = datetime.strptime(f'{day}-{month}-{year} {ora}', "%d-%m-%Y %H:%M:%S")
                        now = datetime.utcnow()
                        delta = int((dataprod-now).total_seconds())
                        if delta > 15:
                            self.time_to_sleep = delta - 15
                            self.warn(f'Timer found {self.date}, sleeping for {self.time_to_sleep} seconds...')
                            time.sleep(self.time_to_sleep)
                            continue
                        else:
                            pass
                    except:
                        pass
                    sizes = r_json['sellableUnits']
                    sizesinstock = []
                    variant = []
                    sizerange = []
                    for element in sizes:
                        if element['stockLevelStatus'] == 'inStock':
                            sizesinstock.append(element['attributes'][0]['value'])
                            variant.append(element['attributes'][0]['id'])
                    mylist = zip(sizesinstock, variant)
                    self.connect = list(mylist)
                    if len(sizesinstock) < 1:
                        self.warn(f'{self.title} is OOS, monitoring...')
                        time.sleep(self.delay)
                        continue
                    else:
                        try:
                            if self.size == "RANDOM":
                                self.success(f'{self.title} in stock')
                                self.sizerandom = random.choice(sizesinstock)
                                for i in self.connect:
                                    if self.sizerandom in i[0]:
                                        self.variant = i[1]
                                        self.sizescelta = i[0]
                                break
                            elif '-' in self.size:
                                self.size1 = str(self.size.split('-')[0])
                                self.size2 = str(self.size.split('-')[1])
                                for x in sizesinstock:
                                    if self.size1 <= str(x) <= self.size2:
                                        sizerange.append(x)      
                                self.sizerandom = random.choice(sizerange)
                                self.success(f'{self.title} size {self.sizerandom} in stock!')
                                for i in self.connect:
                                    if self.sizerandom in i[0]:
                                        self.variant = i[1]
                                        self.sizescelta = i[0]
                                break
                            elif ',' in self.size:
                                self.size1 = str(self.size.split(',')[0])
                                self.size2 = str(self.size.split(',')[1])
                                for x in sizesinstock:
                                    if self.size1 <= str(x) <= self.size2:
                                        sizerange.append(x)        
                                self.sizerandom = random.choice(sizerange)
                                self.success(f'{self.title} size {self.sizerandom} in stock!')
                                for i in self.connect:
                                    if self.sizerandom in i[0]:
                                        self.variant = i[1]
                                        self.sizescelta = i[0]
                                break
                            else:
                                for element in self.connect:
                                    if self.size == element[0]:
                                        self.success(f'{self.title} size {self.size} in stock!')
                                        self.sizescelta = element[0]
                                        self.variant = element[1]
                                break
                        except Exception as e:
                            self.warn(f'{self.title} is OOS, monitoring...')
                            open(self.logs_path, 'a+').write(f'Product Exception API: {r.text}\n\n')
                            time.sleep(self.delay)
                            continue
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy() 
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {mess}...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 529:
                    self.inqueue = True
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed getting product API: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed getting product API: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting product API: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting product API: {e}\n\n')
                self.build_proxy()
                continue
        self.atc()

    def getprod(self):
        self.inqueue = False
        self.warn('Getting product...')
        headers = {
            'Accept': 'application/ld+json',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6'
        }
        self.s.headers.update(headers)
        while True:
            try:
                if self.inqueue:
                    r = self.s.head(
                        f"{self.domain}/product/~/{self.sku}.html", 
                        timeout = self.timeout
                    )
                else:
                    r = self.s.get(
                        f"{self.domain}/product/~/{self.sku}.html", 
                        timeout=self.timeout
                    )
                if r.status_code == 200:
                    if self.inqueue:
                        self.inqueue = False
                        continue
                    jsonhtml = r.text.split('window.footlocker.STATE_FROM_SERVER = ')[1].split('}};')[0]
                    jsonhtml = jsonhtml + "}"
                    jsonhtml = jsonhtml + "}"
                    jsonall = json.loads(jsonhtml)
                    try:
                        self.price = jsonall['details']['data'][f'/product/~/{self.sku}.html'][0]['price']['value']
                        self.title = jsonall['details']['product'][f'/product/~/{self.sku}.html']['name']
                        self.image = f"https://images.footlocker.com/is/image/FLEU/{self.sku}_01?wid=640&hei=640&fmt=png-phoenix"
                    except Exception as e:
                        self.error(f'Failed parsing {e.__class__.__name__}, retrying...')
                        open(self.logs_path, 'a+').write(f'Failed parsing: {e}\n\n')
                        time.sleep(self.delay)
                        self.build_proxy()   
                        continue
                    try:
                        self.date = jsonall['details']['data'][f'/product/~/{self.sku}.html'][0]['skuLaunchDate']
                        if "Jan" in self.date:
                            mese = "Gen"
                            month = "01"
                        elif "Feb" in self.date:
                            mese = "Feb"
                            month = "02"
                        elif "Mar" in self.date:
                            mese = "Mar"
                            month = "03"
                        elif "Apr" in self.date:
                            mese = "Apr"
                            month = "04"
                        elif "May" in self.date:
                            mese = "May"
                            month = "05"
                        elif "Jun" in self.date:
                            mese = "Jun"
                            month = "06"
                        elif "Jul" in self.date:
                            mese = "Jul"
                            month = "07"
                        elif "Aug" in self.date:
                            mese = "Aug"
                            month = "08"
                        elif "Sep" in self.date:
                            mese = "Sep"
                            month = "09"
                        elif "Oct" in self.date:
                            mese = "Oct"
                            month = "10"
                        elif "Nov" in self.date:
                            mese = "Nov"
                            month = "11"
                        elif "Dec" in self.date:
                            mese = "Dec"
                            month = "12"
                        day = self.date.split(f"{mese} ")[1].split(" ")[0]
                        year = self.date.split(f"{day} ")[1].split(" ")[0]
                        ora = self.date.split(f"{year} ")[1].split(" ")[0]
                        dataprod = datetime.strptime(f'{day}-{month}-{year} {ora}', "%d-%m-%Y %H:%M:%S")
                        now = datetime.utcnow()
                        delta = int((dataprod-now).total_seconds())
                        if delta > 15:
                            self.time_to_sleep = delta - 15
                            self.warn(f'Timer found {self.date}, sleeping for {self.time_to_sleep} seconds...')
                            time.sleep(self.time_to_sleep)
                            continue
                        else:
                            pass  
                    except Exception as e:
                        pass
                    sizes = jsonall['details']['sizes'][f'/product/~/{self.sku}.html']
                    sizesinstock = []
                    variant = []
                    sizerange = []
                    for element in sizes:
                        if element['isDisabled'] == False:
                            sizesinstock.append(element['name'])
                            variant.append(element['code'])
                    mylist = zip(sizesinstock, variant)
                    self.connect = list(mylist)
                    if len(sizesinstock) < 1:
                        self.warn(f'{self.title} is OOS, monitoring...')
                        time.sleep(self.delay)
                        continue
                    else:
                        try:
                            if self.size == "RANDOM":
                                self.success(f'{self.title} in stock')
                                self.sizerandom = random.choice(sizesinstock)
                                for i in self.connect:
                                    if self.sizerandom in i[0]:
                                        self.variant = i[1]
                                        self.sizescelta = i[0]
                                break
                            elif '-' in self.size:
                                self.size1 = str(self.size.split('-')[0])
                                self.size2 = str(self.size.split('-')[1])
                                for x in sizesinstock:
                                    if self.size1 <= str(x) <= self.size2:
                                        sizerange.append(x)      
                                self.sizerandom = random.choice(sizerange)
                                self.success(f'{self.title} size {self.sizerandom} in stock!')
                                for i in self.connect:
                                    if self.sizerandom in i[0]:
                                        self.variant = i[1]
                                        self.sizescelta = i[0]
                                break
                            elif ',' in self.size:
                                self.size1 = str(self.size.split(',')[0])
                                self.size2 = str(self.size.split(',')[1])
                                for x in sizesinstock:
                                    if self.size1 <= str(x) <= self.size2:
                                        sizerange.append(x)        
                                self.sizerandom = random.choice(sizerange)
                                self.success(f'{self.title} size {self.sizerandom} in stock!')
                                for i in self.connect:
                                    if self.sizerandom in i[0]:
                                        self.variant = i[1]
                                        self.sizescelta = i[0]
                                break
                            else:
                                for element in self.connect:
                                    if self.size == element[0]:
                                        self.success(f'{self.title} size {self.size} in stock!')
                                        self.sizescelta = element[0]
                                        self.variant = element[1]
                                break
                        except Exception as e:
                            self.warn(f'{self.title} is OOS, monitoring...')
                            open(self.logs_path, 'a+').write(f'Product Exception: {r.text}\n\n')
                            time.sleep(self.delay)
                            continue
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy() 
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {mess}...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 529:
                    self.inqueue = True
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed getting product: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed getting product: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting product: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting product: {e}\n\n')
                self.build_proxy()
                continue
        self.atc()

    def atc(self):
        global carted
        self.oos = False
        self.warn('Adding to cart...')
        headers = {
            'Accept': 'application/json',
            'Referer': f"{self.domain}/product/~/{self.sku}.html",
            'x-fl-productid': self.variant
        }
        payload = {'productQuantity': 1, 'productId': self.variant}
        while True:
            try:
                r = self.s.post(
                    f"{self.domain}/api/users/carts/current/entries?timestamp={int(time.time() * 1000)}", 
                    json = payload, 
                    headers = headers,
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    jsonatc = json.loads(r.text)
                    if jsonatc['totalItems'] == 1:
                        self.success(f'{self.title} added to cart!')
                        self.cartId = jsonatc['guid']
                        carted = carted + 1
                        self.bar()
                        break
                elif r.status_code == 531:
                    if 'Product and/or size is out of stock' in r.text:
                        self.warn(f'{self.title} OOS, retrying...')
                        self.oos = True
                        time.sleep(self.delay)
                        break
                    elif 'The product could not be added to the cart.' in r.text:
                        self.warn(f'{self.title} cannot be added to cart, retrying...')
                        self.oos = True
                        time.sleep(self.delay)
                        break
                    elif 'ProductLowStockException' in r.text:
                        self.warn(f'{self.title} OOS, retrying...')
                        self.oos = True
                        time.sleep(self.delay)
                        break
                    else:
                        self.warn(f'Site is dead, retrying...')
                        open(self.logs_path, 'a+').write(f'Exception adding to cart 531: {r.text}\n\n')
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy() 
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {mess}...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 529:
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed adding to cart: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed adding to cart: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception adding to cart: {e}\n\n')
                self.build_proxy()
                continue
        if self.oos:
            self.getprod()
        else:
            self.shipping()

    def shipping(self):
        self.warn('Submitting shipping...')
        headers = {
            'Referer': f'{self.domain}/checkout',
            'x-csrf-token': self.csrf
        }
        self.s.headers.update(headers)
        payload = {"shippingAddress":{"setAsDefaultBilling":False,"setAsDefaultShipping":False,"firstName":f"{self.name}","lastName":f"{self.surname}","email":False,"phone":f"{self.phone}","country":{"isocode":f"{self.country}","name":f"{self.countryname}"},"id":None,"setAsBilling":True,"type":"default","line1":f"{self.address}","line2":f"{self.housenumber}","companyName":f"{self.address2}","postalCode":f"{self.zipcode}","town":f"{self.city}","shippingAddress":True}}
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]
                t = self.s.put(
                    f"{self.domain}/api/users/carts/current/email/{self.mail}?timestamp={timestamp}", 
                    timeout = self.timeout
                )
                if t.status_code == 200:
                    now = datetime.now()
                    timestamp = str(datetime.timestamp(now)).split('.')[0]      
                    r = self.s.post(
                        f"{self.domain}/api/users/carts/current/addresses/shipping?timestamp={timestamp}", 
                        json = payload,
                        timeout = self.timeout
                    )
                    if r.status_code == 200 or r.status_code == 201:
                        self.success('Succesfully submitted ship!')
                        break
                    elif r.status_code == 403:
                        if "geo.captcha-delivery" in r.text:
                            open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                            self.warn('Datadome found, solving...')
                            self.referer = r.url
                            jsondata = json.loads(r.text)
                            self.ddlink = jsondata['url']
                            if "t=fe" in self.ddlink:
                                self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                                self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                                self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                                cid = []
                                cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                                for cookie in cookies:
                                    if cookie['name'] == "datadome":
                                        cid.append(cookie)
                                ciddo = cid[-1]
                                self.cid = ciddo["value"]
                                self.datadomesolve()
                                continue
                            else:
                                self.error('Proxy banned, rotating...')
                                self.build_proxy()                       
                                continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                    
                            time.sleep(self.delay)
                            continue
                    elif r.status_code == 429:
                        self.error('Rate limit, retrying...')
                        self.build_proxy()  
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 400:
                        r_json = json.loads(r.text)
                        mess = r_json['errors'][0]['message']
                        self.error(f'Unkown error 400: {mess}...')
                        time.sleep(self.delay)
                        continue
                    elif r.status_code == 529:
                        self.warn('Waiting in queue...')
                        time.sleep(self.delay)
                        continue
                    elif r.status_code >= 501 and r.status_code <= 600:
                        self.warn('Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error(f'Failed submitting ship 1: {r.status_code}, retrying...')
                        open(self.logs_path, 'a+').write(f'Failed submitting ship 1: {r.status_code} - {r.text}\n\n')
                        time.sleep(self.delay)
                        continue
                elif t.status_code == 403:
                    if "geo.captcha-delivery" in t.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {t.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = t.url
                        jsondata = json.loads(t.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif t.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif t.status_code == 400:
                    r_json = json.loads(t.text)
                    mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {mess}...')
                    time.sleep(self.delay)
                    continue
                elif t.status_code == 529:
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif t.status_code >= 501 and t.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed submitting ship 2: {t.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed submitting ship 2: {t.status_code} - {t.text}\n\n')
                    time.sleep(self.delay)
                    continue 
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting ship: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting ship: {e}\n\n')
                self.build_proxy()
                continue
        self.billing()

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

    def billing(self):
        self.warn('Submitting billing...')
        headers = {
            'Content-Type': 'application/json'
        }
        self.s.headers.update(headers)
        payload = {"setAsDefaultBilling":False,"setAsDefaultShipping":False,"firstName":f"{self.name}","lastName":f"{self.surname}","email":f"{self.mail}","phone":f"{self.phone}","country":{"isocode":f"{self.country}","name":f"{self.countryname}"},"billingAddress":False,"defaultAddress":False,"id":None,"line1":f"{self.address}","line2":f"{self.housenumber}","postalCode":f"{self.zipcode}","setAsBilling":False,"shippingAddress":True,"town":f"{self.city}","visibleInAddressBook":False,"type":"default"}
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]                
                r = self.s.post(
                    f"{self.domain}/api/users/carts/current/set-billing?timestamp={timestamp}", 
                    json = payload, 
                    timeout = self.timeout
                )
                if r.status_code == 200 or r.status_code == 201:
                    self.success(f'Succesfully submitted billing info!')
                    break
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {mess}...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 529:
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed submitting billing: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed submitting billing: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting billing: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting billing: {e}\n\n')
                self.build_proxy()
                continue
        self.cartid()

    def cartid(self):
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]
                r = self.s.get(
                    f'https://www.footlocker.it/apigate/payment/origin-key?timestamp={timestamp}',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    cok = r.headers['cookie']
                    try:
                        self.cartid = cok.split('cart-guid=')[1].split('"')[0]
                    except:
                        self.cartid = cok.split('cart-guid=')[1].split(';')[0]
                    break
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {mess}...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 529:
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed getting cart id: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed fetting cart id: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while fetting cart id: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception fetting cart id: {e}\n\n')
                self.build_proxy()
                continue
        self.payment()

    def payment(self):
        global checkoutnum, failed
        domainpay = self.domain.split("https://")[1]
        self.warn('Submitting payment...')
        payload = {
            "preferredLanguage":"en",
            "termsAndCondition":"true",
            "deviceId": "0400tyDoXSFjKeoNf94lis1ztlZtWBcopyaUnrp/XmcfWoVVgr+Rt2dAZJwqfugLyw16aHjoci9mfzLNc/p/1y9PHkhCTHg+Ms0Qhlz5wlRFwWJi0FRulruXQQGCQaJkXU7Gbz+TZBGag2SFzKYASkyDKc2w5Oiu8PINGOHB0gntnRvQCIGUostrwxhRl5+BXrF/ZbZo3AYwhwqwrwf88vayC9C1UJgA1BQZQ4JudHOlf1KSnrbJSNyIsWB9R+WFa6fdxifyrThRovESnjwNVGXSgGQ8InPsuf6/kpMgG84gzO5PMQF00uJew9XqxzJ4y+q4yIddtgixYfca8xSYcPQjcMqH41TOqjAbljAlWwXHcT+hgN6tJA4p1nA+k9XRlIy/AN0re1eWCpflW0z0X1sbAkKfK2f2LqDxmXB1Q+kIsL2IeZXnmtbT+R+W/xGFgJx4xA9x3qRKbjNd7ZvazhuGJULH+jv8B8PWfveZj4MPqv5iYfvT/1ZgWFuih4KCV6qpwB5oMrZNKC104hiAcL/dBjV9nBJW1Y3JLACqjtcRnAt1iB/Zpw79oe9RJsn4u3PdHf7WUtiodkRAG1X5+Z1zMigZGn+l3DrnzBRxN5nDyWopQs/EGzmZL52uywT0kPEtmuV8kC9DdyjkY08rRcs5IwQxSxzPuRtycb0H5IjHkCcKSs4KVYKB4nE8CyQlNLm8WJXfiiqf2x9HDo0vYYDC32sBOC7Bb3k7bazR87feXj5NK8155+SfnP10F4hyuT+ZFiKry47CadKyPr0t8ztVFisjUV4dJsOym9ceHDKRCiK4xI1RTIYC8ouD71qCKcmZqa+c5UMfdLNXqLz+1vlqUAr9dE2jcfl0wgroQBfpyuJNserFTujH2c1NyGt/lP5sVTw2C4oQ2p6vWc20/w4QKST/riUqiozfAOitx40UDzaLaxNWMM2S8UTjbKzZpUNBxKb7FG+fia+fFCEvMT9cc6XakoCa7XCW5+Cltm6/m0VPMQF00uJew0LT2BH9Dx8Z6yFodg/w6rrW98ebjBvKOYCZ40cfr7Dqq81Hf8KeTB7xbAbw9wOZT+CAwTHXRztWL77ZVX6Kll4BUtJtVS3P8QKAYonHlAsUl5gsJlyCOs3JuFHPwaxOxjFSc3ug46HsWrjg3IZNlqx9izplUCi1HWHk3C7XHo8gsT5NlJKg73WBGA35nwcAWEYXN3+bqydWqLZcnDBAS9SM8lXpMISOf7T7130BIPii0VbAzVM5zPuCJUUDvOkg9DiEuyx+fdZIO0PdhRirnrvxVajijX/olP0gnWv61S0CmfIlqQ8q/NqROL2vH182cyJUe0rP2ibFLWxZ9Fm3PO2ahWJ6pa8AdANsW6g00ZKC",
            "cartId": self.cartId,
            "encryptedCardNumber":self.maincard(pan = self.cardnumber, key = "10001|B6D07BD544BD5759FA13F1972F229EDFD76D2E39EC209797FC6A6A6B9F3388DD70255D83369FC6A10A9E3DDC90968345D62D73793B480C59458BA5C7E0EFBADC81DAE4060079064C556B4324C9EEA8D26EBB9011BBD8F769A6E463F2D078621ABC1432393FAECE489A68D85A0176A58E7292CB36E124305EB098DFB89C24AD58A27F7A21329DA2FE401199D5952C630340535785323E56F2B72AB8F18EA05DBA7A811C7A83B4B661358B6CCC338498F6BA10C9A16408FD33A231CC00EEE5A9397D92ECF3D616D44A687062833B5BF91EED57E3129B98B559192D65B787AE5A230A86D4ACF23C485318095DC4C589D1E990809BB2B74F0EDD3225FD3A64D89DD1"),
            "encryptedExpiryMonth": self.mainmonth(expiry_month = self.month, key = "10001|B6D07BD544BD5759FA13F1972F229EDFD76D2E39EC209797FC6A6A6B9F3388DD70255D83369FC6A10A9E3DDC90968345D62D73793B480C59458BA5C7E0EFBADC81DAE4060079064C556B4324C9EEA8D26EBB9011BBD8F769A6E463F2D078621ABC1432393FAECE489A68D85A0176A58E7292CB36E124305EB098DFB89C24AD58A27F7A21329DA2FE401199D5952C630340535785323E56F2B72AB8F18EA05DBA7A811C7A83B4B661358B6CCC338498F6BA10C9A16408FD33A231CC00EEE5A9397D92ECF3D616D44A687062833B5BF91EED57E3129B98B559192D65B787AE5A230A86D4ACF23C485318095DC4C589D1E990809BB2B74F0EDD3225FD3A64D89DD1"),
            "encryptedExpiryYear":self.mainyear(expiry_year = self.year, key = "10001|B6D07BD544BD5759FA13F1972F229EDFD76D2E39EC209797FC6A6A6B9F3388DD70255D83369FC6A10A9E3DDC90968345D62D73793B480C59458BA5C7E0EFBADC81DAE4060079064C556B4324C9EEA8D26EBB9011BBD8F769A6E463F2D078621ABC1432393FAECE489A68D85A0176A58E7292CB36E124305EB098DFB89C24AD58A27F7A21329DA2FE401199D5952C630340535785323E56F2B72AB8F18EA05DBA7A811C7A83B4B661358B6CCC338498F6BA10C9A16408FD33A231CC00EEE5A9397D92ECF3D616D44A687062833B5BF91EED57E3129B98B559192D65B787AE5A230A86D4ACF23C485318095DC4C589D1E990809BB2B74F0EDD3225FD3A64D89DD1"),
            "encryptedSecurityCode": self.maincvv(cvc = self.ccv, key = "10001|B6D07BD544BD5759FA13F1972F229EDFD76D2E39EC209797FC6A6A6B9F3388DD70255D83369FC6A10A9E3DDC90968345D62D73793B480C59458BA5C7E0EFBADC81DAE4060079064C556B4324C9EEA8D26EBB9011BBD8F769A6E463F2D078621ABC1432393FAECE489A68D85A0176A58E7292CB36E124305EB098DFB89C24AD58A27F7A21329DA2FE401199D5952C630340535785323E56F2B72AB8F18EA05DBA7A811C7A83B4B661358B6CCC338498F6BA10C9A16408FD33A231CC00EEE5A9397D92ECF3D616D44A687062833B5BF91EED57E3129B98B559192D65B787AE5A230A86D4ACF23C485318095DC4C589D1E990809BB2B74F0EDD3225FD3A64D89DD1"),
            "paymentMethod":"CREDITCARD",
            "returnUrl":f"{self.domain}/adyen/checkout",
            "browserInfo":{
                "screenWidth":1920,
                "screenHeight":1080,
                "colorDepth":24,
                "userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
                "timeZoneOffset":-60,
                "language":"en",
                "javaEnabled":"false"
            }
        }
        declined = False
        copped = False
        tredi = False
        declined2 = False
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]
                r = self.s.post(
                    f"{self.domain}/api/users/orders/adyen?timestamp={timestamp}", 
                    json = payload, 
                    timeout = self.timeout
                )   
                if r.status_code == 200 or r.status_code == 201:
                    if "Unfortunately, we can't process this transaction." in r.text:
                        self.error('Payment Declined!')
                        failed = failed + 1
                        self.bar()
                        declined = True
                        break 
                    elif 'orderCreationDate' in r.text:
                        self.success('Succesfully checked out!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        c = json.loads(r.text)
                        self.ordernum = c['order']['code']
                        copped = True
                        break
                    else:
                        self.jsonpay = json.loads(r.text)
                        self.posturl = self.jsonpay['action']['url']
                        self.paymentdata = self.jsonpay['action']['paymentData']
                        self.md = self.jsonpay['md']
                        self.paReq = self.jsonpay['paReq']
                        self.termurl = self.jsonpay['termUrl']
                        tredi = True
                        break
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    self.mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {self.mess}...')
                    declined2 = True
                    break 
                elif r.status_code == 529:
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed submitting order: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed submitting order: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting order: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting order: {e}\n\n')
                self.build_proxy()
                continue
        if declined:
            self.declined()
        if declined2:
            self.declined2()
        if copped:
            self.SuccessCC()    
        if tredi:
            self.webhook3d()
            asyncio.run(self.main3d())
            if self._3dshort:
                try:
                    self.pares = self.threeddata.split("PaRes=")[1].split('&MD=')[0]
                except:
                    self.pares = self.threeddata.split("PaRes=")[1]
                try:
                    self.md2 = self.threeddata.split("&MD=")[1]
                except:
                    self.md2 = self.threeddata.split('MD=')[1].split('&PaRes=')[0]
                self.order()
            else:
                self.checkoutstopper()

    async def main3d(self):
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
            self._3dshort = False

            async def intercept(request):
                if '/checkout' in request.url:
                    self._3dsAccepted = True
                    self._3dshort = True
                    self.threeddata = request._postData
                    self.threedheaders = request._headers
                    self.threedurl = request.url
                    await request.abort()
                    await chrome.close()
                    return True
                #elif 'challengeShopper' in request.url:
                #    self._3dsAccepted = True
                #    self.threeddata = request._postData
                #    self.threedheaders = request._headers
                #    self.threedurl = request.url
                #    await request.abort()
                #    await chrome.close()
                #    return True
                else:
                    self._3dsAccepted = False
                    await request.continue_()

            page.on('request', lambda req: asyncio.ensure_future(intercept(req)))
            script = html.format(self.posturl, self.paReq, self.termurl, self.md)
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
    
    def checkoutstopper(self):
        headers = {
            'Content-Type':'application/x-www-form-urlencoded',
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer':'https://checkoutshopper-live.adyen.com/checkoutshopper/threeDS2.shtml'
        }
        payload = {
            'MD':self.md,
            'PaReq':self.paReq,
            'TermUrl':self.termurl,
            'transStatus':'Y'
        }
        self.warn('Submitting 3D secure...')
        while True:
            try:
                r = self.s.post(
                    'https://checkoutshopper-live.adyen.com/checkoutshopper/challengeShopper.shtml',
                    data = payload,
                    headers = headers,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.pares = r.text.split('PaRes" value="')[1].split('"')[0]
                    self.success('Succesfully submitted 3d secure!')
                    break
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {mess}...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 529:
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed submitting 3d: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed submitting 3d: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting 3d: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting 3d: {e}\n\n')
                self.build_proxy()
                continue
        self.order()
    
    def sessionredirect(self):
        try:
            self.pares = self.threeddata.split("PaRes=")[1].split('&MD=')[0]
        except:
            self.pares = self.threeddata.split("PaRes=")[1]
        payload = {
            'MD':self.md,
            'PaRes':self.pares
        }
        while True:
            try:
                r = self.s.post(
                   self.threedurl,
                   data = payload,
                   timeout = self.timeout
                )
                if r.status_code == 200:
                    print(r.text)
                    #try:
                    #    self.pares = self.threeddata.split("PaRes=")[1].split('&MD=')[0]
                    #except:
                    #    self.pares = self.threeddata.split("PaRes=")[1]
                    print(self.pares)
                    break
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {mess}...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 529:
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed session redirect: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed session redirect: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while session redirect: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception session redirect: {e}\n\n')
                self.build_proxy()
                continue
        self.order()

    def order(self):
        payload = {
            "md": self.md2,
            "paRes": self.pares,
            "cartId": self.cartid,
            "paymentData": self.paymentdata,
            "paymentMethod": "CREDITCARD"
        }
        headers = {
            'Accept':'application/json'
        }
        self.s.headers.update(headers)
        decline = False
        self.warn('Submitting order...')
        while True:
            try:
                now = datetime.now()
                timestamp = str(datetime.timestamp(now)).split('.')[0]
                r = self.s.post(
                    f'https://www.footlocker.it/api/users/orders/completePayment?timestamp={timestamp}',
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200 or r.status_code == 201:
                    c = json.loads(r.text)
                    self.ordernum = c['order']['code']
                    self.success('Succesfully checked out!')
                    break
                elif r.status_code == 403:
                    if "geo.captcha-delivery" in r.text:
                        open(self.logs_path, 'a+').write(f'Datadome: {r.text}\n\n')
                        self.warn('Datadome found, solving...')
                        self.referer = r.url
                        jsondata = json.loads(r.text)
                        self.ddlink = jsondata['url']
                        if "t=fe" in self.ddlink:
                            self.initialcid = self.ddlink.split("initialCid=")[1].split("&")[0]
                            self.hsh = self.ddlink.split("hash=")[1].split("&")[0]
                            self.sss = self.ddlink.split('&s=')[1].split('"')[0]
                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]
                            self.datadomesolve()
                            continue
                        else:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()                       
                            continue
                    else:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()                    
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    r_json = json.loads(r.text)
                    self.mess = r_json['errors'][0]['message']
                    self.error(f'Unkown error 400: {self.mess}')
                    decline = True
                    break
                elif r.status_code == 529:
                    self.warn('Waiting in queue...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 501 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed submitting order: {r.status_code}, retrying...')
                    open(self.logs_path, 'a+').write(f'Failed submitting order: {r.status_code} - {r.text}\n\n')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting order: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting order: {e}\n\n')
                self.build_proxy()
                continue
        if decline:
            self.declined2()
        self.SuccessCC()
                    
    def Pubblic_Webhook(self):
        webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'**FOOTLOCKER ||{self.country}||**', value = self.title, inline = False)
        embed.add_embed_field(name=f'**PRODUCT**', value = self.sku, inline = False)
        embed.add_embed_field(name='**SIZE**', value = str(self.sizescelta), inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = "Creditcard", inline = False)
        embed.add_embed_field(name='PRICE', value = str(self.price), inline = True)
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

    def webhook3d(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Waiting 3D Secure!', color = 16426522)
        embed.add_embed_field(name=f'**FOOTLOCKER ||{self.country}||**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = str(self.sizescelta), inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = "Creditcard", inline = True)
        embed.add_embed_field(name='PRICE', value = str(self.price), inline = True)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.set_thumbnail(url = self.image)   
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        return self.warn("Waiting for 3D secure..")



    def SuccessCC(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Successfully checked out!', color = 4437377)
        embed.add_embed_field(name=f'**FOOTLOCKER ||{self.country}||**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = str(self.sizescelta), inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = "Creditcard", inline = True)
        embed.add_embed_field(name='PRICE', value = str(self.price), inline = True)
        embed.add_embed_field(name='ORDER NUMBER', value = f"||{str(self.ordernum)}||", inline = True)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.set_thumbnail(url = self.image)   
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook()


    def declined(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Payment declined!', color = 15746887)
        embed.add_embed_field(name=f'**FOOTLOCKER ||{self.country}||**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = str(self.sizescelta), inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = "Creditcard", inline = True)
        embed.add_embed_field(name='PRICE', value = str(self.price), inline = True)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.set_thumbnail(url = self.image)   
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        sys.exit(1)
    
    def declined2(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Payment declined!', color = 15746887)
        embed.add_embed_field(name=f'**FOOTLOCKER ||{self.country}||**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = str(self.sizescelta), inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = "Creditcard", inline = True)
        embed.add_embed_field(name='PRICE', value = str(self.price), inline = True)
        embed.add_embed_field(name='**ERRROR MESSAGE**', value = f"||{self.mess}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.set_thumbnail(url = self.image)   
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        sys.exit(1)
