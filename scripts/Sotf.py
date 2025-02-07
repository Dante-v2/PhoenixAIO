import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
import helheim
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

urllib3.disable_warnings()
version = '0.1.8'
machineOS = platform.system()
sys.dont_write_bytecode = True

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

threads = {}
ipaddr = None

def perform_request(self, method, url, *args, **kwargs):
    if "proxies" in kwargs or "proxy"  in kwargs:
        return super(cloudscraper.CloudScraper, self).request(method, url, *args, **kwargs)
    else:
        return super(cloudscraper.CloudScraper, self).request(method, url, *args, **kwargs, proxies=self.proxies)
cloudscraper.CloudScraper.perform_request = perform_request

checkoutnum = 0
carted = 0
failed = 0

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

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

class SOTF():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'Sotf/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "Sotf/proxies.txt")
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
            self.s = cloudscraper.create_scraper(browser={
                    'browser': 'chrome',
                    'mobile': False,
                    'platform': 'windows'
                },
                captcha={
                    'provider':'anticaptcha',
                    'api_key':config['anticaptcha']
                },
                doubleDown=False,
                requestPostHook=self.injection
            )
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'mobile': False,
                    'platform': 'windows'
                },
                captcha={
                    'provider':'2captcha',
                    'api_key': config['2captcha']
                },
                doubleDown=False,
                requestPostHook=self.injection
            )
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)
        self.discord = DISCORD_ID
        self.account = row['ACCOUNT']
        self.password = row['PASSWORD']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.mail = row['MAIL']
        self.address = row['ADDRESS']
        self.num = row['NUM']
        self.region = row['REGION']
        self.zip = row['POSTCODE']
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.city = row['CITY']
        self.link = row['LINK']
        self.size =  row['SIZE']
        self.payment = row['PAYMENT']
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.delay = int(config["delay"])
        self.iscookiesfucked = False
        self.cfchl = False
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
            self.s.proxies = self.selected_proxies

        self.timeout = 120

        self.balance = balancefunc()

        self.bar()

        if "/en/" in self.link:
            self.dominio = "en"
        elif "/it/" in self.link:
            self.dominio = "it"

        if self.payment == 'PP':
            self.pay = 58
        elif self.payment == 'SOFORT':
            self.pay = 63
        else:
            error(f'[TASK {self.threadID}] [SOTF] - Payment not supported')

        try:
            if self.name.upper() == "RANDOM":
                self.name = names.get_first_name(gender='male')
            if self.surname.upper() == "RANDOM":
                self.surname = names.get_last_name()
            if self.phone.upper() == "RANDOM":
                self.phone = str("0"+str(random.randint(7400000000,7999990000)))
            if self.mail[:6].upper() == "RANDOM":
                self.mail = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.mail.split("@")[1]).lower()
        except: 
            error(f'[TASK {self.threadID}] [SOTF] - Error with csv') 



        self.user_agent = {"user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}

        if self.country == 'FR':
            self.country2 = '58'
        if self.country == 'ES':
            self.country2 = '162'
        if self.country == 'PT':
            self.country2 = '136'
        if self.country == 'GB':
            self.country2 = '138'
        if self.country == 'DE':
            self.country2 = '62'
        if self.country == 'CH':
            self.country2 = '169'
        if self.country == 'NL':
            self.country2 = '128'
        if self.country == 'BE':
            self.country2 = '17'
        if self.country == 'CZ':
            self.country2 = '139'
        if self.country == 'RO':
            self.country2 = '143'
        if self.country == 'DK':
            self.country2 = '47'
        if self.country == 'NO':
            self.country2 = '125'
        if self.country == 'FI':
            self.country2 = '57'
        if self.country == 'PL':
            self.country2 = '135'
        if self.country == 'HU':
            self.country2 = '185'
        if self.country == 'SV':
            self.country2 = '51'
        if self.country == 'HR':
            self.country2 = '45'
        if self.country == 'AT':
            self.country2 = '11'
        if self.country == 'AU':
            self.country2 = '10'
        if self.country == 'LI':
            self.country2 = '98'
        if self.country == 'LU':
            self.country2 = '100'
        if self.country == 'RU':
            self.country2 = '216'
        if self.country == 'BG':
            self.country2 = '27'
        if self.country == 'EE':
            self.country2 = '54'
        if self.country == 'IE':
            self.country2 = '81'
        if self.country == 'CY':
            self.country2 = '37'
        if self.country == 'LV':
            self.country2 = '94'
        if self.country == 'LT':
            self.country2 = '99'
        if self.country == 'MT':
            self.country2 = '107'
        if self.country == 'SI':
            self.country2 = '160'
        if self.country == 'SK':
            self.country2 = '159'
        if self.country == 'SE':
            self.country2 = '168'
        if self.country == 'GR':
            self.country2 = '68'


        warn(f'[TASK {self.threadID}] [SOTF] - Task started!')
        self.cookie()


    def choose_proxy(self, proxy_list):
        px = random.choice(proxy_list)
        self.proxi = px
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
                f'Phoenix AIO {self.version} - SOTF Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')

            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - SOTF Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')
        

    def injection(self, session, response):
        if helheim.isChallenge(session, response):
            self.warn(f'[TASK {self.threadID}] [SOTF] - Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response

    def cookie(self):

        try:


            warn(f'[TASK {self.threadID}] [SOTF] - Getting cookies...')

            r = self.s.get('https://www.sotf.com/it/login.php')

            if r.status_code == 200:
                info(f'[TASK {self.threadID}] [SOTF] - Succesfully got cookies!')
                self.login()

            elif r.status_code == 502:
                warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                time.sleep(self.delay)
                self.cookie()

            elif r.status_code == 504:
                warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                time.sleep(self.delay)
                self.cookie()
            
            elif r.status_code == 524:
                warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                time.sleep(self.delay)
                self.cookie()

            elif r.status_code == 403:
                error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.cookie()

            else:
                error(f'[TASK {self.threadID}] [SOTF] - Error {r.status_code}, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                return self.cookie()

        except Exception as e: 
            error(f'[TASK {self.threadID}] [SOTF] - Exception while getting cookie {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.cookie()

    def login(self):

        try:
            
            warn(f'[TASK {self.threadID}] [SOTF] - Logging in...')

            try:

                if self.country != 'IT':
                    self.ship52()


                login_form = {
                    'logging' : '1',
                    'from_cart' : '',
                    'from_reso' : '',
                    'clienti_user_name' : self.account,
                    'clienti_password' : self.password,
                    'button': 'LOGIN'
                }


                r = self.s.post(f"https://www.sotf.com/login.php", data = login_form, timeout = self.timeout)

                if r.status_code == 200 or 302:
                    
                    if 'di gestire tutti i tuoi dati e tutti i tuoi ordini' in r.text:
                        info(f'[TASK {self.threadID}] [SOTF] - Successfully logged in!')
                        self.parse()
                        
                    elif "In My Account section you can menage" in r.text:
                        info(f'[TASK {self.threadID}] [SOTF] - Successfully logged in!')
                        self.parse()

                    else:
                        error(f'[TASK {self.threadID}] [SOTF] - Error logging in, check your data!')
                        time.sleep(200)

                elif r.status_code == 502:
                    warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                    time.sleep(self.delay)
                    self.login()

                elif r.status_code == 504:
                    warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                    time.sleep(self.delay)
                    self.login()
                
                elif r.status_code == 524:
                    warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                    time.sleep(self.delay)
                    self.login()

                elif r.status_code == 403:
                    error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    self.login()

                else:
                    error(f'[TASK {self.threadID}] [SOTF] - Error {r.status_code}, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    return self.login()

            except Exception as e: 
                error(f'[TASK {self.threadID}] [SOTF] - Exception during login {e.__class__.__name__}, retrying...') 
                time.sleep(self.delay)
                self.login()
        
        except:
            pass

    def parse(self):

        try:

            global carted, failed, checkoutnum

            warn(f'[TASK {self.threadID}] [SOTF] - Scraping sizes...')

            try:

                while True:

                    r = self.s.get(self.link, timeout = self.timeout, allow_redirects = False)

                    soup = bs(r.text, features='lxml')
                    if r.status_code == 200:

                        if r.url != self.link:
                            warn(f'[TASK {self.threadID}] [SOTF] - Page not loaded, retrying...')
                            time.sleep(self.delay)
                            continue

                        elif "Sold out" in r.text:
                            warn(f'[TASK {self.threadID}] [SOTF] - Sold out, retrying...')
                            time.sleep(self.delay)
                            continue

                        else:
                            self.title = soup.find("div", {"class":"details_info_title"}).text
                            self.price = soup.find("div", {"class":"details_info_price"}).text
                            self.cookies = r.cookies
                            
                            id_size3 = soup.find("div", {"class":"details_info_size"})
                            id_size2 = id_size3.find_all("a", {"class":"PdsVariationSelection"})
                            self.sizes = []
                            self.varid = []
                            self.prodid = soup.find("input", {"name":"articoli_ID"})["value"]
                            for a in id_size2:
                                sizes = a.text
                                atcid = a["id"][11:]
                                self.varid.append(atcid)
                                lent = len(sizes)
                                if lent < 4:
                                    self.sizes.append(sizes)
                                
                            connect = zip(self.sizes, self.varid)
                            
                            self.atcvar = list(connect)
                            self.sizerange = []

                            info(f'[TASK {self.threadID}] [SOTF] - Succesfully got product page!')

                            try:
                                if self.size == "RANDOM":
                                    scelta = random.choice(self.atcvar)
                                    idscelto = scelta[1]
                                    self.sizescelta = "".join(idscelto)
                                    size = scelta[0]
                                    self.superattribute = "".join(size)
                                    warn(f'[TASK {self.threadID}] [SOTF] - Choosing size {self.superattribute}')
                                    break
                                
                                elif '-' in self.size:
                                    self.size1 = float(self.size.split('-')[0])
                                    self.size2 = float(self.size.split('-')[1])
                                    for x in self.atcvar:
                                        if self.size1 <= float(x[0]) <= self.size2:
                                            self.sizerange.append(x[0])     
                                    self.sizerandom = random.choice(self.sizerange)   
                                    for Traian in self.atcvar:
                                        if self.sizerandom == Traian[0]:
                                            idscelto = Traian[1]
                                            self.sizescelta = "".join(idscelto)
                                            self.superattribute = self.sizerandom
                                    warn(f'[TASK {self.threadID}] [SOTF] - Choosing size {self.superattribute}')
                                    break
                
                                elif ',' in self.size:
                                    self.size1 = float(self.size.split(',')[0])
                                    self.size2 = float(self.size.split(',')[1])
                                    for x in self.atcvar:
                                        if self.size1 <= float(x[0]) <= self.size2:
                                            self.sizerange.append(x[0])
                                    self.sizerandom = random.choice(self.sizerange)
                                    for Traian in self.atcvar:
                                        if self.sizerandom == Traian[0]:
                                            idscelto = Traian[1]
                                            self.sizescelta = "".join(idscelto)
                                            self.superattribute = self.sizerandom
                                    warn(f'[TASK {self.threadID}] [SOTF] - Choosing size {self.superattribute}')
                                    break

                                else:
                                    try:
                                        for Traian in self.atcvar:
                                            if self.size == Traian[0]:
                                                idscelto = Traian[1]
                                                self.sizescelta = "".join(idscelto)
                                                self.superattribute = self.size
                                    except:
                                        error(f'[TASK {self.threadID}] [SOTF] - Size is oos, retrying...')
                                        continue
                                    warn(f'[TASK {self.threadID}] [SOTF] - Monitoring size {self.size}...')
                                    break


                            except Exception as e: 
                                error(f'[TASK {self.threadID}] [SOTF] - Error parsing sizes {e.__class__.__name__}, retrying...') 


                    elif "404 - File or directory not found" in r.text:
                        warn(f'[TASK {self.threadID}] [SOTF] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 301:
                        warn(f'[TASK {self.threadID}] [SOTF] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 302:
                        warn(f'[TASK {self.threadID}] [SOTF] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 502:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue


                    elif r.status_code == 504:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue


                    elif r.status_code == 500:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue
                        

                    elif r.status_code == 524:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue


                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [SOTF] - Page not laoded, retrying...')
                        time.sleep(self.delay)
                        continue


                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue


                    else:
                        error(f'[TASK {self.threadID}] [SOTF] - Error {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue


                self.atc()

            
            except Exception as e: 
                error(f'[TASK {self.threadID}] [SOTF] - Exception while scraping size {e.__class__.__name__}, retrying...') 
                time.sleep(self.delay)
                self.parse()

        except:
            pass

    def atc(self):

        try:

            global carted, failed, checkoutnum

            warn(f'[TASK {self.threadID}] [SOTF] - Adding to cart...')
            
            try:

                headers = {
                    "Accept" : "*/*",
                    'Referer': self.link,
                    "X-Requested-With" : "XMLHttpRequest",
                }

                payload = {
                    "articoli_ID": self.prodid,
                    "documenti_dettaglio[0][articoli_ID]": self.prodid,
                    "documenti_dettaglio[0][varianti_ID1]" : self.sizescelta,
                    "documenti_dettaglio[0][varianti_ID2]": "0",
                    "documenti_dettaglio[0][varianti_ID3]": "0",
                    "documenti_dettaglio[0][varianti_ID4]": "0",
                    "documenti_dettaglio[0][articoli_quantita]": "1",
                    "postback": "1",
                    "from_dett": "false",
                    "ajaxMode": "true"
                }

                while True:

                    r = self.s.post(
                        f"https://www.sotf.com/{self.dominio}/cart.php", 
                        data = payload, 
                        headers=headers,
                        timeout = self.timeout,
                        allow_redirects=False
                    )

                    if r.status_code == 200 or 302:
                        if 'data-GTMevent="addToCart"' in r.text:
                            info(f'[TASK {self.threadID}] [SOTF] - Added to cart!')
                            carted = carted + 1
                            self.bar()
                            break

                        elif 'You have added a "release" item to your cart' in r.text:
                            info(f'[TASK {self.threadID}] [SOTF] - Added to cart!')
                            carted = carted + 1
                            self.bar()
                            break

                        elif 'un articolo "release' in r.text:
                            info(f'[TASK {self.threadID}] [SOTF] - Added to cart!')
                            carted = carted + 1
                            self.bar()
                            break

                        elif "L'articolo nella taglia o quantit" in r.text:
                            warn(f'[TASK {self.threadID}] [SOTF] - Size is oos, retrying...')
                            time.sleep(self.delay)
                            self.parse()
                            break

                        elif "un ordine contenente questo articolo" in r.text:
                            break
                        
                        elif 'By adding a Release item to your cart, you can lock its availability for 3 minutes. If you do not complete your purchase within this time, the item will be deleted from your cart and will be available for purchase again. So, if the item is already sold out, it is possible that it will come back available soon.' in r.text:
                            info(f'[TASK {self.threadID}] [SOTF] - Added to cart!')
                            carted = carted + 1
                            self.bar()
                            break

                        elif 'The size or the quantity of the requested item is not available' in r.text:
                            warn(f'[TASK {self.threadID}] [SOTF] - Size is oos, retrying...')
                            time.sleep(self.delay)
                            self.parse()
                            break

                        else:
                            error(f'[TASK {self.threadID}] [SOTF] - Cart failed: {r.status_code}, retrying...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(self.delay)
                            self.parse()

                    elif r.status_code == 502:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 504:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 500:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 524:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 522:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        open('sotf403xcc.html', 'w+', encoding='utf-8').write(r.text)
                        error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        error(f'[TASK {self.threadID}] [SOTF] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SOTF] - Error {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue


                if "un ordine contenente questo articolo" in r.text:
                    warn(f'[TASK {self.threadID}] [SOTF] - Product limited x1 for each account, stopping task!')
                else:
                    if self.country == 'IT':
                        self.checkout()
                    else:
                        self.checkest()
                    
            except Exception as e: 
                error(f'[TASK {self.threadID}] [SOTF] - Exception during atc {e}, retrying...') 
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.atc()

        except:
            pass

    def ship52(self):

        try:

            warn(f'[TASK {self.threadID}] [SOTF] - Changing site country...')

            global carted, failed, checkoutnum
            
            try:

                r = self.s.get(f"https://www.sotf.com/{self.dominio}/country_delivery_selection.php")




                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding': 'gzip, deflate',
                    'content-type' : 'application/x-www-form-urlencoded'
                }

                self.s.headers.update(headers)

                payload = {
                    'Nazioni_ID':self.country2
                }

                while True:

                    r = self.s.post(f"https://www.sotf.com/{self.dominio}/country_delivery_selection.php", data = payload, timeout = self.timeout)

                    if r.status_code == 200:    
                        break

                    elif r.status_code == 502:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 504:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 500:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 524:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SOTF] - Error {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue
                
                return info(f'[TASK {self.threadID}] [SOTF] - Country changed!')

            except Exception as e: 
                error(f'[TASK {self.threadID}] [SOTF] - Exception while changing country {e.__class__.__name__}, retrying...') 
                self.login()

        except:
            pass

    def checkout(self):

        try:

            global carted, failed, checkoutnum

            warn(f'[TASK {self.threadID}] [SOTF] - Submitting payment...')
            
            try:
                
                pagamento = {
                    'nazione_opt': '85',
                    'nazione[85]' : 'IT',
                    'province[AG]' : '84',
                    'province[AL]' : '6',
                    'province[AN]' : '42' ,
                    'province[AO]' : '7',
                    'province[AR]' : '51',
                    'province[AP]' : '44',
                    'province[AT]' : '5',
                    'province[AV]' : '64',
                    'province[BA]' : '72',
                    'province[BL]' : '25',
                    'province[BN]' : '62',
                    'province[BG]' : '16' ,
                    'province[BI]' : '96',
                    'province[BO]' : '37',
                    'province[BZ]' : '21',
                    'province[BS]' : '17',
                    'province[BR]' : '74',
                    'province[CA]' : '92',
                    'province[CL]' : '85' ,
                    'province[CB]' : '70',
                    'province[CI]' : '124',
                    'province[CE]' : '61',
                    'province[CT]' : '87',
                    'province[CZ]' : '79',
                    'province[CH]' : '69',
                    'province[VO]' : '105',
                    'province[CO]' : '13',
                    'province[CS]' : '78',
                    'province[CR]' : '19',
                    'province[KR]' : '101',
                    'province[CN]' : '4',
                    'province[EN]' : '86',
                    'province[EE]' : '106',
                    'province[FM]' : '181',
                    'province[FE]' : '38',
                    'province[FI]' : '48',
                    'province[FG]' : '71',
                    'province[FC]' : '40',
                    'province[FR]' : '60',
                    'province[GE]' : '10',
                    'province[GO]' : '31',
                    'province[GR]' : '53',
                    'province[IM]' : '8',
                    'province[IS]' : '94',
                    'province[AQ]' : '66',
                    'province[SP]' : '11',
                    'province[LT]' : '59',
                    'province[LE]' : '75',
                    'province[LC]' : '97',
                    'province[LI]' : '49',
                    'province[LO]' : '98',
                    'province[LU]' : '46',
                    'province[MC]' : '43',
                    'province[MN]' : '20',
                    'province[MS]' : '45',
                    'province[MT]' : '77',
                    'province[MD]' : '123',
                    'province[ME]' : '83',
                    'province[MI]' : '15',
                    'province[MO]' : '36',
                    'province[MB]' : '182',
                    'province[NA]' : '63',
                    'province[NO]' : '3',
                    'province[NU]' : '91',
                    'province[OG]' : '122',
                    'province[OT]' : '121',
                    'province[OR]' : '95',
                    'province[PD]' : '28',
                    'province[PA]' : '82',
                    'province[PR]' : '34',
                    'province[PV]' : '18',
                    'province[PG]' : '54',
                    'province[PU]' : '41',
                    'province[PE]' : '68',
                    'province[PC]' : '33',
                    'province[PI]' : '50',
                    'province[PT]' : '47',
                    'province[PN]' : '93',
                    'province[PZ]' : '76',
                    'province[PO]' : '100',
                    'province[RG]' : '88',
                    'province[RA]' : '39',
                    'province[RC]' : '80',
                    'province[RE]' : '35',
                    'province[SM]' : '104',
                    'province[RI]' : '57',
                    'province[RN]' : '99',
                    'province[RM]' : '58',
                    'province[RO]' : '29',
                    'province[SA]' : '65',
                    'province[SS]' : '90',
                    'province[SV]' : '9',
                    'province[SI]' : '52',
                    'province[SR]' : '89',
                    'province[SO]' : '14',
                    'province[TA]' : '73',
                    'province[TE]' : '67',
                    'province[TR]' : '55',
                    'province[TO]' : '1',
                    'province[TP]' : '81',
                    'province[TN]' : '22',
                    'province[TV]' : '26',
                    'province[TS]' : '32',
                    'province[UD]' : '30',
                    'province[VA]' : '12',
                    'province[VE]' : '27',
                    'province[VB]' : '103',
                    'province[VC]' : '2',
                    'province[VR]' : '23',
                    'province[VV]' : '102',
                    'province[VI]' : '24',
                    'province[VT]' : '56',
                    'Clienti_indirizzo' : self.address,
                    'Clienti_numcivico' : self.num,
                    'Clienti_cap' : self.zip,
                    'Clienti_citta' : self.city,
                    'Province_ID' : self.region,
                    'country' : self.country,
                    'Clienti_tel': self.phone,
                    'sped_to_cli' : '1',
                    'trigger_sped_to_cli' : '1',
                    'Clienti_sedi_ID' : '',
                    'nazione_sedi[211]' : 'AE',
                    'nazione_sedi[1]' : 'AF',
                    'nazione_sedi[2]' : 'AL',
                    'nazione_sedi[3]' : 'DZ',
                    'nazione_sedi[4]' : 'AD',
                    'nazione_sedi[5]' : 'AO',
                    'nazione_sedi[6]' : 'AG',
                    'nazione_sedi[7]' : 'SA',
                    'nazione_sedi[8]' : 'AR',
                    'nazione_sedi[9]' : 'AM',
                    'nazione_sedi[10]' : 'AU',
                    'nazione_sedi[11]' : 'AT',
                    'nazione_sedi[12]' : 'AZ',
                    'nazione_sedi[13]' : 'BS',
                    'nazione_sedi[202]' : 'BH',
                    'nazione_sedi[14]' : 'BH',
                    'nazione_sedi[15]' : 'BD',
                    'nazione_sedi[16]' : 'BB',
                    'nazione_sedi[17]' : 'BE',
                    'nazione_sedi[18]' : 'BZ',
                    'nazione_sedi[19]' : 'BJ',
                    'nazione_sedi[20]' : 'BT',
                    'nazione_sedi[21]' : 'BY',
                    'nazione_sedi[22]' : 'BO',
                    'nazione_sedi[23]' : 'BA',
                    'nazione_sedi[24]' : 'BW',
                    'nazione_sedi[25]' : 'BR',
                    'nazione_sedi[26]' : 'BN',
                    'nazione_sedi[27]' : 'BG',
                    'nazione_sedi[28]' : 'BF',
                    'nazione_sedi[29]' : 'BI',
                    'nazione_sedi[30]' : 'KH',
                    'nazione_sedi[31]' : 'CM',
                    'nazione_sedi[32]' : 'CA',
                    'nazione_sedi[33]' : 'CV',
                    'nazione_sedi[34]' : 'TD',
                    'nazione_sedi[35]' : 'CL',
                    'nazione_sedi[36]' : 'CN',
                    'nazione_sedi[37]' : 'CY',
                    'nazione_sedi[38]' : 'CO',
                    'nazione_sedi[39]' : 'KM',
                    'nazione_sedi[40]' : 'CG',
                    'nazione_sedi[41]' : 'KP',
                    'nazione_sedi[43]' : 'CI',
                    'nazione_sedi[44]' : 'CR',
                    'nazione_sedi[45]' : 'HR',
                    'nazione_sedi[47]' : 'DK',
                    'nazione_sedi[48]' : 'DM',
                    'nazione_sedi[210]' : 'AE',
                    'nazione_sedi[207]' : 'EC',
                    'nazione_sedi[49]' : 'EC',
                    'nazione_sedi[208]' : 'EG',
                    'nazione_sedi[50]' : 'EG',
                    'nazione_sedi[51]' : 'SV',
                    'nazione_sedi[52]' : 'AE',
                    'nazione_sedi[53]' : 'ER',
                    'nazione_sedi[54]' : 'EE',
                    'nazione_sedi[55]' : 'ET',
                    'nazione_sedi[204]' : 'PH',
                    'nazione_sedi[56]' : 'PH',
                    'nazione_sedi[57]' : 'FI',
                    'nazione_sedi[58]' : 'FR',
                    'nazione_sedi[59]' : 'GA',
                    'nazione_sedi[60]' : 'GM',
                    'nazione_sedi[61]' : 'GE',
                    'nazione_sedi[62]' : 'DE',
                    'nazione_sedi[63]' : 'GH',
                    'nazione_sedi[64]' : 'JM',
                    'nazione_sedi[206]' : 'JP',
                    'nazione_sedi[65]' : 'JP',
                    'nazione_sedi[197]' : 'GI',
                    'nazione_sedi[66]' : 'DJ',
                    'nazione_sedi[67]' : 'JO',
                    'nazione_sedi[68]' : 'GR',
                    'nazione_sedi[69]' : 'GD',
                    'nazione_sedi[201]' : 'GL',
                    'nazione_sedi[70]' : 'GT',
                    'nazione_sedi[195]' : 'GGY',
                    'nazione_sedi[71]' : 'GN',
                    'nazione_sedi[72]' : 'GQ',
                    'nazione_sedi[73]' : 'GW',
                    'nazione_sedi[74]' : 'GY',
                    'nazione_sedi[75]' : 'HT',
                    'nazione_sedi[76]' : 'HN',
                    'nazione_sedi[215]' : 'HK',
                    'nazione_sedi[209]' : 'IN',
                    'nazione_sedi[77]' : 'IN',
                    'nazione_sedi[205]' : 'ID',
                    'nazione_sedi[78]' : 'ID',
                    'nazione_sedi[79]' : 'IR',
                    'nazione_sedi[80]' : 'IQ',
                    'nazione_sedi[81]' : 'IE',
                    'nazione_sedi[82]' : 'IS',
                    'nazione_sedi[194]' : 'IM',
                    'nazione_sedi[198]' : 'IB',
                    'nazione_sedi[199]' : 'ES-',
                    'nazione_sedi[200]' : 'FO',
                    'nazione_sedi[83]' : 'FJ',
                    'nazione_sedi[84]' : 'IL',
                    'nazione_sedi[85]' : 'IT',
                    'nazione_sedi[196]' : 'JEY',
                    'nazione_sedi[87]' : 'KZ',
                    'nazione_sedi[88]' : 'KE',
                    'nazione_sedi[89]' : 'KG',
                    'nazione_sedi[90]' : 'KI',
                    'nazione_sedi[91]' : 'KW',
                    'nazione_sedi[92]' : 'LA',
                    'nazione_sedi[93]' : 'LS',
                    'nazione_sedi[94]' : 'LV',
                    'nazione_sedi[95]' : 'LB',
                    'nazione_sedi[96]' : 'LR',
                    'nazione_sedi[97]' : 'LY',
                    'nazione_sedi[98]' : 'LI',
                    'nazione_sedi[99]' : 'LT',
                    'nazione_sedi[100]' : 'LU',
                    'nazione_sedi[101]' : 'MK',
                    'nazione_sedi[102]' : 'MG',
                    'nazione_sedi[103]' : 'MW',
                    'nazione_sedi[203]' : 'MY',
                    'nazione_sedi[104]' : 'MY',
                    'nazione_sedi[105]' : 'MV',
                    'nazione_sedi[106]' : 'ML',
                    'nazione_sedi[107]' : 'MT',
                    'nazione_sedi[108]' : 'MA',
                    'nazione_sedi[109]' : 'MH',
                    'nazione_sedi[110]' : 'MR',
                    'nazione_sedi[111]' : 'MU',
                    'nazione_sedi[112]' : 'MX',
                    'nazione_sedi[113]' : 'FM',
                    'nazione_sedi[114]' : 'MD',
                    'nazione_sedi[115]' : 'MC',
                    'nazione_sedi[116]' : 'MN',
                    'nazione_sedi[117]' : 'MZ',
                    'nazione_sedi[118]' : 'MM',
                    'nazione_sedi[119]' : 'NA',
                    'nazione_sedi[120]' : 'NR',
                    'nazione_sedi[121]' : 'NP',
                    'nazione_sedi[122]' : 'NI',
                    'nazione_sedi[123]' : 'NE',
                    'nazione_sedi[124]' : 'NG',
                    'nazione_sedi[125]' : 'NO',
                    'nazione_sedi[126]' : 'NZ',
                    'nazione_sedi[127]' : 'OM',
                    'nazione_sedi[128]' : 'NL',
                    'nazione_sedi[129]' : 'PK',
                    'nazione_sedi[130]' : 'PW',
                    'nazione_sedi[131]' : 'PA',
                    'nazione_sedi[132]' : 'PG',
                    'nazione_sedi[133]' : 'PY',
                    'nazione_sedi[134]' : 'PE',
                    'nazione_sedi[135]' : 'PL',
                    'nazione_sedi[136]' : 'PT',
                    'nazione_sedi[137]' : 'QA',
                    'nazione_sedi[138]' : 'GB',
                    'nazione_sedi[139]' : 'CZ',
                    'nazione_sedi[140]' : 'CF',
                    'nazione_sedi[142]' : 'DO',
                    'nazione_sedi[143]' : 'RO',
                    'nazione_sedi[144]' : 'RW',
                    'nazione_sedi[216]' : 'RU',
                    'nazione_sedi[146]' : 'KN',
                    'nazione_sedi[147]' : 'LC',
                    'nazione_sedi[148]' : 'VC',
                    'nazione_sedi[150]' : 'WS',
                    'nazione_sedi[151]' : 'SM',
                    'nazione_sedi[152]' : 'VA',
                    'nazione_sedi[153]' : 'ST',
                    'nazione_sedi[154]' : 'SC',
                    'nazione_sedi[155]' : 'SN',
                    'nazione_sedi[156]' : 'SL',
                    'nazione_sedi[157]' : 'SG',
                    'nazione_sedi[158]' : 'SY',
                    'nazione_sedi[159]' : 'SK',
                    'nazione_sedi[160]' : 'SI',
                    'nazione_sedi[161]' : 'SO',
                    'nazione_sedi[162]' : 'ES',
                    'nazione_sedi[163]' : 'LK',
                    'nazione_sedi[164]' : 'US',
                    'nazione_sedi[165]' : 'ZA',
                    'nazione_sedi[212]' : 'KR',
                    'nazione_sedi[42]' : 'KR',
                    'nazione_sedi[166]' : 'SD',
                    'nazione_sedi[167]' : 'SR',
                    'nazione_sedi[168]' : 'SE',
                    'nazione_sedi[169]' : 'CH',
                    'nazione_sedi[170]' : 'SZ',
                    'nazione_sedi[171]' : 'TJ',
                    'nazione_sedi[172]' : 'TW',
                    'nazione_sedi[173]' : 'TZ',
                    'nazione_sedi[213]' : 'TH',
                    'nazione_sedi[174]' : 'TH',
                    'nazione_sedi[175]' : 'TL',
                    'nazione_sedi[176]' : 'TG',
                    'nazione_sedi[177]' : 'TO',
                    'nazione_sedi[178]' : 'TT',
                    'nazione_sedi[179]' : 'TN',
                    'nazione_sedi[214]' : 'TR',
                    'nazione_sedi[180]' : 'TR',
                    'nazione_sedi[181]' : 'TM',
                    'nazione_sedi[182]' : 'TV',
                    'nazione_sedi[183]' : 'UA',
                    'nazione_sedi[184]' : 'UG',
                    'nazione_sedi[185]' : 'HU',
                    'nazione_sedi[186]' : 'UY',
                    'nazione_sedi[187]' : 'UZ',
                    'nazione_sedi[188]' : 'VU',
                    'nazione_sedi[189]' : 'VE',
                    'nazione_sedi[190]' : 'VN',
                    'nazione_sedi[191]' : 'YE',
                    'nazione_sedi[192]' : 'ZM',
                    'nazione_sedi[193]' : 'ZW',
                    'Clienti_sedi_Nazioni_ID' : '85',
                    'province_sedi[AG]' : '84',
                    'province_sedi[AL]' : '6',
                    'province_sedi[AN]' : '42',
                    'province_sedi[AO]' : '7',
                    'province_sedi[AR]' : '51',
                    'province_sedi[AP]' : '44',
                    'province_sedi[AT]' : '5',
                    'province_sedi[AV]' : '64',
                    'province_sedi[BA]' : '72',
                    'province_sedi[BL]' : '25',
                    'province_sedi[BN]' : '62',
                    'province_sedi[BG]' : '16',
                    'province_sedi[BI]' : '96',
                    'province_sedi[BO]' : '37',
                    'province_sedi[BZ]' : '21',
                    'province_sedi[BS]' : '17',
                    'province_sedi[BR]' : '74',
                    'province_sedi[CA]' : '92',
                    'province_sedi[CL]' : '85',
                    'province_sedi[CB]' : '70',
                    'province_sedi[CI]' : '124',
                    'province_sedi[CE]' : '61',
                    'province_sedi[CT]' : '87',
                    'province_sedi[CZ]' : '79',
                    'province_sedi[CH]' : '69',
                    'province_sedi[VO]' : '105',
                    'province_sedi[CO]' : '13',
                    'province_sedi[CS]' : '78',
                    'province_sedi[CR]' : '19',
                    'province_sedi[KR]' : '101',
                    'province_sedi[CN]' : '4',
                    'province_sedi[EN]' : '86',
                    'province_sedi[EE]' : '106',
                    'province_sedi[FM]' : '181',
                    'province_sedi[FE]' : '38',
                    'province_sedi[FI]' : '48',
                    'province_sedi[FG]' : '71',
                    'province_sedi[FC]' : '40',
                    'province_sedi[FR]' : '60',
                    'province_sedi[GE]' : '10',
                    'province_sedi[GO]' : '31',
                    'province_sedi[GR]' : '53',
                    'province_sedi[IM]' : '8',
                    'province_sedi[IS]' : '94',
                    'province_sedi[AQ]' : '66',
                    'province_sedi[SP]' : '11',
                    'province_sedi[LT]' : '59',
                    'province_sedi[LE]' : '75',
                    'province_sedi[LC]' : '97',
                    'province_sedi[LI]' : '49',
                    'province_sedi[LO]' : '98',
                    'province_sedi[LU]' : '46',
                    'province_sedi[MC]' : '43',
                    'province_sedi[MN]' : '20',
                    'province_sedi[MS]' : '45',
                    'province_sedi[MT]' : '77',
                    'province_sedi[MD]' : '123',
                    'province_sedi[ME]' : '83',
                    'province_sedi[MI]' : '15',
                    'province_sedi[MO]' : '36',
                    'province_sedi[MB]' : '182',
                    'province_sedi[NA]' : '63',
                    'province_sedi[NO]' : '3',
                    'province_sedi[NU]' : '91',
                    'province_sedi[OG]' : '122',
                    'province_sedi[OT]' : '121',
                    'province_sedi[OR]' : '95',
                    'province_sedi[PD]' : '28',
                    'province_sedi[PA]' : '82',
                    'province_sedi[PR]' : '34',
                    'province_sedi[PV]' : '18',
                    'province_sedi[PG]' : '54',
                    'province_sedi[PU]' : '41',
                    'province_sedi[PE]' : '68',
                    'province_sedi[PC]' : '33',
                    'province_sedi[PI]' : '50',
                    'province_sedi[PT]' : '47',
                    'province_sedi[PN]' : '93',
                    'province_sedi[PZ]' : '76',
                    'province_sedi[PO]' : '100',
                    'province_sedi[RG]' : '88',
                    'province_sedi[RA]' : '39',
                    'province_sedi[RC]' : '80',
                    'province_sedi[RE]' : '35',
                    'province_sedi[SM]' : '104',
                    'province_sedi[RI]' : '57',
                    'province_sedi[RN]' : '99',
                    'province_sedi[RM]' : '58',
                    'province_sedi[RO]' : '29',
                    'province_sedi[SA]' : '65',
                    'province_sedi[SS]' : '90',
                    'province_sedi[SV]' : '9',
                    'province_sedi[SI]' : '52',
                    'province_sedi[SR]' : '89',
                    'province_sedi[SO]' : '14',
                    'province_sedi[TA]' : '73',
                    'province_sedi[TE]' : '67',
                    'province_sedi[TR]' : '55',
                    'province_sedi[TO]' : '1',
                    'province_sedi[TP]' : '81',
                    'province_sedi[TN]' : '22',
                    'province_sedi[TV]' : '26',
                    'province_sedi[TS]' : '32',
                    'province_sedi[UD]' : '30',
                    'province_sedi[VA]' : '12',
                    'province_sedi[VE]' : '27',
                    'province_sedi[VB]' : '103',
                    'province_sedi[VC]' : '2',
                    'province_sedi[VR]' : '23',
                    'province_sedi[VV]' : '102',
                    'province_sedi[VI]' : '24',
                    'province_sedi[VT]' : '56',
                    'Clienti_sedi_nome' : '',
                    'Clienti_sedi_cognome' : '',
                    'Clienti_sedi_indirizzo' : '',
                    'Clienti_sedi_numcivico' : '',
                    'Clienti_sedi_cap' : '',
                    'Clienti_sedi_citta' : '',
                    'Clienti_sedi_Province_ID' : self.region,
                    'country_sedi' : self.country,
                    'richiede_fattura' : '',
                    'Clienti_sedi_ID_fatt' : '',
                    'Clienti_sedi_Nazioni_ID_fatt' : '85',
                    'Clienti_sedi_ragsociale_fatt' : '',
                    'Clienti_sedi_PI_fatt' : '',
                    'Clienti_sedi_indirizzo_fatt' : '',
                    'Clienti_sedi_numcivico_fatt' : '',
                    'Clienti_sedi_cap_fatt' : '',
                    'Clienti_sedi_citta_fatt' : '',
                    'Clienti_sedi_Province_ID_fatt' : '',
                    'vettori_ID' : '19',
                    'coupon_code': '',
                    'pagamenti_ID' : '58',
                    'sum_up_images_zip' : '1',
                    'Clienti_email' : self.mail
                }

                headers2 = {
                    "content-Type": "application/x-www-form-urlencoded",
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9"
                }
                
                self.s.headers.update(headers2)

                t = self.s.post(f"https://www.sotf.com/{self.dominio}/secure/sum_up.php", data = pagamento, timeout = self.timeout)

                while True:

                    if t.status_code in (200,302):
                        
                        warn(f'[TASK {self.threadID}] [SOTF] - Submitting order...')

                        r = self.s.post(f"https://www.sotf.com/{self.dominio}/check_out.php", data = pagamento)

                        if r.status_code == 200 or 302:
                            
                            try:
                                soup = bs(r.text, features='lxml')
                                pp1 = soup.find_all("meta")[-1]
                                pp2 = pp1["content"]
                                self.paypal = pp2.split("url=")[1]
                                info(f'[TASK {self.threadID}] [SOTF] - Successfully checked out!')
                                self.fallito = False
                                checkoutnum = checkoutnum + 1
                                self.bar()
                                break

                            except:
                                self.paypal = r.text.split("document.location.href='")[1].split("'")[0]
                                info(f'[TASK {self.threadID}] [SOTF] - Successfully checked out!')
                                self.fallito = False
                                checkoutnum = checkoutnum + 1
                                self.bar()
                                break



                        elif r.status_code == 502:
                            warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                            time.sleep(self.delay)
                            continue

                        elif r.status_code == 504:
                            warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                            time.sleep(self.delay)
                            continue

                        elif r.status_code == 500:
                            warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                            time.sleep(self.delay)
                            self.parse()

                        elif r.status_code == 524:
                            warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                            time.sleep(self.delay)
                            continue


                        elif r.status_code == 403:
                            error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, retrying...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(self.delay)
                            continue

                        else:
                            error(f'[TASK {self.threadID}] [SOTF] - Error {r.status_code}, retrying')
                            failed = failed + 1
                            self.bar()
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(self.delay)
                            continue


                    elif t.status_code == 502:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        continue

                    elif t.status_code == 504:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        continue

                    elif t.status_code == 524:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        continue

                    elif t.status_code == 500:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif t.status_code == 403:
                        error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:


                        error(f'[TASK {self.threadID}] [SOTF] - Error {t.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue


                if self.fallito:
                    self.selenium2()
                else:
                    self.selenium()
                
            except Exception as e: 
                error(f'[TASK {self.threadID}] [SOTF] - Exception submitting order {e.__class__.__name__}, retrying...') 
                self.s.cookies.clear()
                self.login()

        except:
            pass

    def checkest(self):

        try:

            global carted, failed, checkoutnum

            warn(f'[TASK {self.threadID}] [SOTF] - Submitting payment...')

            try:
                
                pagamento = {
                    'nazione_sedi[211]':'AE',
                    'nazione_sedi[1]':'AF',
                    'nazione_sedi[2]':'AL',
                    'nazione_sedi[3]':'DZ',
                    'nazione_sedi[4]':'AD',
                    'nazione_sedi[5]':'AO',
                    'nazione_sedi[6]':'AG',
                    'nazione_sedi[8]':'AR',
                    'nazione_sedi[9]':'AM',
                    'nazione_sedi[10]':'AU',
                    'nazione_sedi[11]':'AT',
                    'nazione_sedi[12]':'AZ',
                    'nazione_sedi[13]':'BS',
                    'nazione_sedi[202]':'BH',
                    'nazione_sedi[14]':'BH',
                    'nazione_sedi[198]':'IB',
                    'nazione_sedi[15]':'BD',
                    'nazione_sedi[16]':'BB',
                    'nazione_sedi[21]':'BY',
                    'nazione_sedi[17]':'BE',
                    'nazione_sedi[18]':'BZ',
                    'nazione_sedi[19]':'BJ',
                    'nazione_sedi[20]':'BT',
                    'nazione_sedi[22]':'BO',
                    'nazione_sedi[23]':'BA',
                    'nazione_sedi[24]':'BW',
                    'nazione_sedi[25]':'BR',
                    'nazione_sedi[26]':'BN',
                    'nazione_sedi[27]':'BG',
                    'nazione_sedi[28]':'BF',
                    'nazione_sedi[29]':'BI',
                    'nazione_sedi[30]':'KH',
                    'nazione_sedi[31]':'CM',
                    'nazione_sedi[32]':'CA',
                    'nazione_sedi[199]':'ES-',
                    'nazione_sedi[33]':'CV',
                    'nazione_sedi[140]':'CF',
                    'nazione_sedi[34]':'TD',
                    'nazione_sedi[35]':'CL',
                    'nazione_sedi[36]':'CN',
                    'nazione_sedi[38]':'CO',
                    'nazione_sedi[39]':'KM',
                    'nazione_sedi[40]':'CG',
                    'nazione_sedi[44]':'CR',
                    'nazione_sedi[43]':'CI',
                    'nazione_sedi[45]':'HR',
                    'nazione_sedi[37]':'CY',
                    'nazione_sedi[139]':'CZ',
                    'nazione_sedi[47]':'DK',
                    'nazione_sedi[66]':'DJ',
                    'nazione_sedi[48]':'DM',
                    'nazione_sedi[142]':'DO',
                    'nazione_sedi[210]':'AE',
                    'nazione_sedi[175]':'TL',
                    'nazione_sedi[207]':'EC',
                    'nazione_sedi[49]':'EC',
                    'nazione_sedi[208]':'EG',
                    'nazione_sedi[50]':'EG',
                    'nazione_sedi[51]':'SV',
                    'nazione_sedi[72]':'GQ',
                    'nazione_sedi[53]':'ER',
                    'nazione_sedi[54]':'EE',
                    'nazione_sedi[55]':'ET',
                    'nazione_sedi[200]':'FO',
                    'nazione_sedi[83]':'FJ',
                    'nazione_sedi[57]':'FI',
                    'nazione_sedi[58]':'FR',
                    'nazione_sedi[59]':'GA',
                    'nazione_sedi[60]':'GM',
                    'nazione_sedi[61]':'GE',
                    'nazione_sedi[62]':'DE',
                    'nazione_sedi[63]':'GH',
                    'nazione_sedi[197]':'GI',
                    'nazione_sedi[68]':'GR',
                    'nazione_sedi[201]':'GL',
                    'nazione_sedi[69]':'GD',
                    'nazione_sedi[70]':'GT',
                    'nazione_sedi[195]':'GGY',
                    'nazione_sedi[71]':'GN',
                    'nazione_sedi[73]':'GW',
                    'nazione_sedi[74]':'GY',
                    'nazione_sedi[75]':'HT',
                    'nazione_sedi[152]':'VA',
                    'nazione_sedi[76]':'HN',
                    'nazione_sedi[215]':'HK',
                    'nazione_sedi[185]':'HU',
                    'nazione_sedi[82]':'IS',
                    'nazione_sedi[209]':'IN',
                    'nazione_sedi[77]':'IN',
                    'nazione_sedi[205]':'ID',
                    'nazione_sedi[78]':'ID',
                    'nazione_sedi[79]':'IR',
                    'nazione_sedi[80]':'IQ',
                    'nazione_sedi[81]':'IE',
                    'nazione_sedi[194]':'IM',
                    'nazione_sedi[84]':'IL',
                    'nazione_sedi[85]':'IT',
                    'nazione_sedi[64]':'JM',
                    'nazione_sedi[206]':'JP',
                    'nazione_sedi[65]':'JP',
                    'nazione_sedi[196]':'JEY',
                    'nazione_sedi[67]':'JO',
                    'nazione_sedi[87]':'KZ',
                    'nazione_sedi[88]':'KE',
                    'nazione_sedi[90]':'KI',
                    'nazione_sedi[91]':'KW',
                    'nazione_sedi[89]':'KG',
                    'nazione_sedi[92]':'LA',
                    'nazione_sedi[94]':'LV',
                    'nazione_sedi[95]':'LB',
                    'nazione_sedi[93]':'LS',
                    'nazione_sedi[96]':'LR',
                    'nazione_sedi[97]':'LY',
                    'nazione_sedi[98]':'LI',
                    'nazione_sedi[99]':'LT',
                    'nazione_sedi[100]':'LU',
                    'nazione_sedi[101]':'MK',
                    'nazione_sedi[102]':'MG',
                    'nazione_sedi[103]':'MW',
                    'nazione_sedi[203]':'MY',
                    'nazione_sedi[104]':'MY',
                    'nazione_sedi[105]':'MV',
                    'nazione_sedi[106]':'ML',
                    'nazione_sedi[107]':'MT',
                    'nazione_sedi[109]':'MH',
                    'nazione_sedi[110]':'MR',
                    'nazione_sedi[111]':'MU',
                    'nazione_sedi[112]':'MX',
                    'nazione_sedi[113]':'FM',
                    'nazione_sedi[114]':'MD',
                    'nazione_sedi[115]':'MC',
                    'nazione_sedi[116]':'MN',
                    'nazione_sedi[108]':'MA',
                    'nazione_sedi[117]':'MZ',
                    'nazione_sedi[118]':'MM',
                    'nazione_sedi[119]':'NA',
                    'nazione_sedi[120]':'NR',
                    'nazione_sedi[121]':'NP',
                    'nazione_sedi[128]':'NL',
                    'nazione_sedi[126]':'NZ',
                    'nazione_sedi[122]':'NI',
                    'nazione_sedi[123]':'NE',
                    'nazione_sedi[124]':'NG',
                    'nazione_sedi[41]':'KP',
                    'nazione_sedi[125]':'NO',
                    'nazione_sedi[127]':'OM',
                    'nazione_sedi[129]':'PK',
                    'nazione_sedi[130]':'PW',
                    'nazione_sedi[131]':'PA',
                    'nazione_sedi[132]':'PG',
                    'nazione_sedi[133]':'PY',
                    'nazione_sedi[134]':'PE',
                    'nazione_sedi[204]':'PH',
                    'nazione_sedi[56]':'PH',
                    'nazione_sedi[135]':'PL',
                    'nazione_sedi[136]':'PT',
                    'nazione_sedi[137]':'QA',
                    'nazione_sedi[143]':'RO',
                    'nazione_sedi[216]':'RU',
                    'nazione_sedi[144]':'RW',
                    'nazione_sedi[146]':'KN',
                    'nazione_sedi[147]':'LC',
                    'nazione_sedi[148]':'VC',
                    'nazione_sedi[151]':'SM',
                    'nazione_sedi[7]':'SA',
                    'nazione_sedi[155]':'SN',
                    'nazione_sedi[154]':'SC',
                    'nazione_sedi[156]':'SL',
                    'nazione_sedi[157]':'SG',
                    'nazione_sedi[159]':'SK',
                    'nazione_sedi[160]':'SI',
                    'nazione_sedi[161]':'SO',
                    'nazione_sedi[165]':'ZA',
                    'nazione_sedi[212]':'KR',
                    'nazione_sedi[42]':'KR',
                    'nazione_sedi[162]':'ES',
                    'nazione_sedi[163]':'LK',
                    'nazione_sedi[166]':'SD',
                    'nazione_sedi[167]':'SR',
                    'nazione_sedi[170]':'SZ',
                    'nazione_sedi[168]':'SE',
                    'nazione_sedi[169]':'CH',
                    'nazione_sedi[158]':'SY',
                    'nazione_sedi[172]':'TW',
                    'nazione_sedi[171]':'TJ',
                    'nazione_sedi[173]':'TZ',
                    'nazione_sedi[213]':'TH',
                    'nazione_sedi[174]':'TH',
                    'nazione_sedi[176]':'TG',
                    'nazione_sedi[153]':'ST',
                    'nazione_sedi[177]':'TO',
                    'nazione_sedi[178]':'TT',
                    'nazione_sedi[179]':'TN',
                    'nazione_sedi[214]':'TR',
                    'nazione_sedi[180]':'TR',
                    'nazione_sedi[181]':'TM',
                    'nazione_sedi[182]':'TV',
                    'nazione_sedi[184]':'UG',
                    'nazione_sedi[183]':'UA',
                    'nazione_sedi[52]':'AE',
                    'nazione_sedi[138]':'GB',
                    'nazione_sedi[164]':'US',
                    'nazione_sedi[186]':'UY',
                    'nazione_sedi[187]':'UZ',
                    'nazione_sedi[188]':'VU',
                    'nazione_sedi[189]':'VE',
                    'nazione_sedi[190]':'VN',
                    'nazione_sedi[150]':'WS',
                    'nazione_sedi[191]':'YE',
                    'nazione_sedi[192]':'ZM',
                    'nazione_sedi[193]':'ZW',
                    'Nazioni_ID': self.country2,
                    'Clienti_indirizzo':self.address,
                    'Clienti_numcivico':self.num,
                    'Clienti_cap':self.zip,
                    'Clienti_citta':self.city,
                    'Province_ID':'0',
                    'country':self.country,
                    'Clienti_tel':self.phone,
                    'sped_to_cli':'1',
                    'trigger_sped_to_cli':'1',
                    'Clienti_sedi_ID':'',
                    'nazione_sedi[211]': 'AE',
                    'nazione_sedi[1]': 'AF',
                    'nazione_sedi[2]': 'AL',
                    'nazione_sedi[3]': 'DZ',
                    'nazione_sedi[4]': 'AD',
                    'nazione_sedi[5]': 'AO',
                    'nazione_sedi[6]': 'AG',
                    'nazione_sedi[8]': 'AR',
                    'nazione_sedi[9]': 'AM',
                    'nazione_sedi[10]': 'AU',
                    'nazione_sedi[11]': 'AT',
                    'nazione_sedi[12]': 'AZ',
                    'nazione_sedi[13]': 'BS',
                    'nazione_sedi[202]': 'BH',
                    'nazione_sedi[14]': 'BH',
                    'nazione_sedi[198]': 'IB',
                    'nazione_sedi[15]': 'BD',
                    'nazione_sedi[16]': 'BB',
                    'nazione_sedi[21]': 'BY',
                    'nazione_sedi[17]': 'BE',
                    'nazione_sedi[18]': 'BZ',
                    'nazione_sedi[19]': 'BJ',
                    'nazione_sedi[20]': 'BT',
                    'nazione_sedi[22]': 'BO',
                    'nazione_sedi[23]': 'BA',
                    'nazione_sedi[24]': 'BW',
                    'nazione_sedi[25]': 'BR',
                    'nazione_sedi[26]': 'BN',
                    'nazione_sedi[27]': 'BG',
                    'nazione_sedi[28]': 'BF',
                    'nazione_sedi[29]': 'BI',
                    'nazione_sedi[30]': 'KH',
                    'nazione_sedi[31]': 'CM',
                    'nazione_sedi[32]': 'CA',
                    'nazione_sedi[199]': 'ES-',
                    'nazione_sedi[33]': 'CV',
                    'nazione_sedi[140]': 'CF',
                    'nazione_sedi[34]': 'TD',
                    'nazione_sedi[35]': 'CL',
                    'nazione_sedi[36]': 'CN',
                    'nazione_sedi[38]': 'CO',
                    'nazione_sedi[39]': 'KM',
                    'nazione_sedi[40]': 'CG',
                    'nazione_sedi[44]': 'CR',
                    'nazione_sedi[43]': 'CI',
                    'nazione_sedi[45]': 'HR',
                    'nazione_sedi[37]': 'CY',
                    'nazione_sedi[139]': 'CZ',
                    'nazione_sedi[47]': 'DK',
                    'nazione_sedi[66]': 'DJ',
                    'nazione_sedi[48]': 'DM',
                    'nazione_sedi[142]': 'DO',
                    'nazione_sedi[210]': 'AE',
                    'nazione_sedi[175]': 'TL',
                    'nazione_sedi[207]': 'EC',
                    'nazione_sedi[49]': 'EC',
                    'nazione_sedi[208]': 'EG',
                    'nazione_sedi[50]': 'EG',
                    'nazione_sedi[51]': 'SV',
                    'nazione_sedi[72]': 'GQ',
                    'nazione_sedi[53]': 'ER',
                    'nazione_sedi[54]': 'EE',
                    'nazione_sedi[55]': 'ET',
                    'nazione_sedi[200]': 'FO',
                    'nazione_sedi[83]': 'FJ',
                    'nazione_sedi[57]': 'FI',
                    'nazione_sedi[58]': 'FR',
                    'nazione_sedi[59]': 'GA',
                    'nazione_sedi[60]': 'GM',
                    'nazione_sedi[61]': 'GE',
                    'nazione_sedi[62]': 'DE',
                    'nazione_sedi[63]': 'GH',
                    'nazione_sedi[197]': 'GI',
                    'nazione_sedi[68]': 'GR',
                    'nazione_sedi[201]': 'GL',
                    'nazione_sedi[69]': 'GD',
                    'nazione_sedi[70]': 'GT',
                    'nazione_sedi[195]': 'GGY',
                    'nazione_sedi[71]': 'GN',
                    'nazione_sedi[73]': 'GW',
                    'nazione_sedi[74]': 'GY',
                    'nazione_sedi[75]': 'HT',
                    'nazione_sedi[152]': 'VA',
                    'nazione_sedi[76]': 'HN',
                    'nazione_sedi[215]': 'HK',
                    'nazione_sedi[185]': 'HU',
                    'nazione_sedi[82]': 'IS',
                    'nazione_sedi[209]': 'IN',
                    'nazione_sedi[77]': 'IN',
                    'nazione_sedi[205]': 'ID',
                    'nazione_sedi[78]': 'ID',
                    'nazione_sedi[79]': 'IR',
                    'nazione_sedi[80]': 'IQ',
                    'nazione_sedi[81]': 'IE',
                    'nazione_sedi[194]': 'IM',
                    'nazione_sedi[84]': 'IL',
                    'nazione_sedi[85]': 'IT',
                    'nazione_sedi[64]': 'JM',
                    'nazione_sedi[206]': 'JP',
                    'nazione_sedi[65]': 'JP',
                    'nazione_sedi[196]': 'JEY',
                    'nazione_sedi[67]': 'JO',
                    'nazione_sedi[87]': 'KZ',
                    'nazione_sedi[88]': 'KE',
                    'nazione_sedi[90]': 'KI',
                    'nazione_sedi[91]': 'KW',
                    'nazione_sedi[89]': 'KG',
                    'nazione_sedi[92]': 'LA',
                    'nazione_sedi[94]': 'LV',
                    'nazione_sedi[95]': 'LB',
                    'nazione_sedi[93]': 'LS',
                    'nazione_sedi[96]': 'LR',
                    'nazione_sedi[97]': 'LY',
                    'nazione_sedi[98]': 'LI',
                    'nazione_sedi[99]': 'LT',
                    'nazione_sedi[100]': 'LU',
                    'nazione_sedi[101]': 'MK',
                    'nazione_sedi[102]': 'MG',
                    'nazione_sedi[103]': 'MW',
                    'nazione_sedi[203]': 'MY',
                    'nazione_sedi[104]': 'MY',
                    'nazione_sedi[105]': 'MV',
                    'nazione_sedi[106]': 'ML',
                    'nazione_sedi[107]': 'MT',
                    'nazione_sedi[109]': 'MH',
                    'nazione_sedi[110]': 'MR',
                    'nazione_sedi[111]': 'MU',
                    'nazione_sedi[112]': 'MX',
                    'nazione_sedi[113]': 'FM',
                    'nazione_sedi[114]': 'MD',
                    'nazione_sedi[115]': 'MC',
                    'nazione_sedi[116]': 'MN',
                    'nazione_sedi[108]': 'MA',
                    'nazione_sedi[117]': 'MZ',
                    'nazione_sedi[118]': 'MM',
                    'nazione_sedi[119]': 'NA',
                    'nazione_sedi[120]': 'NR',
                    'nazione_sedi[121]': 'NP',
                    'nazione_sedi[128]': 'NL',
                    'nazione_sedi[126]': 'NZ',
                    'nazione_sedi[122]': 'NI',
                    'nazione_sedi[123]': 'NE',
                    'nazione_sedi[124]': 'NG',
                    'nazione_sedi[41]': 'KP',
                    'nazione_sedi[125]': 'NO',
                    'nazione_sedi[127]': 'OM',
                    'nazione_sedi[129]': 'PK',
                    'nazione_sedi[130]': 'PW',
                    'nazione_sedi[131]': 'PA',
                    'nazione_sedi[132]': 'PG',
                    'nazione_sedi[133]': 'PY',
                    'nazione_sedi[134]': 'PE',
                    'nazione_sedi[204]': 'PH',
                    'nazione_sedi[56]': 'PH',
                    'nazione_sedi[135]': 'PL',
                    'nazione_sedi[136]': 'PT',
                    'nazione_sedi[137]': 'QA',
                    'nazione_sedi[143]': 'RO',
                    'nazione_sedi[216]': 'RU',
                    'nazione_sedi[144]': 'RW',
                    'nazione_sedi[146]': 'KN',
                    'nazione_sedi[147]': 'LC',
                    'nazione_sedi[148]': 'VC',
                    'nazione_sedi[151]': 'SM',
                    'nazione_sedi[7]': 'SA',
                    'nazione_sedi[155]': 'SN',
                    'nazione_sedi[154]': 'SC',
                    'nazione_sedi[156]': 'SL',
                    'nazione_sedi[157]': 'SG',
                    'nazione_sedi[159]': 'SK',
                    'nazione_sedi[160]': 'SI',
                    'nazione_sedi[161]': 'SO',
                    'nazione_sedi[165]': 'ZA',
                    'nazione_sedi[212]': 'KR',
                    'nazione_sedi[42]': 'KR',
                    'nazione_sedi[162]': 'ES',
                    'nazione_sedi[163]': 'LK',
                    'nazione_sedi[166]': 'SD',
                    'nazione_sedi[167]': 'SR',
                    'nazione_sedi[170]': 'SZ',
                    'nazione_sedi[168]': 'SE',
                    'nazione_sedi[169]': 'CH',
                    'nazione_sedi[158]': 'SY',
                    'nazione_sedi[172]': 'TW',
                    'nazione_sedi[171]': 'TJ',
                    'nazione_sedi[173]': 'TZ',
                    'nazione_sedi[213]': 'TH',
                    'nazione_sedi[174]': 'TH',
                    'nazione_sedi[176]': 'TG',
                    'nazione_sedi[153]': 'ST',
                    'nazione_sedi[177]': 'TO',
                    'nazione_sedi[178]': 'TT',
                    'nazione_sedi[179]': 'TN',
                    'nazione_sedi[214]': 'TR',
                    'nazione_sedi[180]': 'TR',
                    'nazione_sedi[181]': 'TM',
                    'nazione_sedi[182]': 'TV',
                    'nazione_sedi[184]': 'UG',
                    'nazione_sedi[183]': 'UA',
                    'nazione_sedi[52]': 'AE',
                    'nazione_sedi[138]': 'GB',
                    'nazione_sedi[164]': 'US',
                    'nazione_sedi[186]': 'UY',
                    'nazione_sedi[187]': 'UZ',
                    'nazione_sedi[188]': 'VU',
                    'nazione_sedi[189]': 'VE',
                    'nazione_sedi[190]': 'VN',
                    'nazione_sedi[150]': 'WS',
                    'nazione_sedi[191]': 'YE',
                    'nazione_sedi[192]': 'ZM',
                    'nazione_sedi[193]': 'ZW',
                    'Clienti_sedi_Nazioni_ID':self.country2,
                    'Clienti_sedi_nome':'',
                    'Clienti_sedi_cognome':'',
                    'Clienti_sedi_indirizzo':'',
                    'Clienti_sedi_numcivico':'',
                    'Clienti_sedi_cap':'',
                    'Clienti_sedi_citta':'',
                    'Clienti_sedi_Province_ID':'0',
                    'vettori_ID': '15',
                    'coupon_code': '',
                    'pagamenti_ID': '58',
                    'Clienti_email': self.account
                }

                headers2 = {
                    "content-Type": "application/x-www-form-urlencoded",
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9"
                }

                self.s.headers.update(headers2)
                
                t = self.s.post(f"https://www.sotf.com/{self.dominio}/secure/sum_up.php", data = pagamento, timeout = self.timeout)

                while True:

                    if t.status_code in (200,302):
                        
                        warn(f'[TASK {self.threadID}] [SOTF] - Submitting order...')


                        r = self.s.post(f"https://www.sotf.com/{self.dominio}/check_out.php", data = pagamento)

                        if r.status_code == 200 or 302:

                            try:
                                soup = bs(r.text, "html.parser")
                                pp1 = soup.find_all("meta")[-1]
                                pp2 = pp1["content"]
                                self.paypal = pp2.split("url=")[1]
                                info(f'[TASK {self.threadID}] [SOTF] - Successfully checked out!')
                                self.fallito = False
                                checkoutnum = checkoutnum + 1
                                self.bar()
                                break

                            except:
                                self.paypal = r.text.split("document.location.href='")[1].split("'")[0]
                                info(f'[TASK {self.threadID}] [SOTF] - Successfully checked out!')
                                self.fallito = False
                                checkoutnum = checkoutnum + 1
                                self.bar()
                                break

                        elif r.status_code == 502:
                            warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                            time.sleep(self.delay)
                            continue

                        elif r.status_code == 504:
                            warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                            time.sleep(self.delay)
                            continue

                        elif r.status_code == 500:
                            warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                            time.sleep(self.delay)
                            self.parse()

                        elif r.status_code == 524:
                            warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                            time.sleep(self.delay)
                            continue


                        elif r.status_code == 403:
                            error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, retrying...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(self.delay)
                            continue

                        else:
                            error(f'[TASK {self.threadID}] [SOTF] - Error {r.status_code}, retrying...')
                            failed = failed + 1
                            self.bar()
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(self.delay)
                            continue


                    elif t.status_code == 502:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        continue

                    elif t.status_code == 504:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        continue

                    elif t.status_code == 524:
                        warn(f'[TASK {self.threadID}] [SOTF] - Site is down, retrying...')
                        continue

                    elif t.status_code == 500:
                        warn(f'[TASK {self.threadID}] [SOTF] - SSite is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif t.status_code == 403:
                        error(f'[TASK {self.threadID}] [SOTF] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:


                        error(f'[TASK {self.threadID}] [SOTF] - Error {t.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue


                if self.fallito:
                    self.selenium2()
                else:
                    self.selenium()
                
            except: 
                error(f'[TASK {self.threadID}] [SOTF] - Exception submitting order, retrying...') 
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.s.cookies.clear()
                self.login()

        except:
            pass

    def selenium(self):

        try:

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
                url = urllib.parse.quote(base64.b64encode(bytes(self.paypal, 'utf-8')).decode())
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
                        writer.writerow({'SITE':'SOTF','SIZE':f'{self.superattribute}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                        
                else:
                    self.expToken = self.token
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'SOTF','SIZE':f'{self.superattribute}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                
                self.webhook()
            
            except Exception as e: 
                error(f'[TASK {self.threadID}] [SOTF] - Exception passing cookies {e.__class__.__name__}, retrying...') 
                sys.exit(1)
        except:
            pass

    def selenium2(self):

        try:

            try:

                cookieStr = ""
                cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]   
                for element in cookies:
                    if 'cf_chl_prog' in element['name']:
                        cookies.remove(element)

                for cookie in cookies:
                    if cookie['domain'][0] == ".":
                        cookie['url'] = cookie['domain'][1:]
                    else:
                        cookie['url'] = cookie['domain']
                    cookie['url'] = "https://"+cookie['url']
                cookies = json.dumps(cookies)
                cookieStr = urllib.parse.quote(base64.b64encode(bytes(cookies, 'utf-8')).decode())
                if not cookieStr: return
                url = urllib.parse.quote(base64.b64encode(bytes(self.paypal, 'utf-8')).decode())
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
                        writer.writerow({'SITE':'SOTF','SIZE':f'{self.superattribute}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                        
                else:
                    self.expToken = self.token
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'SOTF','SIZE':f'{self.superattribute}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                
                self.webhook2()
            
            except Exception as e: 
                error(f'[TASK {self.threadID}] [SOTF] - Exception passing cookies {e.__class__.__name__}, retrying...') 
                sys.exit(1)

        except:
            pass

    def webhook(self):
        try:
            if self.selected_proxies == None:
                self.proxi = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name='**SOTF**', value = f'{self.title}', inline = False)
            embed.add_embed_field(name='**PRODUCT**', value = f'[LINK]({self.link})', inline = False)
            embed.add_embed_field(name='**SIZE**', value = f'{self.superattribute}', inline = False)
            embed.add_embed_field(name='**PRICE**', value = f'{self.price}', inline = False)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='Mail', value = f'||{self.account}||', inline = False)
            embed.add_embed_field(name='Password', value = f'||{self.password}||', inline = True)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass

    def webhook2(self):
        try:
            if self.selected_proxies == None:
                self.proxi = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Manual checkout required!', url = self.expToken, color = 16426522)
            embed.add_embed_field(name='**SOTF**', value = f'{self.title}', inline = False)
            embed.add_embed_field(name='**PRODUCT**', value = f'[LINK]({self.link})', inline = False)
            embed.add_embed_field(name='**SIZE**', value = f'{self.superattribute}', inline = False)
            embed.add_embed_field(name='**PRICE**', value = f'{self.price}', inline = False)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='Mail', value = f'||{self.account}||', inline = False)
            embed.add_embed_field(name='Password', value = f'||{self.password}||', inline = True)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass


    
    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name='**SOTF**', value = f'{self.title}', inline = False)
            embed.add_embed_field(name='**PRODUCT**', value = f'[LINK]({self.link})', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.superattribute}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()

            try:
                playsound('checkout.wav')
                warn("")
            except:
                warn("")
        except:
            pass