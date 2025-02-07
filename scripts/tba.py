import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

checkoutnum = 0
carted = 0
failed = 0
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

class TBA():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'thebrokenarm/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "thebrokenarm/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()

        except:
            error("Failed To Read Proxies File - using no proxies ")
            self.all_proxies = None

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
        else:
            self.selected_proxies = None

        
        if config['anticaptcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'anticaptcha','api_key':config['anticaptcha']},doubleDown=False,requestPostHook=self.injection)
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha']},doubleDown=False,requestPostHook=self.injection)
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)

        
        self.s.proxies = self.selected_proxies
        self.discord = DISCORD_ID
        self.link = row['LINK']
        self.size = row['SIZE']
        self.mail = row['EMAIL']
        self.passw = row['PASSWORD']
        self.name = row['FIRST NAME']
        self.surname = row['LAST NAME']
        self.address = row['ADDRESS LINE 1']
        self.address2 = row['ADDRESS LINE 2']
        self.zipcode = row['ZIP']
        self.city = row['CITY']
        self.region = row['STATE']
        self.phone = row['PHONE NUMBER']
        self.country = row['COUNTRY']
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.twoCaptcha = config['2captcha']
        self.iscookiesfucked = False
        self.cfchl = False
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.timeout = 120

        self.delay = int(config['delay'])
        self.balance = balancefunc()

        self.bar()

        warn(f'[TASK {self.threadID}] [TBA] - Task started!')
        

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
            error("FAILED CSV")

        self.scrapeproduct()


