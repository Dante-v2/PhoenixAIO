import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, string
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from helheim import helheim, isChallenge
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
import traceback
from mods.errorHandler import errorHandler
import traceback

HANDLER = errorHandler(__file__)
urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

QUEUE_DATA = {
    'passed': False,
    'cookie': None,
    'time': 0
}

carted = 0
checkoutnum = 0
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

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

def queueHandler(cookie):
    try:
        if cookie:
            QUEUE_DATA['passed'] = True
            QUEUE_DATA['cookie'] = cookie
            QUEUE_DATA['time'] = int(time.time())
            return True
        else:
            if cookie == None:
                if QUEUE_DATA['passed']:
                    if QUEUE_DATA['time'] + 300 > int(time.time()):
                        return QUEUE_DATA['cookie']
                    else:
                        QUEUE_DATA['passed'] = False
                        return False
                else:
                    return False
            elif cookie == False:
                QUEUE_DATA['passed'] = False
                return False
    except:
        print(traceback.format_exc())

class EMILIOPUCCI():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
        
        self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'emiliopucci/exceptions.log')
        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "emiliopucci/proxies.txt")
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "emiliopucci/proxies.txt")
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
        self.password = row['PASSWORD']
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
        self.cardnumber = row['CARDNUMBER']
        self.expmonth = row['EXPMONTH']
        self.expyear = row['EXPYEAR']
        self.cvv = row['CVV']
        self.cardowner = row['CARDOWNER']
        self.payment = row['PAYMENT']

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
        self.discord = DISCORD_ID
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.password = self.password.replace(" ", '')
        self.mail = self.mail.replace(" ", '')
        self.build_proxy()
        self.balance = balancefunc()
        self.bar()
        self.delay = int(config['delay'])
        self.timeout = 120

        if self.country == "UK":
            self.country = "GB"

        if self.country == "UK" or self.country == "GB":
            self.currency = "GBP"
        elif self.country == "RU":
            self.currency = "RUB"
        elif self.country == "US":
            self.currency = "USD"
        else:
            self.currency = "EUR"


        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB",
            'Accept-Encoding': 'gzip, deflate',
            'content-type': 'application/json',
            'ff-country': self.country,
            'ff-currency': self.currency,
            'referer': 'https://www.emiliopucci.com/',
            'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1'
        }
        
        self.warn('Task started!')
        
        #if self.password != "":
        #    self.login()
        #else:
        self.queue()


#####################################################################################################################  - CHOOSE PROXY

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [EMILIOPUCCI] [{self.sku}] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [EMILIOPUCCI] [{self.sku}] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [EMILIOPUCCI] [{self.sku}] - {text}'
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

    def get_random_string(self, length):
        letters = string.ascii_lowercase
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str

    def get_random_string2(self, length):
        letters = string.ascii_letters + string.digits
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str

    def get_random_string3(self, length):
        letters = string.digits
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str


    def bar(self):
        if machineOS.lower() == 'windows':
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running EMILIOPUCCI | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - | 2cap Balance: {self.balance} | Running EMILIOPUCCI | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')



    def injection(self, session, response):

        #try:
        if isChallenge(response):
            self.warn('Solving Cloudflare v2')
            return helheim('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693', session, response)
        else:
            return response
        #except:
        #    if session.is_New_IUAM_Challenge(response):
        #        self.warn('Solving Cloudflare v2 api 2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
        #    elif session.is_New_Captcha_Challenge(response):
        #        self.warn('Solving Cloudflare v2 api 2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
        #    else:
        #        return response


