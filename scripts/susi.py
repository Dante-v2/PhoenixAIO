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

carted = 0
failed = 0
checkoutnum = 0

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

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

class SUSI():
    def __init__(self, row, webhook, version, i, DISCORD_ID):
        
        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'susi/proxies.txt')
            elif machineOS == "Windows":
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "susi/proxies.txt")
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
        
        self.threadID = i
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
            
        self.s.proxies = self.selected_proxies
        self.discord = DISCORD_ID
        self.delay = int(config['delay'])
        self.link = row['LINK'] 
        self.size = row['SIZE']
        self.email = row['EMAIL']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.phone = row['PHONE NUMBER']
        self.city = row['CITY']
        self.zip = row['ZIPCODE']
        self.state = row['STATE']
        self.country = row['COUNTRY']
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        self.timeout = 25
        self.delay = 1
        self.balance = balancefunc()
        self.bar()
        try:
            if self.name.upper() == "RANDOM":
                self.name = names.get_first_name(gender='male')
            if self.surname.upper() == "RANDOM":
                self.surname = names.get_last_name()
            if self.phone.upper() == "RANDOM":
                self.phone = str("0"+str(random.randint(7400000000,7999990000)))
            if self.email[:6].upper() == "RANDOM":
                self.email = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.email.split("@")[1]).lower()
        except Exception as e:
            error("FAILED CSV")

        self.tokenn()

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
                f'Phoenix AIO {self.version} - SUSI Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - SUSI Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')

    def injection(self, session, response):

        self.balance = balancefunc()
        self.bar()

        try:
            if helheim.isChallenge(session, response):
                self.warn('Solving Cloudflare v2')
                return helheim.solve(session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                warn(f'[TASK {self.threadID}] [SUSI] - Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                warn(f'[TASK {self.threadID}] [SUSI] - Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
            else:
                return response

    def tokenn(self):
        
        try:

            try:

                warn(f'[TASK {self.threadID}] [SUSI] - Getting token...')

                r = self.s.get(
                    'https://www.susi.it/it-IT/cliente/login/?original=%2Fit-IT%2Fcliente%2Fmio-account%2F',
                    timeout=self.timeout
                )
                
                if r.status_code == 200:

                    cftokenhtml = bs(r.text, features='lxml')
                    self.cftoken = cftokenhtml.find(attrs={'name': 'csrf_token'})['value']
                    info(f'[TASK {self.threadID}] [SUSI] - Successfully got token!')
                    if 'https://www.susi.it/' not in self.link:
                        self.variant = self.link
                        self.sizeprint = self.link
                        self.title = self.link
                        self.atc()
                    else:
                        self.getprod()

                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Error getting token {r.status_code}, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    self.tokenn()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
                self.s.cookies.clear()
                self.tokenn()

            except Exception as e:
                error(f'[TASK {self.threadID}] [SUSI] - Unknown error while getting token {e.__class__.__name__}, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.s.cookies.clear()
                self.tokenn()
        
        except:
            pass

    def getprod(self):
        
        try:

            warn(f'[TASK {self.threadID}] [SUSI] - Getting product page...')

            while True:

                r = self.s.get(
                    self.link,
                    timeout = self.timeout                
                )

                if r.status_code == 200:

                    if 'price-sales">NON DISPONIBILE' in r.text:
                        warn(f'[TASK {self.threadID}] [SUSI] - Product OOS, monitoring...')
                        time.sleep(self.delay)
                        continue

                    else:
                    
                        soup = bs(r.text, features='lxml')
                        self.title = r.text.split('<title>')[1].split('</title>')[0]
                        try:
                            self.pid = r.text.split('Product-Variation?pid=')[1].split('&')[0]
                        except:
                            self.pid = r.text.split('data-product-id="')[1].split('"')[0]                


                        try:
                            self.color = r.text.split(f'dwvar_{self.pid}-')[1].split('_')[0]
                        except:
                            self.color = r.text.split(f'dwvar_{self.pid}_color=')[1].split('"')[0]
                            if self.color == '':
                                self.color = r.text.split(f'dwvar_{self.pid}_color=')[2].split('"')[0]

                        saiz = soup.find_all('div',{'class':'value'})[1]

                        sizeprint = []
                        sizenumero = []

                        for i in saiz('a'):
                            if 'swatchanchor' in i['class']:
                                sizeprint.append(i.text.replace('\n',''))
                                sizenumero.append(i['href'].split('_size=')[1].split('&')[0])

                        connect = zip(sizeprint, sizenumero)
                        self.connect = list(connect)
                        print(sizeprint)
                        if len(self.connect) < 1:
                            warn(f'[TASK {self.threadID}] [SUSI] - Product OOS, monitoring...')
                            time.sleep(self.delay)
                            continue

                        else:
                            if self.size == "RANDOM":
                                info(f'[TASK {self.threadID}] [SUSI] - {self.title} in stock!')
                                self.connetto = random.choice(self.connect)
                                self.variante = self.connetto[1]
                                self.sizeprint = self.connetto[0]
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
                                    if float(self.size1) <= float(x[2]) <= float(self.size2):
                                        self.sizerange.append(x[2])

                                if len(self.sizerange) < 1:
                                    warn(f'[TASK {self.threadID}] [SUSI] - {self.title} size {self.size} OOS, monitoring...')
                                    time.sleep(self.delay)
                                    continue
                                else:
                                    self.sizerandom = random.choice(self.sizerange)
                                    info(f'[TASK {self.threadID}] [SUSI] - {self.title} size {self.sizerandom} in stock!')
                                    for i in self.connect:
                                        if self.sizerandom in i[1]:
                                            self.variante = i[1]
                                            self.sizeprint = i[0]
                                    break
                                

                            else:
                                for element in self.connect:
                                    if self.size == element[1]:
                                        info(f'[TASK {self.threadID}] [SUSI] - {self.title} size {self.size} in stock!')
                                        self.variante = element[1]
                                        self.sizeprint = element[0]
                                    
                                break
                        
                        break


                elif r.status_code == 410:
                    warn(f'[TASK {self.threadID}] [SUSI] - Page not loaded, retrtyng...')
                    time.sleep(self.delay)
                    self.s.cookies.clear()
                    continue

                elif r.status_code == 403:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                    error(f'[TASK {self.threadID}] [SUSI] - Proxy banned, retrtyng...')
                    time.sleep(self.delay)
                    continue

                elif r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUSI] - Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed getting product page {r.status_code}, retrtyng...')
                    time.sleep(2)
                    continue
            
            self.getsize()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
            time.sleep(self.delay)
            self.getprod()

        except Exception as e:
            error(f"[TASK {self.threadID}] [SUSI] - Exception while getting product page {e.__class__.__name__}, retrying...")
            time.sleep(self.delay)
            self.getprod()

    def getsize(self):

        global carted, failed, checkoutnum
        
        warn(f'[TASK {self.threadID}] [SUSI] - Getting variant...')

        try:

            while True:

                r = self.s.get(
                    f'https://www.susi.it/on/demandware.store/Sites-susi-Site/it_IT/Product-Variation?pid={self.pid}&dwvar_{self.pid}_size={self.variante}&dwvar_{self.pid}_color={self.color}&Quantity=1&format=ajax',
                    timeout=self.timeout
                )

                if r.status_code == 200:
                    self.variant = r.text.split('pid" value="')[1].split('"')[0]
                    info(f'[TASK {self.threadID}] [SUSI] - Succesfully got variant!')
                    break

                elif r.status_code == 403:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                    error(f'[TASK {self.threadID}] [SUSI] - Proxy banned, retrtyng...')
                    time.sleep(self.delay)
                    continue

                elif r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUSI] - Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed getting sizes {r.status_code}, retrtyng...')
                    time.sleep(self.delay)
                    continue

            self.atc()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
            time.sleep(self.delay)
            self.getsize()

        except Exception as e:
            error(f"[TASK {self.threadID}] [SUSI] - Exception while getting sizes {e.__class__.__name__}, retrying...")
            time.sleep(self.delay)
            self.getsize()


    def atc(self):
        global carted, failed, checkoutnum
        
        warn(f'[TASK {self.threadID}] [SUSI] - Adding to cart...')

        self.checkcart = False

        try:
            
            while True:
                payload = {
                    'Quantity':'1',
                    'cartAction':'add',
                    'pid': self.variant
                }
                r = self.s.post(
                    'https://www.susi.it/on/demandware.store/Sites-susi-Site/it_IT/Cart-AddProduct?format=ajax',
                    data = payload,
                    timeout=self.timeout
                    )

                if 'articolo non &egrave; al momento disponibile.' in r.text.lower():
                    error(f'[TASK {self.threadID}] [SUSI] - Product out of stock, retrying...')
                    time.sleep(self.delay)
                    self.checkcart = True
                    break
                
                elif r.status_code == 403:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrtyng...')
                        time.sleep(self.delay)
                    continue
                
                elif r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUSI] - Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                elif r.status_code == 200 and 'mini-cart-link-checkout' in r.text:
                    info(f'[TASK {self.threadID}] [SUSI] - Product added to cart!')
                    soup = bs(r.text, features='lxml')
                    image = soup.find("div", {"class":"mini-cart-image"})
                    img = image.find("img")["src"]
                    self.image = "https://www.susi.it" + img
                    carted = carted + 1
                    self.bar()
                    break

                elif r.status_code >= 400 and r.status_code < 499:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed adding to cart: {r.status_code}, restarting...')
                    self.s.cookies.clear()
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                    self.tokenn()
                    break
            
                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed submitting billing {r.status_code}, retrtyng...')
                    time.sleep(self.delay)
                    continue
            
            if self.checkcart:
                self.cart()
            self.rates()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
            time.sleep(self.delay)
            self.atc()

        except Exception as e:
            error(f"[TASK {self.threadID}] [SUSI] - Exception while adding to cart {e.__class__.__name__}, retrying...")
            time.sleep(self.delay)
            self.atc()

    def cart(self):

        warn(f'[TASK {self.threadID}] [SUSI] - Getting cart info...')

        try:
            
            while True:

                r = self.s.get(
                    'https://www.susi.it/it-IT/carrello/',
                    timeout=self.timeout
                    )

                if 'prodotti hanno un prezzo non valido o non sono disponibili nella quantit' in r.text:
                    warn(f'[TASK {self.threadID}] [SUSI] - Product out of stock, monitoring...')
                    time.sleep(self.delay)
                    continue

                if 'articolo non &egrave; al momento disponibile.' in r.text.lower():
                    warn(f'[TASK {self.threadID}] [SUSI] - Product out of stock, restarting...')
                    time.sleep(self.delay)
                    continue

                if r.status_code == 200:
                    info(f'[TASK {self.threadID}] [SUSI] - Succesfully got cart info!')
                    break
                
                elif r.status_code == 403:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrtyng...')
                        time.sleep(self.delay)
                    continue

                elif r.status_code == 429:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [SUSI] - Rate limit, retrtyng...')
                        time.sleep(self.delay)
                    continue
                
                elif r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUSI] - Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                elif r.status_code >= 400 and r.status_code < 499:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed getting cart info: {r.text}, restarting...')
                    self.s.cookies.clear()
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                    self.tokenn()
                    break
            
                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed getting cart info {r.status_code}, retrtyng...')
                    time.sleep(self.delay)
                    continue
            
            self.rates()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
            time.sleep(self.delay)
            self.atc()

        except Exception as e:
            error(f"[TASK {self.threadID}] [SUSI] - Exception while getting cart info {e.__class__.__name__}, retrying...")
            time.sleep(self.delay)
            self.atc()


    def rates(self):

        warn(f'[TASK {self.threadID}] [SUSI] - Getting shipping rates...')

        try:

            while True:
                r = self.s.get(
                    f'https://www.susi.it/on/demandware.store/Sites-susi-Site/it_IT/COShipping-GetApplicableShippingMethodsJSON?address1={self.address}&address2={self.address2}&countryCode={self.country}&stateCode={self.state}&postalCode={self.zip}&city={self.city}&shipmentType=homedelivery'
                )

                if r.status_code == 200:
                    self.shippingrates = r.text.split('"')[1]
                    info(f'[TASK {self.threadID}] [SUSI] - Succesfully got shipping rates!')
                    break

                elif r.status_code == 403:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [SUSI] - Proxy banned, retrtyng...')
                        time.sleep(self.delay)
                    continue
                
                elif r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUSI] - Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                elif r.status_code >= 400 and r.status_code < 499:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed getting shipping rates: {r.text}, restarting...')
                    self.s.cookies.clear()
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                    self.tokenn()
                    break
            
                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed getting shipping rates {r.status_code}, retrtyng...')
                    time.sleep(self.delay)
                    continue

            self.fatturazione()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
            time.sleep(self.delay)
            self.rates()

        except Exception as e:
            error(f"[TASK {self.threadID}] [SUSI] - Exception while getting shipping rates {e.__class__.__name__}, retrying...")
            time.sleep(self.delay)
            self.rates()

    
    def fatturazione(self):

        global carted, failed, checkoutnum

        warn(f'[TASK {self.threadID}] [SUSI] - Submitting shipping...')

        try:
            if self.country == 'IT':
                payload = {
                    'dwfrm_singleshipping_shippingAddress_addressFields_firstName':self.name,
                    'dwfrm_singleshipping_shippingAddress_addressFields_lastName':self.surname,
                    'dwfrm_singleshipping_shippingAddress_addressFields_address1':self.address,
                    'dwfrm_singleshipping_shippingAddress_addressFields_address2':self.address2,
                    'dwfrm_singleshipping_shippingAddress_addressFields_postal':self.zip,
                    'dwfrm_singleshipping_shippingAddress_addressFields_city':self.city,
                    'dwfrm_singleshipping_shippingAddress_addressFields_phone':self.phone,
                    'dwfrm_singleshipping_shippingAddress_addressFields_country':self.country,
                    'dwfrm_singleshipping_shippingAddress_addressFields_states_state':self.state,
                    'dwfrm_singleshipping_shippingAddress_useAsBillingAddress':True,
                    'dwfrm_singleshipping_shippingAddress_shippingMethodID':self.shippingrates,
                    'dwfrm_singleshipping_shippingAddress_save':'Passa a Fatturazione >',
                    'csrf_token':self.cftoken
                }

            else:
                payload = {
                    'dwfrm_singleshipping_shippingAddress_addressFields_firstName':self.name,
                    'dwfrm_singleshipping_shippingAddress_addressFields_lastName':self.surname,
                    'dwfrm_singleshipping_shippingAddress_addressFields_address1':self.address,
                    'dwfrm_singleshipping_shippingAddress_addressFields_address2':self.address2,
                    'dwfrm_singleshipping_shippingAddress_addressFields_postal':self.zip,
                    'dwfrm_singleshipping_shippingAddress_addressFields_city':self.city,
                    'dwfrm_singleshipping_shippingAddress_addressFields_phone':self.phone,
                    'dwfrm_singleshipping_shippingAddress_addressFields_country':self.country,
                    #'dwfrm_singleshipping_shippingAddress_addressFields_states_state':self.state,
                    'dwfrm_singleshipping_shippingAddress_useAsBillingAddress':True,
                    'dwfrm_singleshipping_shippingAddress_shippingMethodID':self.shippingrates,
                    'dwfrm_singleshipping_shippingAddress_save':'Passa a Fatturazione >',
                    'csrf_token':self.cftoken
                }
            while True:

                r = self.s.post(
                    'https://www.susi.it/it-IT/cliente/fatturazione/',
                    data = payload,
                    timeout=self.timeout
                )

                
                if r.status_code == 200:
                    info(f'[Task {self.threadID}] [SUSI] - Succesfully submitted ship!')
                    break
                    

                if r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUSI] - Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                elif r.status_code == 403:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [SUSI] - Proxy banned, retrtyng...')
                        time.sleep(self.delay)
                    continue


                
                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed submitting shipping {r.status_code}, retrtyng...')
                    time.sleep(self.delay)
                    continue

            self.riepilogo()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
            time.sleep(self.delay)
            self.fatturazione()

        except Exception as e:
            error(f"[TASK {self.threadID}] [SUSI] - Exception while submitting shipping {e.__class__.__name__}, retrying...")
            time.sleep(self.delay)
            self.fatturazione()

    def riepilogo(self):

        global carted, failed, checkoutnum

        warn(f'[TASK {self.threadID}] [SUSI] - Submitting billing...')

        try:
            if self.country == 'IT':
                payload = {
                    'dwfrm_billing_save':True,
                    'dwfrm_billing_billingAddress_addressFields_firstName':self.name,
                    'dwfrm_billing_billingAddress_addressFields_lastName':self.surname,
                    'dwfrm_billing_billingAddress_addressFields_address1':self.address,
                    'dwfrm_billing_billingAddress_addressFields_address2':self.address2,
                    'dwfrm_billing_billingAddress_addressFields_postal':self.zip,
                    'dwfrm_billing_billingAddress_addressFields_city':self.city,
                    'dwfrm_billing_billingAddress_addressFields_country':self.country,
                    'dwfrm_billing_billingAddress_addressFields_states_state':self.state,
                    'dwfrm_billing_billingAddress_addressFields_phone':self.phone,
                    'dwfrm_billing_billingAddress_email_emailAddress':self.email,
                    'dwfrm_billing_billingAddress_acceptPrivacy':True,
                    'dwfrm_billing_couponCode':'',
                    'dwfrm_billing_paymentMethods_selectedPaymentMethodID':'paypal_pro',
                    'dwfrm_billing_paymentMethods_bml_year':'',
                    'dwfrm_billing_paymentMethods_bml_month':'',
                    'dwfrm_billing_paymentMethods_bml_day':'',
                    'dwfrm_billing_paymentMethods_bml_ssn':'',
                    'dwfrm_billing_save':'Passa a Invia ordine >',
                    'csrf_token':self.cftoken
                }

            else:
                payload = {
                    'dwfrm_billing_save':True,
                    'dwfrm_billing_billingAddress_addressFields_firstName':self.name,
                    'dwfrm_billing_billingAddress_addressFields_lastName':self.surname,
                    'dwfrm_billing_billingAddress_addressFields_address1':self.address,
                    'dwfrm_billing_billingAddress_addressFields_address2':self.address2,
                    'dwfrm_billing_billingAddress_addressFields_postal':self.zip,
                    'dwfrm_billing_billingAddress_addressFields_city':self.city,
                    'dwfrm_billing_billingAddress_addressFields_country':self.country,
                    #'dwfrm_billing_billingAddress_addressFields_states_state':self.state,
                    'dwfrm_billing_billingAddress_addressFields_phone':self.phone,
                    'dwfrm_billing_billingAddress_email_emailAddress':self.email,
                    'dwfrm_billing_billingAddress_acceptPrivacy':True,
                    'dwfrm_billing_couponCode':'',
                    'dwfrm_billing_paymentMethods_selectedPaymentMethodID':'paypal_pro',
                    'dwfrm_billing_paymentMethods_bml_year':'',
                    'dwfrm_billing_paymentMethods_bml_month':'',
                    'dwfrm_billing_paymentMethods_bml_day':'',
                    'dwfrm_billing_paymentMethods_bml_ssn':'',
                    'dwfrm_billing_save':'Passa a Invia ordine >',
                    'csrf_token':self.cftoken
                }
            while True:

                r = self.s.post(
                    'https://www.susi.it/it-IT/cliente/riepilogo-ordine/',
                    data = payload,
                    timeout=self.timeout
                )

                
                if r.status_code == 200:
                    self.notify_url = r.text.split('notify_url" value="')[1].split('"')[0]
                    self.returnurl = r.text.split('return" value="')[1].split('"')[0]
                    self.cancel_return = r.text.split('cancel_return" value="')[1].split('"')[0]
                    self.currency = r.text.split('currency_code" value="')[1].split('"')[0]
                    self.invoice = r.text.split('invoice" value="')[1].split('"')[0]
                    self.amount = r.text.split('subtotal" value="')[1].split('"')[0]
                    info(f'[Task {self.threadID}] [SUSI] - Succesfully submitted billing!')
                    break
                    

                if r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUSI] - Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                elif r.status_code == 403:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [SUSI] - Proxy banned, retrtyng...')
                        time.sleep(self.delay)
                    continue
                
                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed submitting shipping {r.status_code}, retrtyng...')
                    time.sleep(self.delay)
                    continue

            self.secure()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
            time.sleep(self.delay)
            self.riepilogo()

        except Exception as e:
            error(f"[TASK {self.threadID}] [SUSI] - Exception while submitting billing {e.__class__.__name__}, retrying...")
            time.sleep(self.delay)
            self.riepilogo()

    

    def secure(self):

        warn(f'[TASK {self.threadID}] [SUSI] - Submitting order...')
        global carted, failed, checkoutnum

        try:

            payload = {
                'amount':self.amount,
                'shipping':'0.00',
                'handling':'0.00',
                'tax':'0',
                'business':'amministrazione.web@susi.it',
                'notify_url':f'https://www.susi.it/on/demandware.store/Sites-susi-Site/it_IT/PayPalPro-Notify?ref={self.invoice}',
                'currency_code':self.currency,
                'lc':self.country,
                'return':f'https://www.susi.it/on/demandware.store/Sites-susi-Site/it_IT/PayPalPro-Success?ref={self.invoice}',
                'cancel_return':f'https://www.susi.it/on/demandware.store/Sites-susi-Site/it_IT/PayPalPro-Cancel?ref={self.invoice}',
                'address1':self.address,
                'city':self.city,
                'state':self.state,
                'country':self.country,
                'first_name':self.name,
                'last_name':self.surname,
                'night_phone_b':self.phone,
                'zip':self.zip,
                'paymentaction':'sale',
                'billing_address1':self.address,
                'billing_city':self.city,
                'billing_state':self.state,
                'billing_country':self.country,
                'billing_zip':self.zip,
                'invoice':self.invoice,
                'billing_first_name':self.name,
                'billing_last_name':self.surname,
                'address_override':1,
                'rm':2,
                'no_shipping':0
            }

            head = {
                'content-type':'application/x-www-form-urlencoded',
                'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'referer':'https://www.paypal.com/hostedpaymentnodeweb/wps',
                'accept-encoding':'gzip, deflate'
            }

            self.s.headers.update(head)

            while True:
                r = self.s.post(
                    'https://www.paypal.com/cgi-bin/webscr?cmd=_hssnode-merchantpaymentweb',
                    data = payload,
                    timeout=self.timeout,
                    allow_redirects = False
                )

                if r.status_code == 302:
                    self.pp_url = r.headers['Location']
                    if 'StateFatalError' not in self.pp_url:

                        checkoutnum = checkoutnum + 1
                        self.bar()
                        info(f'[TASK {self.threadID}] [SUSI] - Succesfully checked out!')
                        break
                    else:
                        failed = failed + 1
                        self.bar()
                        error(f'[TASK {self.threadID}] [SUSI] - Product oos while opening paypal, restarting...')
                        self.s.cookies.clear()
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        self.tokenn()
                        break
                
                
                if r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUSI] - Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                elif r.status_code == 403:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [SUSI] - Proxy banned, retrtyng...')
                        time.sleep(self.delay)
                    continue


                
                else:
                    error(f'[TASK {self.threadID}] [SUSI] - Failed submitting order {r.status_code}, retrtyng...')
                    time.sleep(self.delay)
                    continue


            self.pass_cookies()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUSI] - Connection error, retrying...')
            time.sleep(self.delay)
            self.secure()

        except Exception as e:
            error(f"[TASK {self.threadID}] [SUSI] - Exception while submitting order {e.__class__.__name__}, retrying...")
            time.sleep(self.delay)
            self.secure()

    


    def webhook(self):
            if self.selected_proxies == None:
                self.proxi = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**||SUSI||**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.sizeprint, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'PAYPAL', inline = False)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False) 
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            try:
                embed.set_thumbnail(url = self.image)   
            except:
                embed.set_thumbnail(url = 'https://www.susi.it/on/demandware.static/Sites-susi-Site/-/default/dw0ceb63a9/images/susi-logo.svg')
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.pubblic()

    def pubblic(self):
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            #webhook = DiscordWebhook(url = 'https://discord.com/api/webhooks/773665832554987550/o6FJp62HUV5p7DzMGyMg1B1fVG9ADfpgu-OU6Ztm89DWefNQHc_ei2D44RoN2479WjHZ', content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**||SUSI||**', value = f"[{self.title}]({self.link})", inline = True)     
            embed.add_embed_field(name='**SIZE**', value = self.sizeprint, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'PAYPAL', inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            try:
                embed.set_thumbnail(url = self.image)   
            except:
                embed.set_thumbnail(url = 'https://www.susi.it/on/demandware.static/Sites-susi-Site/-/default/dw0ceb63a9/images/susi-logo.svg')   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
            except:
                pass

    def pass_cookies(self):

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
            url = urllib.parse.quote(base64.b64encode(bytes(self.pp_url, 'utf-8')).decode())
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
                    writer.writerow({'SITE':'SUSI','SIZE':f'{self.sizeprint}','PAYLINK':f'{self.token}','PRODUCT':f'{self.variant}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'SUSI','SIZE':f'{self.sizeprint}','PAYLINK':f'{self.token}','PRODUCT':f'{self.variant}'})
                    
            self.webhook()
            
        except Exception as e: 
            error(f'[TASK {self.threadID}] [SUSI] - Error while passing cookies {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.pass_cookies()