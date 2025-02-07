import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, pytz
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from helheim import helheim, isChallenge
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from cryptography.hazmat.backends import default_backend
from os import urandom
from pyppeteer import launch
import asyncio

html = '''document.write("<!DOCTYPE html><html><body><form action='{}' method='POST'><input type='hidden' name='PaReq' value='{}'><input type='hidden' name='TermUrl' value='{}'><input type='hidden' name='MD' value='{}'></form><script>document.forms[0].submit()</script></body></html>")'''

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

class DELIBERTI():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
  
        try:
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'deliberti/exceptions.log')
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'deliberti/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "deliberti/proxies.txt")
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
            debug=True,
            requestPostHook=self.injection
        )

        self.link = row['LINK']
        self.size = row['SIZE']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.mail = row['MAIL']
        self.address = row['ADDRESS']
        self.housenumber = row['HOUSENUMBER']
        self.region = row['REGION'].lower()
        self.zip = row['ZIPCODE']
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.city = row['CITY']
        self.password = row['PASSWORD']
        self.cardnumber = row['CARD NUMBER']
        self.month = row['EXP MONTH']
        self.year = row['EXP YEAR']
        self.cvv = row['CVC']
        self.discord = DISCORD_ID
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        
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

        self.countryid = ''

        if self.country == 'AT':
            self.countryid = '14'
        if self.country == 'BE':
            self.countryid = '21'
        if self.country == 'BG':
            self.countryid = '33'
        if self.country == 'HR':
            self.countryid = '53'
        if self.country == 'CZ':
            self.countryid = '56'
        if self.country == 'DK':
            self.countryid = '57'
        if self.country == 'FI':
            self.countryid = '72'
        if self.country == 'FR':
            self.countryid = '73'
        if self.country == 'DE':
            self.countryid = '81'
        if self.country == 'GR':
            self.countryid = '84'
        if self.country == 'HU':
            self.countryid = '97'
        if self.country == 'IE':
            self.countryid = '103'
        if self.country == 'IT':
            self.countryid = '105'
        if self.country == 'LU':
            self.countryid = '124'
        if self.country == 'NL':
            self.countryid = '150'
        if self.country == 'PL':
            self.countryid = '170'
        if self.country == 'PT':
            self.countryid = '171'
        if self.country == 'RO':
            self.countryid = '175'
        if self.country == 'SK':
            self.countryid = '189'
        if self.country == 'SI':
            self.countryid = '190'
        if self.country == 'ES':
            self.countryid = '195'
        if self.country == 'SE':
            self.countryid = '203'
        if self.country == 'UK':
            self.countryid = '222'
        if self.country == 'US':
            self.countryid = '223'

        self.createacc()

    def bar(self):
        if machineOS.lower() == 'windows':
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running DELIBERTI | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running DELIBERTI | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

    def error(self, text):
        message = f'[TASK {self.threadID}] - [DELIBERTI] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [DELIBERTI] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [DELIBERTI] - {text}'
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

    def injection(self, session, response):
        try:
            if isChallenge(response):
                self.warn('Solving Cloudflare v2')
                return helheim('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693', session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                self.warn('Solving Cloudflare v2')
                return CF_2(session,response,key="",captcha=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.warn('Solving captcha v2')
                return CF_2(session,response,key="",captcha=True).solve() 
            elif is_fingerprint_challenge(response):
                self.warn('Solving new challange')
                return Cf_challenge_3(session,response,key="").solve()
            else:
                return response
    
    def createacc(self):
        self.warn('Creating account...')
        payload = {
            'action':'process',
            'lastname':f'{self.name} {self.surname}',
            'email_address':self.mail,
            'street_address':self.address,
            'nr_address':self.housenumber,
            'country':self.countryid,
            'city':self.city,
            'f_state':self.region.upper(),
            's_state':self.region,
            'postcode':self.zip,
            'cellulare':self.phone,
            'password':self.password,
            'confirmation':self.password,
            'newsletter':'0',
            "textarea":"""Deliberti Service srl garantisce che ogni informazione fornita a fini promozionali verr� trattata in conformit� al Decreto Lgs. 196/2003.
            Deliberti Service srl comunica inoltre che ai sensi del Decreto Lgs. 196/2003 i dati degli utenti forniti al momento della sottoscrizione dell'ordine di acquisto e/o della compilazione della fattura, sono esclusi dal consenso dell'interessato in quanto raccolti in base agli obblighi fiscali/tributari previsti dalla legge, dai regolamenti e dalla normativa comunitaria e, in ogni caso, al solo fine di adempiere agli obblighi derivanti dal contratto di acquisto cui � parte interessato e/o per l'acquisizione delle necessarie informative contrattuali sempre ed esclusivamente attivate su richiesta di quest'ultimo (Art. 24, Lett. A e B, D. LGS. 196/2003).
            In particolare Deliberti Service srl precisa che i dati personali forniti dai propri Clienti non saranno utilizzati ai fini di informazione commerciale e/o di invio di materiale pubblicitario ovvero per il compimento di ricerche di mercato o di comunicazione commerciale interattiva, se non a seguito della preventivo consenso da parte del Cliente.
            I dati sono trattati elettronicamente nel rispetto delle leggi vigenti e potranno essere esibiti soltanto su richiesta della autorit� giudiziaria ovvero di altre autorit� all'uopo autorizzate dalla legge.
            L'interessato gode dei diritti di cui all'art. 7 Decreto Lgs. 196/2003, e cio�: di chiedere conferma della esistenza presso la sede della Deliberti Service srl dei propri dati personali; di conoscere la loro origine, la logica e le finalit� del loro trattamento; di ottenere l'aggiornamento, la rettifica, e la integrazione; di chiederne la cancellazione, la trasformazione in forma anonima o il blocco in caso di trattamento illecito; di opporsi al loro trattamento per motivi legittimi o nel caso di utilizzo dei dati per invio di materiale pubblicitario, informazioni commerciali, ricerche di mercato, di vendita diretta e di comunicazione commerciale interattiva.
            L'ottenimento della cancellazione dei propri dati personali e' subordinato all'invio di una comunicazione scritta inviata tramite mail (privacy@deliberti.it o spedizione postale alla sede della societ�. Titolare alla raccolta dei dati personali � Deliberti Service srl, Via J.F. Kennedy, 5 - 80125 Napoli, nella persona del suo legale rappresentante.""",
            'accetto':'on'
        }
        while True:
            try:
                r = self.s.post(
                    'https://deliberti.it/create_account.php',
                    data = payload,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 302 and r.headers['Location'] == 'https://deliberti.it/shopping_cart.php?action=reg?uomodonna=2':
                    self.success('Succesfully created account!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Error while getting product page: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product page: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting product page: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.productScrape()

    def productScrape(self):
        self.warn('Getting product page...')
        while True:
            try:
                r = self.s.get(
                    self.link,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    soup = bs(r.text, features='lxml')
                    try:
                        self.title = soup.find('h1',{'class':'text-primary'}).text.strip().split('-')[0]
                    except:
                        self.title = 'Unkown title'
                    form = soup.find('form',{'name':'cart_quantity'})
                    prod = form.find_all('input',{'name':'products_id'})
                    label = form.find_all('label')
                    sizes = []
                    variants = []
                    for x in label:
                        sizes.append(x.text.strip())
                    for i in prod:
                        variants.append(i['value'])
                    if not variants:
                        self.warn('Product OOS, monitoring...')
                        time.sleep(self.delay)
                        continue
                    connect = zip(sizes, variants)
                    self.connect = list(connect)
                    if len(self.connect) < 1:
                        self.warn('Product OOS, monitoring...')
                        time.sleep(self.delay)
                        continue
                    else:
                        if self.size == "RANDOM":
                            self.success(f'{self.title} in stock!')
                            self.connetto = random.choice(self.connect)
                            self.variante = self.connetto[1]
                            self.sizescelta = self.connetto[0]
                            break
                        elif "," in self.size or "-" in self.size:
                            self.sizerange = []
                            try:
                                self.size1 = str(self.size.split(',')[0])
                                self.size2 = str(self.size.split(',')[1])
                            except:
                                self.size1 = str(self.size.split('-')[0])
                                self.size2 = str(self.size.split('-')[1])
                            for x in self.connect:
                                if str(self.size1) <= str(x[0]) <= str(self.size2):
                                    self.sizerange.append(x[0])
                            if len(self.sizerange) < 1:
                                self.warn(f'{self.title} size {self.size} OOS, monitoring...')
                                time.sleep(self.delay)
                                continue
                            else:
                                self.sizerandom = random.choice(self.sizerange)
                                self.success(f'{self.title} size {self.sizerandom} in stock!')
                                for i in self.connect:
                                    if self.sizerandom in i[0]:
                                        self.variante = i[1]
                                        self.sizescelta = i[0]
                                break
                        else:
                            for element in self.connect:
                                if self.size == element[2]:
                                    self.success(f'{self.title} size {self.size} in stock!')
                                    self.variante = element[1]
                                    self.sizescelta = element[0]
                            break
                elif r.status_code >= 500 and r.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Error while getting product page: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product page: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting product page: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.atc()

    def atc(self):
        self.warn('Adding to cart...')
        head = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.s.headers.update(head)
        payload = {'products_id': self.variante}
        self.link = self.link.split('?')[0]
        while True:
            try:
                r = self.s.post(
                    f'{self.link}?action=add_product&uomodonna=1',
                    data = payload,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 302 and r.headers['Location'] == f'{self.link}?act=tocart&uomodonna=1':
                    self.success('Succesfully added to cart!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Error while adding to cart: {r.status_code}, retrying...')
                    self.build_proxy()
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
        self.checkout()
    
    def checkout(self):
        self.warn('Getting checkout page...')
        while True:
            try:
                r = self.s.get(
                    'https://deliberti.it/checkout.php#payment',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    cookies = []
                    for c in self.s.cookies:
                        print(c)
                        _cookie = {}
                        _cookie['domain'] = c.domain
                        _cookie['name'] = c.name
                        _cookie['value'] = c.value
                        _cookie['path'] = c.path
                        if c.domain[0] == '.':
                            _cookie['url'] = f'https://{c.domain[1:]}'
                        else:
                            _cookie['url'] = f'https://{c.domain}'
                        cookies.append(_cookie)
                    self.dumped = json.dumps(cookies)
                    print(self.dumped)
                    if 'bancasella" CHECKED' in r.text:
                        self.success('Succesfully got checkout page...')
                        break
                    else:
                        self.error('Failed getting checkout page, retrying...')
                        self.build_proxy()
                        continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Error while getting chechkout page: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting chechkout page: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting checkout page: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        asyncio.run(self.main3d())
    
    #def payment(self):
    #    payload = {
    #        'payment': 'mypaypal'
    #    }
    #    self.warn('Submitting payment...')
    #    while True:
    #        try:
    #            r = self.s.post(
    #                'https://deliberti.it/checkout.php',
    #                data = payload,
    #                timeout = self.timeout
    #            )
    #            if r.status_code == 200:
    #                self.check = r.text.split('mypaypal" CHECKED')
    #                self.tcode = r.text.split('id="tcode" value="')[1].split('"')[0]
    #                print(self.tcode)
    #                self.success('Succesfully submitted payment!')
    #                break
    #            elif r.status_code >= 500 and r.status_code <= 600:
    #                time.sleep(self.delay)
    #                self.warn('Site is dead, retrying...')
    #                continue
    #            elif r.status_code == 403:
    #                self.error('Access denied on atc, retrying...')
    #                self.build_proxy()
    #                continue
    #            elif r.status_code== 429:
    #                self.error('Rate limit, retrying...')
    #                self.build_proxy()
    #                continue
    #            else:
    #                error(f'Error while submitting payment: {r.status_code}, retrying...')
    #                self.build_proxy()
    #                continue
    #        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    #            self.error('Connection error, retrying...')
    #            self.build_proxy()
    #            continue
    #        except Exception as e:
    #            self.error(f'Exception submitting payment: {e.__class__.__name__}, retrying...')
    #            open(self.logs_path, 'a+').write(f'Exception submitting payment: {e}\n')
    #            self.build_proxy()
    #            time.sleep(self.delay)
    #            continue
    #    self.payment()

    #def paypal(self):
    #    payload = {
    #        'comments':'',	
    #        'tcode': self.tcode
    #    }
    #    self.warn('Opening paypal...')
    #    while True:
    #        try:
    #            r = self.s.post(
    #                'https://deliberti.it/checkout_to_paypal.php?uomodonna=2',
    #                data = payload,
    #                timeout = self.timeout
    #            )
    #            if r.status_code == 200:
    #                print(r.text)
    #                print(r.url)
    #                break
    #            elif r.status_code >= 500 and r.status_code <= 600:
    #                time.sleep(self.delay)
    #                self.warn('Site is dead, retrying...')
    #                continue
    #            elif r.status_code == 403:
    #                self.error('Access denied on atc, retrying...')
    #                self.build_proxy()
    #                continue
    #            elif r.status_code== 429:
    #                self.error('Rate limit, retrying...')
    #                self.build_proxy()
    #                continue
    #            else:
    #                error(f'Error while opening paypal: {r.status_code}, retrying...')
    #                self.build_proxy()
    #                continue
    #        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    #            self.error('Connection error, retrying...')
    #            self.build_proxy()
    #            continue
    #        except Exception as e:
    #            self.error(f'Exception opening paypal: {e.__class__.__name__}, retrying...')
    #            open(self.logs_path, 'a+').write(f'Exception opening paypal: {e}\n')
    #            self.build_proxy()
    #            time.sleep(self.delay)
    #            continue
    def payment(self):
        payload = {
            'comments':'',
            'tcode':'JFKHYT2JKVUDQOJXPEXSQWL4OE======'
        }
        self.warn('Submitting payment...')
        while True:
            try:
                r = self.s.post(
                    'https://deliberti.it/checkout_to_bank.php?uomodonna=2',
                    data = payload,
                    timeout = 15
                )
                if r.status_code == 200:
                    print(r.status_code)
                    for c in self.s.cookies:
                        print(c)
                        _cookie = {}
                        _cookie['domain'] = c.domain
                        _cookie['name'] = c.name
                        _cookie['value'] = c.value
                        _cookie['path'] = c.get('path', '/')
                        if c.domain[0] == '.':
                            _cookie['url'] = f'https://{c.domain[1:]}'
                        else:
                            _cookie['url'] = f'https://{c.domain}'
                        cookies.append(_cookie)
                    self.dumped = json.dumps(cookies).decode()
                    print(self.dumped)
                    self.success('Succesfully submitted payment!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    time.sleep(self.delay)
                    self.warn('Site is dead, retrying...')
                    continue
                elif r.status_code == 403:
                    self.error('Access denied on atc, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code== 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                else:
                    error(f'Error while submitting payment: {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting payment: {e}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting payment: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        asyncio.run(self.main3d())
    
    async def main3d(self):

        self.warn("Waiting for 3D secure..")

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
            self.dumped = json.loads(self.dumped)
            await page.setCookie(*self.dumped)
            await page.setRequestInterception(True)
            self._3dsAccepted = False
            self._3dsCancelled = False

            #webhook = await send_3ds_webhook(
            #    f'New Balance {self.country.upper()}',
            #    self.pid,
            #    self.chosenSize['displaySize'],
            #    self.webhookPrice,
            #    self._email,
            #    self.task_name,
            #    mode=self.mode,
            #    description=f'Solve 3DS on browser',
            #    thumbnail=self.image
            #)

            async def intercept(request):
                if 'ciao' in request.url:
                    self._3dsAccepted = True
                    self.threeddata = request._postData
                    self.threedheaders = request._headers
                    self.threedurl = request.url
                    await request.abort()
                    await chrome.close()
                    return True
                else:
                    self._3dsAccepted = False
                    await request.continue_()

            page.on('request', lambda req: asyncio.ensure_future(intercept(req)))
            script = html.format(self.postURL, self.pareq, self.termurl, self.MD)
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
                await asyncio.sleep(storage.delay)

        except Exception as e:
            self.error(f"Exception while handling 3DS: {e}")
            return False

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
                    writer.writerow({'SITE':'DELIBERTI','SIZE':f'{self.sizescelta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'DELIBERTI','SIZE':f'{self.sizescelta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            print(self.expToken)
        except Exception as e: 
            self.error(f'Exception while passing cookies: {e}, retrying...') 
            time.sleep(self.delay)
            self.selenium()