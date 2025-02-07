import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
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

UNIQUE_ID = int(time.time() * 1000) * 2**random.randint(10,16)
AUTO_SOLVE = None
CAPTCHA_TOKENS = []
CAPTCHA = None

checkoutnum = 0
failed = 0
carted = 0


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

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

QUEUE_DATA = {
    'passed': False,
    'cookie': None,
    'time': 0
}

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
    except Exception as e:
        error(e)

class AMBUSH():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'ambush/exceptions.log')
        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'ambush/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "ambush/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()

        except:
            error("FAILED TO READ PROXIES, STARTIGN LOCAL HOST")
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
        self.payment = row['PAYMENT']
        self.name = row['FIRST NAME']
        self.surname = row['LAST NAME']
        self.mail = row['EMAIL']
        self.address = row['ADDRESS LINE 1']
        self.address2 = row['ADDRESS 2']
        self.zip = row['ZIP']
        self.phone = row['PHONE NUMBER']  
        self.city = row['CITY']
        self.country = row['COUNTRY']
        self.region = row['STATE']
        self.cardnumber = row['CARD NUMBER']
        self.expmonth = row['EXP MONTH']
        self.expyear = row['EXP YEAR']
        self.cvc = row['CVC']
        self.cardholder = row['CARDHOLDER']
        self.dropmode = row['DROPMODE']
        self.discord = DISCORD_ID

        if self.link == 'VOLT':
            self.link = '17158556'

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

        try:
            if len(self.expyear) == 2:
                self.expyear = "20{}".format(self.expyear)
        except:
            pass

        self.webhook_url = webhook
        self.version = version
        self.threadID = '%03d' % i
        self.balance = balancefunc()
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        self.delay = int(config['delay'])
        self.timeout = 120
        self.build_proxy()
        self.bar()
            
        if self.payment == "PP/CC":
            self.error('PLEASE CHECK CSV PAYMENT MODE (PP OR CC)')
            sys.exit(1)

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

        self.warn('Task started!')
        if self.dropmode == 'DROPS':
            self.cardnumber = f'{self.cardnumber[:4]} {self.cardnumber[4:8]} {self.cardnumber[8:12]} {self.cardnumber[12:16]}'
            self.dropsprod()
        else:
            self.xpid()

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [AMBUSH] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [AMBUSH] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [AMBUSH] - {text}'
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
                f'Phoenix AIO {self.version} - Running AMBUSH | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running AMBUSH | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

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
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
            else:
                return response

    def dropsprod(self):
        self.warn('Getting product page...')
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = \
                        [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies
                         if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='drops.ambushdesign.com', path='/')
                r = self.s.get(
                    f'https://drops.ambushdesign.com/products/{self.link}?subfolder=en-it',
                    timeout=self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    self.s.cookies.set('__cfwaitingroom','Chh5UTRaL1B5SXpHalhPVU8wcjQzeXlnPT0ShAJNSjM2TW9NS292S1FHRFhpQUNlcUNlak0xbDlTMUJNUXd1TndpcDlyY3lGMENIMHlEMnUvL0ZiTlV6cFRNV3RUQ3E5NUd0L1pDMDVQbk5sVTJCQ0Y4OTFlMzQyQWZMcjR3cHRleStyYTMzd1JHaEhJYXA2ZjJJL1BwdGhNRmRMck9UaHlEV1V1RWNlWTAxWjYxbGVqTTVPVm1PVVB6UU1QMDMreFdsVDh4NmpPOXAxZHFWYUtSNFBsWUE1Wm8yUGdTTm1nS1NWNGZHTWljSlp4QkEvak16aGdLenRMbllBMXdmWjZQaWo5TkRJTkUvd2VFZDVuZGlkTVIyai9hR0RDamc9PQ%3D%3D',domain='drops.ambushdesign.com', path='/')
                    continue
                if r.status_code == 200:
                    js = r.text.split('__FLAREACT_DATA" type="application/json">')[1].split('</script><script')[0]
                    r_json = json.loads(js)
                    jsonprod = r_json['props']['productDetails']
                    if r_json['props']['comingSoon'] == True:
                        self.warn('Product not live yet, retrying...')
                        time.sleep(self.delay)
                        continue
                    if r_json['props']['outOfStock'] == True:
                        self.warn('Product out of stock, retrying...')
                        time.sleep(self.delay)
                        continue
                    try:
                        self.title = jsonprod['breadCrumbs'][4]['text'].replace('â¢', '')
                    except:
                        self.title = jsonprod['breadCrumbs'][3]['text'].replace('â¢', '')
                    self.success(f'Succesfully got {self.title}!')
                    try:
                        self.immagine = jsonprod['images'][0]['1000'].replace('\\', '/').replace('u002F', '')
                    except:
                        self.immagine = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg"
                    quantity = []
                    size_id = []
                    scale = []
                    merchantID = []
                    sizereal = []
                    sizegenerale = jsonprod['sizes']
                    for m in sizegenerale:
                        quantity.append(str(m['quantity']))
                        size_id.append(str(m['id']))
                        scale.append(str(m['scale']))
                        merchantID.append(str(m['merchantId']))
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
                    self.error(f'Error while getting product page (drops.): {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting product page (drops.): {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'get prod (drops.): {e}\n')
                time.sleep(self.delay)
                continue
        self.dropsatc()

    def dropsatc(self):
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
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = \
                        [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies
                         if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='drops.ambushdesign.com', path='/')
                r = self.s.get(
                    f'https://drops.ambushdesign.com/_flareact/props/checkout/{self.link}.json?size={self.chosenSize}&subfolder=en-it',
                    timeout=self.timeout
                )
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    self.discount = \
                    r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping']['discount']
                    self.merchant = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption'][
                        'merchantId']
                    self.price = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'price']
                    self.shippingcost = \
                    r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'shippingCostType']
                    self.descripion = \
                    r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'shippingService']['description']
                    self.idd = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'shippingService']['id']
                    self.nameee = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'shippingService']['name']
                    self.type = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'shippingService']['type']
                    self.min = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'shippingService']['minEstimatedDeliveryHour']
                    self.max = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'shippingService']['maxEstimatedDeliveryHour']
                    self.capped = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'shippingWithoutCapped']
                    self.base = r_json['pageProps']['orderDetails']['checkout']['selectedShippingOption']['shipping'][
                        'baseFlatRate']
                    self.success('Succesfully added to cart!')
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
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                time.sleep(self.delay)
                continue
        self.checkoutdrops()

    def solve_v2(self, url):
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.hcaptcha(sitekey='b6e1ef43-16a1-4162-b182-582b6e5d50c0', url=url)
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
                        "type": "HCaptchaTaskProxyless",
                        "websiteURL": url,
                        "websiteKey": "b6e1ef43-16a1-4162-b182-582b6e5d50c0"
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
                    "siteKey" : "b6e1ef43-16a1-4162-b182-582b6e5d50c0",
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

    def checkoutdrops(self):
        global checkoutnum, failed
        self.warn('Submitting order...')
        if self.country == 'FR':
            self.countryName = "France"
            self.countrynum = "70"
            self.alpha1 = "FR"
            self.alpha2 = "FRA"
            self.culture = "fr-FR"
            self.subfolder = "/fr-FR"
            self.continent = "3"
        if self.country == 'NL':
            self.countryName = "Netherlands"
            self.countrynum = "144"
            self.alpha1 = "NL"
            self.alpha2 = "NLD"
            self.culture = "nl-NL"
            self.subfolder = "/nl-NL"
            self.continent = "3"
        if self.country == 'PL':
            self.countryName = "Poland"
            self.countrynum = "164"
            self.alpha1 = "PL"
            self.alpha2 = "POL"
            self.culture = "en-US"
            self.subfolder = "/en-US"
            self.continent = "3"
        if self.country == 'SI':
            self.countryName = "Slovenia"
            self.countrynum = "183"
            self.alpha1 = "SI"
            self.alpha2 = "SVN"
            self.culture = "sl-SI"
            self.subfolder = "/sl-SI"
            self.continent = "3"
        if self.country == 'CH':
            self.countryName = "Switzerland"
            self.countrynum = "197"
            self.alpha1 = "CH"
            self.alpha2 = "CHE"
            self.culture = "de-CH"
            self.subfolder = "/de-CH"
            self.continent = "3"
        if self.country == 'ES':
            self.countryName = "Spain"
            self.countrynum = "187"
            self.alpha1 = "ES"
            self.alpha2 = "ESP"
            self.culture = "es-ES"
            self.subfolder = "/es-ES"
            self.continent = "3"
        if self.country == 'DE':
            self.countryName = "Germany"
            self.countrynum = "77"
            self.alpha1 = "DE"
            self.alpha2 = "DEU"
            self.culture = "de-DE"
            self.subfolder = "/de-DE"
            self.continent = "3"
        if self.country == 'DK':
            self.countryName = "Denmark"
            self.countrynum = "54"
            self.alpha1 = "DK"
            self.alpha2 = "DNK"
            self.culture = "da-DK"
            self.subfolder = "/da-DK"
            self.continent = "3"
        if self.country == 'GB':
            self.countryName = "United Kingdom"
            self.countrynum = "215"
            self.alpha1 = "GB"
            self.alpha2 = "GBR"
            self.culture = "en-GB"
            self.subfolder = "/en-GB"
            self.continent = "3"
        if self.country == 'AT':
            self.countryName = "Austria"
            self.countrynum = "13"
            self.alpha1 = "AT"
            self.alpha2 = "AUT"
            self.culture = "de-AT"
            self.subfolder = "/de-AT"
            self.continent = "3"
        if self.country == 'GR':
            self.countryName = "Greece"
            self.countrynum = "80"
            self.alpha1 = "GR"
            self.alpha2 = "GRC"
            self.culture = "el-GR"
            self.subfolder = "/el-GR"
            self.continent = "3"
        if self.country == 'RU':
            self.countryName = "Russian Federation"
            self.countrynum = "170"
            self.alpha1 = "RU"
            self.alpha2 = "RUS"
            self.culture = "ru-RU"
            self.subfolder = "/ru-RU"
            self.continent = "3"
        if self.country == 'FI':
            self.countryName = "Finland"
            self.countrynum = "69"
            self.alpha1 = "FI"
            self.alpha2 = "FIN"
            self.culture = "fi-FI"
            self.subfolder = "/fi-FI"
            self.continent = "3"
        if self.country == 'SK':
            self.countryName = "Slovakia"
            self.countrynum = "182"
            self.alpha1 = "SK"
            self.alpha2 = "SVK"
            self.culture = "sk-SK"
            self.subfolder = "/sk-SK"
            self.continent = "3"
        if self.country == 'CZ':
            self.countryName = "Czech Republic"
            self.countrynum = "53"
            self.alpha1 = "CZ"
            self.alpha2 = "CZE"
            self.culture = "cs-CZ"
            self.subfolder = "/cs-CZ"
            self.continent = "3"
        if self.country == 'US':
            self.countryName = "United States"
            self.countrynum = "216"
            self.alpha1 = "US"
            self.alpha2 = "USA"
            self.culture = "en-US"
            self.subfolder = "/en-US"
            self.continent = "5"
        if self.country == 'IT':
            self.countryName = "Italy"
            self.countrynum = "101"
            self.alpha1 = "IT"
            self.alpha2 = "ITA"
            self.culture = "it-IT"
            self.subfolder = "/it-IT"
            self.continent = "3"
        self.cardtype = self.cardnumber.replace(' ', '')
        cardtype = identify_card_type(self.cardtype)
        self.restart = False
        isdeclined = False
        if cardtype == "MasterCard":
            card_type = "MC"
        elif cardtype == "Visa":
            card_type = "VISA"
        payload = {"sizeId": self.chosenSize, "productId": self.link,
                   "cancelUrl": f"https://drops.ambushdesign.com/checkout/{self.link}?size={self.chosenSize}&subfolder=en-it",
                   "returnUrl": "https://drops.ambushdesign.com/checkoutdetails/:id?subfolder=en-it&id=:guestUserId",
                   "billingAddress": {"firstName": self.name, "lastName": self.surname,
                                      "country": {"id": self.countrynum, "name": self.country},
                                      "addressLine1": self.address, "addressLine2": self.address2, "addressLine3": "",
                                      "city": {"name": self.city}, "state": {"name": ""}, "zipCode": self.zip,
                                      "phone": self.phone, "vatNumber": ""},
                   "shippingAddress": {"firstName": self.name, "lastName": self.surname,
                                       "country": {"id": self.countrynum, "name": self.country},
                                       "addressLine1": self.address, "addressLine2": self.address2, "addressLine3": "",
                                       "city": {"name": self.city}, "state": {"name": ""}, "zipCode": self.zip,
                                       "phone": self.phone, "vatNumber": ""}, "email": self.mail,
                   "paymentMethod": {"option": card_type,
                                     "creditCard": {"cardCvv": self.cvc, "cardExpiryMonth": self.expmonth,
                                                    "cardHolderName": self.cardholder, "cardNumber": self.cardnumber,
                                                    "cardExpiryYear": self.expyear}},
                   "shippingOption": {"discount": int(self.discount), "merchants": [self.merchant],
                                      "price": int(self.price), "shippingCostType": self.shippingcost,
                                      "shippingService": {"description": self.descripion, "id": self.idd,
                                                          "name": self.nameee, "type": self.type,
                                                          "minEstimatedDeliveryHour": int(self.min),
                                                          "maxEstimatedDeliveryHour": int(self.max),
                                                          "trackingCodes": []},
                                      "shippingWithoutCapped": int(self.capped), "baseFlatRate": int(self.base)}}
        self.warn('Solving captcha...')
        code = self.solve_v2('https://drops.ambushdesign.com/api/checkout')
        headers = {
            'Accept': 'application/json',
            'h-captcha-response': code,
            'Referer': f'https://drops.ambushdesign.com/checkout/{self.link}?size={self.chosenSize}&subfolder=en-it'
        }
        while True:
            try:
                qData = queueHandler(None)
                if qData:
                    if self.s.cookies.get('__cfwaitingroom'):
                        cookie = \
                        [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path} for c in self.s.cookies
                         if c.name == '__cfwaitingroom'][0]
                        self.s.cookies.set('__cfwaitingroom', qData, domain=cookie['domain'], path=cookie['path'])
                    else:
                        self.s.cookies.set('__cfwaitingroom', qData, domain='drops.ambushdesign.com', path='/')
                r = self.s.post(
                    'https://drops.ambushdesign.com/api/checkout',
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                open(f'ambush checkout {int(time.time() * 1000)}.html', 'w+', encoding='utf-8').write(r.text)
                if 'estimated wait time' in r.text:
                    if qData:
                        queueHandler(False)
                    self.warn('Waiting in queue...')
                    time.sleep(10)
                    continue
                if r.status_code in (200, 201):
                    r_json = json.loads(r.text)
                    if r_json['status'] == 'Error':
                        self.declinecode = r_json['chargeInstruments'][0]['declineCode']
                        isdeclined = True
                        failed = failed + 1
                        self.bar()
                        self.error('Payment declined!')
                        break
                    else:
                        self.declinecode = r_json['chargeInstruments'][0]['operationStatus']
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        self.success('Successfully checked out!')
                        isdeclined = False
                        self.ppurl = r.url
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
                    self.error(f'Error while submitting order: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.restart = True
                break
            except Exception as e:
                self.error(f'Exception while submitting order: {e.__class__.__name__}, restarting...')
                open(self.logs_path, 'a+').write(f'{e}\n')
                self.build_proxy()
                self.restart = True
                break
        if self.restart:
            self.s.cookies.clear()
            self.dropsprod()
        if isdeclined:
            self.daclimn()
        else:
            self.passcookies2()

    def passcookies2(self):
        try:
            cookieStr = ""
            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in
                       self.s.cookies]
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
                    cookie['url'] = "https://" + cookie['url']
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
                with open(path, 'a', newline='') as f:
                    fieldnames = ["SITE", "SIZE", "PAYLINK", "PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow(
                        {'SITE': 'DROPS.AMBUSH', 'SIZE': f'{self.sizewebhook}', 'PAYLINK': f'{self.token}',
                         'PRODUCT': f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path, 'a', newline='') as f:
                    fieldnames = ["SITE", "SIZE", "PAYLINK", "PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow(
                        {'SITE': 'DROPS.AMBUSH', 'SIZE': f'{self.sizewebhook}', 'PAYLINK': f'{self.token}',
                         'PRODUCT': f'{self.title}'})
            self.SuccessCC()

        except Exception as e:
            open(self.logs_path, 'a+').write(f'{e}\n')
            self.error(f'Error while passing cookies: {e}, retrying...')
            sys.exit(1)
            return None

    def SuccessCC(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content="")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url=self.expToken,
                                 color=0x715aff)
            embed.add_embed_field(name=f'**AMBUSH**', value=self.title, inline=False)
            embed.add_embed_field(name=f'**PRODUCT**', value=self.link, inline=False)
            embed.add_embed_field(name='**SIZE**', value=self.sizewebhook, inline=True)
            embed.add_embed_field(name='**EMAIL**', value=f'||{self.mail}||', inline=False)
            embed.add_embed_field(name='PAYMENT METHOD', value=self.payment, inline=True)
            embed.add_embed_field(name='**PROXY**', value=f"||{self.px}||", inline=False)
            embed.add_embed_field(name='Status', value=self.declinecode, inline=True)
            embed.add_embed_field(name='Checkout Mobile', value=f"[LINK]({self.expToken2})", inline=False)
            embed.set_thumbnail(url=self.immagine)
            embed.set_footer(text=f"Phoenix AIO v{self.version}",
                             icon_url="https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.pubbli2c()
        except:
            pass

    def pubbli2c(self):
        try:
            webhook = DiscordWebhook(url=random.choice(self.listsuccess), content="")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color=40703)
            embed.add_embed_field(name=f'**AMBUSH**', value=self.title, inline=False)
            embed.add_embed_field(name=f'**PRODUCT**', value=self.link, inline=False)
            embed.add_embed_field(name='**SIZE**', value=self.sizewebhook, inline=True)
            embed.add_embed_field(name='PAYMENT METHOD', value=self.payment, inline=False)
            embed.add_embed_field(name='Delay', value=self.delay, inline=True)
            embed.add_embed_field(name='USER', value=f"<@{self.discord}>", inline=False)
            embed.set_thumbnail(url=self.immagine)
            embed.set_footer(text=f"Phoenix AIO v{self.version}",
                             icon_url="https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
                warn("")
            except:
                warn("")
        except:
            pass

    def daclimn(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content="")
            embed = DiscordEmbed(title='Phoenix AIO - Card declined, please review payment info!', color=15746887)
            embed.add_embed_field(name=f'**AMBUSH**', value=self.title, inline=False)
            embed.add_embed_field(name=f'**PRODUCT**', value=self.link, inline=False)
            embed.add_embed_field(name='**SIZE**', value=self.sizewebhook, inline=True)
            embed.add_embed_field(name='**EMAIL**', value=f'||{self.mail}||', inline=True)
            embed.add_embed_field(name='PAYMENT METHOD', value=self.payment, inline=True)
            embed.add_embed_field(name='Decline Code', value=self.declinecode, inline=True)
            embed.add_embed_field(name='**PROXY**', value=f"||{self.px}||", inline=False)
            embed.set_thumbnail(url=self.immagine)
            embed.set_footer(text=f"Phoenix AIO v{self.version}",
                             icon_url="https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            sys.exit(1)
        except:
            pass

    def xpid(self):
        self.warn('Getting cookies')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
        }
        self.s.headers.update(headers)
        while True:
            try:
                r = self.s.get(
                    'https://www.ambushdesign.com/en-it/api/users/me',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    self.bag = r_json['bagId']
                    self.success('Succesfully got cookies!')
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
                    self.error(f'Error while getting cookies: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while getting cookies: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    continue
        self.getproduct()

    def getproduct(self):
        self.warn('Getting product page...')
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1'
        }
        self.s.headers.update(headers)
        self.stop = False
        while True:
            try:
                r = self.s.get(
                    f'https://www.ambushdesign.com/en-it/shopping/phoenix-{self.link}',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    rex = r.text.split('PRELOADED_STATE__ = ')[1].split('<')[0]
                    r_json = json.loads(rex)
                    siz = r_json['entities']['products'][f'{self.link}']['sizes']
                    if not siz:
                        self.warn('Product oos, monitoring...')
                        time.sleep(self.delay)
                        continue
                    else:
                        try:
                            self.img = r_json['entities']['products'][f'{self.link}']['images'][0]['url']
                        except:
                            self.img = 'https://www.dvrcapital.it/wp-content/uploads/2020/05/ambush_logo-1.jpg'
                        self.title = r_json['entities']['products'][f'{self.link}']['shortDescription']
                        self.pid = r_json['entities']['products'][f'{self.link}']['id']
                        self.price = r_json['entities']['products'][f'{self.link}']['price']['includingTaxesWithoutDiscount']
                        self.success('Succesfully got product page!')
                        saizprint = []
                        sizeid = []
                        scale = []
                        merchan = []
                        quant = []
                        for i in siz:
                            saizprint.append(i['name'])
                            sizeid.append(str(i['id']))
                            scale.append(str(i['scale']))
                            merchan.append(str(i['stock'][0]['merchantId']))
                            quant.append(str(i['stock'][0]['quantity']))
                        tot = zip(saizprint, sizeid, scale, merchan, quant)
                        connect = list(tot)
                        if self.size == "RANDOM":
                            scelta = random.choice(connect)
                            s0 = scelta[0]
                            s1 = scelta[1]
                            s2 = scelta[2]
                            s3 = scelta[3]
                            s4 = scelta[4]
                            self.saizprint = "".join(s0)
                            self.sizeid = "".join(s1)
                            self.scale = "".join(s2)
                            self.merchant = "".join(s3)
                            self.quant = "".join(s4)
                            self.success(f'Succesfully got size {self.saizprint}, qty: {self.quant}')
                            break
                        else:
                            self.error('Only RANDOM is accepted in ambush.csv')
                            self.stop = True
                            break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while getting product page: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while getting product page: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
        if self.stop:
            sys.exit()
        self.atc()
    
    def atc(self):
        global carted, failed, checkoutnum
        self.warn(f'Adding to cart...')
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'FF-Country': self.country,
            'FF-Currency': self.currency,
            'Referer': 'https://www.ambushdesign.com/'
        }
        self.s.headers.update(headers)
        payload = {"merchantId":self.merchant,"productId":self.link,"quantity":'1',"scale":self.scale,"size":self.sizeid,"customAttributes":""}
        while True:
            try:
                r = self.s.post(
                    f'https://www.ambushdesign.com/api/commerce/v1/bags/{self.bag}/items', 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    if r_json['bagSummary']['subTotalAmount'] != 0:
                        self.bagid = r_json['id']
                        self.success('Succesfully added to cart!')
                        carted = carted + 1
                        self.bar()
                        break
                    else:
                        self.error('Failed adding to cart, restarting...')
                        self.restart = True
                        break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    open(self.logs_path, 'a+').write(f'ATC 400: {r.text}\n')
                    self.warn('Error 400 adding to cart...')
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
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
        self.guest()

    def guest(self):
        self.warn('Submitting guest...')
        headers = {
            'X-NewRelic-ID': 'VQUCV1ZUGwIFVlBRDgcA',
            'Accept-Language':'en-US'
        }
        self.s.headers.update(headers)
        payload = {"bagId":self.bagid,"guestUserEmail":self.mail,"usePaymentIntent":True}
        while True:
            try:
                r = self.s.post(
                    'https://www.ambushdesign.com/api/checkout/v1/orders', 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200 or 201:
                    r_json = json.loads(r.text)
                    self.orderid = r_json['id']
                    self.success('Succesfully submitted guest!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while submitting guest: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
        if self.country == 'US':
            self.states()
        else:
            self.ship1()

    def states(self):
        self.warn('Getting state info...')
        headers = {
            'Accept-Language': 'en-US'
        }
        self.s.headers.update(headers)
        while True:
            try:
                r = self.s.get(
                    f'https://www.ambushdesign.com/en-{self.country}/api/states?countryId=216',
                    timeout = self.timeout
                )
                if r.status_code == 200 or 201:
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
                    self.success('Successfully got states info!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while getting states: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while getting states: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
        self.shipus()

    def shipus(self):
        self.warn('Submitting ship...')
        self.country = "United States"
        self.countrynum = "216"
        self.alpha1 = "US"
        self.alpha2 = "USA"
        self.culture = "en-US"
        self.subfolder = "/en-US"
        self.continent = "5"
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
                    "zipCode": self.zip
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
                    "zipCode": self.zip
                }
            }
        while True:
            try:
                r = self.s.patch(
                    f'https://www.ambushdesign.com/api/checkout/v1/orders/{self.orderid}', 
                    json = payload,
                    timeout = self.timeout)
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    self.price = str(r_json['shippingOptions'][0]['price'])
                    self.formattedprice = r_json['shippingOptions'][0]['formattedPrice']
                    self.shippingCostType = str(r_json['shippingOptions'][0]['shippingCostType'])
                    self.description = r_json['shippingOptions'][0]['shippingService']['description']
                    self.idship = str(r_json['shippingOptions'][0]['shippingService']['id'])
                    self.nameship = r_json['shippingOptions'][0]['shippingService']['name']
                    self.typeship = r_json['shippingOptions'][0]['shippingService']['type']
                    self.minEstimatedDeliveryHour = str(r_json['shippingOptions'][0]['shippingService']['minEstimatedDeliveryHour'])
                    self.maxEstimatedDeliveryHour = str(r_json['shippingOptions'][0]['shippingService']['maxEstimatedDeliveryHour'])
                    self.success('Succesfully submitted ship...')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while submitting ship: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while submitting ship: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
        self.ship2()

    def ship1(self):
        self.warn('Submitting ship...')
        if self.country == 'FR':
            self.country = "France"
            self.countrynum = "70"
            self.alpha1 = "FR"
            self.alpha2 = "FRA"
            self.culture = "fr-FR"
            self.subfolder = "/fr-FR"
            self.continent = "3"

        if self.country == 'IT':
            self.country = "Italy"
            self.countrynum = "101"
            self.alpha1 = "IT"
            self.alpha2 = "ITA"
            self.culture = "it-IT"
            self.subfolder = "/it-IT"
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

        if self.country == 'PT':
            self.country = "Portugal"
            self.countrynum = "165"
            self.alpha1 = "PT"
            self.alpha2 = "PRT"
            self.culture = "pt-PT"
            self.subfolder = "/pt-PT"
            self.continent = "3"

        payload = {"shippingAddress":{"firstName":self.name,"lastName":self.surname,"country":{"name":self.country,"id":self.countrynum},"addressLine1":self.address,"addressLine2":self.address2,"addressLine3":"","city":{"name":self.city},"state":{"name":self.region},"zipCode":self.zip,"phone":self.phone,"vatNumber":""},"billingAddress":{"firstName":self.name,"lastName":self.surname,"country":{"name":self.country,"id":self.countrynum},"addressLine1":self.address,"addressLine2":self.address2,"addressLine3":"","city":{"name":self.city},"state":{"name":self.region},"zipCode":self.zip,"phone":self.phone,"vatNumber":""}}
        while True:
            try:
                r = self.s.patch(
                    f'https://www.ambushdesign.com/api/checkout/v1/orders/{self.orderid}', 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    self.price = str(r_json['shippingOptions'][0]['price'])
                    self.formattedprice = r_json['shippingOptions'][0]['formattedPrice']
                    self.shippingCostType = str(r_json['shippingOptions'][0]['shippingCostType'])
                    self.description = r_json['shippingOptions'][0]['shippingService']['description']
                    self.idship = str(r_json['shippingOptions'][0]['shippingService']['id'])
                    self.nameship = r_json['shippingOptions'][0]['shippingService']['name']
                    self.typeship = r_json['shippingOptions'][0]['shippingService']['type']
                    self.minEstimatedDeliveryHour = str(r_json['shippingOptions'][0]['shippingService']['minEstimatedDeliveryHour'])
                    self.maxEstimatedDeliveryHour = str(r_json['shippingOptions'][0]['shippingService']['maxEstimatedDeliveryHour'])
                    self.success('Succesfully submitted ship...')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while submitting ship: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.build_proxy()
                    self.error(f'Exception while submitting ship: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    continue
        self.ship2()

    def ship2(self):
        self.warn('Getting shipping rates...')
        payload = {"shippingOption":{"discount":"0","merchants":[self.merchant],"price":self.price,"formattedPrice":self.formattedprice,"shippingCostType":self.shippingCostType,"shippingService":{"description":self.description,"id":self.idship,"name":self.nameship,"type":self.typeship,"minEstimatedDeliveryHour":self.minEstimatedDeliveryHour,"maxEstimatedDeliveryHour":self.maxEstimatedDeliveryHour,"trackingCodes":[]},"shippingWithoutCapped":"0","baseFlatRate":"0"}}
        while True:
            try:
                r = self.s.patch(
                    f'https://www.ambushdesign.com/api/checkout/v1/orders/{self.orderid}', 
                    json = payload,
                    timeout = self.timeout)
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    self.idd = r_json['checkoutOrder']['billingAddress']['id']
                    self.pricce = str(r_json['checkoutOrder']['grandTotal']).split('.')[0]
                    self.idcoo = self.s.cookies ['ctx'].split('a')[1].split('%')[0]
                    self.paymentinten = r_json['checkoutOrder']['paymentIntentId']
                    self.success('Succesfully got shipping rates...')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while getting shipping rates: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while getting shipping rates: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
        if self.payment == 'PP':
            self.pp()
        elif self.payment == 'CC':
            self.cc()

    def pp(self):
        self.warn('Submitting payment...')
        if self.countrynum == '216':
            payload = {"method":"PayPal","option":"PayPalExp","createToken":False,"payer":{"id":self.idcoo,"firstName":self.name,"lastName":self.surname,"email":self.mail,"birthDate":'null',"address":{"city":{"countryId":self.countrynum,"id":0,"name":self.city},"country":{"alpha2Code":self.alpha1,"alpha3Code":self.alpha2,"culture":self.culture,"id":self.countrynum,"name":self.country,"nativeName":self.country,"region":"The United States & Canada","regionId":"0","continentId":self.continent},"id":self.idd,"lastName":self.surname,"state":{"countryId":self.countrynum,"id":self.stateid,"code":self.statecode,"name":self.statename},"userId":"0","isDefaultBillingAddress":False,"isDefaultShippingAddress":False,"addressLine1":self.address,"addressLine2":self.address2,"firstName":self.name,"phone":self.phone,"zipCode":self.zip}},"amounts":[{"value":self.pricce}],"data":{}}
        else:
            payload = {"method":"PayPal","option":"PayPalExp","createToken":False,"payer":{"id":self.idcoo,"firstName":self.name,"lastName":self.surname,"email":self.mail,"birthDate":'null',"address":{"city":{"countryId":self.countrynum,"id":0,"name":self.city},"country":{"alpha2Code":self.alpha1,"alpha3Code":self.alpha2,"culture":self.culture,"id":self.countrynum,"name":self.country,"nativeName":self.country,"region":"Europe","regionId":0,"continentId":self.continent},"id":self.idd,"lastName":self.surname,"state":{"countryId":"0","id":"0","code":"","name":""},"userId":"0","isDefaultBillingAddress":False,"isDefaultShippingAddress":False,"addressLine1":self.address,"addressLine2":self.address2,"firstName":self.name,"phone":self.phone,"vatNumber":"","zipCode":self.zip}},"amounts":[{"value":self.pricce}],"data":{}}
        while True:
            try:
                r = self.s.post(
                    f'https://www.ambushdesign.com/api/payment/v1/intents/{self.paymentinten}/instruments', 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200 or 201:
                    self.success('Succesfully got payment info!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while submitting payment: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while submitting payment: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
        self.pp2()


    def pp2(self):
        self.warn('Placing order...')
        payload = {"cancelUrl":"https://www.ambushdesign.com/en-it/commerce/checkout","returnUrl":f"https://www.ambushdesign.com/en-it/checkoutdetails?orderid={self.orderid}"}
        while True:
            try:
                r = self.s.post(
                    f'https://www.ambushdesign.com/api/checkout/v1/orders/{self.orderid}/charges', 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200 or 201:
                    r_json = json.loads(r.text)
                    self.redirect_url = r_json['redirectUrl']
                    self.success('Succesfully got paypal info!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while placing order: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Exception while placing order: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
        self.pp3()

    def pp3(self):
        global carted, failed, checkoutnum
        self.warn('Opening paypal...')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        }
        self.s.headers.update(headers)
        while True:
            try:
                r = self.s.get(
                    self.redirect_url,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 302:
                    self.ppurl = r.headers['location']
                    self.success('Succesfully checked out!')
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while opening paypal: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.build_proxy()
                    self.error(f'Exception while opening paypal: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    continue
        self.passpp()

    def passpp(self):
        try:
            cookieStr = ""
            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
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
                    writer.writerow({'SITE':'AMBUSH','SIZE':f'{self.saizprint}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'AMBUSH','SIZE':f'{self.saizprint}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            self.webh1()
        except Exception as e: 
            error(f'Exception sending webhook: {e.__class__.__name__}, retrying...') 
            self.webh1()


    def webh1(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Cooked!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**AMBUSH**', value = f'{self.title}', inline = True)
        embed.add_embed_field(name='**Size**', value = f'{self.saizprint}', inline = True)
        embed.add_embed_field(name='Payment method', value = self.payment, inline = False)
        embed.add_embed_field(name='**Email**', value = f'||{self.mail}||', inline = True)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url = self.img) 
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook()


    def Pubblic_Webhook(self):
        webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Success', color = 40703)
        embed.add_embed_field(name=f'**AMBUSH**', value = f'{self.title}', inline = True)
        embed.add_embed_field(name='**Size**', value = f'{self.saizprint}', inline = True)
        embed.add_embed_field(name='Payment method', value = self.payment, inline = False)
        embed.add_embed_field(name='**PID**', value = self.link, inline = True)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_thumbnail(url = self.img)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()



    def cc(self):
        self.warn('Submitting payment...')
        cardtype = identify_card_type(self.cardnumber)
        if cardtype == "MasterCard":
            card_type = "MC"
        elif cardtype == "Visa":
            card_type = "VISA"
        payload = {"method":"CreditCard","option":card_type,"createToken":False,"payer":{"id":self.idcoo,"firstName":self.name,"lastName":self.surname,"email":self.mail,"birthDate":"null","address":{"city":{"countryId":self.countrynum,"id":0,"name":self.city},"country":{"alpha2Code":self.alpha1,"alpha3Code":self.alpha2,"culture":self.culture,"id":self.countrynum,"name":self.country,"nativeName":self.country,"region":"Europe","regionId":0,"continentId":self.continent},"id":self.idd,"lastName":self.surname,"state":{"countryId":0,"id":0,"code":"","name":""},"userId":0,"isDefaultBillingAddress":False,"isDefaultShippingAddress":False,"addressLine1":self.address,"addressLine2":self.address2,"firstName":self.name,"phone":self.phone,"vatNumber":"","zipCode":self.zip}},"amounts":[{"value":self.pricce}],"data":{"cardHolderName":self.cardholder,"cardNumber":self.cardnumber,"cardExpiryMonth":self.expmonth,"cardExpiryYear":self.expyear,"cardCvv":self.cvc}}
        while True:
            try:
                r = self.s.post(
                    f'https://www.ambushdesign.com/api/payment/v1/intents/{self.paymentinten}/instruments', 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200 or 201:
                    self.success('Succesfully got payment info!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
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
                    self.error(f'Error while submitting payment: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.build_proxy()
                    self.error(f'Exception while submitting payment: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    continue
        self.cc2()


    def cc2(self):
        global failed, checkoutnum, carted
        self.failed = False
        self.warn('Placing order...')
        payload = {"cancelUrl":f"https://www.ambushdesign.com/en-it/commerce/checkout","returnUrl":f"https://www.ambushdesign.com/en-it/checkoutdetails?orderid={self.orderid}"}
        while True:
            try:
                r = self.s.post(f'https://www.ambushdesign.com/api/checkout/v1/orders/{self.orderid}/charges', json = payload)
                if r.status_code == 200 or 201:
                    r_json = json.loads(r.text)
                    if r_json['status'] == 'Completed':
                        self.success('Succesfully checked out!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        break
                    else:
                        failed = failed + 1
                        self.bar()
                        self.error('Payment declined, check your cc info!')
                        self.failed = True
                        break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, monitoring...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 400:
                    open(self.logs_path, 'a+').write(f'CC 400: {r.text}\n')
                    self.warn('Error 400 placing credit card...')
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
                    self.error(f'Error while placing order: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if e.__class__.__name__ == 'ChunkedEncodingError':
                    self.error('Connection error, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.build_proxy()
                    self.error(f'Exception while placing order: {e.__class__.__name__}, retrying...')
                    open(self.logs_path, 'a+').write(f'{e}\n')
                    time.sleep(self.delay)
                    continue
        if self.failed:
            self.webhookfailed()
        self.webhookcc()

    def webhookcc(self):
        if self.selected_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Cooked!', color = 0x715aff)
        embed.add_embed_field(name=f'**AMBUSH**', value = f'{self.title}', inline = True)
        embed.add_embed_field(name='**Size**', value = f'{self.saizprint}', inline = True)
        embed.add_embed_field(name='Payment method', value = self.payment, inline = False)
        embed.add_embed_field(name='**Email**', value = f'||{self.mail}||', inline = False)
        embed.add_embed_field(name='Order ID', value = self.orderid, inline = True)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.set_thumbnail(url = self.img) 
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook2()

    def Pubblic_Webhook2(self):
        webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Success', color = 40703)
        embed.add_embed_field(name=f'**AMBUSH**', value = f'{self.title}', inline = True)
        embed.add_embed_field(name='**Size**', value = f'{self.saizprint}', inline = True)
        embed.add_embed_field(name='Payment method', value = self.payment, inline = False)
        embed.add_embed_field(name='**PID**', value = self.link, inline = True)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_thumbnail(url = self.img)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()

    def webhookfailed(self):
        if self.selected_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Payment Declined', color = 15746887)
        embed.add_embed_field(name='**AMBUSH**', value = f'{self.title}', inline = True)
        embed.add_embed_field(name='**SIZE**', value = f'{self.saizprint}', inline = True)
        embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.set_thumbnail(url = self.img)   
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        sys.exit(1)