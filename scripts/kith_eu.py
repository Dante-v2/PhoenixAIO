import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, datetime, re, urllib
from mods.logger import info, warn, error
import requests
import cloudscraper
from discord_webhook import DiscordWebhook, DiscordEmbed
import lxml
from bs4 import BeautifulSoup as bs
import names
from playsound import playsound
from twocaptcha import TwoCaptcha
from helheim import helheim, isChallenge
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None


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


class KITH_EU():

    def __init__(self, row, webhook, version, i):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'Allike/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "Allike/proxies.txt")
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

        self.s = requests.Session()

        self.build_proxy()

        self.name = row['FIRST NAME']
        self.surname = row['LAST NAME']
        self.mail = row['EMAIL']
        self.address = row['ADDRESS LINE 1']
        self.city = row['CITY']
        self.zip = row['ZIP']
        self.region = row['REGION']
        self.country = row['COUNTRY']
        self.phone = row['PHONE NUMBER']
        self.link = row['LINK']
        self.size = row['SIZE']
        self.payment = row['PAYMENT']
        self.cardnumber = row['CARD NUMBER']
        self.expmonth = row['EXP MONTH']
        self.expyear = row['EXP YEAR']
        self.cvc = row['CVC']
        self.mode = row['MODE']

        self.delay = int(config['delay'])
        self.timeout = 60

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

        self.webhook_url = webhook
        self.version = version
        self.threadID = '%03d' % i

        self.balance = balancefunc()

        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.bar()

        self.warn('Task started!')
        
        self.scraper_frontend()

    # Red logging

    def error(self, text):
        message = f'[TASK {self.threadID}] - [KITH-EU] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [KITH-EU] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [KITH-EU] - {text}'
        warn(message)

    def build_proxy(self):
        cookies = self.s.cookies
        self.s = requests.Session()
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
                f'Phoenix AIO {self.version} - Running ALLIKE | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running ALLIKE | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

    def scraper_frontend(self):
        self.warn('Getting product page...')
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fi;q=0.6',
            'referer': 'https://eu.kith.com/collections/all',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36'
        }
        while True:
            try:
                r = self.s.get(
                    self.link + f'?ids={random.randint(100000, 999999)},{random.randint(100000, 999999)}',
                    headers=headers,
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    self.success('Parsing product')
                    soup = bs(r.text, "lxml")
                    self.product = {}
                    try:
                        self.product['name'] = soup.find('h1', {'class': 'product__title'}).text.strip()
                    except:
                        self.product['name'] = 'Unknown Product'
                    try:
                        self.product['img'] = 'https://' + soup.find('div', {'class': 'product-image-carousel__slide'}).find('img')['data-src'].replace('{width}', '600')
                    except:
                        self.product['img'] = None
                    r_json = json.loads(soup.find('script',{'type':'application/json'}))
                    print(r_json)
                    #sizes = []
                    #sz = soup.find('select', {'name': 'id'}).find_all('option')
                    #for s in sz:
                    #    if not 'disabled' in s.keys():
                    #        sizes.append({
                    #            'value': s.text.strip(),
                    #            'id': s['value']
                    #        })

                    break
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error getting product: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue

        #self.sizegetter()

    def sizegetter(self):
        try:
            self.warn('Getting sizes...')
            try:
                aec = self.product_page.split('AEC.SUPER = [')[1].split(']')[0]
                r_js = json.loads(aec)
                self.superattribute = r_js['id']
            except:
                self.superattribute = '502'
            
            j = self.product_page.split('var spConfig = new Product.Config(')[1].split(')')[0]
            sizejson = json.loads(j)

            attribute = sizejson['attributes'][self.superattribute]

            idvar = []
            sizes = []

            for i in attribute['options']:
                idvar.append(i['id'])
                sizes.append(i['label'])

            tot = zip(idvar, sizes)
            connect = list(tot)

            self.sizerange = []

            if self.size == "RANDOM":
                scelta = random.choice(connect)
                ciao3 = scelta[0]
                self.AttributeValue = "".join(ciao3)
                ciao2 = scelta[1]
                self.sizeweb = "".join(ciao2)
                self.warn(f'Adding to cart size {self.sizeweb}')

            elif '-' in self.size:
                self.size1 = str(self.size.split('-')[0])
                self.size2 = str(self.size.split('-')[1])
                for x in connect:
                    if self.size1 <= str(x[1]) <= self.size2:
                        self.sizerange.append(x[1])     
                self.sizerandom = random.choice(self.sizerange)  
                for t in connect:
                    if self.sizerandom in t:
                        ciao3 = t[0]
                        self.AttributeValue = "".join(ciao3)
                        ciao = t[1]
                        self.sizeweb = "".join(ciao)
                self.warn(f'Adding to cart size {self.sizeweb}')
    
            elif ',' in self.size:
                self.size1 = str(self.size.split(',')[0])
                self.size2 = str(self.size.split(',')[1])
                for x in connect:
                    if self.size1 <= str(x[1]) <= self.size2:
                        self.sizerange.append(x[1])     
                self.sizerandom = random.choice(self.sizerange)   
                for t in connect:
                    if self.sizerandom in t:
                        ciao3 = t[0]
                        self.AttributeValue = "".join(ciao3)
                        ciao = t[1]
                        self.sizeweb = "".join(ciao)   
                self.warn(f'Adding to cart size {self.sizeweb}')

            else:
                for t in connect:
                    if self.size not in sizes:
                        self.warn('No selected sizes available, monitoring...')
                        return self.scraperPid()
                    elif self.size in t:
                        ciao3 = t[0]
                        self.AttributeValue = "".join(ciao3)
                        ciao = t[1]
                        self.sizeweb = "".join(ciao)
                self.warn(f'Adding to cart size {self.sizeweb}')

            if "new AwCountdown" in self.product_page:
                self.timeleft = str(self.product_page).split("'DHMS','")[1].split("','aw")[0]
                self.warn(f'Timer found: {self.timeleft}, waiting for timer...')
                time.sleep(int(self.timeleft)-15)

        except Exception as e:
            self.error(f'Exception while getting sizes {e.__class__.__name__}, retrying...')
            return self.scraperPid()
        else:
            return self.ATC()

    def ATC(self):

        global carted, failed, checkoutnum
        data = {
            "isAjax": 1,
            "form_key": self.form_key,
            f"super_attribute[{self.superattribute}]": self.AttributeValue,
            "parent_id": self.pid,
            "product_id":"",
            "related_product":"",
            "email_notification":"",
        }

        headers = {
            'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'referer': self.link
        }

        encoded = (base64.b64encode(self.link.encode('utf-8'))).decode()
        encoded = encoded.replace("=", ",")

        carting_URL = f'https://www.allikestore.com/default/oxajax/cart/add/uenc/{encoded}/product/{self.pid}/form_key/{self.form_key}/?callback=jQuery111004426187163784743_{int(time.time() * 1000)}'

        while True:
            try:
                r = self.s.post(
                    carting_URL, 
                    data = data,
                    headers = headers,
                    timeout = self.timeout, 
                    allow_redirects = False
                )

                if '"status":"SUCCESS"' in r.text:
                    resp1 = r.text.replace('\\n', '').replace("\\t",'')
                    resp = resp1.replace('\\','')
                    data = bs(resp, 'lxml')
                    try:
                        self.prodName = data.find('p', {'class': 'product-name'}).text
                    except:
                        self.prodName = "Product"
                    try:
                        self.addedSize = data.find('dl', {'class':'item-options'}).find('dd').text.strip()
                    except:
                        self.addedSize = self.size

                    self.success('Successfully added to cart!')
                    carted = carted + 1
                    self.bar()
                    err = False
                    break

                elif 'This product is currently out of stock' in r.text:
                    self.warn('Product OOS while adding to cart')
                    err = True
                    break
                    
                elif r.status_code == 403:
                    self.error('Access denied, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn(f'Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    self.error(f'Error adding to cart: {r.status_code} retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception adding to cart: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue

        if not err:
            if self.payment == "CC":
                self.checkoutpa()
            else:
                self.fetchPaypal()
        else:
            self.scraperPid()

    def fetchPaypal(self):
        global carted, failed, checkoutnum

        headers = {
            'Referer': 'https://www.allikestore.com/default/checkout/cart/'
        }

        self.warn('Getting PayPal link...')

        while True:
            try:
                r = self.s.get(
                    "https://www.allikestore.com/default/paypal/express/start/button/1/", 
                    headers=headers,
                    timeout=self.timeout, 
                    allow_redirects = False
                )

                if r.status_code == 302:
                    try:
                        pp_url = r.headers["Location"]
                    except:
                        pp_url = None

                    if not pp_url or 'paypal' not in pp_url:
                        self.error('Product OOS while checking out')
                        self.s.cookies.clear()
                        self.build_proxy()
                        oos = True
                        break
                    else:
                        self.paypalTok = pp_url
                        self.t1 = time.time()
                        self.success('PayPal link fetched!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
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
                        url = urllib.parse.quote(base64.b64encode(bytes(self.paypalTok, 'utf-8')).decode())
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
                                writer.writerow({'SITE':'ALLIKE','SIZE':f'{self.sizeweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})


                        else:
                            self.expToken = self.token
                            with open(path,'a',newline='') as f:
                                fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writerow({'SITE':'ALLIKE','SIZE':f'{self.sizeweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})
                        oos = False
                        break

                elif r.status_code == 403:
                    self.error(f'Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    self.fetchPaypal()

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error fetching PayPal link: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception fetching PayPal link: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue

        if oos:
            self.scraperPid()
        else:
            self.webhook()
        
    def checkoutpa(self):

        self.warn('Getting checkout page...')

        while True:
            try:
                r = self.s.get(
                    "https://www.allikestore.com/default/checkout/onepage/", 
                    timeout=self.timeout
                )

                if r.status_code == 200:
                    self.success('Successfully got checkout page!')
                    try:
                        soup = bs(r.text, 'lxml')
                        self.form_key = soup.find('input', {'name': 'form_key'})['value']
                    except:
                        pass
                    break

                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue

                elif r.status_code == 429:
                    self.error(f'Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error getting checkout page: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting checkout page: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.guest()

    def guest(self):

        self.warn('Submitting guest checkout...')

        headers = {
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.allikestore.com/default/checkout/onepage/'
        }

        data = {"method": "guest"}

        while True:
            try:
                r = self.s.post(
                    "https://www.allikestore.com/default/checkout/onepage/saveMethod/", 
                    data=data,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=False
                )

                if r.status_code == 200:
                    try:
                        rj = r.json()
                        if type(rj) == list and len(rj) == 0:
                            self.success('Successfully submitted guest!')
                            err = False
                            break
                        else:
                            self.error(f'Something went wrong while submitting guest, retrying...')
                            time.sleep(self.delay)
                            continue
                    except:
                        self.error(f'Something went wrong while submitting guest, retrying...')
                        time.sleep(self.delay)
                        continue

                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn(f'Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    error(f'Error submitting guest: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception submitting guest: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if not err:
            self.ship()
        else:
            self.checkoutpa()

    def ship(self):

        self.warn(f'Getting shipping rates...')

        headers = {
            'accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'x-requested-with': 'XMLHttpRequest',
            'referer': 'https://www.allikestore.com/default/checkout/onepage/'
        }

        payload = {
            'billing[address_id]':'',
            'billing[firstname]':self.name,
            'billing[lastname]':self.surname,
            'billing[company]':'',
            'billing[email]':self.mail,
            'billing[street][]':self.address,
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
            'billing[customer_password]':'',	
            'billing[confirm_password]':'',
            'billing[save_in_address_book]':'1',
            'billing[use_for_shipping]':'1',
            'form_key': self.form_key
        }

        while True:
            self.warn('Solving captcha...')
            code = self.solve_v3('https://www.allikestore.com/default/checkout/onepage/')
            payload['g-recaptcha-response'] = code
            self.success('Successfully solved captcha!')
            try:
                r = self.s.post(
                    "https://www.allikestore.com/default/checkout/onepage/saveBilling/", 
                    headers=headers,
                    data=payload,
                    timeout=self.timeout,
                    allow_redirects=False
                )

                if r.status_code == 200:
                    if 'shipping_method' in r.text:
                        if self.country == "DE":
                            self.smethod = "premiumrate_DHL_GoGreen"
                        elif self.country == 'US':
                            self.smethod = 'premiumrate_UPS_Express_Saver_(excl._Customs_and_Duties)'
                        else:
                            self.smethod = "premiumrate_UPS_Standard"
                        self.success(f'Successfully got shipping rates!')
                        err = False
                        break
                    else:
                        self.error(f'Something went wrong while getting shipping rates, retrying...')
                        err = True
                        break
#
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    continue

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    continue

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    self.error(f'Error while getting shipping rates: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    time.sleep()

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception getting shipping rates: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if not err:
            self.ship2()
        else:
            self.checkoutpa()

    def ship2(self):

        self.warn('Submitting shipping...')

        headers = {
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.allikestore.com/default/checkout/onepage/',
        }

        payload = {
            'shipping_method':self.smethod,
            'form_key':self.form_key
        }

        while True:
            try:
                r = self.s.post(
                    "https://www.allikestore.com/default/checkout/onepage/saveShippingMethod/",
                    headers=headers,
                    data=payload
                )

                if r.status_code == 200:
                    if 'creditcard' in r.text:
                        self.success('Successfully submitted shipping!')
                        c = r.text.replace('\\','').replace('&quot;','').split('name="payment[payone_config]"n')[1]
                        self.aid = c.split('aid:')[1].split(',')[0]
                        self.encodi = c.split('encoding:')[1].split(',')[0]
                        self.has = c.split('hash:')[1].split(',')[0]
                        self.mid = c.split('mid:')[1].split(',')[0]
                        self.portalid = c.split('portalid:')[1].split(',')[0]
                        err = False
                        break
                    else:
                        self.error('Something went wrong while submitting shipping, retrying...')
                        time.sleep(self.delay)
                        continue

                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    self.error(f'Error submitting shipping: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception submitting shipping: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if not err:
            self.cc()
        else:
            self.checkoutpa()

    def cc(self):

        self.warn('Verifying card...')

        global carted, failed, checkoutnum

        headers = {
            'Accept': '*/*',
            'Referer': 'https://secure.pay1.de/client-api/js/v1/payone_iframe.html'
        }

        cardtype = identify_card_type(self.cardnumber)
        if cardtype == "MasterCard":
            card_type = "M"
        elif cardtype == "Visa":
            card_type = "V"

        while True:
            try:
                r = self.s.get(
                    f"https://secure.pay1.de/client-api/?aid={self.aid}&encoding={self.encodi}&errorurl=&hash={self.has}&integrator_name=&integrator_version=&key=&language=&mid={self.mid}&mode=live&portalid={self.portalid}&request=creditcardcheck&responsetype=JSON&solution_name=&solution_version=&storecarddata=yes&successurl=&cardpan={self.cardnumber}&cardexpiremonth={self.expmonth}&cardexpireyear={self.expyear}&cardtype={card_type}&channelDetail=payoneHosted&cardcvc2={self.cvc}&callback_method=PayoneGlobals.callback", 
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=False
                )
                if r.status_code == 200:
                    try:
                        z = json.loads(r.text.split('PayoneGlobals.callback(')[1].split(');')[0])
                        if z['status'] == 'VALID':
                            self.pseudocardpan = z['pseudocardpan']
                            self.cardtype = z['cardtype']
                            self.truncatedcardpan = z['truncatedcardpan']
                            self.cardexpiredate = z['cardexpiredate']
                            self.success('Card Successfully verified!')
                            break
                        else:
                            self.error('Something went wrong veryfing card')
                            time.sleep(self.delay)
                            continue
                    except:
                        self.error('Something went wrong veryfing card')
                        time.sleep(self.delay)
                        continue
                else:
                    self.error(f'Error while verifying card: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception verifying card: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue

        self.submitorder()

    def submitorder(self):

        self.warn('Submitting order...')

        global carted, failed, checkoutnum

        headers = {
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.allikestore.com/default/checkout/onepage/'
        }

        payload = {
            'payment[method]':'payone_creditcard',
            'payone_creditcard_cc_type_select':f'4_{self.cardtype}',
            'payment[cc_type]':self.cardtype,
            'payment[payone_pseudocardpan]':self.pseudocardpan,
            'payment[payone_cardexpiredate]':self.cardexpiredate,
            'payment[cc_number_enc]':self.truncatedcardpan,
            'payment[payone_config_payment_method_id]':'4',
            'payment[payone_config]':{
                "gateway": {
                    "4": {
                        "aid": { self.aid },
                        "encoding": { self.encodi },
                        "errorurl":"",
                        "hash": { self.has },
                        "integrator_name":"",
                        "integrator_version":"",
                        "key":"",
                        "language":"",
                        "mid": { self.mid },
                        "mode":"live",
                        "portalid": { self.portalid },
                        "request":"creditcardcheck",
                        "responsetype":"JSON",
                        "solution_name":"",
                        "solution_version":"",
                        "storecarddata":"yes",
                        "successurl":""
                    }
                }
            },
            'payment[payone_config_cvc]':'{"4_V":"always","4_M":"always"}',
            'form_key':self.form_key,
            'agreement[2]':'1',
            'agreement[4]':'1',
            'customer_order_comment':''
        }

        while True:
            try:
                r = self.s.post(
                    f"https://www.allikestore.com/default/checkout/onepage/saveOrder/", 
                    data=payload, 
                    headers=headers
                )

                if r.status_code == 200:
                    try:
                        z = json.loads(r.text)
                        if z['success'] == True:
                            self.redirect = z['redirect']
                            self.success('Successfully checked out!')
                            checkoutnum += 1
                            self.bar()
                            err = False
                            break
                        else:
                            self.error(f'Payment failed, card was probably declined.')
                            failed +=1
                            self.bar()
                            self.declined()
                            err = True
                            break
                    except:
                        self.error('Something went wrong submitting order, card was probably declined.')
                        failed +=1
                        self.bar()
                        self.declined()
                        err = True
                        break

                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    self.error(f'Error checking out: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception checking out: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if not err:
            self.passCookies2()
        else:
            self.s.cookies.clear()
            self.build_proxy()
            self.scraperPid()

    def passCookies2(self):

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
        url = urllib.parse.quote(base64.b64encode(bytes(self.redirect, 'utf-8')).decode())
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
                writer.writerow({'SITE':'ALLIKE','SIZE':f'{self.sizeweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})

        else:
            self.expToken = self.token
            with open(path,'a',newline='') as f:
                fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow({'SITE':'ALLIKE','SIZE':f'{self.sizeweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})

        self.webhook2()

    def declined(self):
        try:
            if self.all_proxies == None:
                self.proxi = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Payment Declined', color = 15746887)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
        except:
            pass


    def webhook2(self):

        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Wating 3d Secure!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass


    def Pubblic_Webhook2(self):
        try:
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = False)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.set_thumbnail(url = self.image)    
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


    def webhook(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO SUCCESS- PAYPAL READY!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()

        except:
            pass

    
    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Success', color = 40703)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = False)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.set_thumbnail(url = self.image)    
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