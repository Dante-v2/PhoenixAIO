import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
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

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

class EINHALB():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), '43einhalb/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "43einhalb/proxies.txt")
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
            time.sleep(5)
            sys.exit(1)

        self.s = cloudscraper.create_scraper(
            browser= {
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
            },
            captcha=self.captcha,
            doubleDown=False,
            requestPostHook=self.injection
        )

        self.link = row['LINK'] 
        self.size = row['SIZE']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.mail = row['MAIL']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.postcode = row['ZIPCODE']
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.city = row['CITY']
        self.housenumber = row['HOUSENUMBER']

        self.password = "" #password della pagina prodotto
        self.username = "" #username per accedere a pagina prodotto

        self.webhook_url = webhook
        self.version = version
        self.threadID = '%03d' % i
        self.delay = int(config['delay'])
        self.discord = DISCORD_ID

        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        #self.fullpassword = f"{self.username}:{self.password}"
        #self.encoded = (base64.b64encode(self.fullpassword.encode('utf-8'))).decode()
        self.fullpassword = ''
        self.encoded = '' #sempre per la password

        self.host = 'https://www.43einhalb.com/'
        self.atc_url = 'https://www.43einhalb.com/warenkorb/hinzufuegen'
        self.address_url = 'https://www.43einhalb.com/en/cart/guest'
        self.payment_url = 'https://www.43einhalb.com/en/cart/paymentmethod'
        self.check_url = 'https://www.43einhalb.com/en/cart/last-check'

        self.timeout = 120
        self.build_proxy()
        self.balance = balancefunc()
        self.bar()


        if self.country == "DE":
            countryno = 1
        elif self.country == "UK":
            countryno = 43
        elif self.country == "NL":
            countryno = 47
        elif self.country == "BG":
            countryno = 53
        elif self.country == "HR":
            countryno = 34
        elif self.country == "DK":
            countryno = 39
        elif self.country == "EE":
            countryno = 28
        elif self.country == "BE":
            countryno = 38
        elif self.country == "AT":
            countryno = 45
        elif self.country == "FI":
            countryno = 40
        elif self.country == "FR":
            countryno = 51
        elif self.country == "GR":
            countryno = 44
        elif self.country == "HU":
            countryno = 34
        elif self.country == "IE":
            countryno = 41
        elif self.country == "IL":
            countryno = 59
        elif self.country == "IT":
            countryno = 50
        elif self.country == "HK":
            countryno = 61
        elif self.country == "LV":
            countryno = 24
        elif self.country == "LI":
            countryno = 5
        elif self.country == "LT":
            countryno = 23
        elif self.country == "LU":
            countryno = 37
        elif self.country == "SE":
            countryno = 42
        elif self.country == "ES":
            countryno = 49
        elif self.country == "CH":
            countryno = 57
        elif self.country == "PL":
            countryno = 48
        elif self.country == "SI":
            countryno = 26
        elif self.country == "UA":
            countryno = 11
        elif self.country == "NO":
            countryno = 27
        elif self.country == "CZ":
            countryno = 32
        elif self.country == "PT":
            countryno = 46
        elif self.country == "SK":
            countryno = 30
        elif self.country == "RO":
            countryno = 25
        elif self.country == "GB":
            self.country = "UK"
            countryno = 43
        else:
            self.error('COUNTRY NOT SUPPORTED, PLEASE REPORT')
            sys.exit()

        self.country = countryno

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

        if self.username == "":
            self.headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding': 'gzip, deflate'
            }
            self.s.headers.update(self.headers)
        else:
            self.headers = {
                'authorization': f'Basic {self.encoded}',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
            }
            self.s.headers.update(self.headers)

        self.warn('Task started!') 
        self.connection()

    # Red logging

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [43EINHALB] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [43EINHALB] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [43EINHALB] - {text}'
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
                f'Phoenix AIO {self.version} - Running 43EINHALB | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running 43EINHALB | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')


    def injection(self, session, response):
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
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
        #    else:
        #        return response

    def connection(self):
        self.warn('Connecting to 43einhalb...')
        while True:
            try:
                proxyGet = self.s.get(
                    self.host, 
                    timeout = self.timeout
                )
                if proxyGet.status_code == 200:
                    self.success('Connected to 43einhalb')
                    break
                elif proxyGet.status_code in (403, 429):
                    self.build_proxy()
                    self.error('Proxy banned, retrying...')
                    continue
                else:
                    warn(f'Error connecting: {proxyGet.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.warn(f'Something went wrong connecting to 43einhalb: {e}, retrying...') 
                self.s.cookies.clear()
                self.build_proxy()
                continue
        self.productscrape()

    def productscrape(self):
        while True:
            try:
                prod = self.s.get(
                    self.link, 
                    timeout=self.timeout
                )
                if prod.status_code == 200:
                    sizeRow = self.size
                    oneSize = False
                    isRandom = False
                    if sizeRow.upper() == 'RANDOM':
                        isRandom = True
                    elif sizeRow == '' or sizeRow == 'OS':
                        oneSize = True
                    elif ',' in sizeRow:
                        sizeRange = sizeRow.replace(" ", '').split(',')
                    else:
                        size1 = sizeRow.replace(" ", '')
                        sizeRange = []
                        sizeRange.append(size1)
                        sizeRange.append(size1)
                    if oneSize == False and isRandom == False:
                        sizeRange = [float(i) for i in sizeRange]
                    try:
                        prod_xml = bs(prod.text, "lxml")
                        try:
                            self.prod_name = prod_xml.find('div', {'class':'productTitle'}).find("span", {"class": "productName"}).text
                        except:
                            self.prod_name = "Product"
                        if oneSize == False:
                            self.valuesList = []
                            sizeList = []
                            rangedSizes = []
                            sizes = ''
                            divList2 = prod_xml.find('div', attrs={'class': 'selectVariants clear'})
                            for option in divList2:
                                divList = divList2.findAll('option', {'class': ''})
                            divList.pop(0)
                            for div in divList:
                                sizes = div.text.strip()
                                sizes = re.sub(r'.*-.\w+', '', sizes, flags=re.I)
                                sizes = sizes.replace(',', '.').strip()
                                if 'US' in sizes:
                                    sizes = sizes.split('EUR ')[1].split(' US')[0]
                                    sizes = sizes[2:]
                                if 'UK' in sizes:
                                    sizes = sizes.split('EUR ')[1].split(' UK')[0]
                                    sizes = sizes[2:]
                                if 'Y' in sizes:
                                    sizes = sizes.replace('Y', '')
                                sizes = float(sizes)
                                sizeList.append(sizes)
                                if isRandom == True:
                                    rangedSizes.append(sizes)
                                    values = div.get('value')
                                    self.valuesList.append(values)
                                elif sizeRange[0] <= sizes <= sizeRange[1]:
                                    rangedSizes.append(sizes)
                                    values = div.get('value')
                                    self.valuesList.append(values)
                            if self.valuesList == []:
                                if isRandom == True:
                                    self.warn(f'{self.prod_name} out of stock, retrying...')
                                    time.sleep(self.delay)
                                    continue
                                else:
                                    self.warn(f'{self.prod_name} {sizeRange} out of stock, retrying...')
                                    time.sleep(self.delay)
                                    continue
                            else:
                                self.success(f'{self.prod_name} in stock!')
                                self.secret()
                                break
                        else:
                            pid = prod_xml.find('input', {'name': 'product_id'})['value']
                            bsId = prod_xml.find('input', {'name': 'product_bs_id'})['value']
                            self.bsid = bsId
                            self.pid = pid
                            break
                    except Exception as e:
                        self.error(f'Failed parsing: {e}, retrying...')
                        continue
                elif 'contentPageContent' in prod.text:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif prod.status_code in (502, 522):
                    self.warn('Site is overcrowded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif prod.status_code == 500:
                    self.warn('Internal error, retrying...')
                    time.sleep(self.delay)
                    continue
                elif prod.status_code in [403, 429]:
                    self.warn('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif prod.status_code == 401:
                    self.warn('Auth required, change to drop mode!')
                    sys.exit()
                    break
                else:
                    self.warn(f'Error getting product page: {prod.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product: {e}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.atc()

    def secret(self):
        self.sizeValue = random.choice(self.valuesList)
        product_data = {
            'chosen_attribute_value': self.sizeValue,
            'returnHtmlSnippets[partials][0][module]': 'product',
            'returnHtmlSnippets[partials][0][path]': '_productDetail',
            'returnHtmlSnippets[partials][0][partialName]': 'buybox',
            'returnHtmlSnippets[partials][0][params][template]': 'default'
        }
        while True:
            try:                  
                prodPost = self.s.post(
                    self.link, 
                    data=product_data,
                    timeout=self.timeout
                )
                if prodPost.status_code == 200:
                    r_json = json.loads(prodPost.text)
                    self.bsid = r_json['initializedProduct']['bsId']
                    self.pid = prodPost.text.split('product_id\\" type=\\"hidden\\" value=\\"')[1].split('\\"')[0]
                    self.sec = prodPost.text.split('secret\\" type=\\"hidden\\" value=\\"')[1].split('\\"')[0]
                    break
                elif prodPost.status_code in (502, 522):
                    self.warn('Site is overcrowded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif prodPost.status_code == 500:
                    self.warn('Internal error, retrying...')
                    time.sleep(self.delay)
                    continue
                elif prodPost.status_code in [403, 429]:
                    self.warn('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.warn(f'Error getting secret: {prodPost.status_code}, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting secret: {e}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        return self.success("Pid and Bsid taken!")      
   
    def atc(self):
        global carted, failed, checkoutnum
        decodedString = base64.b64decode(self.sec).decode('utf-8')
        decoded = json.loads(decodedString)
        codice = decoded['action']
        while True:
            try:
                atc = f'https://www.43einhalb.com{codice}'
                atc_data = {
                    'secret':self.sec,
                    'product_bs_id': self.bsid,
                    'product_id': self.pid,
                    'amount': '1',
                    'ajax':	'true',
                    'forward[module]': 'cart',
                    'forward[action]': 'wasadded',
                    'addToCart': '',
                    'returnHtmlSnippets[partials][0][module]':'cart',
                    'returnHtmlSnippets[partials][0][partialName]':'headerCart',
                    'returnHtmlSnippets[partials][0][returnName]':'headerCartDesktop',
                    'returnHtmlSnippets[partials][0][params][template]':'default',
                    'returnHtmlSnippets[partials][1][module]':'cart',
                    'returnHtmlSnippets[partials][1][partialName]':'headerCart',
                    'returnHtmlSnippets[partials][1][returnName]':'headerCartMobile',
                    'returnHtmlSnippets[partials][1][params][template]':'mobile',
                    'returnHtmlSnippets[partials][2][module]':'cart',
                    'returnHtmlSnippets[partials][2][partialName]':'cartPreview',
                    'returnHtmlSnippets[partials][2][returnName]':'cartPreview',
                    'returnHtmlSnippets[partials][3][module]':'product',
                    'returnHtmlSnippets[partials][3][path]':'_productDetail',
                    'returnHtmlSnippets[partials][3][partialName]':'buybox',
                    'returnHtmlSnippets[partials][3][params][template]':'default',
                    'returnHtmlSnippets[partials][3][params][bsId]':self.bsid,
                    'returnHtmlSnippets[partials][4][module]':'cart',
                    'returnHtmlSnippets[partials][4][partialName]':'modalWasadded'
                }
                referer = self.link
                if "/nl/" in atc:
                    if "/nl/" in referer:
                        pass
                    elif "/fr/" in referer:
                        referer = referer.replace("/fr/", "/nl/")
                    elif "/es/" in referer:
                        referer = referer.replace("/es/", "/nl/")
                    elif "/en/" in referer:
                        referer = referer.replace("/en/", "/nl/")
                    else:
                        referer = referer.replace(".com/", ".com/nl/")
                elif "/fr/" in atc:
                    if "/nl/" in referer:
                        referer = referer.replace("/nl/", "/fr/")
                    elif "/fr/" in referer:
                        pass
                    elif "/es/" in referer:
                        referer = referer.replace("/es/", "/fr/")
                    elif "/en/" in referer:
                        referer = referer.replace("/en/", "/fr/")
                    else:
                        referer = referer.replace(".com/", ".com/fr/")
                elif "/es/" in atc:
                    if "/nl/" in referer:
                        referer = referer.replace("/nl/", "/es/")
                    elif "/fr/" in referer:
                        referer = referer.replace("/fr/", "/es/")
                    elif "/es/" in referer:
                        pass
                    elif "/en/" in referer:
                        referer = referer.replace("/en/", "/es/")
                    else:
                        referer = referer.replace(".com/", ".com/es/")
                elif "/en/" in atc:
                    if "/nl/" in referer:
                        referer = referer.replace("/nl/", "/en/")
                    elif "/fr/" in referer:
                        referer = referer.replace("/fr/", "/en/")
                    elif "/es/" in referer:
                        referer = referer.replace("/es/", "/en/")
                    elif "/en/" in referer:
                        pass
                    else:
                        referer = referer.replace(".com/", ".com/en/")
                else:
                    if "/nl/" in referer:
                        referer = referer.replace("/nl/", "")
                    elif "/fr/" in referer:
                        referer = referer.replace("/fr/", "")
                    elif "/es/" in referer:
                        referer = referer.replace("/es/", "")
                    elif "/en/" in referer:
                        referer = referer.replace("/en/", "")
                    else:
                        pass
                atc_headers = {
                    'accept': '*/*',
                    'X-Requested-With':'XMLHttpRequest',
                }
                self.s.headers.update(atc_headers)
                self.warn("Adding to cart...")
                cartPost = self.s.post(
                    atc, 
                    data = atc_data, 
                    timeout=self.timeout, 
                    allow_redirects = False
                )
                if '1x' in cartPost.text:
                    break
                elif cartPost.status_code in (503, 522):
                    self.warn("Site is overcrowded, retrying...")
                    time.sleep(self.delay)
                    continue
                elif cartPost.status_code in (403, 1020, 429):
                    self.error("Atc blocked, retrying...")
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif cartPost.status_code == 200:
                    warn(f"{self.prod_name} OOS, retrying...")
                    time.sleep(self.delay)
                    self.productscrape()
                    break
                elif cartPost.status_code == 500:
                    self.warn("Internal error, retrying..")
                    time.sleep(self.delay)
                    continue
                else:
                    self.warn(f"Error [{cartPost.status_code}] during ATC, retrying...")
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.build_proxy()
                error(f"Exception while adding to cart: {e.__class__.__name__}, retrying...")
                continue
        try:
            self.cartSize = cartPost.text.split('class=\\"attributes\\"> ')[1].split(' EUR')[0]
        except Exception as e:
            self.cartSize = '1x'
        self.success("Succesfully added to cart!")
        carted = carted + 1
        self.bar()
        self.getAddress()

    def getAddress(self):
        self.warn("Submitting address...")
        address_data = {
            'billAddressId': '-1',
            'guestdata[email]': self.mail,
            'billaddress[company]': '',
            'billaddress[vatid]': '',
            'billaddress[salutation]': '1',
            'billaddress[forename]': self.name,
            'billaddress[lastname]': self.surname,
            'billaddress[street]': self.address,
            'billaddress[street_number]': self.housenumber,
            'billaddress[addition]': self.address2,
            'billaddress[zipcode]': self.postcode,
            'billaddress[city]': self.city,
            'billaddress[country]': self.country,
            'billaddress[phone]': self.phone,
            'guestdata[date_of_birth]' : '',
            'shippingaddress[use_shipping_address]': '0',
            'shippingAddressId': '-1',
            'shippingaddress[company]': '',
            'shippingaddress[salutation]': '1',
            'shippingaddress[forename]': self.name,
            'shippingaddress[lastname]': self.surname,
            'shippingaddress[street]': self.address,
            'shippingaddress[street_number]': self.housenumber,
            'shippingaddress[addition]': self.address,
            'shippingaddress[zipcode]': self.postcode,
            'shippingaddress[city]': self.city,
            'shippingaddress[country]': self.country,
            'back_x_value': '@cart',
            'next_x': 'Continue to payment',
            'next_x_value': '@cart_payment'
        }
        while True:
            try:
                addressPost = self.s.post(
                    self.address_url, 
                    data = address_data, 
                    timeout = self.timeout
                )
                if 'paymentmethod' in addressPost.url:
                    break
                elif addressPost.url.split('/')[-1] == 'cart':
                    self.error(f"Failed submitting shipping, retrying...")
                    time.sleep(self.delay)
                    continue
                if addressPost.status_code == 200:
                    self.s.cookies.clear()
                    self.error("Cart is oos, restarting...")
                    self.build_proxy()
                    self.connection()
                    break
                elif addressPost.status_code in (403, 429):
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif addressPost.status_code in (503, 522):
                    self.warn("Site is overcrowded, retrying...")
                    time.sleep(self.delay)
                    continue
                elif addressPost.status_code == 500:
                    self.warn("Internal error, retrying...")
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f"Error submitting address: {addressPost.status_code}, retrying...")
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.build_proxy()
                error(f"Error submitting address: {e.__class__.__name__}, retrying...")
                continue
        self.success("Successfully submitted address!")
        self.payment_xml = bs(addressPost.text, features='lxml')
        self.payment()

    def payment(self):
        global carted, failed, checkoutnum
        self.warn("Submitting payment...")
        shipping_method = self.payment_xml.find('input', {'name': 'shipping_method_id'})['value']
        payment_data = {
            'payment_method_id': '9',
            'shipping_method_id': shipping_method,
            'back_x_value': '@cart_address',
            'next_x': 'Continue to summary',
            'next_x_value': '@cart_check'
        }
        while True:
            try:
                paymentPost = self.s.post(
                    self.payment_url, 
                    data = payment_data, 
                    timeout = self.timeout, 
                    allow_redirects = False
                )
                if 'last-check' in paymentPost.headers['Location']:
                    break
                elif paymentPost.status_code in (503, 522):
                    self.warn("Site is overcrowded, retrying...")
                    time.sleep(self.delay)
                    continue
                elif paymentPost.status_code == 500:
                    self.warn("Internal error, retrying...")
                    time.sleep(self.delay)
                    continue
                elif paymentPost.status_code in [403, 429]:
                    self.error("Proxy banned, rotating...")
                    self.build_proxy()
                    continue
                elif 'paymentmethod' in paymentPost.url:
                    self.error("Payment failed, retrying...")
                    failed = failed + 1
                    self.bar()
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    self.error(f"Payment failed: {paymentPost.status_code}, retrying...")
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.build_proxy()
                self.error(f"Exception while submitting payment: {e.__class__.__name__}, retrying...")
                continue
        self.success("Successfully submitted payment!")
        self.check()

    def check(self):
        global carted, failed, checkoutnum
        self.warn("Getting paypal link...")
        while True:
            try:
                check_data = {
                    'next_x': '',
                    'next_x_value': '@order_finished',
                    'chk_privacy': 'guest_order_privacy_consent',
                    'chk_uwg': 'emarsys_cart_check_uwg',
                    'next_x': 'Order now (with costs)',
                    'next_x': '',
                    'next_x_value': '@order_finished'
                }
                self.checkPost = self.s.post(
                    self.check_url, 
                    data = check_data, 
                    timeout = self.timeout, 
                    allow_redirects = False
                )
                if 'paypal' in self.checkPost.headers['Location']:
                    break
                elif self.checkPost.status_code in (503, 522):
                    self.warn("Site is overcrowded, retrying...")
                    time.sleep(self.delay)
                    continue
                elif self.checkPost.status_code in [403, 429]:
                    self.error(f"Proxy banned, retrying...")
                    self.build_proxy()
                    continue
                elif self.checkPost.status_code == 302:
                    self.error("Failed submitting order product went oos, restarting")
                    failed = failed + 1
                    self.bar()
                    time.sleep(self.delay)
                    self.s.cookies.clear()
                    self.connection()
                    break
                else:
                    self.error(f"Failed submitting order [{self.checkPost.status_code}], retrying...")
                    failed = failed + 1
                    self.bar()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception submitting order: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        checkoutnum = checkoutnum + 1
        self.bar()
        self.zcookies = self.s.cookies
        self.success("Successfully checked out!")
        self.pass_cookies()
        
    def pass_cookies(self):
        try:
            cookieStr = ""
            self.zcookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
            try:
                for element in self.zcookies:
                    if 'cf_chl' in element['name']:
                        self.zcookies.remove(element)
            except:
                pass
            try:
                for cookie in self.zcookies:
                    if cookie['domain'][0] == ".":
                        cookie['url'] = cookie['domain'][1:]
                    else:
                        cookie['url'] = cookie['domain']
                    cookie['url'] = "https://"+cookie['url']
            except:
                pass
            cookies = json.dumps(self.zcookies)
            cookieStr = urllib.parse.quote(base64.b64encode(bytes(cookies, 'utf-8')).decode())
            if not cookieStr: return
            url = urllib.parse.quote(base64.b64encode(bytes(self.checkPost.headers['Location'], 'utf-8')).decode())
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
                    writer.writerow({'SITE':'43EINHALB','SIZE':f'{self.cartSize}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prod_name}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'43EINHALB','SIZE':f'{self.cartSize}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prod_name}'})
            self.webhook1()
        except Exception as e:
            self.error(f"Error while passing cookies: {e}, retrying...")
            self.pass_cookies()       

    def webhook1(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**43EINHALB**', value = self.prod_name, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.cartSize, inline = True)
        embed.add_embed_field(name='**PID**', value = self.pid, inline = True)
        embed.add_embed_field(name='**BSID**', value = self.bsid, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = "Paypal", inline = True) 
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook()

    def Pubblic_Webhook(self):
        webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'**43EINHALB**', value = self.prod_name, inline = False)
        embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = True)       
        embed.add_embed_field(name='**PID**', value = self.pid, inline = True)
        embed.add_embed_field(name='**BSID**', value = self.bsid, inline = True)
        embed.add_embed_field(name='**SIZE**', value = self.cartSize, inline = False)
        embed.add_embed_field(name='PAYMENT METHOD', value = "Paypal", inline = True)
        embed.add_embed_field(name='Delay', value = self.delay, inline = False)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = True)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        try:
            playsound('checkout.wav')
            sys.exit(1)
        except:
            sys.exit(1)