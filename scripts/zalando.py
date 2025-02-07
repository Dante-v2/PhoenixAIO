from urllib3.util import ssl_
from requests.adapters import HTTPAdapter
import ssl
import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, pytz, traceback
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from card_identifier.card_type import identify_card_type
from cryptography.hazmat.backends import default_backend
from os import urandom
from urllib import parse
from akamai_api import Akamai
import ghttp as client
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

failed = 0
checkoutnum = 0
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

class ZALANDO():

    def __init__(self, row, webhook, version, threadID, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'zalando/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "zalando/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()
        except Exception as e:
            error("Failed To Read Proxies File - using no proxies ")
            self.all_proxies = None

        self.build_proxy()
        
        self.pid = row['PID'] 
        self.pidpreload = row['PRELOAD']
        self.size = row['SIZE']
        self.mail = row['MAIL']
        self.password = row['PASSWORD']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.city = row['CITY']
        self.zipcode = row['ZIPCODE']
        self.phone = row['PHONE']
        self.country = row['COUNTRY']
        self.payment = row['PAYMENT']
        self.mode = row['MODE']
        self.cardnumber = row['CARDNUMBER']
        self.expmonth = row['EXPMONTH']
        self.expyear = row['EXPYEAR']
        self.cvv = row['CVV']
        self.discountcode = row['PROMOCODE']
        self.timer = row['TIMER']
        self.discounted = False
        self.version = version
        self.webhook_url = webhook

        self.listsuccess = 'https://discord.com/api/webhooks/773665832554987550/o6FJp62HUV5p7DzMGyMg1B1fVG9ADfpgu-OU6Ztm89DWefNQHc_ei2D44RoN2479WjHZ'
        #self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.discord = DISCORD_ID
        self.timeout = 120
        self.threadID = '%03d' % threadID
        self.bar()
        self.delay = int(config["delay"])

        self.apiHeaders = {
            "Accept-Encoding": "gzip, deflate",
            "X-Api-Key": 'e396e5b7-9bb2-44da-a3d1-7f1a5a1f0565',
            "X-Sec": "low"
        }

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
                
        self.discountsubmitted = False
        self.preloadmode = False
        self.preloadone = False
        self.cartcleaned = False
        if self.mode == '':
            self.mode == 'NORMAL'
        if self.pidpreload != '':
            self.preloadmode = True
        
        self.timermode = False
        if self.timer != '':
            self.timermode = True

        self.warn('Task started!')
        
        self.get_login_redirect()

    def error(self, text):
        message = f'[TASK {self.threadID}] - [ZALANDO] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [ZALANDO] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [ZALANDO] - {text}'
        warn(message)

    def build_proxy(self):
        if self.all_proxies == [] or not self.all_proxies:
            return None
        else:
            self.px = random.choice(self.all_proxies)
            splitted = self.px.split(':')
            if len(splitted) == 2:
                self.proxies = {
                    'http': 'http://{}'.format(self.px),
                    'https': 'http://{}'.format(self.px)
                }
            elif len(splitted) == 4:
                self.proxies = {
                    'http': 'http://{}:{}@{}:{}'.format(splitted[2], splitted[3], splitted[0], splitted[1]),
                    'https': 'http://{}:{}@{}:{}'.format(splitted[2], splitted[3], splitted[0], splitted[1])
                }
            else:
                self.error('Invalid proxy: "{}", rotating'.format(self.px))
                return None
        try: 
            cookies = self.s.cookies
        except:
            cookies = {}
        #self.proxies = {'http': None}
        self.s = client.Session(self.proxies['http'], client.Fingerprint.CHROME_83, timeout=20, redirect=False, settings={"HEADER_TABLE_SIZE": 65536, "SETTINGS_ENABLE_PUSH": 0, "SETTINGS_MAX_CONCURRENT_STREAMS": 1000, "SETTINGS_INITIAL_WINDOW_SIZE": 6291456, "SETTINGS_MAX_FRAME_SIZE": 16384, "SETTINGS_MAX_HEADER_LIST_SIZE": 262144})
        self.s.cookies = cookies
        
    def bar(self):
        if machineOS.lower() == 'windows':
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - ZALANDO Running | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - ZALANDO Running | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')
    
    def getua(self):
        while True:
            try:
                z = self.s.get(
                    'https://ak01-eu.hwkapi.com/akamai/ua',
                    headers=self.apiHeaders
                )
                if z.status == 200:
                    self.user_agent = z.text
                    break
                else:
                    self.error('Request error getting user agent')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error getting user agent')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception getting user agent: {e}')
                self.build_proxy()
                continue

    def get_login_redirect(self):
        self.getua()
        self.warn('Getting login page [1/4]')
        headers = {
            ':method': 'GET',
            ':authority': 'www.zalando.it',
            ':scheme': 'https',
            ':path': '/login',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en'
        }
        while True:
            try:
                r = self.s.get(
                    'https://www.zalando.it/login',
                    headers = headers
                )
                if r.status == 307:
                    if 'Location' in r.headers.keys():
                        self.authorize_url = r.headers['Location'][0]
                        self.success('Successfully got login page! [1/4]')
                        break
                    else:
                        print(r.headers)
                        self.error('Request Error: Couldn\'t get login page [1/4]')
                        self.build_proxy()
                        continue
                elif r.status == 403:
                    self.error('Error getting login page [1/4]: Proxy banned')
                    self.build_proxy()
                    continue
                else:
                    self.error(f'Request error getting login page [1/4]: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error getting login page [1/4]')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception getting login page [1/4]: {e}')
                self.build_proxy()
                continue
        self.get_login_authenticate()

    def get_login_authenticate(self):
        self.warn('Getting login page [2/4]')
        headers = {
            ':method': 'GET',
            ':authority': 'accounts.zalando.com',
            ':scheme': 'https',
            ':path': self.authorize_url.split('accounts.zalando.com/')[1],
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en',
        }
        while True:
            try:
                r = self.s.get(
                    self.authorize_url,
                    headers = headers
                )
                if r.status == 302:
                    if 'Location' in r.headers.keys():
                        self.sso_path = r.headers['Location'][0]
                        self.success('Successfully got login page! [2/4]')
                        break
                    else:
                        self.error('Request Error: Couldn\'t get login page [2/4]')
                        self.build_proxy()
                        continue
                else:
                    self.error(f'Request error getting login page [2/4]: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error getting login page [2/4]')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception getting login page [2/4]: {e}')
                self.build_proxy()
                continue
        self.get_login_sso()

    def get_login_sso(self):
        self.warn('Getting login page [3/4]')
        headers = {
            ':method': 'GET',
            ':authority': 'accounts.zalando.com',
            ':scheme': 'https',
            ':path': self.sso_path,
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en',
        }
        while True:
            try:
                r = self.s.get(
                    f'https://accounts.zalando.com{self.sso_path}',
                    headers = headers
                )
                if r.status == 302:
                    if 'Location' in r.headers.keys():
                        self.login_path = r.headers['Location'][0]
                        self.success('Successfully got login page! [3/4]')
                        break
                    else:
                        self.error('Request Error: Couldn\'t get login page [3/4]')
                        self.build_proxy()
                        continue
                else:
                    self.error(f'Request error getting login page [3/4]: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error getting login page [3/4]')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception getting login page [3/4]: {e}')
                self.build_proxy()
                continue
        self.get_login_page()

    def get_login_page(self):
        self.warn('Getting login page [4/4]')
        headers = {
            ':method': 'GET',
            ':authority': 'accounts.zalando.com',
            ':scheme': 'https',
            ':path': self.login_path,
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en'
        }
        while True:
            try:
                r = self.s.get(
                    f'https://accounts.zalando.com{self.login_path}',
                    headers = headers
                )
                if r.status == 200:
                    soup = bs(r.text, features='lxml')
                    self.login_flow_id = r.text.split('''x-flow-id%22%3A%22''')[1].split('''%22%2C%22''')[0]
                    self.akamai_login_path = soup.find_all('script')[-1]['src']
                    self.success('Successfully got login page! [4/4]')
                    break
                else:
                    self.error(f'Request error getting login page [4/4]: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error getting login page [4/4]')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception getting login page [4/4]: {e}, retrying...')
                self.build_proxy()
                continue
        self.akamai_login_get()

    def akamai_login_get(self):
        headers = {
            ':method': 'GET',
            ':authority': 'accounts.zalando.com',
            ':scheme': 'https',
            ':path': self.akamai_login_path,
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': self.user_agent,
            'sec-ch-ua-platform': '"Windows"',
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'referer': f'https://accounts.zalando.com{self.login_path}',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en',
        }
        while True:
            try:
                r = self.s.get(
                    f'https://accounts.zalando.com{self.akamai_login_path}',
                    headers = headers
                )
                if r.status == 200 or r.status == 201:
                    break
                else:
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error getting akamai')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception getting akamai: {e}')
                self.build_proxy()
                continue
        for i in range(2): self.akamai_login_gen()
        if '~-1~||-1||~-1' in self.s.cookies['accounts.zalando.com']['_abck']:
            self.akamai_login_gen()
        self.akamai_login_submit()

    def akamai_login_gen(self):
        params = {
            "user_agent": self.user_agent,
            "site": 'https://accounts.zalando.com',
            "abck": self.s.cookies['accounts.zalando.com']['_abck'],
            "type": "sensor",
            "events": "0,0"
        }
        while True:
            try:
                r = self.s.post(
                    'https://ak01-eu.hwkapi.com/akamai/generate',
                    json = params,
                    headers = self.apiHeaders
                )
                if r.status == 200:
                    self.sensor = r.text.split('*')[0]
                    break
                elif r.status == 408:
                    self.error('Error generating akamai cookie: API timed out')
                    time.sleep(5)
                    continue
                else:
                    self.error(f'Error generating akamai cookie: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error generating akamai cookie')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception generating akamai cookie: {e}, retrying...')
                continue

    def akamai_login_submit(self):
        headers = {
            ':method': 'POST',
            ':authority': 'accounts.zalando.com',
            ':scheme': 'https',
            ':path': self.login_path,
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': self.user_agent,
            'sec-ch-ua-platform': '"Windows"',
            'content-type': 'text/plain;charset=UTF-8',
            'accept': '*/*',
            'origin': 'https://accounts.zalando.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'https://accounts.zalando.com{self.login_path}',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en',
        }
        payload = {"sensor_data": self.sensor}
        while True:
            try:
                r = self.s.post(
                    f'https://accounts.zalando.com{self.akamai_login_path}',
                    data = json.dumps(payload),
                    headers = headers
                )
                if r.status == 201:
                    self.success('Successfully generated akamai!')
                    break
                else:
                    self.error(f'Error submitting akamai cookie: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error submitting akamai cookie')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception submitting akamai cookie: {e}, retrying...')
                continue
        self.loginpost()

    def loginpost(self):
        err = False
        self.warn('Submitting login info [1/4]')
        headers = {
            ':method':'POST',
            ':authority':'accounts.zalando.com',
            ':scheme':'https',
            ':path':'/api/login',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'x-csrf-token':self.s.cookies['accounts.zalando.com']['csrf-token'],
            'sec-ch-ua-mobile':'?0',
            'user-agent':self.user_agent,
            'content-type':'application/json',
            'accept':'application/json',
            'x-flow-id': self.login_flow_id,
            'sec-ch-ua-platform': '"Windows"',
            'origin':'https://accounts.zalando.com',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'cors',
            'sec-fetch-dest':'empty',
            'referer':f'https://accounts.zalando.com{self.login_path}',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en'
        }
        payload = {
            "email": self.mail,
            "secret": self.password,
            "request": self.login_path.split('?request=')[1].split('&')[0]
        }
        while True:
            try:
                r = self.s.post(
                    'https://accounts.zalando.com/api/login',
                    json = payload,
                    headers = headers
                )
                if r.status == 201:
                    try:
                        r_json = json.loads(r.text)
                    except:
                        self.error('Error submitting login info [1/4]: Invalid response')
                        self.build_proxy()
                        continue
                    else:
                        if r_json['status']:
                            self.login_redirect = r_json['redirect_url']
                            self.success('Successfully submitted login info! [1/4]')
                            break
                        else:
                            self.error('Error submitting login info [1/4], check your credentials')
                            self.build_proxy()
                            continue
                elif r.status == 403:
                    self.error('Error submitting login info [1/4]: Proxy banned')
                    err = True
                    self.s.cookies = {}
                    self.build_proxy()
                    break
                else:
                    self.error(f'Error submitting login info [1/4]: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection Error submitting login info [1/4]')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception logging in [1/4]: {e}')
                self.build_proxy()
                continue
        if err:
            self.get_login_redirect()
        else:
            self.login_submit_authenticate()

    def login_submit_authenticate(self):
        self.warn('Submitting login [2/4]')
        headers = {
            ':method': 'GET',
            ':authority': 'accounts.zalando.com',
            ':scheme': 'https',
            ':path': self.login_redirect,
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en',
        }
        while True:
            try:
                r = self.s.get(
                    f'https://accounts.zalando.com{self.login_redirect}',
                    headers = headers
                )
                if r.status == 302:
                    if 'Location' in r.headers.keys():
                        self.authorize_submit_path = r.headers['Location'][0]
                        self.success('Successfully submitted login info! [2/4]')
                        break
                    else:
                        self.error('Request Error: Couldn\'t submit login info [2/4]')
                        self.build_proxy()
                        continue
                else:
                    self.error(f'Request error submitting login info [2/4]: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error submitting login info [2/4]')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception submitting login info [2/4]: {e}')
                self.build_proxy()
                continue
        self.login_submit_authorize()

    def login_submit_authorize(self):
        self.warn('Submitting login [3/4]')
        headers = {
            ':method': 'GET',
            ':authority': 'accounts.zalando.com',
            ':scheme': 'https',
            ':path': self.authorize_submit_path,
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en',
        }
        while True:
            try:
                r = self.s.get(
                    f'https://accounts.zalando.com{self.authorize_submit_path}',
                    headers = headers
                )
                if r.status == 302:
                    if 'Location' in r.headers.keys():
                        self.sso_submit_url = r.headers['Location'][0]
                        self.success('Successfully submitted login info! [3/4]')
                        break
                    else:
                        self.error('Request Error: Couldn\'t submit login info [3/4]')
                        self.build_proxy()
                        continue
                else:
                    self.error(f'Request error submitting login info [3/4]: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error submitting login info [3/4]')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception submitting login info [3/4]: {e}')
                self.build_proxy()
                continue
        self.login_submit_sso()

    def login_submit_sso(self):
        self.warn('Submitting login [4/4]')
        headers = {
            ':method': 'GET',
            ':authority': 'www.zalando.it',
            ':scheme': 'https',
            ':path': self.sso_submit_url.split('zalando.it/')[1],
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en',
        }
        while True:
            try:
                r = self.s.get(
                    self.sso_submit_url,
                    headers = headers
                )
                if r.status == 307:
                    if 'Location' in r.headers.keys():
                        if r.headers['Location'][0] == '/':
                            self.success('Successfully submitted login info! [4/4]')
                            break
                        else:
                            self.error('Error submitting login info [4/4]: Invalid response')
                    else:
                        self.error('Request Error: Couldn\'t submit login info [4/4]')
                        self.build_proxy()
                        continue
                else:
                    self.error(f'Request error submitting login info [4/4]: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error submitting login info [4/4]')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception submitting login info [4/4]: {e}')
                self.build_proxy()
                continue
        self.get_akamai_normal_path()

    def get_akamai_normal_path(self):
        headers = {
            ':method': 'GET',
            ':authority': 'www.zalando.it',
            ':scheme': 'https',
            ':path': '/uomo-home',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': self.user_agent,
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'referer': 'https://www.zalando.it/uomo-home/',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en'
        }
        while True:
            try:
                r = self.s.get(
                    f'https://www.zalando.it/uomo-home/',
                    headers = headers
                )
                if r.status == 200:
                    self.akamaipath = r.text.split('src="')[-1].split('"')[0]
                    break
                else:
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting login page:{e}, retrying...')
                self.build_proxy()
                continue
        self.akamai_normal_get()

    def akamai_normal_get(self):
        headers = {
            ':method': 'GET',
            ':authority': 'www.zalando.it',
            ':scheme': 'https',
            ':path': self.akamaipath,
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': self.user_agent,
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'referer': 'https://www.zalando.it/uomo-home',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en'
        }
        while True:
            try:
                r = self.s.get(
                    f'https://www.zalando.it{self.akamaipath}',
                    headers = headers
                )
                if r.status == 200 or r.status == 201:
                    break
                else:
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error getting akamai')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception getting akamai: {e}')
                self.build_proxy()
                continue
        for i in range(2): self.akamai_normal_gen()
        if '~-1~||-1||~-1' in self.s.cookies['www.zalando.it']['_abck']:
            self.akamai_normal_gen()
        self.akamai_normal_submit()

    def akamai_normal_gen(self):
        params = {
            "user_agent": self.user_agent,
            "site": 'https://www.zalando.it',
            "abck": self.s.cookies['www.zalando.it']['_abck'],
            "type": "sensor",
            "events": "0,0"
        }
        while True:
            try:
                r = self.s.post(
                    'https://ak01-eu.hwkapi.com/akamai/generate',
                    json = params,
                    headers = self.apiHeaders
                )
                if r.status == 200:
                    self.sensor = r.text.split('*')[0]
                    break
                elif r.status == 408:
                    self.error('Error generating akamai cookie: API timed out')
                    time.sleep(5)
                    continue
                else:
                    self.error(f'Error generating akamai cookie: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error generating akamai cookie')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception generating akamai cookie: {e}, retrying...')
                self.build_proxy()
                continue

    def akamai_normal_submit(self):
        headers = {
            ':method': 'POST',
            ':authority': 'www.zalando.it',
            ':scheme': 'https',
            ':path': self.akamaipath,
            'content-length': '',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': self.user_agent,
            'content-type': 'text/plain;charset=UTF-8',
            'accept': '*/*',
            'origin': 'https://www.zalando.it',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.zalando.it/uomo-home',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en'
        }
        payload = {"sensor_data": self.sensor}
        while True:
            try:
                r = self.s.post(
                    f'https://www.zalando.it{self.akamaipath}',
                    data = json.dumps(payload),
                    headers = headers
                )
                if r.status == 201:
                    self.success('Successfully generated akamai!')
                    break
                else:
                    self.error(f'Error submitting akamai cookie: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error submitting akamai cookie')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception submitting akamai cookie: {e}, retrying...')
                self.build_proxy()
                continue
        if self.preloadmode == True:
            if self.cartcleaned == False:
                self.getcart()
            if self.preloadone == True:
                if self.mode == 'DROP':
                    if self.timermode:
                        self.warn(f'Wainting for drop till :{self.timer}...')
                        while True:
                            n = datetime.now()
                            p = str(n).split(':')[1].split(':')[0]
                            f = str(n).split(':')[-1]
                            m = str(n).replace(p,f'{self.timer}').replace(f,'00.000000')
                            if str(datetime.now()) >= m:
                                self.success(datetime.now())
                                break
                        cookies = self.s.cookies
                        self.s = client.Session(self.proxies['http'], client.Fingerprint.CHROME_83, timeout=20, redirect=False, settings={"HEADER_TABLE_SIZE": 65536, "SETTINGS_ENABLE_PUSH": 0, "SETTINGS_MAX_CONCURRENT_STREAMS": 1000, "SETTINGS_INITIAL_WINDOW_SIZE": 6291456, "SETTINGS_MAX_FRAME_SIZE": 16384, "SETTINGS_MAX_HEADER_LIST_SIZE": 262144})
                        self.s.cookies = cookies
                        self.atc()
                    else:
                        self.atc()
                elif self.mode == 'RESTOCK':
                    self.cartrestock()
                else:
                    self.getprodlink()
            else:
                self.preloadget()
        else:
            if self.mode == 'DROP':
                if self.timermode:
                    while True:
                        n = datetime.now()
                        p = str(n).split(':')[1].split(':')[0]
                        f = str(n).split(':')[-1]
                        m = str(n).replace(p,f'{self.timer}').replace(f,'00.000000')
                        if str(datetime.now()) >= m:
                            self.success(datetime.now())
                            break
                        cookies = self.s.cookies
                        self.s = client.Session(self.proxies['http'], client.Fingerprint.CHROME_83, timeout=20, redirect=False, settings={"HEADER_TABLE_SIZE": 65536, "SETTINGS_ENABLE_PUSH": 0, "SETTINGS_MAX_CONCURRENT_STREAMS": 1000, "SETTINGS_INITIAL_WINDOW_SIZE": 6291456, "SETTINGS_MAX_FRAME_SIZE": 16384, "SETTINGS_MAX_HEADER_LIST_SIZE": 262144})
                        self.s.cookies = cookies
                    self.atc()
                else:
                    self.atc()
            elif self.mode == 'RESTOCK':
                self.cartrestock()
            else:
                self.getprodlink()

    def getcart(self):
        self.warn('Getting cart...')
        headers = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/cart/',
            'cache-control':'max-age=0',
            'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile':'?0',
            'sec-ch-ua-platform':'"Windows"',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
        }
        while True:
            try:
                r = self.s.get(
                    f'https://www.zalando.it/cart',
                    headers = headers
                )
                if r.status == 200:
                    dat = r.text.split('data-data="')[1].split('"')[0].replace('%22','"').replace('%3A',':').replace('%7B',"{").replace('%5B','[').replace('%2C',',').replace('%5D',']').replace('%7D','}').replace('%C2%A0','').replace('%E2%82%AC','`').replace('%20',' ').replace('%2F','/')
                    r_json = json.loads(dat)
                    self.cartid = r_json['cart']['id']
                    try:
                        xxx = r_json['cart']['groups'][0]['articles']
                    except:
                        break
                    itemlist = []
                    for i in r_json['cart']['groups'][0]['articles']:
                        itemlist.append(i['articleModel']['simpleSku'])
                    for m in itemlist:
                        self.item = itemlist[0]
                        self.clearcart2()
                        del itemlist[0]
                    if not itemlist:
                        break
                    else: 
                        continue
                else:
                    self.error(f'Error getting cart: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error getting cart')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting cart: {e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        self.cartcleaned = True
        self.success('Cart cleared!')
        

    def clearcart2(self):
        self.warn('Item found, clearing cart...')
        headers = {
            ':method':'DELETE',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':f'/api/cart-gateway/carts/{self.cartid}/items/{self.item}',
            'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'accept':'application/json',
            'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
            'sec-ch-ua-mobile':'?0',
            'content-type':'application/json',
            'user-agent':self.user_agent,
            'sec-ch-ua-platform':'"Windows"',
            'origin':'https://www.zalando.it',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'cors',
            'sec-fetch-dest':'empty',
            'referer':'https://www.zalando.it/cart/',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
        }
        while True:
            try:
                r = self.s.delete(
                    f'https://www.zalando.it/api/cart-gateway/carts/{self.cartid}/items/{self.item}',
                    headers = headers
                )
                if r.status == 204:
                    break
                else:
                    self.error(f'Error submitting akamai cookie: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error submitting akamai cookie')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception submitting akamai cookie: {e}, retrying...')
                continue
        return self.success('Item deleted')

    def cartrestock(self):
        headers = {
            ':method': 'POST',
            ':authority': 'www.zalando.it',
            ':scheme': 'https',
            ':path': '/api/cart-gateway/carts',
            'content-length': '',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': self.user_agent,
            'viewport-width':'1920',
            'content-type': 'application/json',
            'accept': 'application/json',
            'dpr':'1',
            'sec-ch-ua-platform':'"Windows"',
            'origin': 'https://www.zalando.it',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en'
        }
        while True:
            try:
                r = self.s.post(
                    f'https://www.zalando.it/api/cart-gateway/carts',
                    headers = headers
                )
                if r.status == 200:
                    print(r.text)
                    
                else:
                    self.error(f'Error submitting akamai cookie: {r.status}')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error submitting akamai cookie')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception submitting akamai cookie: {e}, retrying...')
                continue

    def getprodlink(self):
        self.warn('Getting product page...')
        headers = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':f'/catalogo/?q={self.pid}',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile':'?0',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site':'none',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en'
        }
        while True:
            try:
                r = self.s.get(
                    f'https://www.zalando.it/catalogo/?q={self.pid}',
                    headers = headers
                )
                if r.status == 302:
                    self.product_path = r.headers['Location'][0]
                    break
                else:
                    print(r.text)
                    print(r.status)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting product page:{e}, retrying...')
                self.build_proxy()
                continue
        self.monitor()

    def monitor(self):
        headers = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':self.product_path,
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile':'?0',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site':'none',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en'
        }
        while True:
            try:
                r = self.s.get(
                    f'https://www.zalando.it{self.product_path}',
                    headers = headers
                )
                self.url = f'https://www.zalando.it/catalogo/?q={self.pid}'
                if r.status == 200:
                    r_json = json.loads(r.text.split('id="z-vegas-pdp-props" type="application/json"><![CDATA[')[1].split(']]></script>')[0])
                    if r_json['model']['articleInfo']['available'] == True and r_json['model']['articleInfo']['coming_soon'] == False:
                        self.pageimpressionid = r.text.split('pageImpressionId":"')[1].split('"')[0]
                        unit = r_json['model']['articleInfo']['units']
                        self.success('Successfully got product page!')
                        sizes = []
                        variants = []
                        stock = []
                        for i in unit:
                            if i['available'] == True:
                                if i['stock'] > 0:
                                    stock.append(i['stock'])
                                    sizes.append(i['size']['local'])
                                    variants.append(i['id'])
                        tot = zip(sizes, variants, stock)
                        connect = list(tot)
                        self.sizerange = []
                        if self.size == "RANDOM":
                            scelta = random.choice(connect)
                            self.size = scelta[0]
                            self.variant = scelta[1]
                            self.stock = scelta[2]
                            self.warn(f'Adding to cart size {self.size}, stock: [{self.stock}]')
                            break
                        elif '-' in self.size:
                            self.size1 = float(self.size.split('-')[0])
                            self.size2 = float(self.size.split('-')[1])
                            for x in connect:
                                if self.size1 <= float(x[0]) <= self.size2:
                                    self.sizerange.append(x[0])        
                            self.sizerandom = random.choice(self.sizerange)
                            for x in connect:
                                if self.sizerandom == x[0]:
                                    self.size = x[0]
                                    self.variant = x[1]
                                    self.stock = x[2]
                                    self.warn(f'Adding to cart size {self.size}, stock: [{self.stock}]')
                            break
                        elif ',' in self.size:
                            self.size1 = float(self.size.split(',')[0])
                            self.size2 = float(self.size.split(',')[1])
                            for x in connect:
                                if self.size1 <= float(x[0]) <= self.size2:
                                    self.sizerange.append(x[0])        
                            self.sizerandom = random.choice(self.sizerange)
                            for x in connect:
                                if self.sizerandom == x[0]:
                                    self.size = x[0]
                                    self.variant = x[1]
                                    self.stock = x[2]
                                    self.warn(f'Adding to cart size {self.size}, stock: [{self.stock}]')
                            break
                        else:
                            for i in connect:
                                if self.size not in sizes:
                                    self.warn('Size OOS, retrying...')
                                    time.sleep(self.delay)
                                    continue
                                elif self.size == i[0]:
                                    self.size = x[0]
                                    self.variant = x[1]
                                    self.stock = x[2]
                            self.warn(f'Adding to cart size {self.size}')
                            break
                        break
                    else:
                        self.warn('Product oos, monitoring...')
                        time.sleep(self.delay)
                        continue
                else:
                    print(r.text)
                    print(r.status)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting product page:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        self.atc()
    
    def atc(self):
        global carted
        if self.mode == 'DROP':
            self.warn('Adding to cart...')
            x = self.pid.split(';')
            variant = []
            payload = []
            for i in x:
                variant.append(i)
            for p in variant:
                payload.append({"id":"e7f9dfd05f6b992d05ec8d79803ce6a6bcfb0a10972d4d9731c6b94f6ec75033","variables":{"addToCartInput":{"productId":f"{p}","clientMutationId":"addToCartMutation"}}})
            headers = {
                ':method':'POST',
                ':authority':'www.zalando.it',
                ':scheme':'https',
                ':path':'/api/graphql/add-to-cart/',
                'content-length':'',
                'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                #'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
                'x-zalando-feature':'pdp',
                'sec-ch-ua-mobile':'?0',
                'user-agent':self.user_agent,
                'x-zalando-intent-context':'navigationTargetGroup=ALL',
                'content-type':'application/json',
                'x-zalando-request-uri':f'/catalogo/?q={variant[0]}',
                #'x-page-impression-id':self.pageimpressionid,
                'dpr':'1',
                'viewport-width':'1920',
                #'x-zalando-experiments':self.zalandoexperiments,
                'accept':'*/*',
                'origin':'https://www.zalando.it',
                'sec-fetch-site':'same-origin',
                'sec-fetch-mode':'cors',
                'sec-fetch-dest':'empty',
                'referer':f'https://www.zalando.it/catalogo/?q={variant[0]}',
                'accept-encoding':'gzip, deflate, br',
                'accept-language':'en',
            }
        else:
            headers = {
                ':method':'POST',
                ':authority':'www.zalando.it',
                ':scheme':'https',
                ':path':'/api/graphql/add-to-cart/',
                'content-length':'',
                'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
                'x-zalando-feature':'pdp',
                'sec-ch-ua-mobile':'?0',
                'user-agent':self.user_agent,
                'x-zalando-intent-context':'navigationTargetGroup=ALL',
                'content-type':'application/json',
                'x-zalando-request-uri':f'/catalogo/?q={self.pid}',
                'x-page-impression-id':self.pageimpressionid,
                'dpr':'1',
                'viewport-width':'1920',
                #'x-zalando-experiments':self.zalandoexperiments,
                'accept':'*/*',
                'origin':'https://www.zalando.it',
                'sec-fetch-site':'same-origin',
                'sec-fetch-mode':'cors',
                'sec-fetch-dest':'empty',
                'referer':f'https://www.zalando.it/catalogo/?q={self.pid}',
                'accept-encoding':'gzip, deflate, br',
                'accept-language':'en',
            }
            payload = [{"id":"e7f9dfd05f6b992d05ec8d79803ce6a6bcfb0a10972d4d9731c6b94f6ec75033","variables":{"addToCartInput":{"productId":f"{self.variant}","clientMutationId":"addToCartMutation"}}}]
        while True:
            try:
                r = self.s.post(
                    'https://www.zalando.it/api/graphql/add-to-cart/',
                    json = payload,
                    headers = headers
                )
                if r.status == 200:
                    print(r.text)
                    r_json = json.loads(r.text)
                    if any(i['data']['addToCart'] for i in r_json):
                        carted = carted + 1
                        self.bar()
                        self.success('Successfully added to cart!')
                        break
                    else:
                        self.error('Failed adding to cart, retrying...')
                        time.sleep(self.delay)
                        self.build_proxy()
                        continue
                else:
                    print(r.text)
                    print(r.status)
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while adding to cart:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        if self.preloadone == True:
            self.paymentget5()
        else:
            if self.address != '':
                self.addresschange()
            else:
                self.checkoutget()
    
    def checkoutget(self):
        self.warn('Getting checkout page...')
        headers = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/checkout/address',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile':'?0',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'referer':'https://www.zalando.it/cart',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en',
        }
        while True:
            try:
                r = self.s.get(
                    'https://www.zalando.it/checkout/address',
                    headers = headers
                )
                if r.status == 200:
                    self.addressid = r.text.split('defaultShippingAddress&quot;:{&quot;id&quot;:&quot;')[1].split('&')[0]
                    self.success('Successfully got checkout page!')
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting checkout page:{e}, retrying...')
                self.build_proxy()
                print(traceback.format_exc())
                continue
        self.addresspost()

    def paymentselection(self):
        self.warn('Selecting payment...')
        headers = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/api/checkout/next-step',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile':'?0',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'referer':'https://www.zalando.it/checkout/address',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en'
        }
        while True:
            try:
                r = self.s.get(
                    'https://www.zalando.it/api/checkout/next-step',
                    headers = headers
                )
                if r.status == 200:
                    r_json = json.loads(r.text)
                    self.selecturl = r_json['url']
                    self.sessionid = self.selecturl.split('session/')[1].split('/')[0]
                    self.success('Successfully selected payment!')
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting payment page:{e}, retrying...')
                self.build_proxy()
                print(traceback.format_exc())
                continue
        self.paymentget2()

    def paymentget2(self):
        h = {
            'Host':'checkout.payment.zalando.com',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile':'?0',
            'Upgrade-Insecure-Requests':'1',
            'User-Agent':self.user_agent,
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site':'cross-site',
            'Sec-Fetch-Mode':'navigate',
            'Sec-Fetch-User':'?1',
            'Sec-Fetch-Dest':'document',
            'Referer':'https://www.zalando.it/',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en'
        }
        self.warn('Getting last step [1/4]...')
        while True:
            try:
                r = self.s.get(
                    self.selecturl,
                    headers = h
                )
                if r.status == 307:
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting payment page:{e}, retrying...')
                self.build_proxy()
                print(traceback.format_exc())
                continue

        self.paymentget3()

    def paymentget3(self):
        cookies = self.s.cookies
        self.s = client.Session(self.proxies['http'], client.Fingerprint.CHROME_83, timeout=20, redirect=False, settings={"HEADER_TABLE_SIZE": 65536, "SETTINGS_ENABLE_PUSH": 0, "SETTINGS_MAX_CONCURRENT_STREAMS": 1000, "SETTINGS_INITIAL_WINDOW_SIZE": 6291456, "SETTINGS_MAX_FRAME_SIZE": 16384, "SETTINGS_MAX_HEADER_LIST_SIZE": 262144})
        self.s.cookies = cookies
        head = {
            'Host':'checkout.payment.zalando.com',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile':'?0',
            'Upgrade-Insecure-Requests':'1',
            'User-Agent':self.user_agent,
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site':'cross-site',
            'Sec-Fetch-Mode':'navigate',
            'Sec-Fetch-User':'?1',
            'Sec-Fetch-Dest':'document',
            'Referer':'https://www.zalando.it/',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en'
        }
        post = False
        self.warn('Getting last step [2/4]...')
        while True:
            try:
                r = self.s.get(
                    'https://checkout.payment.zalando.com/selection',
                    headers = head
                )
                if r.status == 200:
                    post = True
                    break
                elif r.status == 303 and r.headers['Location'] == 'https://www.zalando.it/checkout/payment-complete':
                    break
                else:
                    print(r.headers)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting payment page:{e}, retrying...')
                self.build_proxy()
                continue
        if post:
            self.paymentpost()
        else:
            self.paymentget4()


    

    def paymentpost(self):
        h = {
            'Host':'checkout.payment.zalando.com',
            'Connection':'keep-alive',
            'Content-Length':'',
            'Cache-Control':'max-age=0',
            'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile':'?0',
            'sec-ch-ua-platform':'"Windows"',
            'Upgrade-Insecure-Requests':'1',
            'Origin':'https://checkout.payment.zalando.com',
            'Content-Type':'application/x-www-form-urlencoded',
            'User-Agent':self.user_agent,
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site':'same-origin',
            'Sec-Fetch-Mode':'navigate',
            'Sec-Fetch-User':'?1',
            'Sec-Fetch-Dest':'document',
            'Referer':'https://checkout.payment.zalando.com/selection',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fi;q=0.6'
        }
        payload = {
            'payz_credit_card_former_payment_method_id':'-1',
            'payz_selected_payment_method':'PAYPAL',
            'iframe_funding_source_id':''
        }
        self.warn('Getting last step - Setting payment [1/2]...')
        while True:
            try:
                r = self.s.post(
                    self.selecturl,
                    data = payload,
                    headers = h
                )
                if r.status == 307:
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting payment page:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        self.paymentpost2()

    def paymentpost2(self):
        h = {
            'Host':'checkout.payment.zalando.com',
            'Connection':'keep-alive',
            'Content-Length':'',
            'Cache-Control':'max-age=0',
            'Upgrade-Insecure-Requests':'1',
            'Origin':'https://checkout.payment.zalando.com',
            'Content-Type':'application/x-www-form-urlencoded',
            'User-Agent':self.user_agent,
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site':'same-origin',
            'Sec-Fetch-Mode':'navigate',
            'Sec-Fetch-User':'?1',
            'Sec-Fetch-Dest':'document',
            'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile':'?0',
            'sec-ch-ua-platform':'"Windows"',
            'Referer':'https://checkout.payment.zalando.com/selection',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fi;q=0.6'
        }
        payload = {
            'payz_credit_card_former_payment_method_id':'-1',
            'payz_selected_payment_method':'PAYPAL',
            'iframe_funding_source_id':''
        }
        self.warn('Getting last step - Setting payment [2/2]...')
        while True:
            try:
                r = self.s.post(
                    'https://checkout.payment.zalando.com/selection',
                    data = payload,
                    headers = h
                )
                if r.status == 303 and r.headers['Location'] == 'https://www.zalando.it/checkout/payment-complete':
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting payment page:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        self.paymentget4()
    
    def paymentget4(self):
        head = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/checkout/payment-complete',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile':'?0',
            'sec-ch-ua-platform':'"Windows"',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'referer':'https://www.zalando.it/',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
        }
        self.warn('Getting last step [3/4]...')
        while True:
            try:
                r = self.s.get(
                    'https://www.zalando.it/checkout/payment-complete',
                    headers = head
                )
                if r.status == 302:
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting payment page:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        self.paymentget5()
    
    def paymentget5(self):
        head = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/checkout/confirm',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'sec-ch-ua-mobile':'?0',
            'sec-ch-ua-platform':'"Windows"',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'referer':'https://www.zalando.it/',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
        }
        fail = False
        self.warn('Getting last step [4/4]...')
        while True:
            try:
                r = self.s.get(
                    'https://www.zalando.it/checkout/confirm',
                    headers = head
                )
                if r.status == 200:
                    soup = bs(r.text, features='lxml')
                    if self.discountcode != '':
                        self.pagerender = soup.find('div',{'id':'TrackingFlowidBearer'})['data-flow-id']
                    else:
                        pass
                    r_json = json.loads(r.text.split("data-props='")[1].split("'")[0].replace('&quot;','"').replace('&quot',''))
                    self.size = r_json['model']['groups'][0]['articles'][0]['size']
                    self.name = r_json['model']['groups'][0]['articles'][0]['name']
                    self.img = r_json['model']['groups'][0]['articles'][0]['imageUrl']
                    self.price = soup.find('z-grid',{'valign':'baseline'}).text.split(')')[1]
                    self.checkoutid = r.text.split('checkoutId&quot;:&quot;')[1].split('&')[0]
                    self.etag = r.text.split('eTag&quot;:&quot;\&quot;')[1].split('\\')[0]
                    self.success('Succefully got payment page!')
                    break
                elif r.status == 302:
                    fail = True
                    print(r.headers)
                    print(r.status)
                    break
                else:
                    fail = True
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting payment page:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        if fail:
            raise SystemExit
        if self.discountcode != '':
            if self.discounted == True:
                self.finalpost()
            else:
                self.discountredeem()
        elif self.preloadone == True:
            self.finalpost()
        elif self.preloadmode == True:
            self.clearcartcheckout()
        else:
            self.finalpost()

    def discountredeem(self):
        self.discounted = True
        self.warn('Submitting discount code...')
        headers = {
            ':method':'POST',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/api/checkout/redeem',
            'content-length':'',
            'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
            'sec-ch-ua-mobile':'?0',
            'x-zalando-header-mode':'desktop',
            'x-zalando-checkout-app':'web',
            'content-type':'application/json',
            'x-zalando-footer-mode':'desktop',
            'accept':'application/json',
            'user-agent':self.user_agent,
            'sec-ch-ua-platform':'"Windows"',
            'origin':'https://www.zalando.it',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'cors',
            'sec-fetch-dest':'empty',
            'referer':'https://www.zalando.it/checkout/confirm',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
        }
        payload = {
            "code": self.discountcode,
            "pageRenderFlowId": self.pagerender
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.zalando.it/api/checkout/redeem',
                    json = payload,
                    headers = headers
                )
                if r.status == 200:
                    r_json = json.loads(r.text)
                    self.coupon = r_json['coupon']['success']
                    if self.coupon == True:
                        self.discountsubmitted = True
                        self.success('Successfully submitted discount code')
                        break
                    else:
                        self.error('Failed submitting discount, proceeding without...')
                        break

                elif r.status == 400:
                    print(r.text)
                    self.error('Invalid code, proceeding without...')
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting discount:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        if self.preloadmode == True:
            self.clearcartcheckout()
        else:
            self.finalpost()

    def finalpost(self):
        global checkoutnum
        self.warn('Submitting payment...')
        headers = {
            ':method':'POST',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/api/checkout/buy-now',
            'content-length':'',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
            'sec-ch-ua-mobile':'?0',
            'x-zalando-header-mode':'desktop',
            'x-zalando-checkout-app':'web',
            'content-type':'application/json',
            'accept':'application/json',
            'user-agent':self.user_agent,
            'x-zalando-footer-mode':'desktop',
            'origin':'https://www.zalando.it',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'cors',
            'sec-fetch-dest':'empty',
            'referer':'https://www.zalando.it/checkout/confirm',
            'accept-encoding':'gzip, deflate',
            'accept-language':'en',
        }
        payload = {
            "checkoutId": self.checkoutid,
            "eTag": f'\"{self.etag}\"'
        }
        failed = False
        while True:
            try:
                r = self.s.post(
                    'https://www.zalando.it/api/checkout/buy-now',
                    json = payload,
                    headers = headers
                )
                print(r.text)
                if r.status == 200:
                    fail = 0
                    r_json = json.loads(r.text)
                    self.ppurl = r_json['url']
                    if self.ppurl == '/checkout/confirm?error=zalando.checkout.confirmation.quantity.error':
                        if fail > 1:
                            self.error('Failed checking out, restarting...')
                            failed = True
                            break
                        else:
                            self.error('Failed checking out, retrying...')
                            fail = fail + 1
                            continue
                    else:
                        print(self.ppurl)
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        self.success('Successfully checked out!')
                        break
                elif r.status == 403:
                    print(r.text)
                    self.error('Error 403, retrying...')
                    continue
                elif r.status == 400:
                    print(r.text)
                    self.error('Checkout failed, stopping!')
                    failed = True
                    continue
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting payment:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        if failed:
            self.cartcleaned = False
            self.s.cookies = {}
            self.get_login_redirect()
        self.pass_cookies()

    def pass_cookies(self):
        try:
            cookies = []
            for domain in self.s.cookies.keys():
                cookies.extend([{'name': key, 'value': value, 'domain': domain, 'path': '/'} for key, value in self.s.cookies[domain].items()])
            try:
                for element in copy.deepcopy(cookies):
                    for x in ['_abck', 'ak_bmsc', 'bm_sv', 'bm_sz', 'bm_mi']:
                        if x in element['name']:
                            cookies.remove(element)
                            break
            except Exception as e:
                print(e)
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
                    writer.writerow({'SITE':'ZALANDO','SIZE':f'{self.size}','PAYLINK':f'{self.expToken}','PRODUCT':f'{self.pid}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'ZALANDO','SIZE':f'{self.size}','PAYLINK':f'{self.expToken}','PRODUCT':f'{self.pid}'})
            self.webhook()
        except Exception as e: 
            self.error(f'Exception error while passing cookies {e}, retrying...')
            print(traceback.format_exc()) 

    def webhook(self):
            if self.all_proxies == None:
                self.px = 'LOCAL'
            if self.discountcode == '':
                self.discountcode = 'None'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**ZALANDO IT**', value = f'[{self.name}](https://www.zalando.it/catalogo/?q={self.pid})', inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.size, inline = True)
            embed.add_embed_field(name='**PRICE**', value = self.price, inline = True)
            embed.add_embed_field(name='MAIL', value = f'||{self.mail}||', inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'PAYPAL', inline = True)
            embed.add_embed_field(name='MODE', value = self.mode, inline = True)
            embed.add_embed_field(name='DISCOUNT', value = f'||{self.discountcode}||', inline = True)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False) 
            embed.add_embed_field(name='**Paypal Link**', value = f"||{self.ppurl}||", inline = False) 
            embed.set_thumbnail(url = self.img)   
            embed.set_footer(text = f"Phoenix AIO v2.0", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.pubblic()

    def pubblic(self):
            if self.discountsubmitted:
                self.disc = 'YES'
            else:
                self.disc = 'NO'
            webhook = DiscordWebhook(url = self.listsuccess, content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**ZALANDO IT**', value = f'[{self.name}](https://www.zalando.it/catalogo/?q={self.pid})', inline = False)    
            embed.add_embed_field(name=f'**PRODUCT**', value = self.pid, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.size, inline = True)
            embed.add_embed_field(name='**PRICE**', value = self.price, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'PAYPAL', inline = True)
            embed.add_embed_field(name='MODE', value = self.mode, inline = True)
            embed.add_embed_field(name='DISCOUNT', value = f'{self.disc}', inline = True)
            embed.add_embed_field(name='Delay', value = self.delay, inline = False)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = True)
            embed.set_thumbnail(url = self.img)   
            embed.set_footer(text = f"Phoenix AIO v2.0", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
                raise SystemExit
            except:
                raise SystemExit

    def preloadget(self):
        self.warn('Getting product page...')
        headers = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':f'/catalogo/?q={self.pid}',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile':'?0',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site':'none',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en'
        }
        while True:
            try:
                r = self.s.get(
                    f'https://www.zalando.it/catalogo/?q={self.pidpreload}',
                    headers = headers
                )
                if r.status == 302:
                    self.product_pathpreload = r.headers['Location'][0]
                    break
                else:
                    print(r.text)
                    print(r.status)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting product page:{e}, retrying...')
                self.build_proxy()
                continue
        self.preloadmonitor()

    def preloadmonitor(self):
        headers = {
            ':method':'GET',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':f'/catalogo/?q={self.pid}',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile':'?0',
            'upgrade-insecure-requests':'1',
            'user-agent':self.user_agent,
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site':'none',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en'
        }
        self.warn('Starting preload...')
        while True:
            try:
                r = self.s.get(
                    f'https://www.zalando.it{self.product_pathpreload}',
                    headers = headers
                )
                if r.status == 200:
                    r_json = json.loads(r.text.split('id="z-vegas-pdp-props" type="application/json"><![CDATA[')[1].split(']]></script>')[0])
                    if r_json['model']['articleInfo']['available'] == True and r_json['model']['articleInfo']['coming_soon'] == False:
                        self.pageimpressionid = r.text.split('pageImpressionId":"')[1].split('"')[0]
                        #self.zalandoexperiments = r.text.split('x-zalando-experiments":"')[1].split('"')[0]
                        unit = r_json['model']['articleInfo']['units']
                        sizes = []
                        variants = []
                        stock = []
                        for i in unit:
                            if i['available'] == True:
                                if i['stock'] > 0:
                                    variants.append(i['id'])
                        tot = zip(variants)
                        connect = list(tot)
                        scelta = random.choice(connect)
                        self.variantpreload = scelta[0]
                        break
                    else:
                        self.warn('Product oos, monitoring...')
                        time.sleep(self.delay)
                        continue
                else:
                    print(r.text)
                    print(r.status)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while getting product page:{e}, retrying...')
                self.build_proxy()
                print(traceback.format_exc())
                continue
        self.atcpreload()

    def atcpreload(self):
        headers = {
            ':method':'POST',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/api/graphql/add-to-cart/',
            'content-length':'',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
            'x-zalando-feature':'pdp',
            'sec-ch-ua-mobile':'?0',
            'user-agent':self.user_agent,
            'x-zalando-intent-context':'navigationTargetGroup=ALL',
            'content-type':'application/json',
            'x-zalando-request-uri':f'/catalogo/?q={self.pidpreload}',
            'x-page-impression-id':self.pageimpressionid,
            'dpr':'1',
            'viewport-width':'1920',
            #'x-zalando-experiments':self.zalandoexperiments,
            'accept':'*/*',
            'origin':'https://www.zalando.it',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'cors',
            'sec-fetch-dest':'empty',
            'referer':f'https://www.zalando.it/catalogo/?q={self.pidpreload}',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en'
        }
        payload = [{"id":"e7f9dfd05f6b992d05ec8d79803ce6a6bcfb0a10972d4d9731c6b94f6ec75033","variables":{"addToCartInput":{"productId":f"{self.variantpreload}","clientMutationId":"addToCartMutation"}}}]
        while True:
            try:
                r = self.s.post(
                    'https://www.zalando.it/api/graphql/add-to-cart/',
                    json = payload,
                    headers = headers
                )
                if r.status == 200:
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while adding to cart:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        if self.address != '':
            self.addresschange()
        else:
            self.checkoutget()

    def addresschange(self):
        self.warn('Setting new address...')
        headers = {
            ':method':'POST',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/api/checkout/create-or-update-address',
            'content-length':'',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
            'sec-ch-ua-mobile':'?0',
            'x-zalando-header-mode':'desktop',
            'x-zalando-checkout-app':'web',
            'content-type':'application/json',
           'accept':'application/json',
            'user-agent':self.user_agent,
            'x-zalando-footer-mode':'desktop',
            'origin':'https://www.zalando.it',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'cors',
            'sec-fetch-dest':'empty',
            'referer':'https://www.zalando.it/checkout/address',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
        }
        payload = {
            "address": {
                "city": self.city,
                "street": f'{self.address} {self.address2}',
                "country_code": "IT",
                "last_name": self.surname,
                "salutation": "Ms",
                "first_name": self.name,
                "zip": self.zipcode
            },
            "addressDestination": {
                "destination": {
                    "address": {
                        "salutation": "Ms",
                        "first_name": self.name,
                        "last_name": self.surname,
                        "country_code": "IT",
                        "city": self.city,
                        "zip": self.zipcode,
                        "street": f'{self.address} {self.address2}'
                    }
                },
                "normalized_address": {
                    "country_code": "IT",
                    "city": self.city,
                    "zip": self.zipcode,
                    "street": f'{self.address} {self.address2}',
                    "house_number": self.address2
                },
                "status": "https://docs.riskmgmt.zalan.do/address/correct",
                "blacklisted": False
            },
            "isDefaultShipping": True
        }
        while True:
            try:
                r = self.s.post(
                    'https://www.zalando.it/api/checkout/create-or-update-address',
                    json = payload,
                    headers = headers
                )
                if r.status == 200:
                    r_json = json.loads(r.text)
                    self.addressid = r_json['defaultShippingAddress']['id']
                    self.success('Successfully added new address!')
                    break
                elif r.status == 403:
                    r_json = json.loads(r.text)
                    time.sleep(r_json['wait'])
                    continue
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while submitting ship:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        self.addresspost()

    def addresspost(self):
        self.warn('Submitting shipping...')
        headers = {
            ':method':'POST',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':f'/api/checkout/address/{self.addressid}/default',
            'content-length':'',
            'sec-ch-ua':'"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
            'sec-ch-ua-mobile':'?0',
            'x-zalando-header-mode':'desktop',
            'x-zalando-checkout-app':'web',
            'content-type':'application/json',
            'accept':'application/json',
            'user-agent':self.user_agent,
            'x-zalando-footer-mode':'desktop',
            'origin':'https://www.zalando.it',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'cors',
            'sec-fetch-dest':'empty',
            'referer':'https://www.zalando.it/checkout/address',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en',
        }
        payload = {"isDefaultShipping": True}
        while True:
            try:
                r = self.s.post(
                    f'https://www.zalando.it/api/checkout/address/{self.addressid}/default',
                    json = payload,
                    headers = headers
                )
                if r.status == 200:
                    self.success('Successfully submitted shipping info!')
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                if 'Client.Timeout' in e:
                    self.error('Request timed out, retrying...')
                    continue
                else:
                    self.error(f'Exception while submitting ship:{e}, retrying...')
                    print(traceback.format_exc())
                    self.build_proxy()
                    continue
        self.paymentselection()

    def clearcartcheckout(self):
        self.warn('Clearing cart from preload...')
        headers = {
            ':method':'POST',
            ':authority':'www.zalando.it',
            ':scheme':'https',
            ':path':'/api/checkout/remove-confirmation-item',
            'content-length':'',
            'sec-ch-ua':'"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            'x-xsrf-token':self.s.cookies['www.zalando.it']['frsx'],
            'sec-ch-ua-mobile':'?0',
            'x-zalando-header-mode':'desktop',
            'x-zalando-checkout-app':'web',
            'content-type':'application/json',
            'x-zalando-footer-mode':'desktop',
            'accept':'application/json',
            'user-agent':self.user_agent,
            'sec-ch-ua-platform':'"Windows"',
            'origin':'https://www.zalando.it',
            'sec-fetch-site':'same-origin',
            'sec-fetch-mode':'cors',
            'sec-fetch-dest':'empty',
            'referer':'https://www.zalando.it/checkout/confirm',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
        }
        payload = {"simpleSku":self.variantpreload,"ids":[]}
        self.restart = False
        while True:
            try:
                r = self.s.post(
                    'https://www.zalando.it/api/checkout/remove-confirmation-item',
                    json = payload,
                    headers = headers
                )
                if r.status == 200:
                    self.preloadone = True
                    self.success('Successfully removed item from cart!')
                    break
                elif r.status == 403:
                    print(r.text)
                    self.build_proxy()
                    self.error('Proxy banned, restarting...')
                    self.restart = True
                    break
                else:
                    print(r.text)
                    print(r.status)
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e: 
                self.error(f'Exception while clearing cart:{e}, retrying...')
                print(traceback.format_exc())
                self.build_proxy()
                continue
        if self.restart:
            self.cartcleaned = False
            self.s.cookies = {}
            self.get_login_redirect()
        self.get_akamai_normal_path()