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



class GENGALERIES():

    def __init__(self, row, i):


        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'gengaleries/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "gengaleries/proxies.txt")
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

        if config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha']},doubleDown=False,requestPostHook=self.injection)
        elif config['anticaptcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'anticaptcha','api_key':config['anticaptcha']},doubleDown=False,requestPostHook=self.injection)
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)

        self.name = names.get_first_name()
        self.surname = names.get_last_name()
        self.phone = str("0"+str(random.randint(7400000000,7999990000)))
        self.mail = row['MAIL']
        self.password = row['PASSWORD'] 
        self.threadID = '%03d' % i
        self.timeout = 120
        self.twoCaptcha = str(config['2captcha'])

        if self.mail[:6].upper() == "RANDOM":
            self.mail = "{}{}{}@{}".format(self.name, self.surname.split(' ')[0], str(random.randint(1000,9999)), self.mail.split("@")[1]).lower()

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
        self.s.proxies = self.selected_proxies
        self.bar()

        warn(f'[TASK {self.threadID}] [GEN_GALERIES] - Starting tasks...')
        self.get_info()


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
                f'Phoenix AIO - GALERIES ACC Running | Generated: {cnum}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO - GALERIES ACC Running | Generated: {cnum}\x07')
    
    def injection(self, session, response):
        if helheim.isChallenge(session, response):
            warn(f'[TASK {self.threadID}] [GEN_GALERIES] - Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response

            #if session.is_New_IUAM_Challenge(response):
            #    warn(f'[TASK {self.threadID}] [GEN_GALERIES] - Solving Cloudflare v2 api 2')
            #    return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            #elif session.is_New_Captcha_Challenge(response):
            #    warn(f'[TASK {self.threadID}] [GEN_GALERIES] - Solving Cloudflare v2 api 2')
            #    return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
            #else:
            #    return response

   
    def get_info(self):

        global cnum

        warn(f'[TASK {self.threadID}] [GEN_GALERIES] - Getting login info...')
        try:
            while True:
                r = self.s.get(
                    'https://www.galerieslafayette.com/login', 
                    allow_redirects = True, 
                    timeout = self.timeout
                )

                if r.status_code == 200:
                    soup = bs(r.text, features='lxml')
                    ci = soup.find('div',{'class':'content-wrapper'})
                    forms = ci.find('form',{'id':'login-form'})
                    self.login_url = forms['action']
                    self.register_url = forms['action'].split('tab_id=')[1]
                    break

                else:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    error(f'[TASK {self.threadID}] [GEN_GALERIES] - Failed getting login info - {r.status_code}')
                    time.sleep(2)
                    continue

            self.register()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [GEN_GALERIES] - Connection error, retrying...')
            time.sleep(2)
            self.get_info()

        except TimeoutError:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [GEN_GALERIES] - Timeout reached, retrying...')
            time.sleep(2)
            self.get_info()
    
        except Exception as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [GEN_GALERIES] - Exception creating account: {e}')
            time.sleep(2)
            self.get_info()

    def register(self):

        try:

            try:
                while True:

                    x = self.s.get(
                        f'https://secure.galerieslafayette.com/auth/realms/gl/login-actions/registration?client_id=ecom-front&tab_id={self.register_url}', 
                        timeout = self.timeout, 
                        allow_redirects = True
                    )

                    if x.status_code == 200:

                        soup = bs(x.text, features='lxml')
                        ci = soup.find('div',{'class':'content-wrapper'})
                        forms = ci.find('form',{'id':'create-new-account-form'})
                        self.registration = forms['action']

                        day = str(random.randint(10,31))
                        month = str(random.randint(10,12))
                        year = str(random.randint(1990,2000))

                        warn(f'[TASK {self.threadID}] [GEN_GALERIES] - Solving captcha...')
                        solver = TwoCaptcha(config['2captcha'])
                        result = solver.recaptcha(sitekey='6LezI7AUAAAAAAzEiviPwx1gNVPcH2TMVsOMxxbd', url=x.url)
                        code = result['code']
                        info(f'[TASK {self.threadID}] [GEN_GALERIES] - Captcha solved')

                        payload = {
                            'rememberMe': 'on',
                            'user.attributes.brand': 'GL',
                            'siteUrl': 'https://www.galerieslafayette.com',
                            'isGC': 'false',
                            'isFid': 'false',
                            'user.attributes.title': 'MR',
                            'lastName': self.surname,
                            'firstName': self.name,
                            'email': self.mail,
                            'user.attributes.phoneNumber': '',
                            'user.attributes.birthDate': f'{day}-{month}-{year}',
                            'password': self.password,
                            'password-confirm': self.password,
                            'g-recaptcha-response':code,
                            'gl-soft-cs': 'd021bbf0-735d-438f-a272-fa638ac1d2fa'
                        }


                        s = self.s.post(self.registration, data = payload, timeout = self.timeout, allow_redirects = True) 

                        if s.status_code == 200 and 'Votre compte est' in s.text and not 'Une erreur est survenue' in s.text:
                            info(f'[TASK {self.threadID}] [GEN_GALERIES] - Account Successfully registered')
                            self.s.cookies.clear()
                            break

                        elif s.status_code >= 500 and s.status_code <= 600:
                            warn(f'[TASK {self.threadID}] [GALERIES] - Site dead, retrying...')
                            time.sleep(2)
                            continue

                        elif s.status_code == 403:
                            error(f'[TASK {self.threadID}] [GALERIES] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(2)
                            continue

                        elif s.status_code == 404:
                            error(f'[TASK {self.threadID}] [GALERIES] - Page not loaded, retrying...')
                            time.sleep(2)
                            continue

                        elif s.status_code == 429:
                            error(f'[TASK {self.threadID}] [GALERIES] - Rate limit, retrying...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(2)
                            continue

                        else:
                            error(f'[TASK {self.threadID}] [GALERIES] - Error {s.status_code}, retrying...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(2)
                            continue
                        

                    elif x.status_code >= 500 and x.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [GALERIES] - Site dead, retrying...')
                        time.sleep(2)
                        continue

                    elif x.status_code == 403:
                        error(f'[TASK {self.threadID}] [GALERIES] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(2)
                        continue

                    elif x.status_code == 404:
                        error(f'[TASK {self.threadID}] [GALERIES] - Page not loaded, retrying...')
                        time.sleep(2)
                        continue

                    elif x.status_code == 429:
                        error(f'[TASK {self.threadID}] [GALERIES] - Rate limit, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(2)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [GALERIES] - Error {x.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(2)
                        continue

                self.save_account()

            except Exception as e:
                error(f'[TASK {self.threadID}] [GALERIES] - Exception creating account: {e}, retrying...')
                time.sleep(2)
                self.register()
        except:
            pass

    def save_account(self):

        global cnum
        txt = self.mail + ':' + self.password
        warn(f'[TASK {self.threadID}] [GEN_GALERIES] - Saving account...')
        try:
            path = os.path.dirname(__file__).rsplit('/', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), "gengaleries")
            file_to_open = os.path.join(path, "output.txt")
            with open(file_to_open, 'a') as output:
                output.writelines(f'{txt}\n')
                output.close()
                info(f'[TASK {self.threadID}] [GEN_GALERIES] - Account saved in txt')
                cnum = cnum + 1
                self.bar()
        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_GALERIES] - Failed saving account')
            input("")