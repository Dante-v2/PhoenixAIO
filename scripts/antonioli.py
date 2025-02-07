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
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')


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

class ANTONIOLI():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
  
        try:
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'antonioli/exceptions.log')
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'antonioli/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "antonioli/proxies.txt")
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
        self.mail = row['MAIL']
        self.passw = row['PASSWORD']
        self.payment = row['PAYMENT']
        self.discord = DISCORD_ID

        self.delay = int(config['delay'])
        self.webhook_url = webhook
        self.version = version
        self.threadID = '%03d' % i
        self.build_proxy()
        self.balance = balancefunc()
        self.bar()
        self.timeout = 120

        self.login()

    def bar(self):
        if machineOS.lower() == 'windows':
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running ANTONIOLI | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running ANTONIOLI | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

    def error(self, text):
        message = f'[TASK {self.threadID}] - [ANTONIOLI] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [ANTONIOLI] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [ANTONIOLI] - {text}'
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
            if helheim.isChallenge(session, response):
                self.warn('Solving Cloudflare v2')
                return helheim.solve(session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                self.warn('Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.warn('Solving captcha v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True).solve() 
            elif is_fingerprint_challenge(response):
                self.warn('Solving new challange')
                return Cf_challenge_3(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b").solve()
            else:
                return response

    def login(self):
        self.warn('Attempting login...')
        payload = {
            'utf8':'✓',
            'authenticity_token':'',
            'spree_user[email]':self.mail,
            'spree_user[password]':self.passw,
            'spree_user[remember_me]':'0',
            'spree_user[remember_me]':'1',
            'commit':'Accedi'
        }
        headers = {
            'content-type':'application/x-www-form-urlencoded',
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.antonioli.eu/it/IT/login',
                    headers = headers,
                    data = payload,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 302 and r.headers['location'] == 'https://www.antonioli.eu/it/IT':
                    self.success('Succesfully logged in!')
                    break
                elif r.status_code == 403:
                    self.error('Proxy Banned, rotating...')
                    self.build_proxy()
                    continue
                else:
                    print(r.status_code)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while logging in: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Login: {e}\n')
                time.sleep(self.delay)
                continue
        self.atc()

    def atc(self):
        self.warn('Adding to cart...')
        payload = {"variant_id":self.link, "quantity":1, "options":{}}
        headers = {
            'content-type': 'application/json; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.antonioli.eu/it/IT/orders/populate.json',
                    headers = headers,
                    json = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    r_json = json.loads(r.text.strip())
                    if r_json['cart']['item_count'] >= 1:
                        try:
                            self.img = r_json['cart']['line_items'][0]['image_url']
                        except:
                            self.img = 'https://www.promocode.ac/wp-content/uploads/2019/04/antonioli_Coupons-480x275.png'
                        self.title = r_json['cart']['line_items'][0]['name']
                        self.size = r_json['cart']['line_items'][0]['variant_size']
                        self.price = r_json['cart']['line_items'][0]['full_price']
                        self.success('Succesfully added to cart!')
                        break
                    else:
                        print(r.text)
                elif r.status_code == 422 and 'quantity' in r.text:
                    self.warn('Product OOS, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy Banned, rotating...')
                    self.build_proxy()
                    continue
                else:
                    print(r.status_code)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while adding to cart: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Atc: {e}\n')
                time.sleep(self.delay)
                continue
        self.checkout()
    
    def checkout(self):
        self.warn('Getting checkout page...')
        while True:
            try:
                r = self.s.get(
                    'https://www.antonioli.eu/it/IT/checkout/payment',
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    self.token = r.text.split('authenticity_token" value="')[1].split('"')[0]
                    self.success('Succesfully got checkout page!')
                    break
                elif r.status_code == 403:
                    self.error('Proxy Banned, rotating...')
                    self.build_proxy()
                    continue
                else:
                    print(r.status_code)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while checkout page: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Atc: {e}\n')
                time.sleep(self.delay)
                continue
        self.order()
    
    def order(self):
        self.warn('Submitting order...')
        payload = {
            'utf8': '✓',
            '_method': 'patch',
            'authenticity_token': self.token,
            'order[payments_attributes][][payment_method_id]': 1,
            'commit': 'Pay with Bank Transfer'
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.antonioli.eu/it/IT/checkout/update/payment',
                    data = payload,
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 302 and 'orders' in r.headers['location']:
                    self.order = r.headers['location'].split('rders/')[1]
                    self.success('Succesfully checked out!')
                    break
                elif r.status_code == 403:
                    self.error('Proxy Banned, rotating...')
                    self.build_proxy()
                    continue
                else:
                    print(r.status_code)
                    print(r.headers)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while checkout page: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Atc: {e}\n')
                time.sleep(self.delay)
                continue
        self.successCC()

    def Pubblic_Webhook_CC(self):
        webhook = DiscordWebhook(url = 'https://discord.com/api/webhooks/848225765370757150/jhbxqUfu3aS6pDDOVa6orSVdFQOB0kRwIfF-2MfGD_Mp52Vb3lfmpmzqWRua98YnxGt8', content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'||ANTONIOLI||', value = f'{self.title}', inline = True)
        embed.add_embed_field(name='**Variant**', value = f'||{self.link}||', inline = False)
        embed.add_embed_field(name='**Size**', value = f'{self.size}', inline = True)
        embed.add_embed_field(name='**Price**', value = f'{self.price}', inline = True)
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


    def successCC(self):
        if self.all_proxies == None:
            self.px = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 0x715aff)
        embed.add_embed_field(name=f'||ANTONIOLI||', value = f'{self.title}', inline = True)
        embed.add_embed_field(name='**Variant**', value = f'||{self.link}||', inline = False)
        embed.add_embed_field(name='**Size**', value = f'{self.size}', inline = True)
        embed.add_embed_field(name='**Price**', value = f'{self.price}', inline = True)
        embed.add_embed_field(name='**Email**', value = f'||{self.mail}||', inline = False)
        embed.add_embed_field(name='**Order**', value = f'||{self.order}||', inline = False)
        embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
        embed.set_thumbnail(url = self.img)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic_Webhook_CC()
