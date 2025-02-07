import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, pytz
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from cryptography.hazmat.backends import default_backend
from os import urandom
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
failed = 0
carted = 0

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

class BSTN():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
  
        try:
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'bstn/exceptions.log')
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'bstn/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "bstn/proxies.txt")
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
            requestPostHook=self.injection
        )
        helheim.wokou(self.s)
        self.link = row['LINK']
        self.size = row['SIZE']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.mail = row['MAIL']
        self.address = row['ADDRESS']
        self.housenumber = row['HOUSENUMBER']
        self.region = row['REGION']
        self.zip = row['ZIPCODE']
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.city = row['CITY']
        self.payment = row['PAYMENT']
        self.cardnumber = row['CARD NUMBER']
        self.month = row['EXP MONTH']
        self.year = row['EXP YEAR']
        self.cvv = row['CVC']
        self.discord = DISCORD_ID
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        
        if '/p/' in self.link:
            self.paeselink = 'eu_en'
        else:
            self.paeselink = self.link.split('bstn')[1].split('/')[1].split('/')[0]

        self.delay = int(config['delay'])
        self.webhook_url = webhook
        self.version = version
        self.threadID = '%03d' % i
        self.build_proxy()
        self.balance = balancefunc()
        self.bar()
        self.timeout = 120
        
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

        self.productScrape()

    def bar(self):
        if machineOS.lower() == 'windows':
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running BSTN | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running BSTN | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [BSTN] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [BSTN] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [BSTN] - {text}'
        warn(message)

    def build_proxy(self):
        cookies = self.s.cookies
        try:
            kasada = self.s.kasada
        except:
            pass
        self.s = cloudscraper.create_scraper(
            captcha=self.captcha,
            browser={
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
            },
            requestPostHook=self.injection
        )
        helheim.wokou(self.s)
        self.s.cookies = cookies
        try:
            self.s.kasada = kasada
        except:
            pass
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

    def injection(self, session, response):
        #try:
        if helheim.isChallenge(session, response):
            self.warn('Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response
        #except:
        #    if session.is_New_IUAM_Challenge(response):
        #        self.warn('Solving Cloudflare v2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False).solve() 
        #    elif session.is_New_Captcha_Challenge(response):
        #        self.warn('Solving captcha v2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True).solve() 
        #    elif is_fingerprint_challenge(response):
        #        self.warn('Solving new challange')
        #        return Cf_challenge_3(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b").solve()
        #    else:
        #        return response

    def remove_line(self, line):
        return line[:line.rfind('\n')]

    def productScrape(self):
        self.warn('Getting product...')
        while True:
            try:
                prod = self.s.get(
                    self.link,
                    timeout = self.timeout
                )
                if prod.status_code == 200:
                    if 'upcoming-release__date-attributes' in prod.text:
                        self.warn('Product not released yet, retrying...')
                        time.sleep(self.delay)
                        continue
                    else:
                        try:
                            self.title = prod.text.split('product-title"> ')[1].split('<')[0]
                        except:
                            time.sleep(self.delay)
                            print('a')
                            continue
                        soup = bs(prod.text, features='lxml')
                        try:
                            self.img = soup.find('div',{'class':'product-page__gallery'}).find('div',{'class':'row'}).find('img',{'class':'lazyload bstn-zoomable'})['src']
                        except:
                            self.img = ''
                        wtf = str(soup.find('div',{'class':'product-add-form'}))
                        self.atc2link = wtf.split('form action="')[1].split('"')[0]
                        self.hot = prod.text.split('is_hot" value="')[1].split('"')[0]
                        self.oldprice = prod.text.split('item_old_price" value="')[1].split('"')[0]
                        self.price = prod.text.split('item_price" value="')[1].split('"')[0]
                        self.formkey = soup.find('div',{'class':'product-add-form'}).find('form',{'method':'post'}).find('input',{'name':'form_key'})['value']
                        self.s.cookies['form_key'] = re.search(
                            r'''"formKey":"(?P<formkey>\w+)"''',
                            prod.text,
                            re.S | re.M
                        ).groupdict()['formkey']
                        try:
                            r_json = prod.text.split('"[data-role=swatch-options]": ')[1].split('"*"')[0]
                        except:
                            self.warn('Product oos, retrying...')
                            time.sleep(self.delay)
                            continue
                        r_json = json.loads(self.remove_line(r_json)[:-1])
                        euiddd = r_json['Magento_Swatches/js/swatch-renderer']['jsonConfig']['attributes']['203']['options']
                        usiddd = r_json['Magento_Swatches/js/swatch-renderer']['jsonConfig']['attributes']['205']['options']
                        ukiddd = r_json['Magento_Swatches/js/swatch-renderer']['jsonConfig']['attributes']['204']['options']
                        saiz = []
                        idd = []
                        codicepiddaconfront = []
                        iddeu = []
                        idduk = []
                        for i in usiddd:
                            saiz.append(i['label'].replace(',','.'))
                            idd.append(i['id'])
                            codicepiddaconfront.append(i['products'][0])
                        sizeweb= []
                        for m in saiz:
                            if '.0' in m:
                                sizeweb.append(m.split('.0')[0])
                            else:
                                sizeweb.append(m)
                        for b in euiddd:
                            iddeu.append(b['id'])
                        for o in ukiddd:
                            idduk.append(o['id'])
                        tot = zip(sizeweb, idd, iddeu, idduk, codicepiddaconfront)
                        connecto = list(tot)
                        connect = []
                        for i in connecto:
                            stock = r_json['Magento_Swatches/js/swatch-renderer']['jsonConfig']['stock'][i[4]]
                            if stock != 0:
                                connect.append(i)
                        if self.size == "RANDOM":
                            scelta = random.choice(connect)
                            s0 = scelta[0]
                            s1 = scelta[1]
                            s2 = scelta[2]
                            s3 = scelta[3]
                            s4 = scelta[4]
                            self.sizwebb = "".join(s0)
                            self.idus = "".join(s1)
                            self.ideu = "".join(s2)
                            self.iduk = "".join(s3)
                            self.produc = "".join(s4)
                            self.success(f'{self.title} size {self.sizwebb} in stock!')
                            break
                        elif "," in self.size or "-" in self.size:
                            self.sizerange = []
                            try:
                                self.size1 = str(self.size.split(',')[0])
                                self.size2 = str(self.size.split(',')[1])
                            except:
                                self.size1 = str(self.size.split('-')[0])
                                self.size2 = str(self.size.split('-')[1])
                            for x in sizeweb:
                                if float(self.size1) <= float(x) <= float(self.size2):
                                    self.sizerange.append(x)

                            if len(self.sizerange) < 1:
                                self.warn(f'{self.title} OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                            else:
                                self.sizerandom = random.choice(self.sizerange)
                                for i in connect:
                                    if self.sizerandom == i[0]:
                                        s0 = i[0]
                                        s1 = i[1]
                                        s2 = i[2]
                                        s3 = i[3]
                                        s4 = i[4]
                                        self.sizwebb = "".join(s0)
                                        self.idus = "".join(s1)
                                        self.ideu = "".join(s2)
                                        self.iduk = "".join(s3)
                                        self.produc = "".join(s4)
                                self.success(f'{self.title} size {self.sizwebb} in stock!')
                                break
                        else:
                            try:
                                for element in connect:
                                    if self.size == element[0]:    
                                        s0 = element[0]
                                        s1 = element[1]
                                        s2 = element[2]
                                        s3 = element[3]
                                        s4 = element[4]
                                        self.sizwebb = "".join(s0)
                                        self.idus = "".join(s1)
                                        self.ideu = "".join(s2)
                                        self.iduk = "".join(s3)
                                        self.produc = "".join(s4)
                                self.success(f'{self.title} size {self.sizwebb} in stock!')
                                break
                            except:
                                self.warn(f'{self.title} OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                elif prod.status_code >= 500 and prod.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif prod.status_code == 404:
                    self.warn('Product paged pulled')
                    time.sleep(self.delay)
                    continue
                elif prod.status_code == 429 or prod.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Failed getting product: {prod.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting product: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.ATC()

    def ATC(self):
        global failed, checkoutnum, carted
        self.oosduringatc = False
        while True:
            try:
                try:
                    payload = {
                        'product': self.produc,
                        'is_hot':self.hot,
                        'selected_configurable_option': '',
                        'related_product': '',
                        'item': self.produc,
                        'alert_type': '',
                        'item_old_price':self.oldprice,
                        'item_price':self.price,
                        'form_key': self.s.cookies['form_key'],
                        'super_attribute[203]': self.ideu,
                        'super_attribute[205]': self.idus,
                        'super_attribute[204]': self.iduk,
                        'qty': '1',
                        'product_page': 'true'
                    }
                except:
                    print('a')
                    payload = {
                        'product': self.produc,
                        'is_hot':self.hot,
                        'selected_configurable_option': '',
                        'related_product': '',
                        'item': self.produc,
                        'alert_type': '',
                        'item_old_price':self.oldprice,
                        'item_price':self.price,
                        'form_key': self.formkey,
                        'super_attribute[203]': self.ideu,
                        'super_attribute[205]': self.idus,
                        'super_attribute[204]': self.iduk,
                        'qty': '1',
                        'product_page': 'true'
                    }
                print(self.s.cookies)
                cartPost = self.s.post(
                    f'https://www.bstn.com/{self.paeselink}/amasty_cart/cart/add/', 
                    data = payload, 
                    headers = {'referer': self.link,'X-Requested-With': 'XMLHttpRequest','Accept': 'application/json, text/javascript, */*; q=0.01'},
                    timeout = self.timeout
                )
                if cartPost.status_code == 200:
                    try:
                        r_json = json.loads(r.text)
                        print(r_json)
                        self.success('Added to cart!')
                        carted = carted + 1
                        self.bar()
                        break
                    except:
                        self.error('Failed adding to cart, restarting...')
                        self.s.cookies.clear()
                        self.build_proxy()
                        self.oosduringatc = True
                        break
                elif cartPost.status_code >= 500 and cartPost.status_code <= 600:
                    self.warn('Site is overcrowded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif cartPost.status_code == 403:
                    self.error('Proxy banned on atc, retrying...')
                    self.build_proxy()
                    continue
                elif cartPost.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                elif cartPost.status_code == 401:
                    self.error('Bad request, rotating proxy...')
                    self.build_proxy()
                    continue
                elif cartPost.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    self.oosduringatc = True
                    break
                else:
                    self.error(f'Unexpected error {cartPost.status_code} during atc, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception adding to cart: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception adding to cart: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if self.oosduringatc:
            self.productScrape()
        else:
            self.getcheckoutpage()

    def getcheckoutpage(self):
        self.warn('Getting checkout page...')
        while True:
            try:
                shippingget = self.s.get(
                    f'https://www.bstn.com/{self.paeselink}/checkout/',
                    timeout = self.timeout
                )
                if shippingget.status_code == 200:
                    print(shippingget.text)
                    try:
                        self.agree = shippingget.text.split('agreementId":"')[1].split('"')[0]
                    except:
                        time.sleep(self.delay)
                        print('a')
                        continue
                    self.entity = shippingget.text.split('entity_id":"')[1].split('"')[0]
                    self.success('Succesfully got checkout page!')
                    break
                elif shippingget.status_code >= 500 and shippingget.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif shippingget.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif shippingget.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                elif shippingget.status_code == 401:
                    self.error('Bad request, rotating proxy...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Error while getting checkout page: {shippingget.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting checkout page: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting checkout page: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.rates()

    def rates(self):
        payload = {"address":{"street":[self.address],"city":self.city,"region":self.region,"country_id":self.country,"postcode":self.zip,"firstname":self.name,"lastname":self.surname,"company":"","telephone":self.phone,"custom_attributes":[{"attribute_code":"gender","value":"3"}]}}
        try:
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
        except:
            pass
        self.warn('Getting shipping rates...')
        while True:
            try:
                addressPost = self.s.post(
                    f'https://www.bstn.com/{self.paeselink}/rest/{self.paeselink}/V1/guest-carts/{self.entity}/estimate-shipping-methods', 
                    json = payload, 
                    headers = headers,
                    timeout = self.timeout
                )
                if addressPost.status_code == 200:
                    try:
                        self.carrier_code = addressPost.text.split('carrier_code":"')[1].split('"')[0]
                    except:
                        time.sleep(self.delay)
                        print('a')
                        continue
                    self.method_code = addressPost.text.split('method_code":"')[1].split('"')[0]
                    self.success('Succesfully got shipping rates!')
                    break
                elif addressPost.status_code >= 500 and addressPost.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif addressPost.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif addressPost.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unexpected error while getting shipping rates: {addressPost.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting shipping rates: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception while getting shipping rates: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue 
        self.ship()

    def ship(self):
        try:
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
        except:
            pass
        payload = {"addressInformation":{"shipping_address":{"countryId":self.country,"region":self.region,"street":[self.address,self.housenumber],"company":"","telephone":self.phone,"postcode":self.zip,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":[{"attribute_code":"gender","value":"3"}],"extension_attributes":{"gender":"3"}},"billing_address":{"countryId":self.country,"region":self.region,"street":[self.address],"company":"","telephone":self.phone,"postcode":self.zip,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":[{"attribute_code":"gender","value":"3"}],"saveInAddressBook":None},"shipping_method_code":self.method_code,"shipping_carrier_code":self.carrier_code,"extension_attributes":{}}}
        self.warn('Submitting ship...')
        while True:
            try:
                addressPost = self.s.post(
                    f'https://www.bstn.com/{self.paeselink}/rest/{self.paeselink}/V1/guest-carts/{self.entity}/shipping-information', 
                    json = payload, 
                    headers = headers,
                    timeout = self.timeout
                )
                if addressPost.status_code == 200:
                    self.success(f'Succesfully submitted ship!')
                    break

                elif addressPost.status_code >= 500 and addressPost.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif addressPost.status_code == 403:
                    self.error(f'Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif addressPost.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unexpected error while submitting ship {addressPost.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting ship: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception while submitting ship: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue 
        if self.payment == 'CC':
            self.cc2()
        elif self.payment == 'SOFORT':
            self.sofort()
        else:
            self.pp()

    def pp(self):
        global failed, checkoutnum, carted
        payload = {"cartId":self.entity,"paymentMethod":{"method":"paypal_express","po_number":None,"additional_data":None,"extension_attributes":{"agreement_ids":["4"]}},"email":self.mail,"billingAddress":{"countryId":self.country,"regionCode":"","region":self.region,"street":[self.address,self.housenumber],"company":"","telephone":self.phone,"postcode":self.zip,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":[{"attribute_code":"gender","value":"3"}],"extension_attributes":{"gender":"3"},"saveInAddressBook":None}}
        try:
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
        except:
            pass
        self.warn('Opening paypal...')
        while True:
            try:
                addressPost = self.s.post(
                    f'https://www.bstn.com/{self.paeselink}/rest/{self.paeselink}/V1/guest-carts/{self.entity}/set-payment-information', 
                    json = payload, 
                    headers = headers,
                    timeout = self.timeout
                )
                if addressPost.status_code == 200:
                    x = self.s.get(
                        f'https://www.bstn.com/{self.paeselink}/paypal/express/start/', 
                        allow_redirects = False,
                        timeout = self.timeout
                    )
                    try:
                        self.ppurl = x.headers['Location']
                    except:
                        time.sleep(self.delay)
                        print('a')
                        continue
                    self.success('Successfully checked out!')
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break
                elif addressPost.status_code >= 500 and addressPost.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif addressPost.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif addressPost.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unexpected error while getting paypal {addressPost.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting paypal: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception while getting paypal: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.selenium()

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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
        return encryptedAesData

    def cc2(self):
        self.warn('Submitting cc info...')
        self.declined = False
        global failed, checkoutnum, carted
        cardtype = identify_card_type(self.cardnumber)
        if cardtype == "MasterCard":
            card_type = "MC"
        elif cardtype == "Visa":
            card_type = "VI"
        payload = {"cartId":f"{self.entity}","billingAddress":{"countryId":f"{self.country}","region":f"{self.region}","street":[f"{self.address}",f"{self.housenumber}"],"company":"","telephone":f"{self.phone}","postcode":f"{self.zip}","city":f"{self.city}","firstname":f"{self.name}","lastname":f"{self.surname}","customAttributes":[{"attribute_code":"gender","value":"3"}],"saveInAddressBook":None},"paymentMethod":{"method":"adyen_cc","additional_data":{"guestEmail":f"{self.mail}","cc_type":f"{card_type}","number":self.maincard(pan = self.cardnumber, key = "10001|C621C7E8267CF5A0758EC2E0530AF2B59625EFA2A26174690B401476BA5FF1AD079D881838CD625384D546DAB4E82CF1E414F1F2C7EB5420AFD9F8FF516479FD2F7EDA66572BB9C08672961C8BF528FFD0B1951B29C2332FBF301A96BA1D41DA28F39718095222C4CCFF0C0BCAECDEF944D2994D45FB81FE210090B46E5BE22CCCBAC4F413C08F90229D0E9096046BDB6745E5C549A7FEDC907646661C79A0A14ECE4EA351A07832D7228AA8D3398874D173076E475196E1DFBF35E0FDA83C047DED0156D6839D67DF1DC0D00509E8876DF209169832607B3FAE834F0DD8E78123A991E50EFD485740622FBE3EAAE6FA33BEE2DDA42465DA36D468500AF7BD01"),"cvc": self.maincvv(cvc = self.cvv, key = "10001|C621C7E8267CF5A0758EC2E0530AF2B59625EFA2A26174690B401476BA5FF1AD079D881838CD625384D546DAB4E82CF1E414F1F2C7EB5420AFD9F8FF516479FD2F7EDA66572BB9C08672961C8BF528FFD0B1951B29C2332FBF301A96BA1D41DA28F39718095222C4CCFF0C0BCAECDEF944D2994D45FB81FE210090B46E5BE22CCCBAC4F413C08F90229D0E9096046BDB6745E5C549A7FEDC907646661C79A0A14ECE4EA351A07832D7228AA8D3398874D173076E475196E1DFBF35E0FDA83C047DED0156D6839D67DF1DC0D00509E8876DF209169832607B3FAE834F0DD8E78123A991E50EFD485740622FBE3EAAE6FA33BEE2DDA42465DA36D468500AF7BD01"),"expiryMonth":self.mainmonth(expiry_month = self.month, key = "10001|C621C7E8267CF5A0758EC2E0530AF2B59625EFA2A26174690B401476BA5FF1AD079D881838CD625384D546DAB4E82CF1E414F1F2C7EB5420AFD9F8FF516479FD2F7EDA66572BB9C08672961C8BF528FFD0B1951B29C2332FBF301A96BA1D41DA28F39718095222C4CCFF0C0BCAECDEF944D2994D45FB81FE210090B46E5BE22CCCBAC4F413C08F90229D0E9096046BDB6745E5C549A7FEDC907646661C79A0A14ECE4EA351A07832D7228AA8D3398874D173076E475196E1DFBF35E0FDA83C047DED0156D6839D67DF1DC0D00509E8876DF209169832607B3FAE834F0DD8E78123A991E50EFD485740622FBE3EAAE6FA33BEE2DDA42465DA36D468500AF7BD01"),"expiryYear":self.mainyear(expiry_year = self.year, key = "10001|C621C7E8267CF5A0758EC2E0530AF2B59625EFA2A26174690B401476BA5FF1AD079D881838CD625384D546DAB4E82CF1E414F1F2C7EB5420AFD9F8FF516479FD2F7EDA66572BB9C08672961C8BF528FFD0B1951B29C2332FBF301A96BA1D41DA28F39718095222C4CCFF0C0BCAECDEF944D2994D45FB81FE210090B46E5BE22CCCBAC4F413C08F90229D0E9096046BDB6745E5C549A7FEDC907646661C79A0A14ECE4EA351A07832D7228AA8D3398874D173076E475196E1DFBF35E0FDA83C047DED0156D6839D67DF1DC0D00509E8876DF209169832607B3FAE834F0DD8E78123A991E50EFD485740622FBE3EAAE6FA33BEE2DDA42465DA36D468500AF7BD01"),"holderName":f"{self.name} {self.surname}","store_cc":False,"number_of_installments":"","java_enabled":False,"screen_color_depth":24,"screen_width":1920,"screen_height":1080,"timezone_offset":-60,"language":"en","combo_card_type":"credit"},"extension_attributes":{"agreement_ids":[f"{self.agree}"]}},"email":f"{self.mail}"}
        try:
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            self.s.headers.update(headers)
        except:
            pass
        while True:
            try:
                addressPost = self.s.post(
                    f'https://www.bstn.com/{self.paeselink}/rest/{self.paeselink}/V1/guest-carts/{self.entity}/payment-information', 
                    json = payload, 
                    timeout = self.timeout
                )

                if addressPost.status_code == 200:
                    break
                elif addressPost.status_code == 400:
                    self.declined = True
                    self.error('Payment declined!')
                    try:
                        r_json = json.loads(addressPost.text)
                        self.msg = r_json['message']
                    except:
                        self.msg = 'Unkown Error'
                    break
                elif addressPost.status_code in (500, 600):
                    self.warn('Site is overcrowded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif addressPost.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif addressPost.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unexpected error while submitting cc {addressPost.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting cc: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception while submitting cc: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if self.declined:
            self.decl()
        else:
            self.tred()

    def tred(self):
        try:
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            self.s.headers.update(headers)
        except:
            pass
        self.warn('Processing payment...')
        while True:
            try:
                r = self.s.get(
                    f'https://www.bstn.com/{self.paeselink}/adyen/process/redirect/',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    if 'PaReq' in r.text:
                        pareq = r.text.split('PaReq" value="')[1].split('"')[0]
                        urlpo = r.text.split('POST" action="')[1].split('"')[0]
                        md = r.text.split('MD" value="')[1].split('"')[0]
                        termur = r.text.split('TermUrl" value="')[1].split('"')[0]
                        payload = {
                            'PaReq':pareq,
                            'MD':md,
                            'TermUrl':termur
                        }
                        x = self.s.post(urlpo, headers = headers, data = payload)
                        self.warn('Getting 3d secure...')
                        if 'token:' in x.text:
                            revtoken = x.text.split('token: "')[1].split('"')[0]
                            payload2 = {"transToken": revtoken}
                            k = self.s.post(
                                "https://poll.touchtechpayments.com/poll", 
                                headers = headers, 
                                json = payload2,
                                timeout = self.timeout
                            )
                            while "pending" in k.text:
                                self.warn('Waiting 3d secure...')
                                time.sleep(5)
                                k = self.s.post(
                                    "https://poll.touchtechpayments.com/poll", 
                                    headers = headers, 
                                    json = payload2,
                                    timeout = self.timeout
                                )
                            if "success" in k.text:
                                r_json = json.loads(k.text)
                                authToken = r_json['authToken']
                            payload = {
                                "transToken": revtoken,
                                "authToken": authToken
                            }
                            r = self.s.post(
                                "https://macs.touchtechpayments.com/v1/confirmTransaction", 
                                headers = headers, 
                                json = payload,
                                timeout = self.timeout
                            )
                            r_json = json.loads(r.text)
                            pares = r_json['Response']
                            payload = {
                                "MD":md,
                                "PaRes":pares
                            }
                            try:
                                headers = {
                                    'content-type': 'application/x-www-form-urlencoded',
                                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
                                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                                    'sec-fetch-site': 'cross-site',
                                    'sec-fetch-mode': 'navigate',
                                    'sec-fetch-dest': 'document',
                                    'referer': 'https://verifiedbyvisa.acs.touchtechpayments.com/',
                                    'accept-encoding': 'gzip, deflate',
                                    'accept-language': 'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
                                }
                                self.s.headers.update(headers)
                            except:
                                pass
                            z = self.s.post(
                                f'https://www.bstn.com/{self.paeselink}/adyen/transparent/redirect/', 
                                data = payload,
                                timeout = self.timeout
                            )
                            if z.status_code == 200:
                                try:
                                    headers = {
                                        'content-type': 'application/x-www-form-urlencoded',
                                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
                                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                                        'sec-fetch-site': 'cross-site',
                                        'sec-fetch-mode': 'navigate',
                                        'sec-fetch-dest': 'document',
                                        'referer': 'https://verifiedbyvisa.acs.touchtechpayments.com/',
                                        'accept-encoding': 'gzip, deflate',
                                        'accept-language': 'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
                                    }
                                    self.s.headers.update(headers)
                                except:
                                    pass
                                b = self.s.post(
                                    f'https://www.bstn.com/{self.paeselink}/adyen/process/redirect/', 
                                    data = payload,
                                    timeout = self.timeout
                                )
                                if 'success' in b.url:
                                    self.success('Succesfully checked out!')
                                    checkoutnum = checkoutnum + 1
                                    self.bar()
                                    break
                        else:
                            pares = x.text.split('var pares = "')[1].split('"')[0]
                            payload = {
                                "MD":md,
                                "PaRes":pares
                            }
                            try:
                                headers = {
                                    'content-type': 'application/x-www-form-urlencoded',
                                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
                                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                                    'sec-fetch-site': 'cross-site',
                                    'sec-fetch-mode': 'navigate',
                                    'sec-fetch-dest': 'document',
                                    'referer': 'https://verifiedbyvisa.acs.touchtechpayments.com/',
                                    'accept-encoding': 'gzip, deflate',
                                    'accept-language': 'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
                                }
                                self.s.headers.update(headers)
                            except:
                                pass
                            z = self.s.post(
                                f'https://www.bstn.com/{self.paeselink}/adyen/transparent/redirect/', 
                                data = payload,
                                tiemout = self.timeout
                            )
                            if z.status_code == 200:
                                try:
                                    headers = {
                                        'content-type': 'application/x-www-form-urlencoded',
                                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
                                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                                        'sec-fetch-site': 'cross-site',
                                        'sec-fetch-mode': 'navigate',
                                        'sec-fetch-dest': 'document',
                                        'referer': 'https://verifiedbyvisa.acs.touchtechpayments.com/',
                                        'accept-encoding': 'gzip, deflate',
                                        'accept-language': 'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
                                    }
                                    self.s.headers.update(headers)
                                except:
                                    pass
                                b = self.s.post(
                                    f'https://www.bstn.com/{self.paeselink}/adyen/process/redirect/', 
                                    data = payload,
                                    timeout = self.timeout
                                )
                                if 'success' in b.url:
                                    self.success('Succesfully checked out!')
                                    checkoutnum = checkoutnum + 1
                                    self.bar()
                                    break
                elif r.status_code in (500, 600):
                    self.warn('Site is down, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Access denied, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unexpected error while processing payment {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while processing payment: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception while processing payment: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.SuccessCC()
    
    def sofort(self):
        global failed, checkoutnum, carted
        self.warn('Submitting Sofort payment...')
        payload = {
            "cartId": self.entity,
            "billingAddress": {
                "countryId": self.country,
                "regionCode": "",
                "region": "",
                "street": [f"{self.address}", f"{self.housenumber}"],
                "company": "",
                "telephone": "",
                "postcode": self.zip,
                "city": self.city,
                "firstname": self.name,
                "lastname": self.surname,
                "customAttributes": [{
                    "attribute_code": "gender",
                    "value": "3"
                }],
                "extension_attributes": {
                    "gender": "3"
                },
                "saveInAddressBook": None
            },
            "paymentMethod": {
                "method": "adyen_hpp",
                "additional_data": {
                    "brand_code": "directEbanking"
                },
                "extension_attributes": {
                    "agreement_ids": [self.agree]
                }
            },
            "email": self.mail
        }
        try:
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            self.s.headers.update(headers)
        except:
            pass
        while True:
            try:
                r = self.s.post(
                    f'https://www.bstn.com/eu_it/rest/{self.paeselink}/V1/guest-carts/{self.entity}/payment-information', 
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    headers={
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json, text/javascript, */*; q=0.01'
                    }
                    self.s.headers.update(headers)
                    x = self.s.get(f'https://www.bstn.com/{self.paeselink}/adyen/process/redirect/', allow_redirects = True)
                    if x.status_code == 200:
                        self.ppurl = x.text.split('window.location.replace("')[1].split('")')[0].replace('\\u003A',':').replace('\\u002F','/').replace('\\u003F','?').replace('\\u0026','&').replace('\\u003D','=').replace('\\u002A','*').replace('\\u002D','-')
                        self.success('Succesfully checked out!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        break
                    else:
                        self.error(f'Unexpected error while getting sofort {x.status_code}, retrying...')
                        self.build_proxy()
                        continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Unexpected error while getting sofort {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while getting sofort: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception while getting sofort: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.selenium()

    def selenium(self):
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
                    writer.writerow({'SITE':'BSTN','SIZE':f'{self.sizwebb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'BSTN','SIZE':f'{self.sizwebb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            if self.payment == 'SOFORT':
                self.SuccessSofort()
            else:
                self.SuccessPP()
        except Exception as e: 
            self.error(f'Exception while passing cookies: {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.selenium()

    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url =random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**BSTN**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizwebb, inline = True)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = False)
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
            embed.add_embed_field(name=f'**BSTN**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizwebb, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = False) 
            embed.add_embed_field(name='EMAIL', value = f"||{self.mail}||", inline = True) 
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.img) 
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()

        except:
            pass

    def Pubblic_WebhookCC(self):
        try:
            webhook = DiscordWebhook(url =random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**BSTN**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizwebb, inline = True)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = False)
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

    def SuccessCC(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', color = 4437377)
            embed.add_embed_field(name=f'**BSTN**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizwebb, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = False) 
            embed.add_embed_field(name='EMAIL', value = f"||{self.mail}||", inline = True) 
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.set_thumbnail(url = self.img) 
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_WebhookCC()

        except:
            pass

    def decl(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Payment declined!', color = 15746887)
            embed.add_embed_field(name=f'**BSTN**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizwebb, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = False) 
            embed.add_embed_field(name='EMAIL', value = f"||{self.mail}||", inline = True)
            embed.add_embed_field(name='MESSAGE', value = f"||{self.msg}||", inline = False)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.set_thumbnail(url = self.img)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()

        except:
            pass

    def Pubblic_Webhook3(self):
        try:
            webhook = DiscordWebhook(url =random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**BSTN**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizwebb, inline = True)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Sofort', inline = False)
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

    def SuccessSofort(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**BSTN**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizwebb, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Sofort', inline = False) 
            embed.add_embed_field(name='EMAIL', value = f"||{self.mail}||", inline = True) 
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.img) 
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook3()

        except:
            pass