#####################################################################################################################  - CHOOSE PROXY


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
                f'Phoenix AIO {self.version} - TBA Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - TBA Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')

    def injection(self, session, response):

        self.balance = balancefunc()
        self.bar()

        #try:
        if helheim.isChallenge(session, response):
            warn(f'[Task {self.threadID}] [TBA] - Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response
        #except:
        #    if session.is_New_IUAM_Challenge(response):
        #        self.mom = True
        #        warn(f'[TASK {self.threadID}] [TBA] - Solving Cloudflare v2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
        #    elif session.is_New_Captcha_Challenge(response):
        #        self.mom = True
        #        warn(f'[TASK {self.threadID}] [TBA] - Solving Cloudflare v2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
        #    else:
        #        return response


################################################################################################################################# - GET AL PRODOTTO
        


    def scrapeproduct(self):

        try:

            global carted, failed, checkoutnum

            self.mom = False

            warn(f"[Task {self.threadID}] [TBA] - Getting product...")

            try:
                headers = {
                    'Upgrade-Insecure-Requests': '1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Dest': 'document',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en'
                }

                while True:
                    r = self.s.get(self.link, headers = headers)

                    if r.status_code == 200 or r.status_code == 201:

                        try:
                            
                            self.statictoken = r.text.split('static_token":"')[1].split('"')[0]
                            r_json = json.loads(r.text.split('var prestashop = ')[1].split(';')[0])
                            self.title = r_json['page']['meta']['title']
                            self.pid = r.text.split('name="id_product" value="')[1].split('"')[0]
                            self.img = f'https://www.the-broken-arm.com/{self.pid}-large_default/phoenix.jpg'
                            soup = bs(r.text, features='lxml')
                            sazihtm = soup.find('div',{'class':'custom-select2'})
                            self.group = soup.find('select',{'class':'name'})
                            size = []
                            value = []
                            for i in sazihtm('option'):
                                if 'Sold out' not in i.text:
                                    value.append(i['value'])
                                    size.append((i.text.split('US')[0].split('\n')[1]).replace(' ',''))

                            if not size:
                                warn(f'[TASK {self.threadID}] [TBA] - Product oos, monitoring...')
                                time.sleep(self.delay)
                                continue

                            else:
                                info(f'[TASK {self.threadID}] [TBA] - {self.title} in stock: {size}')
                                tot = zip(value, size)
                                self.connect = list(tot)
                                break
                                
                        except Exception as e:
                            warn(f'[TASK {self.threadID}] [TBA] - Exception parsing product , retrying...')
                            time.sleep(self.delay)
                            continue
                   
                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [TBA] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f"[Task {self.threadID}] [TBA] - Proxy banned, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 429:
                        error(f"[Task {self.threadID}] [TBA] - Rate limit, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [TBA] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue  

                    else:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [TBA] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        continue

                self.atc()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [TBA] - Connection error, retrying...')
                time.sleep(self.delay)
                self.scrapeproduct()

            except Exception as e:
                error(f'[TASK {self.threadID}] [TBA] - Exception getting product {e}, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.scrapeproduct()

        except:
            pass


    def atc(self):

        try:

            global carted, failed, checkoutnum

            try:
                headers = {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Referer': self.link,
                }
                self.s.headers.update(headers)

                self.sizerange = []

                if self.size == "RANDOM":
                    scelta = random.choice(self.connect)
                    ciao3 = scelta[0]
                    self.value = "".join(ciao3)
                    ciao2 = scelta[1]
                    self.saiz = "".join(ciao2)
                    warn(f'[TASK {self.threadID}] [TBA] - Adding to cart size {self.saiz}...')

                elif '-' in self.size:
                    self.size1 = float(self.size.split('-')[0])
                    self.size2 = float(self.size.split('-')[1])
                    for x in self.connect:
                        if self.size1 <= float(x[1]) <= self.size2:
                            self.sizerange.append(x[1])        
                    self.sizerandom = random.choice(self.sizerange)
                    for Traian in self.connect:
                        if self.sizerandom == Traian[1]:
                            ciao0 = Traian[0]
                            self.value = "".join(ciao0)
                            ciao1 = Traian[1]
                            self.saiz = "".join(ciao1)
                    warn(f'[TASK {self.threadID}] [TBA] - Adding to cart size {self.saiz}')
                            
                elif ',' in self.size:
                    self.size1 = float(self.size.split(',')[0])
                    self.size2 = float(self.size.split(',')[1])
                    for x in self.connect:
                        if self.size1 <= float(x[1]) <= self.size2:
                            self.sizerange.append(x[1])        
                    self.sizerandom = random.choice(self.sizerange)
                    for Traian in self.connect:
                        if self.sizerandom == Traian[1]:
                            ciao0 = Traian[0]
                            self.value = "".join(ciao0)
                            ciao1 = Traian[1]
                            self.saiz = "".join(ciao1)
                    warn(f'[TASK {self.threadID}] [TBA] - Adding to cart size {self.saiz}')

                else:
                    for Traian in self.connect:
                        if self.size == Traian[1]:
                            ciao0 = Traian[0]
                            self.value = "".join(ciao0)
                            ciao1 = Traian[1]
                            self.saiz = "".join(ciao1)
                    warn(f'[TASK {self.threadID}] [TBA] - Adding to cart size {self.saiz}')


                payload = {
                    'token':self.statictoken,
                    'id_product':self.pid,
                    'id_customization':'0',
                    self.group:self.value,
                    'author':'',
                    'friend_name':'',	
                    'friend_email':'',
                    'id_product':self.pid,
                    'add':'1',
                    'action':'update'
                }


                while True:

                    r = self.s.post('https://www.the-broken-arm.com/en/panier', data = payload)

                    if r.status_code == 200 or r.status_code == 201:
                        r_json = json.loads(r.text)
                        try:
                            if r_json['success'] == True:
                                info(f'[TASK {self.threadID}] [TBA] - Succesfully added to cart!')
                                carted = carted + 1
                                self.bar()
                                break

                            if r_json['success'] == False:
                                if 'enough product in stock' in r_json['errors'][0]:
                                    warn(f'[TASK {self.threadID}] [TBA] - Product oos, monitoring...')
                                    time.sleep(self.delay)
                                    continue

                            else:
                                error(f'[TASK {self.threadID}] [TBA] - Unkown error while adding to cart, restarting...')
                                self.s.cookies.clear()
                                if self.all_proxies != None:
                                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                                    self.s.proxies = self.selected_proxies
                                self.scrapeproduct()

                        except:
                            if r_json['hasError'] == True:
                                warn(f'[TASK {self.threadID}] [TBA] - Product oos, restarting...')
                                self.s.cookies.clear()
                                if self.all_proxies != None:
                                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                                    self.s.proxies = self.selected_proxies
                                self.scrapeproduct()
                            else:
                                error(f'[TASK {self.threadID}] [TBA] - Unkown error, restarting...')
                                self.s.cookies.clear()
                                if self.all_proxies != None:
                                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                                    self.s.proxies = self.selected_proxies
                                self.scrapeproduct()


                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [TBA] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f"[Task {self.threadID}] [TBA] - Proxy banned, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 429:
                        error(f"[Task {self.threadID}] [TBA] - Rate limit, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [TBA] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue  

                    else:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [TBA] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        continue

                self.createacc()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [TBA] - Connection error, retrying...')
                time.sleep(self.delay)
                self.scrapeproduct()

            except Exception as e:
                error(f'[TASK {self.threadID}] [TBA] - Exception adding to cart, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.scrapeproduct()

        except:
            pass

    def createacc(self):

        try:
            warn(f'[TASK {self.threadID}] [TBA] - Creating account...')

            global carted, failed, checkoutnum

            try:
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Referer': 'https://www.the-broken-arm.com/en/connexion?create_account=1'
                }
                self.s.headers.update(headers)

                payload = {
                    'email':self.mail,
                    'firstname':self.name,
                    'lastname':self.surname,
                    'password':self.passw,
                    'conf_password':self.passw,
                    'psgdpr':'1',
                    'submitCreate':'1'
                }

                while True:
                    r = self.s.post('https://www.the-broken-arm.com/en/connexion?create_account=1', data = payload)

                    if r.status_code == 200 and r.url == 'https://www.the-broken-arm.com/en/':
                        info(f'[TASK {self.threadID}] [TBA] - Account succesfully created!')
                        time.sleep(self.delay)
                        break

                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [TBA] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f"[Task {self.threadID}] [TBA] - Proxy banned, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 429:
                        error(f"[Task {self.threadID}] [TBA] - Rate limit, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [TBA] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue  

                    else:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [TBA] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        continue

                self.getcouregion()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [TBA] - Connection error, retrying...')
                time.sleep(self.delay)
                self.scrapeproduct()

            except Exception as e:
                error(f'[TASK {self.threadID}] [TBA] - Exception creating account, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.scrapeproduct()

        except:
            pass

    def getcouregion(self):

        try:
            warn(f'[TASK {self.threadID}] [TBA] - Getting country info...')

            global carted, failed, checkoutnum
            self.error = False
            try:


                while True:

                    r = self.s.get('https://www.the-broken-arm.com/en/commande')


                    if r.status_code == 200:

                        soup = bs(r.text, features='lxml')
                        countr = soup.find('div',{'class':'custom-select2'})
                        self.countryid = ''
                        try:
                            for i in countr('option'):
                                if self.country == i.text:
                                    self.countryid = i['value']
                        except:
                            error(f'[TASK {self.threadID}] [TBA] - Wrong Country check your csv!')
                            self.error = True
                            break

                        payload = {
                            'id_country':self.countryid,
                            'id_address':'0'
                        }

                        x = self.s.post('https://www.the-broken-arm.com/en/commande?ajax=1&action=addressForm', data = payload)


                        if x.status_code == 200:
                            r_json = x.text.replace('\\n','').replace('\\','').split('address_form":"')[1]
                            soup = bs(r_json, features='lxml')
                            pro = soup.find('div',{'class':'custom-select2'})
                            self.token2 = x.text.replace('\\n','').replace('\\','').split('name="token" value="')[1].split('"')[0]
                            if 'id_state' in x.text:
                                self.regionid = ''
                                try:
                                    for z in pro('option'):
                                        if self.region == z.text:
                                            self.regionid = z['value']
                                    break

                                except:
                                    error(f'[TASK {self.threadID}] [TBA] - Wrong State check your csv!')
                                    self.error = True
                                    break
                            else:
                                self.regionid = ''
                                break

                        elif x.status_code >= 500 and x.status_code <= 600:
                            warn(f'[TASK {self.threadID}] [TBA] - Site is dead, retrying...')
                            time.sleep(self.delay)
                            continue

                        elif x.status_code == 403:
                            error(f"[Task {self.threadID}] [TBA] - Proxy banned, retrying...")
                            time.sleep(self.delay)
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            continue

                        elif x.status_code == 429:
                            error(f"[Task {self.threadID}] [TBA] - Rate limit, retrying...")
                            time.sleep(self.delay)
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            continue

                        elif x.status_code == 404:
                            warn(f'[TASK {self.threadID}] [TBA] - Page not loaded, retrying...')
                            time.sleep(self.delay)
                            continue  

                        else:
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            error(f'[TASK {self.threadID}] [TBA] - Error {x.status_code}, retrying...')
                            time.sleep(self.delay)
                            continue


                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [TBA] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f"[Task {self.threadID}] [TBA] - Proxy banned, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 429:
                        error(f"[Task {self.threadID}] [TBA] - Rate limit, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [TBA] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue  

                    else:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [TBA] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        continue

                if self.error:
                    sys.exit()
                else:
                    self.ship()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [TBA] - Connection error, retrying...')
                time.sleep(self.delay)
                self.scrapeproduct()

            except Exception as e:
                error(f'[TASK {self.threadID}] [TBA] - Exception getting country info, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.scrapeproduct()

        except:
            pass

    def ship(self):

        try:
            warn(f'[TASK {self.threadID}] [TBA] - Submitting shipping...')

            global carted, failed, checkoutnum

            try:

                payload = {
                    'back':'',
                    'token':self.token2,
                    'alias':'',
                    'firstname':self.name,
                    'lastname':self.surname,
                    'company':'',
                    'vat_number':'',
                    'address1':self.address,
                    'address2':self.address2,
                    'postcode':self.zipcode,
                    'city':self.city,
                    'id_state':self.regionid,
                    'id_country':self.countryid,
                    'phone':self.phone,
                    'saveAddress':'delivery',
                    'use_same_address':'1',
                    'submitAddress':'1',
                    'confirm-addresses':'1'
                }


                while True:
                    r = self.s.post('https://www.the-broken-arm.com/en/commande?id_address=0', data = payload)

                    if r.status_code == 200:
                        soup = bs(r.text, features='lxml')
                        delz = soup.find('div',{'class':'delivery-options'}).find('input',{'type':'radio'})
                        self.pay1 = delz['name']
                        self.rates = delz['value']
                        info(f'[TASK {self.threadID}] [TBA] - Succesfully submitted ship!')
                        break


                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [TBA] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f"[Task {self.threadID}] [TBA] - Proxy banned, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 429:
                        error(f"[Task {self.threadID}] [TBA] - Rate limit, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [TBA] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue  

                    else:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [TBA] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        continue

                self.shippingrates()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [TBA] - Connection error, retrying...')
                time.sleep(self.delay)
                self.ship()

            except Exception as e:
                error(f'[TASK {self.threadID}] [TBA] - Exception submitting ship, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.ship()

        except:
            pass

    def shippingrates(self):

        try:
            warn(f'[TASK {self.threadID}] [TBA] - Submitting shipping rates...')

            global carted, failed, checkoutnum

            try:

                payload = {
                    self.pay1:self.rates,
                    'confirmDeliveryOption':'1'
                }


                while True:
                    r = self.s.post('https://www.the-broken-arm.com/en/commande', data = payload)

                    if r.status_code == 200:
                        info(f'[TASK {self.threadID}] [TBA] - Succesfully submitted shipping rates!')
                        break


                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [TBA] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f"[Task {self.threadID}] [TBA] - Proxy banned, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 429:
                        error(f"[Task {self.threadID}] [TBA] - Rate limit, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [TBA] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue  

                    else:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [TBA] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        continue

                
                self.pp()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [TBA] - Connection error, retrying...')
                time.sleep(self.delay)
                self.shippingrates()

            except Exception as e:
                error(f'[TASK {self.threadID}] [TBA] - Exception submitting shipping rates, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.shippingrates()

        except:
            pass

    def pp(self):

        try:
            warn(f'[TASK {self.threadID}] [TBA] - Getting paypal...')

            global carted, failed, checkoutnum

            try:
                headers = {
                    'Upgrade-Insecure-Requests':'1',
                    'Origin': 'https://www.the-broken-arm.com',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document',
                    'Referer': 'https://www.the-broken-arm.com/en/module/paypal/ecInit?credit_card=0&getToken=1',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en'
                }


                while True:
                    if self.mom:
                        r = self.s.get('https://www.the-broken-arm.com/en/module/paypal/ecInit?credit_card=0&getToken=1')
                    else:
                        r = self.s.get('https://www.the-broken-arm.com/en/module/paypal/ecInit?credit_card=0&getToken=1', headers = headers)

                    if r.status_code == 200:
                        r_json = json.loads(r.text)
                        if r_json['success'] == True:
                            token = r_json['token']
                            self.ppurl = f'https://www.paypal.com/checkoutnow?token={token}'
                            info(f'[TASK {self.threadID}] [TBA] - Succesfully checked out!')
                            break


                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [TBA] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 403:
                        error(f"[Task {self.threadID}] [TBA] - Proxy banned, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 429:
                        error(f"[Task {self.threadID}] [TBA] - Rate limit, retrying...")
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [TBA] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue  

                    else:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [TBA] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        continue

                self.pass_cookies()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [TBA] - Connection error, retrying...')
                time.sleep(self.delay)
                self.pp()

            except Exception as e:
                error(f'[TASK {self.threadID}] [TBA] - Exception getting paypal, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.pp()

        except:
            pass

    
    def pass_cookies(self):
        try:
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
                        writer.writerow({'SITE':'TBA','SIZE':f'{self.saiz}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                        

                else:
                    self.expToken = self.token
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'TBA','SIZE':f'{self.saiz}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                
                self.SuccessPP()

            except Exception as e: 
                error(f'[TASK {self.threadID}] [TBA] - Error passing cookies, retrying...') 
                time.sleep(self.delay)
                self.pass_cookies()

        except:
            pass

    
    def Pubblic_Webhook(self):
        try:
            #webhook = DiscordWebhook(url='https://discord.com/api/webhooks/732534095158050861/Bf6qvBp0wFIDqg4UXIpSkKleAuj_WmWsTefUi8NLhSoxaCYBjywgghXVspJx2ooc1jgJ', content = "")
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**THE BROKEN ARM**', value = self.title, inline = False)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.saiz, inline = True)
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
            if self.selected_proxies == None:
                self.proxi = 'LOCAL'
            #webhook = DiscordWebhook(url='https://discord.com/api/webhooks/732534095158050861/Bf6qvBp0wFIDqg4UXIpSkKleAuj_WmWsTefUi8NLhSoxaCYBjywgghXVspJx2ooc1jgJ', content = "")
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**THE BROKEN ARM**', value = self.title, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.saiz, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = True)
            embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.img)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass