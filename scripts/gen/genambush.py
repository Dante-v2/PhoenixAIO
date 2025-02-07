import json, requests, threading, certifi, ssl, socket, hashlib, psutil, tempfile, csv, urllib3, sys, random, base64, platform, hashlib, random, atexit, ctypes, logging, webbrowser, signal, os, uuid, string
from mods.logger import info, warn, error
from random import randint
import requests
import cloudscraper
from discord_webhook import DiscordWebhook, DiscordEmbed
import lxml
from bs4 import BeautifulSoup as bs
import logging
import time, datetime
import re
import urllib.parse
import names
from card_identifier.card_type import identify_card_type
import uuid
from requests_html import HTMLSession
from twocaptcha import TwoCaptcha
from hawk_cf_api.hawk_cf import CF_2
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

cnum = 0

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

    error("FAILED TO READ CONFIG")
    pass



class GENAMBUSH():

    def __init__(self, row, i):


        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'genambush/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "genambush/proxies.txt")
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

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
        else:
            self.selected_proxies = None


        
        if config['anticaptcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'anticaptcha','api_key':config['anticaptcha'], 'no_proxy':True},doubleDown=False,requestPostHook=self.injection,debug=False)
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha'], 'no_proxy':True},doubleDown=False,requestPostHook=self.injection,debug=False)
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)
        
        self.name = names.get_first_name()
        self.surname = row['SURNAME']
        self.phone = str("0"+str(random.randint(7400000000,7999990000)))
        self.email = row['MAIL']
        self.password = row['PASSWORD']
        self.address1 = row['ADDRESS 1']
        self.address2 = row['ADDRESS 2']
        self.city = row['CITY']
        self.zip = row['ZIP']
        self.state = row['STATE']
        self.country = row['COUNTRY']

        self.address1 = f'{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)} {self.address1}'
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

        self.threadID = '%03d' % i
        self.twoCaptcha = str(config['2captcha'])

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
            self.s.proxies = self.selected_proxies
        self.bar()
        if self.surname == 'RANDOM':
            self.surname = names.get_last_name()
        if self.email[:6].upper() == "RANDOM":
            self.email = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.email.split("@")[1]).lower()

        self.year = str(random.randrange(1950, 2000))
        month = random.randrange(1,12)
        if month > 9:
            self.month = str(month)
        else:
            self.month = "0" + str(month)
        date = random.randrange(1,28)
        if date > 9:
            self.date = str(date)
        else:
            self.date = "0" + str(date)

        warn(f'[TASK {self.threadID}] [GEN_AMBUSH] - Starting tasks...')
        self.register()


    def choose_proxy(self, proxy_list):
        px = random.choice(proxy_list)
        if len(px.split(':')) == 2:
            return {
                'http': 'http://{}'.format(px),
                'https': 'http://{}'.format(px)
            }

        elif len(px.split(':')) == 4:
            splitted = px.split(':')
            return {
                'http': 'http://{0}:{1}@{2}:{3}'.format(splitted[2], splitted[3], splitted[0], splitted[1]),
                'https': 'http://{0}:{1}@{2}:{3}'.format(splitted[2], splitted[3], splitted[0], splitted[1])
            }

    def bar(self):
        if machineOS.lower() == 'windows':
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO - AMBUSH ACC GEN Running | Generated: {cnum}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO - AMBUSH ACC GEN Running | Generated: {cnum}\x07')

    def injection(self, session, response):
        self.bar()
        try:
            if helheim.isChallenge(session, response):
                self.warn('Solving Cloudflare v2')
                return helheim.solve(session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                warn(f'[TASK {self.threadID}] [GEN_AMBUSH] - Solving Cloudflare v2 api2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                warn(f'[TASK {self.threadID}] [GEN_AMBUSH] - Solving Cloudflare v2 api2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
            else:
                return response
   
    def register(self):

        self.mom = False

        global cnum

        try:

            if self.country == 'IT':
                self.countrynum = '101'

            if self.country == 'FR':
                self.countrynum = "70"

            if self.country == 'CH':
                self.countrynum = "197"

            if self.country == 'ES':
                self.countrynum = "187"

            if self.country == 'DE':
                self.countrynum = "77"

            if self.country == 'DK':
                self.countrynum = "54"

            if self.country == 'GB':
                self.countrynum = "215"

            if self.country == 'AT':
                self.countrynum = "13"

            if self.country == 'GR':
                self.countrynum = "80"

            if self.country == 'RU':
                self.countrynum = "170"

            if self.country == 'FI':
                self.countrynum = "69"
            
            if self.country == 'SK':
                self.countrynum = "182"

            if self.country == 'CZ':
                self.countrynum = "53"
            
            if self.country == 'NL':
                self.countrynum = "144"

            if self.country == 'SI':
                self.countrynum = "183"

            if self.country == 'PL':
                self.countrynum = "164"

            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US",
                'Accept-Encoding': 'gzip, deflate, br',
                'content-type': 'application/json',
                'ff-country': self.country,
                'ff-currency': self.currency,
                'referer': 'https://www.ambushdesign.com',
                'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1'
            }
            self.s.headers.update(headers)
            data = {
                "name": f"{self.name} {self.surname}",
                "firstName":self.name,
                "lastName":self.surname,
                "username": self.email,
                "email": self.email,
                "password": self.password
            }
            data2 = {
                "firstName": self.name,
                "lastName": self.surname,
                "phone": self.phone,
                "country": {
                    "id": self.countrynum
                },
                "addressLine1": self.address1,
                "addressLine2": self.address2,
                "addressLine3": f"{self.address1}, {self.address2}",
                "city": {
                    "name": self.city
                },
                "state": {
                    "name": self.state
                },
                "zipCode": self.zip,
                "vatNumber": ""
            }
            response = self.s.post('https://www.ambushdesign.com/api/legacy/v1/account/register', json = data)
            if response.status_code == 200:
                info(f'[TASK {self.threadID}] [GEN_AMBUSH] - Account created!')
                head = {
                    'x-newrelic-id': 'VQUCV1ZUGwIFVlBRDgcA'
                }
                self.s.headers.update(head)
                r = self.s.post('https://www.ambushdesign.com/api/legacy/v1/addressbook', json = data2)
                if r.status_code == 200:
                    js = json.loads(r.text)
                    idd = js['id']
                    self.s.put(f'https://www.ambushdesign.com/en-it/api/addressbook/shipping/{idd}')
                    if r.status_code == 200:
                        self.s.put(f'https://www.ambushdesign.com/en-it/api/addressbook/billing/{idd}')
                        info(f'[TASK {self.threadID}] [GEN_AMBUSH] - Address Saved!')
                        self.SavingAccount()
            else:
                error(response.status_code)


        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_AMBUSH] - Exception generating account: {e}')



    def SavingAccount(self):

        global cnum
        txt = self.email + ':' + self.password
        warn(f'[TASK {self.threadID}] [GEN_AMBUSH] - Saving account...')
        try:
            path = os.path.dirname(__file__).rsplit('/', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), "genambush")
            file_to_open = os.path.join(path, "output.txt")
            with open(file_to_open, 'a') as output:
                output.writelines(f'{txt}\n')
                output.close()
                info(f'[TASK {self.threadID}] [GEN_AMBUSH] - Accoutn saved in txt!')
                cnum = cnum + 1
                self.bar()
        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_AMBUSH] - Failed saving account {e}')