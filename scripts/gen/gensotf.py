import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, os, time, re, urllib, cloudscraper, names, lxml, pytz, copy
from mods.logger import info, warn, error
from random import randint
import cloudscraper
from discord_webhook import DiscordWebhook, DiscordEmbed
import lxml
from bs4 import BeautifulSoup as bs
import time, datetime
import re
import urllib.parse
import names
from twocaptcha import TwoCaptcha
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')


urllib3.disable_warnings()
version = '0.1.8'
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



class GENSOTF():

    def __init__(self, row, i):


        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'gensotf/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "gensotf/proxies.txt")
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

        

        
        self.headers = {
            "accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding" : "gzip, deflate",
            "accept-language" : "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6" ,
            "sec-fetch-dest" : "document" ,
            "sec-fetch-mode" : "navigate",
            "sec-fetch-site" : "none",
            "sec-fetch-user" : "?1",
            "upgrade-insecure-requests" : "1",
            "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
        }

        self.generator_url = "https://www.sotf.com/it/secure/request_account.php"
        self.name = names.get_first_name()
        self.surname = names.get_last_name()
        self.email = row['GMAIL']
        self.password = row['PASSWORD']
        self.threadID = '%03d' % i
        self.twoCaptcha = str(config['2captcha'])

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
            self.s.proxies = self.selected_proxies
        self.bar()

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

        warn(f'[TASK {self.threadID}] [GEN_SOTF] - Starting tasks...')
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
                'https': 'https://{0}:{1}@{2}:{3}'.format(splitted[2], splitted[3], splitted[0], splitted[1])
            }

    def bar(self):
        if machineOS.lower() == 'windows':
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO - SOTF ACC Running | Generated: {cnum}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO - SOTF ACC Running | Generated: {cnum}\x07')

    def injection(self, session, response):
        try:
            if helheim.isChallenge(session, response):
                warn('Solving Cloudflare v2')
                return helheim.solve(session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                warn('Solving Cloudflare v2 api 2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                warn('Solving Cloudflare v2 api 2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
            else:
                return response
   
    def register(self):

        self.mom = False

        global cnum

        try:
            t = self.s.get("https://www.sotf.com/it/secure/request_account.php")

            try:
                warn(f'[TASK {self.threadID}] [GEN_SOTF] - Solving captcha...')
                solver = TwoCaptcha(self.twoCaptcha)
                result = solver.recaptcha(sitekey="6Lcm-XIUAAAAAMSMGVyiOx_jSYwkq9XyZgyj8pL9", url='https://www.sotf.com/it/secure/request_account.php')
                self.captcha = result['code']

                info(f'[TASK {self.threadID}] [GEN_SOTF] - Captcha Solved!')

                try:
                    
                    warn(f'[TASK {self.threadID}] [GEN_SOTF] - Creating account...')
                    payload = {
                        "from_cart" : "",
                        "no_reg" : "",
                        "SendData" : "1",
                        "Clienti_codice_alternativo" : "",
                        "is_azienda" : "0",
                        "Clienti_nome" : self.name,
                        "Clienti_password" : self.password,
                        "Clienti_email" : self.email,
                        "Clienti_ritenuta_sesso" : "M",
                        "Clienti_cognome" : self.surname,
                        "Clienti_password2" : self.password,
                        "Clienti_ritenuta_datanascita" : self.date + "/" + self.month + "/" + self.year,
                        "gg" : self.date,
                        "mm" : self.month,
                        "aa" : self.year,
                        "g-recaptcha-response": self.captcha,
                        "newsletter" : "1",
                        "LocationRedirect" : "Search.php",
                        "action" : "ins",
                        "clienti_ID" : "0",
                        "Clienti" : "",
                        "doit" : "1",
                        "user_track": "0"
                    }

                    if self.mom:
                        r = self.s.post("https://www.sotf.com/it/secure/request_account.php", data = payload)
                    else:
                        r = self.s.post("https://www.sotf.com/it/secure/request_account.php", data = payload, headers = self.headers)


                    if "Si sono verificati i seguenti errori" in r.text:
                        error(f'[TASK {self.threadID}] [GEN_SOTF] - Error creating account, restarting...')
                        self.register()

                    else:
                        info(f'[TASK {self.threadID}] [GEN_SOTF] - Account created!')
                        self.SavingAccount()

                except Exception as e:
                    error(f'[TASK {self.threadID}] [GEN_SOTF] - Error creating account')
            except:
                error(f'[TASK {self.threadID}] [GEN_SOTF] - Captcha failed')

        except:
            error(f'[TASK {self.threadID}] [GEN_SOTF] - Connection error')



    def SavingAccount(self):

        global cnum
        txt = self.email + ':' + self.password
        warn(f'[TASK {self.threadID}] [GEN_SOTF] - Saving account...')
        try:
            path = os.path.dirname(__file__).rsplit('/', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), "gensotf")
            file_to_open = os.path.join(path, "output.txt")
            with open(file_to_open, 'a') as output:
                output.writelines(f'{txt}\n')
                output.close()
                info(f'[TASK {self.threadID}] [GEN_SOTF] - Accoutn saved in txt!')
                cnum = cnum + 1
                self.bar()
        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_SOTF] - Failed saving account')