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

def encode(data, boundary):
    fields = [
        f'--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{value}\r\n' for field, value in data.items()
    ]

    body = ''.join(fields) + f'--{boundary}--\r\n'

    return body

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



class GENCORNER():

    def __init__(self, row, i):


        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'gencorner/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "gencorner/proxies.txt")
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
            error('2Captcha or AntiCaptcha needed. Stopping task.')
            sys.exit(1)

        self.s = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
                },
                captcha=self.captcha,
                doubleDown=False,
                requestPostHook=self.injection
        )

        self.name = names.get_first_name()
        self.surname = names.get_last_name()
        self.mail = row['MAIL']
        self.password = row['PASSWORD'] 
        self.threadID = '%03d' % i
        self.twoCaptcha = str(config['2captcha'])

        if self.mail[:6].upper() == "RANDOM":
            self.mail = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.mail.split("@")[1]).lower()

        self.build_proxy()

        self.bar()

        warn(f'[TASK {self.threadID}] [GEN_CORNER] - Starting tasks...')
        self.register()


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
                f'Phoenix AIO - CORNER ACC Running | Generated: {cnum}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO - CORNER ACC Running | Generated: {cnum}\x07')


    def injection(self, session, response):
        #try:
        if helheim.isChallenge(session, response):
            warn(f'[TASK {self.threadID}] [GEN_CORNER] - Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response
        #except:
        #    if session.is_New_IUAM_Challenge(response):
        #        warn(f'[TASK {self.threadID}] [GEN_CORNER] - Solving Cloudflare v2 api 2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
        #    elif session.is_New_Captcha_Challenge(response):
        #        warn(f'[TASK {self.threadID}] [GEN_CORNER] - Solving Cloudflare v2 api 2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
        #    else:
        #        return response

   
    def register(self):

        self.mom = False

        global cnum

        warn(f'[TASK {self.threadID}] [GEN_CORNER] - Getting account information...')
        try:
            while True:
                t = self.s.get("https://www.cornerstreet.fr/customer/account/create/")

                if t.status_code == 200:
                    soup = bs(t.text, features='lxml')
                    title = soup.find('div',{'class':'columns'})
                    form = title.find('div',{'class':'column main'})
                    self.formkey = form.find('input',{'name':'form_key'})['value']
                    try:

                        warn(f'[TASK {self.threadID}] [GEN_CORNER] - Creating account...')
                        payload = {
                            'form_key':self.formkey,
                            'success_url':'',		
                            'error_url':'',
                            'firstname':self.name,
                            'lastname':self.surname,
                            'assistance_allowed':1,
                            'email':self.mail,
                            'password':self.password,
                            'password_confirmation':self.password
                        }

                        self.formData = encode(payload, "----WebKitFormBoundaryaRResNFUbNPlP8am")

                        headers = {
                            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
                            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                            'sec-fetch-site':'same-origin',
                            'sec-fetch-mode':'navigate',
                            'sec-fetch-user':'?1',
                            'sec-fetch-dest':'document',
                            'referer':'https://www.cornerstreet.fr/customer/account/create/',
                            'content-type': 'multipart/form-data; boundary=----WebKitFormBoundaryaRResNFUbNPlP8am'
                        }

                        r = self.s.post("https://www.cornerstreet.fr/customer/account/createpost/", data = self.formData, headers = headers, allow_redirects = False)
                        
                        if r.headers['location'] == 'https://www.cornerstreet.fr/customer/account/':
                            info(f'[TASK {self.threadID}] [GEN_CORNER] - Account created!')
                            break
                        else:
                            error(f'[TASK {self.threadID}] [GEN_CORNER] - Error creating account, check your information')
                            sys.exit()

                    except Exception as e:
                        error( f"[TASK {self.threadID}] [GEN_CORNER] - Error getting account information")  

                else:
                    error(f'[TASK {self.threadID}] [GEN_CORNER] - Failed getting information')
            self.SavingAccount()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [GEN_CORNER] - Connection error, retrying...')
            time.sleep(2)
            self.register()

        except TimeoutError:
            error(f'[TASK {self.threadID}] [GEN_CORNER] - Timeout reached, retrying...')
            time.sleep(2)
            self.register()
    
        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_CORNER] - Exception creating account {e}')
            time.sleep(2)
            self.register()



    def SavingAccount(self):

        global cnum
        txt = self.mail + ':' + self.password
        warn(f'[TASK {self.threadID}] [GEN_CORNER] - Saving account...')
        try:
            path = os.path.dirname(__file__).rsplit('/', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), "gencorner")
            file_to_open = os.path.join(path, "output.txt")
            with open(file_to_open, 'a') as output:
                output.writelines(f'{txt}\n')
                output.close()
                info(f'[TASK {self.threadID}] [GEN_CORNER] - Account saved in txt')
                cnum = cnum + 1
                self.bar()
        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_CORNER] - Failed saving account')
            input("")