import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

carted = 0
failed = 0
checkoutnum = 0

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


def Region(json_obj, w_file):

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
        path = os.path.join(os.path.dirname(sys.argv[0]), "suppa/region.json")
    elif machineOS == "Windows":
        path = os.path.dirname(__file__).rsplit('\\', 1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), "suppa/region.json")
    with open(f'{path}', 'r') as f:
        prov = json.load(f)
        f.close()

except Exception as e:

    error(f"FAILED TO READ REGION FILE")
    pass

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

class SUPPASTORE():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
        try:
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'suppa/exceptions.log')
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'suppa/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "suppa/proxies.txt")
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
            self.error('2Captcha or AntiCaptcha needed. Stopping task.')
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

        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.email = row['EMAIL']
        self.street = row['STREET']
        self.num = row['NUM']
        self.city = row["CITY"]
        self.postcode = row['POSTCODE']
        self.region = row['REGION']
        self.regionid = row["REGIONID"]
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.link = row['LINK']
        self.size = row['SIZE']
        self.payment = row["PAYMENT"]

        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        self.webhook = webhook
        self.discord = DISCORD_ID
        self.threadID = '%03d' % i
        self.version = version
        self.delay = int(config["delay"])
        self.build_proxy()
        self.timeout = 120
        self.balance = balancefunc()
        self.bar()
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
        self.warn('Task started!')
        self.start()
                        
    def error(self, text):
        message = f'[TASK {self.threadID}] - [SUPPASTORE] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [SUPPASTORE] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [SUPPASTORE] - {text}'
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
                f'Phoenix AIO {self.version} - SUPPASTORE Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - SUPPASTORE Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')


    def injection(self, session, response):
        if helheim.isChallenge(session, response):
            self.warn('Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response

    def start(self): 
        self.warn('Getting token...')
        while True:
            try:
                r = self.s.get(
                    "https://www.suppastore.com/en/customer/section/load/", 
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    for cookie in self.s.cookies:
                        if cookie.name == "__cfduid":
                            self.cf = cookie.value
                    try:
                        roba= str(r.headers)
                        self.php = roba.split("PHPSESSID=")[1].split(";")[0]
                        self.success('Succesfully got token!')
                        break
                    except:
                        self.error('Error getting token, retrying...')
                        self.build_proxy()
                        self.s.clear.cookies()
                        continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while getting token: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'Token: {e}\n')
                self.error(f'Exception while getting token: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
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
                    if 'title="Notify Me"' in r.text:
                        time.sleep(self.delay)
                        self.warn(f'Product OOS, monitoring...')
                        continue
                    else:
                        soup = bs(r.text, features='lxml')  
                        resp = r.text
                        self.image = resp.split(',"img":"')[1].split('","')[0]
                        self.imm = self.image.replace("\/","/")
                        titolo = soup.find("div", {"class":"product-info-main"})
                        titles = titolo.find("div", {"class":"product attribute manufacturer"})
                        self.title = titles.find("div", {"class":"value"}).text
                        title2 = titolo.find("div", {"class":"page-title-wrapper product"})
                        bob = title2.find("h1")
                        self.title2 = bob.find("span").text
                        self.sky = soup.find("li",{"class":"item additional-attribute sku"}).text
                        self.headers = r.headers
                        self.cookies22 = r.cookies
                        rmkey = soup.find("input",{"name":"form_key"})
                        self.formkey = rmkey["value"]
                        ropt = soup.find("form",{"data-product-sku":self.sky})
                        self.atc_url = ropt["action"]
                        diocan = soup.find("div",{"class":"product-add-form"})
                        dioporco = diocan.find("script",{"type":"text/x-magento-init"})
                        r_json = json.loads(dioporco.string)
                        self.conf = r_json["#conf-select-attr-173"]["Magento_ConfigurableProduct/js/configurable/select/action"]["config"]
                        self.prodid = self.conf["productId"]
                        self.super = self.conf["attributes"]["173"]["options"]
                        self.iditem = []
                        self.sizeid = []
                        self.variz = []
                        for a in self.super:
                            m = a["products"][0]
                            if self.conf['stock'][m]['qty'] > 0:
                                self.iditem.append(a["id"])
                                sizef = a["label"]
                                sizeg = sizef.split("Footwear-")[1]
                                self.sizeid.append(sizeg)
                                self.variz.append(a["products"])
                        tot = zip(self.iditem, self.sizeid, self.variz)
                        connect = list(tot)
                        self.sizerange = []
                        if self.size == "RANDOM":
                            scelta = random.choice(connect)
                            ciao3 = scelta[0]
                            self.superattribute = "".join(ciao3)
                            ciao = scelta[2]
                            self.variante = "".join(ciao)
                            ciao2 = scelta[1]
                            self.moni = "".join(ciao2)
                            self.warn(f'Monitoring size {ciao2}...')
                            self.swebhs = ciao2
                            self.stock = self.conf["stock"][self.variante]["qty"]
                            if self.stock == 0:
                                self.warn(f'Product OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                            else:
                                self.success(f'Product in stock quantity:{self.stock}')
                                break
                        elif '-' in self.size:
                            self.size1 = str(self.size.split('-')[0])
                            self.size2 = str(self.size.split('-')[1])
                            for x in connect:
                                if self.size1 <= str(x[1]) <= self.size2:
                                    self.sizerange.append(x[1])     
                            self.sizerandom = random.choice(self.sizerange)   
                            for Traian in connect:
                                if self.sizerandom == Traian[1]:
                                    ciao0 = Traian[0]
                                    self.superattribute = "".join(ciao0)
                                    ciao2 = Traian[2]
                                    self.variante = "".join(ciao2)
                                    ciao1 = Traian[1]
                                    self.moni = "".join(ciao1)
                            self.swebhs = ciao1
                            self.stock = self.conf["stock"][self.variante]["qty"]
                            if self.stock == 0:
                                self.warn(f'Product OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                            else:
                                self.success(f'Product in stock quantity:{self.stock}')
                                break
                        elif ',' in self.size:
                            self.size1 = str(self.size.split(',')[0])
                            self.size2 = str(self.size.split(',')[1])
                            for x in connect:
                                if self.size1 <= str(x[1]) <= self.size2:
                                    self.sizerange.append(x[1])     
                            self.sizerandom = random.choice(self.sizerange)   
                            for Traian in connect:
                                if self.sizerandom == Traian[1]:
                                    ciao0 = Traian[0]
                                    self.superattribute = "".join(ciao0)
                                    ciao2 = Traian[2]
                                    self.variante = "".join(ciao2)
                                    ciao1 = Traian[1]
                                    self.moni = "".join(ciao1)
                            self.swebhs = ciao1
                            self.stock = self.conf["stock"][self.variante]["qty"]
                            if self.stock == 0:
                                self.warn(f'Product OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                            else:
                                self.success(f'Product in stock quantity:{self.stock}')
                                break
                        else:
                            for Traian in connect:
                                if self.size == Traian[1]:
                                    ciao0 = Traian[0]
                                    self.superattribute = "".join(ciao0)
                                    ciao2 = Traian[2]
                                    self.variante = "".join(ciao2)
                                    ciao1 = Traian[1]
                                    self.moni = "".join(ciao1)
                            self.swebhs = ciao1
                            self.stock = self.conf["stock"][self.variante]["qty"]
                            if self.stock == 0:
                                self.warn(f'Product OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                            else:
                                self.success(f'Product in stock quantity:{self.stock}')
                                break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while getting product page:{r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'Product page: {e}\n')
                self.error(f'Exception while getting product page: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue     
        self.atc()

    def atc(self):
        global carted, failed, checkoutnum
        self.warn('Adding to cart...')
        payload = {
            "product": self.prodid,
            "selected_configurable_option": self.variante,
            "related_product": "",
            "form_key": self.formkey,
            "super_attribute[173]": self.superattribute
        }
        headers = {
            'cookie' : f'PHPSESSID={self.php}; form_key={self.formkey}',
        }
        self.s.headers.update(headers)
        self.fail = False
        while True:
            try:
                r = self.s.post(
                    self.atc_url, 
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if "You have no items in your shopping cart" in r.text:
                        self.error('Failed adding to cart, retrying...')
                        self.fail = True
                        break
                    else:
                        self.success('Succesfully added to cart!')
                        carted = carted + 1
                        self.bar()
                        break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while adding to cart: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'ATC: {e}\n')
                self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue   
        if self.fail:
            self.s.cookies.clear()
            self.build_proxy()
            self.start()
        else:
            self.check1()

    def check1(self):
        self.warn('Getting checkout page...')
        headers = {
            'Accept': '*/*',
            'Referer' : 'https://www.suppastore.com/en/checkout/cart/',
        }
        while True:
            try:
                r = self.s.get(
                    'https://www.suppastore.com/en/checkout/',
                    headers = headers,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    colum = r.text
                    self.pp = colum.split('token=EC-')[1].split('",')[0]
                    self.entity = colum.split('entity_id":"')[1].split('",')[0]
                    self.success('Succesfully got checkout page!')
                    break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while getting checkout page: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'Checkout page: {e}\n')
                self.error(f'Exception while getting checkout page: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue   
        self.check2()

    def check2(self):
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Referer' : 'https://www.suppastore.com/en/checkout/'
        }
        payload = {"address":{"street":[self.street],"city":self.city,"region":self.region,"country_id":self.country,"postcode":self.postcode,"firstname":self.name,"lastname":self.surname,"company":"","telephone":self.phone,"custom_attributes":{"house_number":self.num,"amorderattr_additional_info":""}}}
        self.warn('Getting shipping rates...')
        while True:
            try:
                r = self.s.post(
                    f'https://www.suppastore.com/en/rest/en/V1/guest-carts/{self.entity}/estimate-shipping-methods', 
                    headers = headers, 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    r_json = json.loads(r.text)
                    self.carrier = r_json[0]["carrier_code"]
                    self.rate = r_json[0]["method_code"]
                    self.success('Succesfully got shipping rates!')
                    break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while getting shipping rates: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'Rates: {e}\n')
                self.error(f'Exception while getting shipping rates: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.check3()

    def check3(self):
        payload = {"addressInformation":{"shipping_address":{"countryId":self.country,"region":self.region,"street":[self.street],"company":"","telephone":self.phone,"postcode":self.postcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":{"house_number":self.num,"amorderattr_additional_info":""},"custom_attributes":{"house_number":self.num,"amorderattr_additional_info":""},"extension_attributes":{"house_number":self.num}},"billing_address":{"countryId":self.country,"region":self.region,"street":[self.street],"company":"","telephone":self.phone,"postcode":self.postcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":{"house_number":self.num,"amorderattr_additional_info":""},"custom_attributes":{"house_number":self.phone,"amorderattr_additional_info":""},"saveInAddressBook":0},"shipping_method_code":self.rate,"shipping_carrier_code":self.carrier,"extension_attributes":{}}}
        self.warn('Submitting ship...')
        while True:
            try:
                r = self.s.post(
                    f'https://www.suppastore.com/en/rest/en/V1/guest-carts/{self.entity}/shipping-information',
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.success('Succesfully submitted ship!')
                    break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while submitting ship: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'Ship: {e}\n')
                self.error(f'Exception while submitting ship: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        if self.payment == 'PP':
            self.paypal1()
        elif self.payment == 'TRANSFER':
            self.banktransfer()
        else:
            self.error('Wrong payment selected, using paypal!')
            self.paypal1()

    def paypal1(self):
        self.warn('Getting paypal info...')
        payload = {
            'ecToken':f'EC-{self.pp}',
            'continueButton':'outside',
            'preselection':'UGF5UGFs',
            'surcharging':'false',
            'country':self.country,
            'language':'en_US',
            'thirdPartyMethods':'W3sibWV0aG9kTmFtZSI6IkJhbmsgVHJhbnNmZXIgUGF5bWVudCIsImltYWdlVXJsIjoiIiwiZGVzY3JpcHRpb24iOiJZb3Ugd2lsbCByZWNlaXZlIHRoZSBiYW5rIHRyYW5zZmVyIGRldGFpbHMgd2l0aCB5b3VyIGNvbmZpcm1hdGlvbiBlbWFpbCBhZnRlciBjb21wbGV0aW5nIHRoZSBjaGVja291dCJ9XQ%3D%3D',
            'styles':'',
            'showPuiOnSandbox':'false'
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.paypal.com/paymentwall/payment-selection', 
                    headers = headers, 
                    proxies = None,
                    data = payload
                )
                if r.status_code == 200: 
                    resp = r.text
                    soup = bs(resp, features='lxml')
                    pay = soup.find('div',{"id":"wrapper"})
                    payp = pay.find('div',{"id":"paymentMethodContainer"})
                    pp2 = payp.find('div',{"data-pm":"PayPal"})["id"]
                    self.pp2 = pp2.split('-')[1]
                    self.success('Successfully got paypal info!')
                    break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while getting paypal info: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'Paypal Info: {e}\n')
                self.error(f'Exception while getting paypal info: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.paypal2()

    def paypal2(self):
        global carted, failed, checkoutnum
        self.warn('Opening paypal...')
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json'
        }
        payload = {"cartId":self.entity,"email":self.email,"paymentMethod":{"method":"iways_paypalplus_payment","po_number":0,"additional_data":None},"billingAddress":{"countryId":self.country,"region":self.region,"street":[self.street],"company":"","telephone":self.phone,"postcode":self.postcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":{"house_number":self.num,"amorderattr_additional_info":""},"custom_attributes":{"house_number":self.num,"amorderattr_additional_info":""},"saveInAddressBook":0}}
        while True:
            try:
                r = self.s.post(
                    f'https://www.suppastore.com/en/rest/en/V1/guest-carts/{self.entity}/set-ppp-payment-information',
                    headers = headers, 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:   
                    if r.text == 'true':
                        linkpp = f'https://www.paypal.com/paymentwall/payment-approval?ecToken=EC-{self.pp}&paymentMethod=pp-{self.pp2}&country=IT&language=en_US&useraction=commit'
                        t = self.s.get(linkpp)
                        if t.status_code == 200:
                            self.pp_url = t.url
                        self.success('Successfully checked out!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                    break
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while opening paypal: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'Opening paypal: {e}\n')
                self.error(f'Exception while opening paypal: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.passCookies()

    def banktransfer(self):
        global carted, failed, checkoutnum
        self.warn('Completing bank transfer checkout...')
        payload = {"cartId":self.entity,"billingAddress":{"countryId":self.country,"region":self.region,"street":[self.street],"company":"","telephone":self.phone,"postcode":self.postcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":{"house_number":self.num,"amorderattr_additional_info":""},"custom_attributes":{"house_number":self.num,"amorderattr_additional_info":""},"saveInAddressBook":0},"paymentMethod":{"method":"banktransfer","po_number":0,"additional_data":None,"extension_attributes":{"agreement_ids":["3","4"]}},"email":self.email}
        while True:
            try:
                r = self.s.post(
                    f'https://www.suppastore.com/en/rest/en/V1/guest-carts/{self.entity}/payment-information', 
                    json = payload,
                    timeout = self.timeout
                ) 
                if r.status_code == 200:
                    x = self.s.get(
                        'https://www.suppastore.com/en/checkout/onepage/success/',
                        timeout = self.timeout
                    )
                    if x.status_code == 200:
                        soup = bs(x.text, features='lxml')
                        self.order = soup.find("div",{"class":"checkout-success"}).text
                        self.num = self.order.split('is:')[1].split('.')[0]
                        self.success('Successfully checked out!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        break
                    elif x.status_code == 403:
                        self.error('Proxy banned, retrying...')
                        self.build_proxy()
                        continue
                    elif x.status_code >= 500 and x.status_code <= 600:
                        self.error('Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue
                    elif x.status_code == 404:
                        self.error('Page not loaded, retrying...')
                        time.sleep(self.delay)
                        self.build_proxy()
                        continue
                    else:
                        error(f'Unkown error while submitting ship: {x.status_code}, retrying...')
                        self.build_proxy()
                        continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif 'The requested Payment Method is not available.' in r.text:
                    self.error('Bank transfer not available, switching to paypal...')
                    time.sleep(self.delay)
                    self.payment = 'PP'
                    self.paypal1()
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.error('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    self.build_proxy()
                    continue
                else:
                    error(f'Unkown error while completing bank transfer checkout: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                open(self.logs_path, 'a+').write(f'Bank: {e}\n')
                self.error(f'Exception while completing bank transfer checkout: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.webhookbank()

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
                    writer.writerow({'SITE':'SUPPASTORE','SIZE':f'{self.swebhs}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title2}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'SUPPASTORE','SIZE':f'{self.swebhs}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title2}'})
            self.SuccessPP()
        except Exception as e: 
            self.error(f'Error while passing cookies:{e}, retrying...')
            time.sleep(self.delay)
            self.SuccessPP()

    def Pubblic_Webhook(self):
        webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO Cooked!', color = 40703)
        embed.add_embed_field(name=f'**SUPPASTORE**', value = f'{self.title} {self.title2}', inline = False)
        embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.swebhs, inline = True)
        embed.add_embed_field(name='**MODE**', value = self.payment, inline = True)  
        embed.add_embed_field(name='Delay', value = self.delay, inline = True)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_thumbnail(url = self.imm) 
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        try:
            playsound('checkout.wav')
            sys.exit(1)
        except:
            sys.exit(1)

    def SuccessPP(self):
        if self.payment == 'PP':
            self.payment = 'PAYPAL'
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**SUPPASTORE**', value =f'{self.title} {self.title2}', inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.swebhs, inline = True)
        embed.add_embed_field(name='**MODE**', value = self.payment, inline = True)   
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False) 
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url = self.imm) 
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook()

    def webhookbank(self):
        if self.payment == 'TRANSFER':
            self.payment = 'BANK TRANSFER'
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 0x715aff)
        embed.add_embed_field(name=f'**SUPPASTORE**', value =f'{self.title} {self.title2}', inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.swebhs, inline = True)
        embed.add_embed_field(name='**MODE**', value = self.payment, inline = True)   
        embed.add_embed_field(name='**ORDER NUMBER**', value = f'||{self.num}||', inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False) 
        embed.set_thumbnail(url = self.imm) 
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook()