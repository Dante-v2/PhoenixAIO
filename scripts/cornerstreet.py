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

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

class CORNERSTREET():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'cornerstreet/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "cornerstreet/proxies.txt")
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
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
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

        self.user = row['MAIL']
        self.passw = row['PASSWORD']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.address1 = row['ADDRESS']
        self.address2 = row['ADDRESS 2']
        self.region = row['REGION']
        self.zip = row['ZIPCODE']
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.city = row['CITY']
        self.link = row['LINK']  
        self.size = row['SIZE']
        self.payment = row['PAYMENT']

        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.delay = int(config["delay"])
        self.discord = DISCORD_ID

        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.timeout = 120
        self.build_proxy()
        self.balance = balancefunc()
        self.bar()

        try:
            if self.name.upper() == "RANDOM":
                self.name = names.get_first_name(gender='male')
            if self.surname.upper() == "RANDOM":
                self.surname = names.get_last_name()
            if self.phone.upper() == "RANDOM":
                self.phone = str("0"+str(random.randint(7400000000,7999990000)))
            if self.user[:6].upper() == "RANDOM":
                self.user = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.user.split("@")[1]).lower()
        except Exception as e:
            self.error(e)

        self.warn('Starting tasks...')

        if self.passw != '':
            self.login()
        else:
            self.cookie()

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [CORNERSTREET] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [CORNERSTREET] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [CORNERSTREET] - {text}'
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
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} -  Running CORNERSTREET | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running CORNERSTREET | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

    def injection(self, session, response):
        if helheim.isChallenge(session, response):
            self.warn('Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response

    def cookie(self):
        self.warn('Getting cookies...')
        while True:
            try:
                r = self.s.get(
                    'https://www.cornerstreet.fr/customer/account/login/',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.success('Succesfully got cookies!')
                    break
                elif r.status_code == 403:
                    self.error(f'Proxy banned, retrying...')         
                    self.build_proxy()
                    continue 
                elif r.status_code >= 500 and r.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error while getting cookies: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue     
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting cookies: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        
        self.getprod()

    def login(self):
        self.emtypcart = False
        self.warn('Logging in...') 
        while True:
            try:
                x = self.s.get(
                    'https://www.cornerstreet.fr/customer/account/login/',
                    timeout = self.timeout
                )
                if x.status_code == 200:
                    if 'revient dans quelques instants' in x.text:
                        self.error('Cookies needed, restarting...')
                        self.emtypcart = True
                        break
                    else:
                        self.loginform = x.text.split('name="form_key" type="hidden" value="')[1].split('"')[0]
                        payload = {
                            'form_key':self.loginform,
                            'login[username]':self.user,
                            'login[password]':self.passw
                        }
                        r = self.s.post(
                            'https://www.cornerstreet.fr/customer/account/loginPost/',
                            data = payload, 
                            timeout = self.timeout, 
                            allow_redirects = False
                        )
                        if r.status_code == 302 and r.headers['location'] == 'https://www.cornerstreet.fr/customer/account/':
                            self.success('Successfully logged in!') 
                            break
                        elif r.status_code == 302:
                            self.error('Login failed, check your info!')
                            time.sleep(self.delay)
                            sys.exit()
                            break
                        elif r.status_code == 403:
                            self.error(f'Proxy banned, rotating...')                 
                            self.build_proxy()                      
                            continue
                        elif r.status_code >= 500 and r.status_code < 600:
                            self.warn('Site is dead, retrying...')
                            time.sleep(self.delay)
                            continue
                        elif r.status_code == 404:
                            self.warn('Page not loaded, retrying...')
                            time.sleep(self.delay)
                            continue
                        else:
                            self.error(f'Unkown error {r.status_code}, retrying...')
                            self.build_proxy()  
                            continue  
                elif x.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.build_proxy()
                    continue 
                elif x.status_code >= 500 and x.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif x.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {x.status_code}, retrying...')
                    self.build_proxy()
                    continue     
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                if self.passw != '':
                    self.login()
                else:
                    self.cookie()

            except Exception as e:
                self.error(f'Exception during login: {e}, retrying...')
                self.build_proxy()
                self.s.cookies.clear()
                if self.passw != '':
                    self.login()
                else:
                    self.cookie()

        if self.emtypcart:
            self.getprod()
        else:
            self.clear()

    def clear(self):
        self.warn('Checking cart...')
        while True:
            try:
                r = self.s.get(
                    'https://www.cornerstreet.fr/checkout/cart/', 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'Votre panier est vide.' in r.text:
                        self.success('Cart empty, proceding...')
                        break
                    else:
                        self.warn('Cart not empty, clearing...')
                        soup = bs(r.text, features='lxml')
                        table = soup.find('table',{'id':'shopping-cart-table'})
                        infzo = table.find('td',{'class':'product-cart-info'})
                        self.cartc = infzo.find('a',{'class':'btn-remove btn-remove2'})['href']
                        t = self.s.get(
                            self.cartc, 
                            timeout = self.timeout
                        )
                        continue
                elif r.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.build_proxy()
                    continue 
                elif r.status_code >= 500 and r.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue     
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.clear()
            except Exception as e:
                self.error(f'Exception clearing cart:{e.__class__.__name__}, retrying...')
                self.s.cookies.clear()
                self.clear()
        self.getprod()
         
    def getprod(self):
        self.warn('Getting product page...')
        while True:
            try:
                r = self.s.get(
                    self.link, 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    try:
                        soup = bs(r.text, features='lxml')
                        self.title = soup.find('title').text
                        try:
                            self.title = self.title.split(' -')[0]
                        except:
                            pass
                    except Exception as e:
                        self.warn(f'Product page pulled {e}, monitoring...')
                        time.sleep(self.delay)
                        continue
                    if 'Product.Config' in r.text: 
                        try:
                            ciao = r.text
                            po = soup.find('div',{'class':'product-add-form'})
                            self.atc_url = po.find('form',{'id':'product_addtocart_form'})['action']
                            self.formkey = po.find('input',{'name':'form_key'})['value']
                            self.productid = po.find('input',{'name':'product'})['value']
                            img = soup.find('div',{'data-gallery-role':'gallery-placeholder'})
                            self.img = img.find('img',{'alt':'main product photo'})['src']
                            print(self.img)
                            try:
                                varconf = ciao.split('"spConfig": ')[1].split(');')[0]
                            except:
                                self.warn(f'{self.title} OOS, retrying...')
                                time.sleep(self.delay)
                                continue
                            r_json = json.loads(varconf)
                            self.value = []
                            self.saize = []
                            kill = r_json['attributes']['531']['options']
                            for a in kill:
                                self.value.append(a['id'])
                                self.saize.append(a['label'])
                            tot = zip(self.value, self.saize)
                            connecto = list(tot)
                            self.sizerange = []
                            if len(connecto) >= 1:
                                self.success(f'{self.title} in stock!') 
                            else:
                                self.warn(f'{self.title} OOS, retrying...')
                                time.sleep(self.delay)
                                continue
                            if self.size == "RANDOM":
                                scelta = random.choice(connecto)
                                ciao3 = scelta[0]
                                self.value = "".join(ciao3)
                                ciao2 = scelta[1]
                                self.saiz = "".join(ciao2)
                                self.warn(f'Adding to cart size {self.saiz}...')
                                break
                            elif '-' in self.size:
                                self.size1 = str(self.size.split('-')[0])
                                self.size2 = str(self.size.split('-')[1])
                                for x in connecto:
                                    if self.size1 <= str(x[1]) <= self.size2:
                                        self.sizerange.append(x[1])        
                                self.sizerandom = random.choice(self.sizerange)
                                for Traian in connecto:
                                    if self.sizerandom == Traian[1]:
                                        ciao0 = Traian[0]
                                        self.value = "".join(ciao0)
                                        ciao1 = Traian[1]
                                        self.saiz = "".join(ciao1)
                                self.warn(f'Adding to cart size {self.saiz}')
                                break    
                            elif ',' in self.size:
                                self.size1 = str(self.size.split(',')[0])
                                self.size2 = str(self.size.split(',')[1])
                                for x in connecto:
                                    if self.size1 <= str(x[1]) <= self.size2:
                                        self.sizerange.append(x[1])        
                                self.sizerandom = random.choice(self.sizerange)
                                for Traian in connecto:
                                    if self.sizerandom == Traian[1]:
                                        ciao0 = Traian[0]
                                        self.value = "".join(ciao0)
                                        ciao1 = Traian[1]
                                        self.saiz = "".join(ciao1)
                                self.warn(f'Adding to cart size {self.saiz}')
                                break
                            else:
                                for Traian in connecto:
                                    if self.size == Traian[1]:
                                        ciao0 = Traian[0]
                                        self.value = "".join(ciao0)
                                        ciao1 = Traian[1]
                                        self.saiz = "".join(ciao1)
                                self.warn(f'Adding to cart size {self.saiz}')
                                break
                        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                            self.error('Connection error, retrying...')
                            self.build_proxy()
                            continue
                        except Exception as e:
                            self.error(f'Exception getting product page: {e.__class__.__name__}, retrying...')
                            self.build_proxy()
                            continue
                    else:
                        self.warn(f'{self.title} OOS, retrying...')
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 403:
                    self.error(f'Proxy banned, retrying...')         
                    self.build_proxy()
                    continue 
                elif r.status_code >= 500 and r.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue     
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product page: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.atc() 

    def atc(self):
        self.atcfailed = False
        global carted, failed, checkoutnum
        payload = {
            'form_key':self.formkey,
            'product':self.productid,
            'related_product':'',
            'super_attribute[531]':self.value,
            'qty':'1'
        }
        headers = {
            'referer': self.link,
        }
        atctry = 0
        while True:
            try:
                r = self.s.post(
                    self.atc_url, 
                    timeout=self.timeout,
                    headers=headers,
                    data=payload,
                    allow_redirects=False
                )
                if r.status_code == 302:
                    self.success('Successfully added to cart!')
                    carted = carted + 1
                    self.bar()
                    break
                elif r.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.build_proxy()
                    continue 
                elif r.status_code >= 500 and r.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue    
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                self.build_proxy()
                self.getprod()
                break
        if self.atcfailed:
            self.getprod()
        self.checkx()
        self.ship()

    def checkx(self):
        self.warn('Getting checkout info')
        while True:
            try:
                r = self.s.get(
                    'https://www.cornerstreet.fr/checkout/onepage/',
                    timeout= self.timeout
                )
                if r.status_code == 200:
                    break
                elif r.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.build_proxy()
                    continue 
                elif r.status_code >= 500 and r.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue    
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting checkout info: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                self.build_proxy()
                self.getprod()
                break
        return self.success('Succesfully got checkout info!')

    def guest(self):
        headers = {
            'Accept':'text/javascript, text/html, application/xml, text/xml, */*',
            'x-prototype-version':'1.7',
            'x-requested-with':'XMLHttpRequest',
            'referer':'https://www.cornerstreet.fr/checkout/onepage/',
        }
        self.warn('Getting checkout page...')
        self.emtypcart = False
        payload = {
            'method': 'guest'
        }
        while True:
            try:
                x = self.s.post(
                    'https://www.cornerstreet.fr/checkout/onepage/saveMethod/', 
                    data = payload, 
                    headers=headers,
                    timeout = self.timeout
                )
                if x.status_code == 200:
                    if 'Votre panier est vide.' in x.text:
                        self.error(f'Cart is empty, restarting...')
                        self.emtypcart = True
                        self.s.cookies.clear()
                        break
                    else:
                        self.success('Succesfully got checkout page!')
                        break
                elif x.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.emtypcart = True
                    self.s.cookies.clear()
                    continue 
                elif x.status_code >= 500 and x.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif x.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error('Product oos while submitting ship, restarting...')
                    self.emtypcart = True
                    self.build_proxy()
                    self.s.cookies.clear()
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.build_proxy()
                self.error('Connection error, retrying...')
                continue
            except Exception as e:
                self.error(f'Exception submitting shipping: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                self.build_proxy()
                continue
        if self.emtypcart:
            if self.passw != '':
                self.login()
            else:
                self.cookie()
        else:
            self.ship2()

    def ship2(self):
        self.emtypcart = False
        self.warn('Submitting shipping...')
        headers = {
            'Accept':'text/javascript, text/html, application/xml, text/xml, */*',
            'x-prototype-version':'1.7',
            'x-requested-with':'XMLHttpRequest',
            'referer':'https://www.cornerstreet.fr/checkout/onepage/',
        }
        payload = {
            'billing[address_id]':'',
            'billing[prefix]':'Mr',
            'billing[firstname]':self.name,
            'billing[lastname]':self.surname,
            'billing[company]':'',
            'billing[email]':self.user,
            'billing[street][]':self.address1,
            'billing[street][]':self.address2,
            'billing[city]':self.city,
            'billing[region_id]':self.region,
            'billing[region]':'',
            'billing[postcode]':self.zip,
            'billing[country_id]':self.country,
            'billing[telephone]':self.phone,
            'billing[fax]':'',
            'billing[day]':'',
            'billing[month]':'',
            'billing[year]':'',
            'billing[dob]':'',
            'billing[gender]':'1',
            'billing[customer_password]':'',
            'billing[confirm_password]':'',
            'billing[save_in_address_book]':'1',
            'billing[use_for_shipping]':'1',
            'form_key':self.formkey
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.cornerstreet.fr/checkout/onepage/saveBilling/',
                    data = payload, 
                    headers=headers,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'Votre panier est vide.' in r.text:
                        self.error('Cart empty, restarting...')
                        self.emtypcart = True
                        break
                    elif 'CornerStreet revient dans quelques instants...' in r.text:
                        self.error('Cookies needed, restarting...')
                        self.emtypcart = True
                        break
                    else: 
                        self.success('Successfully submitted shipping!')
                        resp = r.text
                        respo = resp.replace('\\n', '')
                        x = respo.replace('\\','')
                        if self.country == 'FR':
                            if 'socolissimo_domicile_sign_fr_3' in r.text:
                                self.shipping_rate = 'socolissimo_domicile_sign_fr_3'
                            elif 'socolissimo_domicile_sign_fr_5' in r.text:
                                    self.shipping_rate = 'socolissimo_domicile_sign_fr_5'
                            else:
                                self.shipping_rate = 'socolissimo_domicile_sign_fr_6'
                        else:
                            self.shipping_rate = x.split('value="')[1].split('"')[0]
                        break
                elif r.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.build_proxy()
                    continue 
                elif r.status_code >= 500 and r.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue  
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception submitting shipping: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        if self.emtypcart:
            if self.passw != '':
                self.login()
            else:
                self.cookie()
        else:
            self.rate()

    def ship(self):
        headers = {
            'Accept':'text/javascript, text/html, application/xml, text/xml, */*',
            'x-prototype-version':'1.7',
            'x-requested-with':'XMLHttpRequest',
            'referer':'https://www.cornerstreet.fr/checkout/onepage/',
        }
        if self.passw == '':
            self.guest()
        else:
            self.emtypcart = False
        self.warn('Getting shipping page...')
        while True:
            try:
                x = self.s.get(
                    'https://www.cornerstreet.fr/checkout/onepage/', 
                    headers=headers,
                    timeout = self.timeout
                )
                if x.status_code == 200:
                    if 'Votre panier est vide.' in x.text:
                        self.error('Cart is empty, restarting...')
                        self.emtypcart = True
                        break
                    else:
                        self.warn('Submitting shipping...')
                        soup = bs(x.text, features='lxml')
                        fiel = soup.find('div',{'class':'fieldset'})
                        self.billingid = fiel.find('input',{'name':'billing[address_id]'})['value']
                        payload = {
                            'billing[address_id]':self.billingid,
                            'billing[prefix]':'Mr',
                            'billing[firstname]':self.name,
                            'billing[lastname]':self.surname,
                            'billing[company]':'',
                            'billing[street][]':self.address1,
                            'billing[street][]':self.address2,
                            'billing[city]':self.city,
                            'billing[region_id]':self.region,
                            'billing[region]':'',
                            'billing[postcode]':self.zip,
                            'billing[country_id]':self.country,
                            'billing[telephone]':self.phone,
                            'billing[fax]':'',
                            'billing[save_in_address_book]':'1',
                            'billing[use_for_shipping]':'1',
                            'form_key':self.formkey
                        }
                        r = self.s.post(
                            'https://www.cornerstreet.fr/checkout/onepage/saveBilling/', 
                            data = payload, 
                            timeout = self.timeout
                        )
                        if r.status_code == 200:
                            if 'Votre panier est vide.' in r.text:
                                self.error('Cart empty, restarting...')
                                self.emtypcart = True
                                break
                            elif 'CornerStreet revient dans quelques instants...' in r.text:
                                self.error('Cookies needed, restarting...')
                                self.emtypcart = True
                                break
                            else: 
                                self.success('Successfully submitted shipping!')
                                resp = r.text
                                respo = resp.replace('\\n', '')
                                x = respo.replace('\\','')
                                if self.country == 'FR':
                                    if 'socolissimo_domicile_sign_fr_3' in r.text:
                                        self.shipping_rate = 'socolissimo_domicile_sign_fr_3'
                                    elif 'socolissimo_domicile_sign_fr_5' in r.text:
                                        self.shipping_rate = 'socolissimo_domicile_sign_fr_5'
                                    else:
                                        self.shipping_rate = 'socolissimo_domicile_sign_fr_6'
                                else:
                                    self.shipping_rate = x.split('value="')[1].split('"')[0]
                                break
                        elif r.status_code == 403:
                            self.error(f'Proxy banned, retrying...')                 
                            self.build_proxy()
                            continue 
                        elif r.status_code >= 500 and r.status_code < 600:
                            self.warn('Site is dead, retrying...')
                            time.sleep(self.delay)
                            continue
                        elif r.status_code == 404:
                            self.warn('Page not loaded, retrying...')
                            time.sleep(self.delay)
                            continue
                        else:
                            self.error(f'Unkown error: {r.status_code}, retrying...')
                            self.build_proxy()
                            continue  
                elif x.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.build_proxy()
                    continue 
                elif x.status_code >= 500 and x.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif x.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.build_proxy()
                self.error('Connection error, retrying...')
                continue
            except Exception as e:
                self.error(f'Exception while getting shipping page: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        if self.emtypcart:
            if self.passw != '':
                self.login()
            else:
                self.cookie()
        else:
            self.rate() 

    def rate(self):
        self.emtypcart = False
        self.warn('Getting shipping rates...')
        payload = {
            'shipping_method':self.shipping_rate,
            'form_key':self.formkey
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.cornerstreet.fr/checkout/onepage/saveShippingMethod/', 
                    timeout = self.timeout, 
                    data = payload
                )
                if r.status_code == 200:
                    if 'Votre panier est vide.' in r.text:
                        self.error('Cart empty, retrying...')
                        self.s.cookies.clear()
                        self.emtypcart = True
                        break
                    else:
                        if 'paypal' in r.text:
                            self.success('Successfully submitted rates!') 
                            break
                        else:
                            self.error('Failed getting shipping rates, retrying...')
                            time.sleep(self.delay)
                            continue
                elif r.status_code == 403:
                    self.emtypcart = True
                    self.s.cookies.clear()
                    continue
                elif r.status_code >= 500 and r.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue  
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.build_proxy()
                self.error(f'Connection error, retrying...')
                time.sleep(self.delay)
                continue
            except Exception as e:
                self.error(f'Exception while getting shipping rates: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                self.build_proxy()
                continue
        if self.emtypcart:
            if self.passw != '':
                self.login()
            else:
                self.cookie()
        else:
            if self.country == 'FR':
                if self.payment == 'CC':
                    self.creditcard()
                elif self.payment == 'PP':
                    self.paypal()   
            else:
                self.payment = 'PP'
                self.paypal()

    def creditcard(self):
        self.emtypcart = False
        global carted, failed, checkoutnum
        self.warn('Getting checkout...')
        payload = {
            'payment[method]':'payplug_payments',
            'form_key':self.formkey,
            'amgdpr_agree':'1'
        }
        while True:
            try:
                x = self.s.post(
                    f'https://www.cornerstreet.fr/checkout/onepage/saveOrder/form_key/{self.formkey}/', 
                    data = payload, 
                    timeout = self.timeout, 
                    allow_redirects = True
                )
                if x.status_code == 200 and x.url != 'https://www.cornerstreet.fr/checkout/cart/':
                    if 'Votre panier est vide.' in x.text:
                        self.error('Cart empty, retrying...')
                        failed = failed + 1
                        self.bar()
                        self.s.cookies.clear()
                        self.emtypcart = True
                        break
                    elif 'Ce priduit est' in x.text:
                        self.error('Cart empty, retrying...')
                        failed = failed + 1
                        self.bar()
                        self.s.cookies.clear()
                        self.emtypcart = True
                        break
                    elif 'error occurred while processing the order' in x.text:
                        self.error('Cart empty, retrying...')
                        failed = failed + 1
                        self.bar()
                        self.s.cookies.clear()
                        self.emtypcart = True
                        break
                    else:
                        self.warn(f'Opening CC payment link...')
                        r = self.s.get(
                            'https://www.cornerstreet.fr/payplug_payments/payment/redirect/', 
                            timeout = self.timeout, 
                            allow_redirects = False
                        )
                        if r.status_code == 302 and 'secure' in r.headers['location']:
                            if 'Votre panier est vide.' in r.text:
                                self.error('Cart empty, retrying...')
                                failed = failed + 1
                                self.bar()
                                self.s.cookies.clear()
                                self.emtypcart = True
                                break
                            elif 'Ce priduit est' in x.text:
                                self.error('Cart empty, retrying...')
                                failed = failed + 1
                                self.bar()
                                time.sleep(self.delay)
                                self.s.cookies.clear()
                                self.emtypcart = True
                                break
                            elif 'error occurred while processing the order' in x.text:
                                self.error('Cart empty, retrying...')
                                failed = failed + 1
                                self.bar()
                                self.s.cookies.clear()
                                self.emtypcart = True
                                break
                            else:
                                self.success('Successfully checked out!')
                                checkoutnum = checkoutnum + 1
                                self.bar()
                                self.pp_url = r.headers['Location']
                                break     
                        elif r.status_code == 302:
                            self.error('Product went oos while checking out, restarting...')
                            failed = failed + 1
                            self.bar()
                            time.sleep(self.delay)
                            self.s.cookies.clear()
                            self.build_proxy()
                            self.emtypcart = True
                            break
                        elif r.status_code == 403:
                            self.error(f'Proxy banned, retrying...')                 
                            self.build_proxy()
                            continue 
                        elif r.status_code >= 500 and r.status_code < 600:
                            self.warn('Site is dead, retrying...')
                            time.sleep(self.delay)
                            continue
                        elif r.status_code == 404:
                            self.warn('Page not loaded, retrying...')
                            time.sleep(self.delay)
                            continue
                        else:
                            self.error(f'Unkown error: {r.status_code}, retrying...')
                            self.build_proxy()
                            continue       
                elif x.status_code == 200:
                    self.error('Product went oos while checking out, restarting...')
                    failed = failed + 1
                    self.bar()
                    time.sleep(self.delay)
                    self.s.cookies.clear()
                    self.build_proxy()
                    self.emtypcart = True
                    break
                elif x.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.build_proxy()
                    continue 
                elif x.status_code >= 500 and x.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif x.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.build_proxy
                self.error('Connection error, retrying...')
                continue
            except Exception as e:
                self.warn(f'Exception while submitting order: {e.__class__.__name__}, retrying...')
                failed = failed + 1
                self.bar()
                time.sleep(self.delay)
                self.build_proxy()
                continue
        if self.emtypcart:
            if self.passw != '':
                self.login()
            else:
                self.cookie()
        else:
            self.passCookies()  

    def paypal(self):
        self.emtypcart = False
        global carted, failed, checkoutnum
        self.warn('Getting paypal...')
        while True:
            try:
                r = self.s.get(
                    'https://www.cornerstreet.fr/paypal/express/start/', 
                    timeout = self.timeout, 
                    allow_redirects = False
                )
                if r.status_code == 302:
                    if 'Votre panier est vide.' in r.text:
                        self.error('Cart empty, retrying...')
                        failed = failed + 1
                        self.bar()
                        self.s.cookies.clear()
                        self.emtypcart = True
                        break   
                    else:
                        self.success('Successfully checked out!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        self.pp_url = r.headers['Location']
                        break
                elif r.status_code == 403:
                    self.error(f'Proxy banned, retrying...')                 
                    self.build_proxy()
                    continue 
                elif r.status_code >= 500 and r.status_code < 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unkown error: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue        
            except ConnectionError as e:
                self.build_proxy()
                self.error(f'[TASK {self.threadID}] [CORNERSTREET] - Connection error, retrying...')
                continue
            except Exception as e:
                self.warn(f'Exception while getting paypal: {e.__class__.__name__}, retrying...')
                failed = failed + 1
                self.bar()
                self.build_proxy()
                continue
        if self.emtypcart:
            if self.passw != '':
                self.login()
            else:
                self.cookie()
        else:
            self.passCookies()  

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
                    writer.writerow({'SITE':'CORNERSTREET','SIZE':f'{self.saiz}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'CORNERSTREET','SIZE':f'{self.saiz}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            self.SuccessPP()
        except Exception as e: 
            self.error(f'Error passing cookies: {e.__class__.__name__}, retrying...') 
            self.passCookies()

    def Pubblic_Webhook(self):
        webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'**CORNERSTREET**', value = self.title, inline = False)
        embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.saiz, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = False)
        embed.add_embed_field(name='Delay', value = self.delay, inline = True)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_thumbnail(url = self.img)  
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        sys.exit()

    def SuccessPP(self):
        if self.passw != '':
            self.pppp = self.passw
        else:
            self.pppp = 'GUEST'
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**CORNERSTREET**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.saiz, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.user}||", inline = False)
        embed.add_embed_field(name='**PASSWORD**', value = f"||{self.pppp}||", inline = True)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url = self.img)   
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        try:
            playsound('checkout.wav')
        except:
            pass
        self.Pubblic_Webhook()