################################################################################################################################# - GET AL PRODOTTO


    def login(self):
        self.warn('Attempting login...')
        while True:
            try:
                headers = {
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-GB",
                    'Accept-Encoding': 'utf-8',
                    'content-type': 'application/json',
                    'ff-country': self.country,
                    'ff-currency': self.currency,
                    'referer': 'https://www.emiliopucci.com/',
                    "cookie": "ss=sdjfpdsjfjkdspfds-fds-fdsfdsfdsjifdspjofd",
                    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1'
                }
                self.s.headers.update(headers)
                payload = {"username":self.mail,"password":self.password,"rememberMe":True}
                r = self.s.post(
                    f"https://www.emiliopucci.com/en-{self.country}/api/account/login", 
                    json = payload,
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code == 200:
                    self.bagid = r.text.split('{"bagId":"')[1].split('"')[0]   
                    self.success('Successfully logged in!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while logging in: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while logging in: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.stockapi()

    def queue(self):
        while True:
            try:
                headers = {
                    'authority': 'www.emiliopucci.com',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'x-newrelic-id': 'VQUCV1ZUGwIFVlBRDgcA',
                    'ff-country': self.country,
                    'ff-currency': self.currency,
                    'Accept-Language': 'en-GB',
                    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'upgrade-insecure-requests': '1',
                    'referer': 'https://www.emiliopucci.com/'
                }
                self.s.headers.update(headers)   
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')             
                r = self.s.get(
                    'https://www.emiliopucci.com/', 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    self.bagid = r.text.split('{"bagId":"')[1].split('"')[0]   
                    self.success('Successfully got user info!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting user info: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting user info: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.bag()

    def bag(self):
        self.warn('Getting user info...')
        while True:
            try:
                headers = {
                    'authority': 'www.emiliopucci.com',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'x-newrelic-id': 'VQUCV1ZUGwIFVlBRDgcA',
                    'ff-country': self.country,
                    'ff-currency': self.currency,
                    'Accept-Language': 'en-GB',
                    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'upgrade-insecure-requests': '1',
                    'referer': 'https://www.emiliopucci.com/',
                }
                self.s.headers.update(headers)   
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')             
                r = self.s.get(
                    'https://www.emiliopucci.com/api/legacy/v1/users/me', 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    self.bagid = r.text.split('{"bagId":"')[1].split('"')[0]   
                    self.success('Successfully got user info!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting user info: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting user info: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.stockcheck()

    def stockapi(self):
        self.warn('Getting product...')
        while True:
            try:               
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')   
                r = self.s.get(
                    f"https://www.emiliopucci.com/en-{self.country}/api/products/{self.sku}", 
                    timeout = self.timeout
                )
                print(r.text)
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code == 200:
                    if self.s.cookies.get('__cfwaitingroom'):
                        queueHandler(self.s.cookies.get('__cfwaitingroom'))
                    jsonprod2 = json.loads(r.text)
                    jsonprod = jsonprod2                 
                    try:
                        self.title = jsonprod['breadCrumbs'][4]['text']
                    except:
                        self.title = jsonprod['breadCrumbs'][3]['text']
                    self.success(f'Got {self.title}!')
                    try:
                        self.immagine = jsonprod['imageGroups'][0]['images'][0]['url']
                    except:
                        self.immagine = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg"
                    quantity = []
                    size_id = []
                    scale = []
                    merchantID = []
                    sizereal = []
                    sizegenerale = jsonprod['sizes']
                    for m in sizegenerale:
                        quantity.append(str(m['variants'][0]['quantity']))
                        size_id.append(str(m['sizeId']))
                        scale.append(str(m['scale']))
                        merchantID.append(str(m['variants'][0]['merchantId']))
                        sizereal.append(m['sizeDescription'])
                    self.element = zip(quantity, size_id, scale, merchantID, sizereal)
                    self.all_sizes = list(self.element)
                    self.instock = []
                    self.sizeinstock = []
                    for element in self.all_sizes:
                        if element[0] != "0":
                            self.instock.append(element)
                    for h in self.instock:
                        self.sizeinstock.append(h[4])
                    if self.size == "RANDOM":
                        if len(self.instock) >= 1:
                            self.success(f'Size available! {self.sizeinstock}')
                            break
                        else:
                            self.warn('Product OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                    else:
                        if len(self.instock) >= 1:
                            if self.size in self.instock[4]:
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
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting product: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting product: {e}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.atc()

    def stockcheck(self):
        self.warn('Getting product...')
        while True:
            try:               
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')   
                r = self.s.get(
                    f"https://www.emiliopucci.com/en-{self.country}/shopping/item-{self.sku}", 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code == 200:
                    
                    if self.s.cookies.get('__cfwaitingroom'):
                        queueHandler(self.s.cookies.get('__cfwaitingroom'))
                    json1 = r.text.split("__PRELOADED_STATE__ = ")[1].split("</script>")[0]
                    jsonprod2 = json.loads(json1)
                    jsonprod = jsonprod2['products']['details']['products']['result'][self.sku]                   
                    try:
                        self.title = jsonprod['name']
                    except:
                        self.title = 'Unkown title'
                    self.success(f'Got {self.title}!')
                    try:
                        self.immagine = jsonprod['resources']['primary']['sources']['1000'].replace('\\','/').replace('u002F','')
                    except:
                        self.immagine = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg"
                    quantity = []
                    size_id = []
                    scale = []
                    merchantID = []
                    sizereal = []
                    sizegenerale = jsonprod['sizes']
                    for m in sizegenerale:
                        quantity.append(str(m['stock'][0]['quantity']))
                        size_id.append(str(m['id']))
                        scale.append(str(m['scale']))
                        merchantID.append(str(m['stock'][0]['merchantId']))
                        sizereal.append(m['name'])
                    self.element = zip(quantity, size_id, scale, merchantID, sizereal)
                    self.all_sizes = list(self.element)
                    self.instock = []
                    self.sizeinstock = []
                    for element in self.all_sizes:
                        if element[0] != "0":
                            self.instock.append(element)
                    for h in self.instock:
                        self.sizeinstock.append(h[4])
                    if self.size == "RANDOM":
                        if len(self.instock) >= 1:
                            self.success(f'Size available! {self.sizeinstock}')
                            break
                        else:
                            self.warn('Product OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                    else:
                        if len(self.instock) >= 1:
                            if self.size in self.instock[4]:
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
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting product: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting product: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.atc()

    def atc(self):
        global carted, failed, checkoutnum
        if self.size == "RANDOM":
            self.scelto = random.choice(self.instock)
            self.chosenSize = self.scelto[1]
            self.merchant = self.scelto[3]
            self.scale = self.scelto[2]
            self.sizewebhook = self.scelto[4]
        else:
            for element in self.instock:
                if self.size in element[4]:
                    self.scelto = element
                    self.chosenSize = self.scelto[1]
                    self.merchant = self.scelto[3]
                    self.scale = self.scelto[2]
                    self.sizewebhook = self.scelto[4]
        self.warn(f'Adding size {self.sizewebhook} to cart...')
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB",
            'Accept-Encoding': 'gzip, deflate',
            'content-type': 'application/json',
            'ff-country': self.country,
            'ff-currency': self.currency,
            'referer': 'https://www.emiliopucci.com/',
            'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1'
        }
        self.s.headers.update(headers)
        try:
            del self.s.headers['cookie']
        except:
            pass
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                data = {"merchantId":self.merchant,"productId":self.sku,"quantity":"1","scale":self.scale,"size":self.chosenSize,"customAttributes":""}
                r = self.s.post(
                    f'https://www.emiliopucci.com/api/commerce/v1/bags/{self.bagid}/items', 
                    json = data, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code == 200:
                    self.success('Product added to cart!')   
                    carted = carted + 1
                    self.bar()
                    break
                if "This item already exists" in r.text:
                    self.warn('Item already in bag, proceding...')
                    break
                elif "No stock available for this item" in r.text or 'One or more of the items in your bag cannot be shipped' in r.text:
                    self.warn('Product is OOS, retrying...')
                    time.sleep(self.delay)
                    self.s.cookies.clear()
                    self.build_proxy()
                    if self.password != "":
                        self.login()
                    else:
                        self.bag()
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while adding to cart: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        if self.password != "":
            self.guest2()
        else:
            self.guest()

    def guest(self):
        self.warn('Submitting guest...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                payload = {"bagId": self.bagid,"guestUserEmail": self.mail}
                r = self.s.post(
                    "https://www.emiliopucci.com/api/checkout/v1/orders", 
                    json = payload, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code == 201:
                    data = json.loads(r.content)
                    self.ordernumber = data['id']
                    self.success('Successfully submitted guest!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting guest: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting guest: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        if self.country == 'IT':
            self.shipit()
        elif self.country == 'US':
            self.states()
        else:
            self.ship()

    def guest2(self):
        self.warn('Getting order id...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                payload = {"bagId": self.bagid}
                r = self.s.post(
                    "https://www.emiliopucci.com/api/checkout/v1/orders", 
                    json = payload, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code == 201:
                    data = json.loads(r.content)
                    self.ordernumber = data['id']
                    self.success('Successfully got order id!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting order id: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting order id: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        if self.payment == 'CC':
            self.paymentcc()
        else:
            self.paymentpp()

    def states(self):
        self.warn('Getting states info...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                r = self.s.get(
                    f'https://www.emiliopucci.com/en-{self.country}/api/states?countryId=216', 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    r_json = json.loads(r.text)
                    teid = []
                    tename = []
                    tecode = []
                    for i in r_json:
                        tecode.append(i['code'])
                        tename.append(i['name'])
                        teid.append(i['id'])
                    self.statezip = zip(tecode, tename, teid)
                    self.statelist = list(self.statezip)
                    for element in self.statelist:
                        if self.region in element[0]:
                            self.scelto = element
                            self.statecode = self.scelto[0]
                            self.statename = self.scelto[1]
                            self.stateid = self.scelto[2]
                    self.success('Successfully got user info!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting states info: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting states info: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.shipus()

    def shipus(self):
        self.country = "United States"
        self.countrynum = "216"
        self.alpha1 = "US"
        self.alpha2 = "USA"
        self.culture = "en-US"
        self.subfolder = "/en-US"
        self.continent = "5"
        self.warn('Submitting shipping...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                payload = {
                    "shippingAddress": {
                        "firstName": self.name,
                        "lastName": self.surname,
                        "phone": self.phone,
                        "country": {
                            "name": self.country,
                            "id": self.countrynum
                        },
                        "addressLine1": self.address,
                        "addressLine2": self.address2,
                        "addressLine3": "",
                        "city": {
                            "name": self.city
                        },
                        "state": {
                            "id": self.stateid,
                            "code": self.statecode,
                            "name": self.statename
                        },
                        "zipCode": self.zipcode
                    },
                    "billingAddress": {
                        "firstName": self.name,
                        "lastName": self.surname,
                        "phone": self.phone,
                        "country": {
                            "name": self.country,
                            "id": self.countrynum
                        },
                        "addressLine1": self.address,
                        "addressLine2": self.address2,
                        "addressLine3": "",
                        "city": {
                            "name": self.city
                        },
                        "state": {
                            "id": self.stateid,
                            "code": self.statecode,
                            "name": self.statename
                        },
                        "zipCode": self.zipcode
                    }
                }
                r = self.s.patch(f"https://www.emiliopucci.com/api/checkout/v1/orders/{self.ordernumber}", json = payload, timeout = self.timeout)
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    jsonship = json.loads(r.text)
                    t = jsonship['shippingOptions'][0]
                    self.priceship = t['formattedPrice']
                    self.price = t['price']
                    self.shippingcost = t['shippingCostType']
                    ao = t['shippingService']
                    self.descripion = ao['description']
                    self.id = ao['id']
                    self.nameship = ao['name']
                    self.type = ao['type']
                    self.min = ao['minEstimatedDeliveryHour']
                    self.max = ao['maxEstimatedDeliveryHour']
                    self.capped = t['shippingWithoutCapped']
                    self.base = t['baseFlatRate']
                    self.discount = t['discount']
                    self.ppid = "f56d6086-f08d-4c2e-b55b-63b2d32aa645"
                    if self.payment == "CC":
                        self.ccid = "e13bb06b-392b-49a0-8acd-3f44416e3234"
                    self.success('Successfully submitted shipping!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting shipping: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting shipping: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.Rates()

    def ship(self):
        self.warn('Submitting shipping...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                if self.country == 'FR':
                    self.country = "France"
                    self.countrynum = "70"
                    self.alpha1 = "FR"
                    self.alpha2 = "FRA"
                    self.culture = "fr-FR"
                    self.subfolder = "/fr-FR"
                    self.continent = "3"

                if self.country == 'NL':
                    self.country = "Netherlands"
                    self.countrynum = "144"
                    self.alpha1 = "NL"
                    self.alpha2 = "NLD"
                    self.culture = "nl-NL"
                    self.subfolder = "/nl-NL"
                    self.continent = "3"
                
                if self.country == 'PL':
                    self.country = "Poland"
                    self.countrynum = "164"
                    self.alpha1 = "PL"
                    self.alpha2 = "POL"
                    self.culture = "en-US"
                    self.subfolder = "/en-US"
                    self.continent = "3"

                if self.country == 'SI':
                    self.country = "Slovenia"
                    self.countrynum = "183"
                    self.alpha1 = "SI"
                    self.alpha2 = "SVN"
                    self.culture = "sl-SI"
                    self.subfolder = "/sl-SI"
                    self.continent = "3"

                if self.country == 'CH':
                    self.country = "Switzerland"
                    self.countrynum = "197"
                    self.alpha1 = "CH"
                    self.alpha2 = "CHE"
                    self.culture = "de-CH"
                    self.subfolder = "/de-CH"
                    self.continent = "3"

                if self.country == 'ES':
                    self.country = "Spain"
                    self.countrynum = "187"
                    self.alpha1 = "ES"
                    self.alpha2 = "ESP"
                    self.culture = "es-ES"
                    self.subfolder = "/es-ES"
                    self.continent = "3"

                if self.country == 'DE':
                    self.country = "Germany"
                    self.countrynum = "77"
                    self.alpha1 = "DE"
                    self.alpha2 = "DEU"
                    self.culture = "de-DE"
                    self.subfolder = "/de-DE"
                    self.continent = "3"

                if self.country == 'DK':
                    self.country = "Denmark"
                    self.countrynum = "54"
                    self.alpha1 = "DK"
                    self.alpha2 = "DNK"
                    self.culture = "da-DK"
                    self.subfolder = "/da-DK"
                    self.continent = "3"

                if self.country == 'GB':
                    self.country = "United Kingdom"
                    self.countrynum = "215"
                    self.alpha1 = "GB"
                    self.alpha2 = "GBR"
                    self.culture = "en-GB"
                    self.subfolder = "/en-GB"
                    self.continent = "3"

                if self.country == 'AT':
                    self.country = "Austria"
                    self.countrynum = "13"
                    self.alpha1 = "AT"
                    self.alpha2 = "AUT"
                    self.culture = "de-AT"
                    self.subfolder = "/de-AT"
                    self.continent = "3"

                if self.country == 'GR':
                    self.country = "Greece"
                    self.countrynum = "80"
                    self.alpha1 = "GR"
                    self.alpha2 = "GRC"
                    self.culture = "el-GR"
                    self.subfolder = "/el-GR"
                    self.continent = "3"

                if self.country == 'RU':
                    self.country = "Russian Federation"
                    self.countrynum = "170"
                    self.alpha1 = "RU"
                    self.alpha2 = "RUS"
                    self.culture = "ru-RU"
                    self.subfolder = "/ru-RU"
                    self.continent = "3"

                if self.country == 'FI':
                    self.country = "Finland"
                    self.countrynum = "69"
                    self.alpha1 = "FI"
                    self.alpha2 = "FIN"
                    self.culture = "fi-FI"
                    self.subfolder = "/fi-FI"
                    self.continent = "3"
                
                if self.country == 'SK':
                    self.country = "Slovakia"
                    self.countrynum = "182"
                    self.alpha1 = "SK"
                    self.alpha2 = "SVK"
                    self.culture = "sk-SK"
                    self.subfolder = "/sk-SK"
                    self.continent = "3"

                if self.country == 'CZ':
                    self.country = "Czech Republic"
                    self.countrynum = "53"
                    self.alpha1 = "CZ"
                    self.alpha2 = "CZE"
                    self.culture = "cs-CZ"
                    self.subfolder = "/cs-CZ"
                    self.continent = "3"

                payload ={
                    "shippingAddress": {
                        "firstName": self.name,
                        "lastName": self.surname,
                        "phone": self.phone,
                        "country": {
                            "name": self.country,
                            "id": self.countrynum
                        },
                        "addressLine1": f"{self.address}, {self.housenumber}",
                        "addressLine2": self.address2,
                        "addressLine3": "",
                        "city": {
                            "name": self.city
                        },
                        "state": {
                            "name": self.region
                        },
                        "zipCode": self.zipcode
                    },
                    "billingAddress": {
                        "firstName": self.name,
                        "lastName": self.surname,
                        "phone": self.phone,
                        "country": {
                            "name": self.country,
                            "id": self.countrynum
                        },
                        "addressLine1": f"{self.address}, {self.housenumber}",
                        "addressLine2": self.address2,
                        "addressLine3": "",
                        "city": {
                            "name": self.city
                        },
                        "state": {
                            "name": self.region
                        },
                        "zipCode": self.zipcode
                    }
                }
                r = self.s.patch(
                    f"https://www.emiliopucci.com/api/checkout/v1/orders/{self.ordernumber}", 
                    json = payload, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    jsonship = json.loads(r.text)
                    t = jsonship['shippingOptions'][0]
                    self.priceship = t['formattedPrice']
                    self.price = t['price']
                    self.shippingcost = t['shippingCostType']
                    ao = t['shippingService']
                    self.descripion = ao['description']
                    self.id = ao['id']
                    self.nameship = ao['name']
                    self.type = ao['type']
                    self.min = ao['minEstimatedDeliveryHour']
                    self.max = ao['maxEstimatedDeliveryHour']
                    self.capped = t['shippingWithoutCapped']
                    self.base = t['baseFlatRate']
                    self.discount = t['discount']
                    self.ppid = "f56d6086-f08d-4c2e-b55b-63b2d32aa645"
                    if self.payment == "CC":
                        self.ccid = "e13bb06b-392b-49a0-8acd-3f44416e3234"
                    self.success('Successfully submitted shipping!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting shipping: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting shipping: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.Rates()

    def shipit(self):
        self.warn('Submitting shipping...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                self.country = "Italy"
                self.countrynum = "101"
                self.alpha1 = "IT"
                self.alpha2 = "ITA"
                self.culture = "it-IT"
                self.subfolder = "/it-IT"
                self.continent = "3"
                payload ={
                    "shippingAddress": {
                        "firstName": self.name,
                        "lastName": self.surname,
                        "phone": self.phone,
                        "country": {
                            "name": self.country,
                            "id": self.countrynum
                        },
                        "addressLine1": f"{self.address}, {self.housenumber}",
                        "addressLine2": self.address2,
                        "addressLine3": "",
                        "city": {
                            "name": self.city
                        },
                        "state": {
                            "name": self.region
                        },
                        "zipCode": self.zipcode
                    },
                    "billingAddress": {
                        "firstName": self.name,
                        "lastName": self.surname,
                        "phone": self.phone,
                        "country": {
                            "name": self.country,
                            "id": self.countrynum
                        },
                        "addressLine1": f"{self.address}, {self.housenumber}",
                        "addressLine2": self.address2,
                        "addressLine3": "",
                        "city": {
                            "name": self.city
                        },
                        "state": {
                            "name": self.region
                        },
                        "zipCode": self.zipcode
                    }
                }
                r = self.s.patch(
                    f"https://www.emiliopucci.com/api/checkout/v1/orders/{self.ordernumber}", 
                    json = payload, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    jsonship = json.loads(r.text)
                    t = jsonship['shippingOptions'][0]
                    self.priceship = t['formattedPrice']
                    self.price = t['price']
                    self.shippingcost = t['shippingCostType']
                    ao = t['shippingService']
                    self.descripion = ao['description']
                    self.id = ao['id']
                    self.nameship = ao['name']
                    self.type = ao['type']
                    self.min = ao['minEstimatedDeliveryHour']
                    self.max = ao['maxEstimatedDeliveryHour']
                    self.capped = t['shippingWithoutCapped']
                    self.base = t['baseFlatRate']
                    self.discount = t['discount']
                    self.ppid = "f56d6086-f08d-4c2e-b55b-63b2d32aa645"
                    if self.payment == "CC":
                        self.ccid = "e13bb06b-392b-49a0-8acd-3f44416e3234"
                    self.success('Successfully submitted shipping!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting shipping: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting shipping: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.Rates()

    def Rates(self):
        self.warn('Submitting shipping rates...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                payload = {
                    "shippingOption": {
                        "discount": int(self.discount),
                        "merchants": [self.merchant],
                        "price": int(self.price),
                        "formattedPrice": self.priceship,
                        "shippingCostType": self.shippingcost,
                        "shippingService": {
                            "description": self.descripion,
                            "id": self.id,
                            "name": self.nameship,
                            "type": self.type,
                            "minEstimatedDeliveryHour": int(self.min),
                            "maxEstimatedDeliveryHour": int(self.max),
                            "trackingCodes": []
                        },
                        "shippingWithoutCapped": int(self.capped),
                        "baseFlatRate": int(self.base)
                    }
                }
                r = self.s.patch(f"https://www.emiliopucci.com/api/checkout/v1/orders/{self.ordernumber}", json = payload, timeout = self.timeout)
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    self.success('Successfully submitted shipping rates!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting shipping rates: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting shipping rates: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        if self.country == 'United States':
            self.billingus()
        else:
            self.billingpost()

    def billingus(self):
        self.warn('Submitting billing...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/') 
                payload ={
                    "billingAddress": {
                        "city": {
                            "countryId": self.countrynum,
                            "id": 0,
                            "name": self.city
                        },
                        "country": {
                            "alpha2Code": self.alpha1,
                            "alpha3Code": self.alpha2,
                            "culture": self.culture,
                            "id": self.countrynum,
                            "name": "United States",
                            "nativeName": "United States",
                            "region": "The United States & Canada",
                            "regionId": 0,
                            "subfolder": self.subfolder,
                            "continentId": self.continent
                        },
                        "lastName": self.surname,
                        "state": {
                            "countryId": self.countrynum,
                            "id": self.stateid,
                            "code": self.statecode,
                            "name": self.statename
                        },
                        "userId": 0,
                        "isDefaultBillingAddress": False,
                        "isDefaultShippingAddress": False,
                        "addressLine1": self.address,
                        "addressLine2": self.address2,
                        "firstName": self.name,
                        "phone": self.phone,
                        "zipCode": self.zipcode
                    }
                }

                r = self.s.patch(
                    f"https://www.emiliopucci.com/api/checkout/v1/orders/{self.ordernumber}", 
                    json = payload, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    self.success('Successfully submitted billing!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting billing: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting billing: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        if self.payment == "PP":
            self.paymentpp()
        else:
            self.paymentcc()

    def billingpost(self):
        self.warn('Submitting billing...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/') 
                payload ={
                    "billingAddress": {
                        "city": {
                            "countryId": self.countrynum,
                            "id": 0,
                            "name": self.city
                        },
                        "country": {
                            "alpha2Code": self.alpha1,
                            "alpha3Code": self.alpha2,
                            "culture": self.culture,
                            "id": self.countrynum,
                            "name": self.country,
                            "nativeName": self.country,
                            "region": "Europe",
                            "regionId": 0,
                            "subfolder": self.subfolder,
                            "continentId": self.continent
                        },
                        "lastName": self.surname,
                        "state": {
                            "countryId": 0,
                            "id": 0,
                            "code": self.region,
                            "name": self.region
                        },
                        "userId": 0,
                        "isDefaultBillingAddress": False,
                        "isDefaultShippingAddress": False,
                        "addressLine1": f"{self.address}, {self.housenumber}",
                        "addressLine2": f"{self.address}, {self.housenumber}",
                        "firstName": self.name,
                        "phone": self.phone,
                        "zipCode": self.zipcode
                    }
                }
                r = self.s.patch(
                    f"https://www.emiliopucci.com/api/checkout/v1/orders/{self.ordernumber}", 
                    json = payload, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    self.success('Successfully submitted billing!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting billing: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting billing: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        if self.payment == "PP":
            self.paymentpp()
        else:
            self.paymentcc()

    def paymentpp(self):
        global carted, failed, checkoutnum
        self.warn('Submitting paypal order...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                payload = {"paymentMethodId": "f56d6086-f08d-4c2e-b55b-63b2d32aa645","paymentMethodType": "CustomerAccount"}
                r = self.s.post(
                    f"https://www.emiliopucci.com/api/checkout/v1/orders/{self.ordernumber}/finalize", 
                    json = payload, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    jsoncheckout = json.loads(r.text)
                    self.ppurl = jsoncheckout['confirmationRedirectUrl']
                    self.success('Successfully checked out!')
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting paypal order: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting paypal order: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.passcookies()

    def paymentcc(self):
        global carted, failed, checkoutnum
        self.warn('Submitting credit card order...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])  
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='www.emiliopucci.com', path='/')  
                payload = {
                    "cardNumber": self.cardnumber,
                    "cardExpiryMonth": self.expmonth,
                    "cardExpiryYear": self.expyear,
                    "cardName": self.cardowner,
                    "cardCvv": self.cvv,
                    "paymentMethodType": "CreditCard",
                    "paymentMethodId": self.ccid,
                    "savePaymentMethodAsToken": True
                }
                r = self.s.post(
                    f"https://www.emiliopucci.com/api/checkout/v1/orders/{self.ordernumber}/finalize", 
                    json = payload, 
                    timeout = self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200,201):
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    self.success('Successfully checked out!')
                    isdeclined = False
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    if 'Back Soon' in r.text:
                        self.error('Back soon page up, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                    else:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 400:
                    self.error('Payment failed, restarting...')
                    isdeclined = True
                    failed = failed + 1
                    self.bar()
                    break
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting paypal order: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting paypal order: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        if isdeclined:
            self.s.cookies.clear()
            self.declined()
        else:
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
            path = os.path.dirname(__file__).rsplit('/', 1)[0]
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
                    writer.writerow({'SITE':'EMILIOPUCCI','SIZE':f'{self.sizewebhook}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'EMILIOPUCCI','SIZE':f'{self.sizewebhook}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            self.SuccessPP()
            
        except Exception as e: 
            open(self.logs_path, 'a+').write(f'{e}\n')
            error(f'[TASK {self.threadID}] [OFF--WHITE] [{self.sku}] - Error while passing cookies, retrying...') 
            sys.exit(1)
            return None

    def SuccessPP(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**EMILIO PUCCI**', value = self.title, inline = False)
            embed.add_embed_field(name=f'**PRODUCT**', value = self.sku, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.sizewebhook, inline = True)
            embed.add_embed_field(name='**ORDER**', value = f'||{self.ordernumber}||', inline = True)
            embed.add_embed_field(name='**EMAIL**', value = f'||{self.mail}||', inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.immagine)  
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.pubblic()
        except:
            pass

    def pubblic(self):
        try:
            webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**EMILIO PUCCI**', value = self.title, inline = False)
            embed.add_embed_field(name=f'**PRODUCT**', value = self.sku, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.sizewebhook, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.immagine)  
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
                warn("")
            except:
                warn("")
        except:
            pass

    def declined(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Card declined, please review payment info!', color = 15746887)
            embed.add_embed_field(name=f'**EMILIO PUCCI**', value = self.title, inline = False)
            embed.add_embed_field(name=f'**PRODUCT**', value = self.sku, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.sizewebhook, inline = True)
            embed.add_embed_field(name='**ORDER**', value = f'||{self.ordernumber}||', inline = True)
            embed.add_embed_field(name='**EMAIL**', value = f'||{self.mail}||', inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.set_thumbnail(url = self.immagine)  
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.declinedpubblic()
        except:
            pass

    def declinedpubblic(self):
        try:
            webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Checkout failed!', color = 15746887)
            embed.add_embed_field(name=f'**EMILIO PUCCI**', value = self.title, inline = False)
            embed.add_embed_field(name=f'**PRODUCT**', value = self.sku, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.sizewebhook, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.immagine)  
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.stockcheck()
        except:
            pass