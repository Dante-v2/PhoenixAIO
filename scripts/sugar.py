import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

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


carted = 0
checkoutnum = 0
failed = 0

CIPHERS = (
    'EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH'
    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+HIGH:!aNULL:'
    '!eNULL:!MD5'
)

class DESAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(DESAdapter, self).init_poolmanager(*args, **kwargs)#
    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(DESAdapter, self).proxy_manager_for(*args, **kwargs)


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


class SUGAR():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'sugar/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "sugar/proxies.txt")
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
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'anticaptcha','api_key':config['anticaptcha']},doubleDown=False,requestPostHook=self.injection, cipherSuite="ECDHE-RSA-AES256-SHA")
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha']},doubleDown=False,requestPostHook=self.injection, cipherSuite="ECDHE-RSA-AES256-SHA")
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)
        
        self.discord = DISCORD_ID
        self.s.mount('https://', DESAdapter())
        self.s.proxies = self.selected_proxies
        self.link = row['LINK'] 
        self.size = row['SIZE']
        self.mail = row['MAIL']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.country = row['COUNTRY']
        self.address = row['ADDRESS']
        self.rid = row['REGIONID']
        self.region = row['REGION']
        self.zipcode = row['ZIPCODE']
        self.city = row['CITY']
        self.phone = row['PHONE']
        self.payment = row['PAYMENT']
        self.cardnumber = row['CARD NUMBER']
        self.month = row['EXP MONTH']
        self.year = row['EXP YEAR']
        self.cvv = row['CVV']
        self.webhook = webhook
        self.threadID = '%03d' % i
        self.version = version
        self.delay = int(config["delay"])
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]
        
        self.timeout = 120

        self.balance = balancefunc()

        self.bar()

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


        warn(f'[TASK {self.threadID}] [SUGAR] - Tasks started!')

        
        self.getprod()


    def choose_proxy(self, proxy_list):
        px = random.choice(proxy_list)
        self.proxi =px
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


    def injection(self, session, response):

        self.balance = balancefunc()
        self.bar()

        try:   
            if isChallenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [SUGAR] - Solving Cloudflare v2 api 2')
                return helheim('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693', session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [SUGAR] - Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [SUGAR] - Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
            else:
                return response



    def bar(self):
        if machineOS.lower() == 'windows':
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running SUGAR | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - SUGAR Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')


################################################################################################################################# - GET AL PRODOTTO


    def getprod(self):

        try: 

            warn(f'[TASK {self.threadID}] [SUGAR] - Getting product page...')

            head = {
                'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
                'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding':'gzip, deflate',
                'accept-language':'en'
            }

            while True:

                self.r =self.s.get(self.link, headers=head)

                if self.r.status_code == 200:
                    
                    try:
                        soup = bs(self.r.text, features='lxml')
                        oos = soup.find("div",{"class":"product-info-main"})
                        oos = oos.text
                        tit = soup.find("div",{"class":"page-title-wrapper product"})
                        self.title = tit.find("span",{"data-ui-id":"page-title-wrapper"}).text
                        gal = soup.find("div",{"class":"gallery-desktop"})
                        self.image = gal.find("img",{"class":"box1"})["src"]
                        if "Sold out" in oos:
                            warn(f'[TASK {self.threadID}] [SUGAR] - {self.title} oos, monitoring...')
                            time.sleep(self.delay)
                            continue

                        else:
                            prod = soup.find("div",{"class":"field configurable required"})
                            tutto = prod.find("select",{"class":"super-attribute-select size"})
                            self.super = tutto["name"] #superattribute
                            self.att = tutto["id"]
                            self.atx = self.att.split("attribute")[1]

                            add = soup.find("div",{"class":"product-add-form"})
                            form = add.find("form",{"id":"product_addtocart_form"})
                            self.productid = form.find("input",{"name":"product"})["value"]
                            self.atc_url = form["action"]
                            #self.selection = form.find("input",{"name":"selected_configurable_option"})
                            self.formkey = form.find("input",{"name":"form_key"})["value"]
                            #print(self.selection)

                            fiel = soup.find("div",{"class":"fieldset"})
                            js = fiel.find("script",{"type":"text/x-magento-init"})
                            r_json = json.loads(js.string)
                            ciao = r_json["#product_addtocart_form"]["configurable"]["spConfig"]["attributes"][self.atx]["options"]
                            info(f'[TASK {self.threadID}] [SUGAR] - Succesfully got product page!')
                            try:
                                self.image = str(self.r['html']).split("class=box1 src=")[1].split(" alt=")[0]
                            except:
                                pass
                            self.iditem = []
                            self.sizeid = []
                            self.var = []
                            for a in ciao:
                                self.iditem.append(a["id"])
                                c = a["label"]
                                if "\u00bd" in c:
                                    c = c.replace("\u00bd",".5")
                                self.sizeid.append(c) 
                                p = str(a["products"])
                                g = p.replace("['","")
                                x = g.replace("']","")
                                self.var.append(x)

                            if self.var == '':
                                warn(f'[TASK {self.threadID}] [SUGAR] - {self.title} oos, monitoring...')
                                time.sleep(self.delay)
                                continue
                            
                            tot = zip(self.iditem, self.sizeid, self.var)
                            connecto = list(tot)
                            connect = []
                            self.sizerange = []

                            for x in connecto:
                                if len(x[2]) > 3:
                                    connect.append(x)
                            
                            if not connect:
                                warn(f'[TASK {self.threadID}] [SUGAR] - {self.title} oos, monitoring...')
                                time.sleep(self.delay)
                                continue

                            if self.size == "RANDOM":
                                scelta = random.choice(connect)
                                ciao3 = scelta[0]
                                self.id = "".join(ciao3)
                                ciao = scelta[2]
                                self.var = "".join(ciao)
                                ciao2 = scelta[1]
                                self.saiz = "".join(ciao2)
                                warn(f'[TASK {self.threadID}] [SUGAR] - Adding to cart size {self.saiz}')
                                break

                            elif '-' in self.size:
                                self.size1 = float(self.size.split('-')[0])
                                self.size2 = float(self.size.split('-')[1])
                                for x in connect:
                                    if self.size1 <= float(x[1]) <= self.size2:
                                        self.sizerange.append(x[1])     
                                self.sizerandom = random.choice(self.sizerange)   
                                for Traian in connect:
                                    if self.sizerandom == Traian[1]:
                                        ciao0 = Traian[0]
                                        self.id = "".join(ciao0)
                                        ciao2 = Traian[2]
                                        self.var = "".join(ciao2)
                                        ciao1 = Traian[1]
                                        self.saiz = "".join(ciao1) 
                                warn(f'[TASK {self.threadID}] [SUGAR] - Adding to cart size {self.saiz}')
                                break
                
                            elif ',' in self.size:
                                self.size1 = float(self.size.split(',')[0])
                                self.size2 = float(self.size.split(',')[1])
                                for x in connect:
                                    if self.size1 <= float(x[1]) <= self.size2:
                                        self.sizerange.append(x[1])     
                                self.sizerandom = random.choice(self.sizerange)   
                                for Traian in connect:
                                    if self.sizerandom == Traian[1]:
                                        ciao0 = Traian[0]
                                        self.id = "".join(ciao0)
                                        ciao2 = Traian[2]
                                        self.var = "".join(ciao2)
                                        ciao1 = Traian[1]
                                        self.saiz = "".join(ciao1) 
                                warn(f'[TASK {self.threadID}] [SUGAR] - Adding to cart size {self.saiz}')
                                break

                            else:
                                for Traian in connect:
                                    if self.size == Traian[1]:
                                        ciao0 = Traian[0]
                                        self.id = "".join(ciao0)
                                        ciao2 = Traian[2]
                                        self.var = "".join(ciao2)
                                        ciao1 = Traian[1]
                                        self.saiz = "".join(ciao1)
                                warn(f'[TASK {self.threadID}] [SUGAR] - Adding to cart size {self.saiz}')
                                break



                    except ConnectionError as e:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
                        time.sleep(self.delay)
                        continue

                    except Exception as e:
                        warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while getting product {e}, retrying...')
                        time.sleep(self.delay)
                        continue


                elif self.r.status_code == 403:
                    error(f'[TASK {self.threadID}] [SUGAR] - Proxy banned, retrying...')                 
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies      
                        self.prox = self.selected_proxies['http']                  
                    time.sleep(self.delay)
                    continue

                elif self.r.status_code >= 500 and self.r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying')
                    time.sleep(self.delay)
                    continue

                elif self.r.status_code == 404:
                    warn(f'[TASK {self.threadID}] [SUGAR] - Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    error(f'[TASK {self.threadID}] [SUGAR] - Error {self.r.status_code}, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    continue    
            
            self.atc()
            
        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
            time.sleep(self.delay)
            self.getprod()

        except TimeoutError:
            error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
            time.sleep(self.delay)
            self.getprod()

        except Exception as e:
            warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while getting product, retrying...')
            time.sleep(self.delay)
            self.getprod()


    def atc(self):

        global carted, failed, checkoutnum

        try:

            payload = {
                'product':self.productid,
                'selected_configurable_option':self.var,
                'related_product':'',
                'item':self.productid,
                'form_key':self.formkey,
                self.super:self.id
            }


            h = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'x-requested-with': 'XMLHttpRequest',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
                'content-type': 'application/x-www-form-urlencoded',
                'referer': self.link,
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6'
            }

            o = requests.cookies.create_cookie(domain='.www.sugar.it', name = 'form_key', value = self.formkey)
            self.s.cookies.set_cookie(o)

            while True:

                r = self.s.post(self.atc_url, data = payload, headers = h)
                
                if r.status_code == 200:

                    if "Your bag is empty you better back to shopping" in r.text:
                        error(f'[TASK {self.threadID}] [SUGAR] - Failed adding to cart, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        self.getprod()

                    else:
                        info(f'[TASK {self.threadID}] [SUGAR] - Successfully added to cart!')
                        carted = carted + 1
                        self.bar()
                        break

                elif r.status_code == 403:
                    error(f'[TASK {self.threadID}] [SUGAR] - Proxy banned, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    continue

                elif r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    error(f'[TASK {self.threadID}] [SUGAR] - Error {r.status_code}, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    continue

            self.check1()


        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
            time.sleep(self.delay)
            self.atc()

        except TimeoutError:
            error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
            time.sleep(self.delay)
            self.atc()

        except Exception as e:
            warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while adding to cart, retrying...')
            time.sleep(self.delay)
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            time.sleep(self.delay)
            self.atc()


    def check1(self):

        global carted, failed, checkoutnum

        warn(f'[TASK {self.threadID}] [SUGAR] - Getting checkout page...')

        self.appost = True

        try:

            while True:

                r = self.s.get('https://www.sugar.it/onestepcheckout/')
                
                if r.status_code == 200:

                    if "Your bag is empty you better back to shopping" in r.text:
                        error(f'[TASK {self.threadID}] [SUGAR] - Cart empty, restarting...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        self.appost = False
                        break

                    else:
                        colum = r.text
                        self.entity = colum.split('entity_id":"')[1].split('",')[0]
                        info(f'[TASK {self.threadID}] [SUGAR] - Succesfully got checkout page!')
                        break

                elif r.status_code == 403:
                    error(f'[TASK {self.threadID}] [SUGAR] - Proxy banned, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        self.prox = self.selected_proxies['http']
                    time.sleep(self.delay)
                    continue

                elif r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
    
                else:
                    error(f'[TASK {self.threadID}] [SUGAR] - Error {r.status_code}, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        self.prox = self.selected_proxies['http']
                    time.sleep(self.delay)
                    continue

            if self.appost == False:
                self.getprod()
            elif self.payment == 'CC':
                self.stripe()
            else:
                self.check3()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
            time.sleep(self.delay)
            self.check1()

        except TimeoutError:
            error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
            time.sleep(self.delay)
            self.check1()

        except Exception as e:
            warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while getting checkout page, retrying...')
            time.sleep(self.delay)
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            self.check1()

    def check2(self):

        try:

            warn(f'[TASK {self.threadID}] [SUGAR] - Getting shipping rates...')

            global carted, failed, checkoutnum

            try:


                p = {
                    'Accept': '*/*',
                    'X-Requested-With': 'XMLHttpRequest',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'Content-Type': 'application/json',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Dest': 'empty',
                    'Referer': 'https://www.sugar.it/onestepcheckout/',
                    'Accept-Language': 'en'
                }

                if self.rid != '':
                    payload = '''{"address":{"street":["self.address"],"city":"self.city","region_id":"self.rid","region":"self.region","country_id":"self.country","postcode":"self.zipcode","firstname":"self.name","lastname":"self.surname","company":"","telephone":"self.phone","custom_attributes":[{"attribute_code":"gender","value":"1"}]},"isAddressSameAsShipping":true}'''.replace("self.country", f"{self.country}").replace("self.region", f"{self.region}").replace('self.address', f"{self.address}").replace("self.phone", f"{self.phone}").replace("self.zipcode", f"{self.zipcode}").replace("self.city", f"{self.city}").replace("self.name", f"{self.name}").replace("self.surname", f"{self.surname}").replace("self.rid", f"{self.rid}")
                else:
                    payload = '''{"address":{"street":["self.address"],"city":"self.city","region":"self.region","country_id":"self.country","postcode":"self.zipcode","firstname":"self.name","lastname":"self.surname","company":"","telephone":"self.phone","custom_attributes":[{"attribute_code":"gender","value":"1"}]},"isAddressSameAsShipping":true}'''.replace("self.country", f"{self.country}").replace("self.region", f"{self.region}").replace('self.address', f"{self.address}").replace("self.phone", f"{self.phone}").replace("self.zipcode", f"{self.zipcode}").replace("self.city", f"{self.city}").replace("self.name", f"{self.name}").replace("self.surname", f"{self.surname}")

                while True:
                    
                    r = self.s.post(f'https://www.sugar.it/rest/default/V1/guest-carts/{self.entity}/osc-estimate-shipping-methods', json = payload, headers = p)
                    if r.status_code == 200:
                        r_json = json.loads(r.text)
                        self.carrier = r_json["shipping_methods"][0]["carrier_code"]
                        self.rate = r_json["shipping_methods"][0]["method_code"]
                        warn(f'[TASK {self.threadID}] [SUGAR] - Submitting shipping rates...')
                        break
                        
                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [SUGAR] - Forbidden access, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code >= 500 and r.status_code < 600:
                        error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                        
                    else:
                        error(f'[TASK {self.threadID}] [SUGAR] - Error while getting shipping rates{r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                if self.payment == 'CC':
                    self.stripe()
                elif self.payment == 'PP':
                    self.check3()
                else:
                    error(f'[TASK {self.threadID}] [SUGAR] - Something is wrong in your csv!')

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
                time.sleep(self.delay)
                self.check2()

            except TimeoutError:
                error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
                time.sleep(self.delay)
                self.check2()

            except Exception as e:
                warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while getting shipping rates, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.check2()

        except:
            pass

    def stripe(self):

        try:

            warn(f'[TASK {self.threadID}] [SUGAR] - Getting stripe info...')

            global carted, failed, checkoutnum

            try:

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'Content-Type': 'text/plain;charset=UTF-8',
                    'Accept': '*/*',
                    'Origin': 'https://m.stripe.network',
                    'Sec-Fetch-Site': 'cross-site',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Dest': 'empty',
                    'Referer': 'https://m.stripe.network/',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
                }
                
                while True:
                    
                    r = self.s.post(f'https://m.stripe.com/6', headers = headers)
                    
                    if r.status_code == 200:
                        r_json = json.loads(r.text)
                        self.muid = r_json['muid']
                        self.guid = r_json['guid']
                        self.sid = r_json['sid']
                        info(f'[TASK {self.threadID}] [SUGAR] - Succesfully got stripe info!')
                        break
                        
                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [SUGAR] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code >= 500 and r.status_code < 600:
                        error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue
                        
                    else:
                        error(f'[TASK {self.threadID}] [SUGAR] - Error while getting stripe info {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                self.cc()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                    self.prox = self.selected_proxies['http']
                error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
                time.sleep(self.delay)
                self.stripe()

            except TimeoutError:
                error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
                time.sleep(self.delay)
                self.stripe()

            except Exception as e:
                warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while getting stripe info, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.stripe()

        except:
            pass


    def cc(self):

        try:

            warn(f'[TASK {self.threadID}] [SUGAR] - Submitting credit card...')

            global carted, failed, checkoutnum
            self.error = False
            try:


                headers = {
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://js.stripe.com',
                    'Sec-Fetch-Site': 'same-site',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Dest': 'empty',
                    'Referer': 'https://js.stripe.com/',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'en,it-IT;q=0.9,it;q=0.8,en-US;q=0.7,de;q=0.6,es;q=0.5,fr;q=0.4'
                }

                payload = {
                    'type':'card',
                    'billing_details[name]':f'{self.name+self.surname}',
                    'billing_details[email]':self.mail,
                    'billing_details[phone]':self.phone,
                    'billing_details[address][city]':self.city,
                    'billing_details[address][country]':self.country,
                    'billing_details[address][line1]':self.address,
                    'billing_details[address][postal_code]':self.zipcode,
                    'billing_details[address][state]':self.region,
                    'card[number]':self.cardnumber,
                    'card[cvc]':self.cvv,
                    'card[exp_month]':self.month,
                    'card[exp_year]':self.year,
                    'guid':self.guid,
                    'muid':self.muid,
                    'sid':self.sid,
                    'payment_user_agent':'stripe.js/a58b3a46; stripe-js-v3/a58b3a46',
                    'time_on_page':'37218',
                    'referrer':'https://www.sugar.it/',
                    'key':'pk_live_9nkJCmQ9Glh9LgSbxugunjYI00cNVIIE9u'
                }

                while True:

                    x = requests.Session()
                    
                    r = x.post('https://api.stripe.com/v1/payment_methods', headers = headers, data = payload)

                    if r.status_code == 200:
                        r_json = json.loads(r.text)
                        self.id = r_json['id']
                        info(f'[TASK {self.threadID}] [SUGAR] - Succesfully submitted credit card...')
                        break

                        
                    elif r.status_code == 400:
                        r_json = json.loads(r.text)
                        if r_json['error']['code'] == 'parameter_invalid_empty':
                            error(f'[TASK {self.threadID}] [SUGAR] - Cart parameter empty, check your csv')
                            self.error = True
                            break
                        else:
                            error(f'[TASK {self.threadID}] [SUGAR] - Unkown error, check your csv')
                            self.error = True
                            break

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [SUGAR] - Forbidden access, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code >= 500 and r.status_code < 600:
                        error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue
                        
                    else:
                        error(f'[TASK {self.threadID}] [SUGAR] - Error {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                if self.error:
                    sys.exit()
                else:
                    self.check3()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
                time.sleep(self.delay)
                self.cc()

            except TimeoutError:
                error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
                time.sleep(self.delay)
                self.cc()

            except Exception as e:
                warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while submitting cc, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.cc()

        except:
            pass

    
    def cc2(self):

        try:
            warn(f'[TASK {self.threadID}] [SUGAR] - Processing order...')

            global carted, failed, checkoutnum

            self.error2 = False

            try:

                h = {
                    'accept': '*/*',
                    'x-requested-with': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
                    'content-type': 'application/json',
                    'referer': 'https://www.sugar.it/onestepcheckout/',
                    'accept-encoding': 'gzip, deflate',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6'
                }


                cardtype = identify_card_type(self.cardnumber)
                if cardtype == "MasterCard":
                    card_type = "mastercard"
                elif cardtype == "Visa":
                    card_type = "visa"

                self.ultime4 = self.cardnumber[-4:]


                payload = {"cartId":self.entity,"billingAddress":{"countryId":self.country,"region":self.region,"street":[self.address],"company":"","telephone":self.phone,"postcode":self.zipcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":[{"attribute_code":"gender","value":"1"}],"extension_attributes":{},"saveInAddressBook":0},"paymentMethod":{"method":"stripe_payments","additional_data":{"cc_stripejs_token":f"{self.id}:{card_type}:{self.ultime4}","cc_save":False}},"email":self.mail}
                
                while True:
                    r = self.s.post(f'https://www.sugar.it/rest/default/V1/guest-carts/{self.entity}/payment-information',json =  payload, headers = h)


                    if r.status_code == 200:
                        info(f'[TASK {self.threadID}] [SUGAR] - Succesfully checked out!')
                        break

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [SUGAR] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code >= 500 and r.status_code < 600:
                        error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue
                        
                    elif r.status_code == 400:
                        r_json = json.loads(r.text)
                        if r_json['message'] == 'Your card has insufficient funds.':
                            error(f'[TASK {self.threadID}] [SUGAR] - Your card got insufficent funds!')
                            self.error2 = True
                            self.messerr = r_json['message']
                            break

                        elif r_json['message'] == 'Your card was declined.':
                            error(f'[TASK {self.threadID}] [SUGAR] - Your card was declined!')
                            self.error2 = True
                            self.messerr = r_json['message']
                            break

                        else:
                            error(f'[TASK {self.threadID}] [SUGAR] - Unkown error, check your csv!')
                            self.error2 = True
                            self.messerr = r_json['message']
                            break

                    else:
                        error(f'[TASK {self.threadID}] [SUGAR] - Error while processing order{r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue
                if self.error2:
                    self.declined()
                else:
                    self.SuccessCC()

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
                time.sleep(self.delay)
                self.cc2()

            except TimeoutError:
                error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
                time.sleep(self.delay)
                self.cc2()

            except Exception as e:
                warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while processing order, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.cc2()

        except:
            pass


    def check3(self):

        try:
            warn(f'[TASK {self.threadID}] [SUGAR] - Submitting informations...')

            global carted, failed, checkoutnum

            try:
                h = {
                    'accept': '*/*',
                    'x-requested-with': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
                    'content-type': 'application/json',
                    'referer': 'https://www.sugar.it/onestepcheckout/',
                    'accept-encoding': 'gzip, deflate',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6'
                }

                self.rate = 'bestway'
                self.carrier = 'tablerate'


                if self.rid != '':
                    payload = {"addressInformation":{"shipping_address":{"countryId":self.country,"regionCode":self.rid,"region":self.region,"street":[self.address],"company":"","telephone":self.phone,"postcode":self.zipcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":[{"attribute_code":"gender","value":"1"}],"extension_attributes":{}},"billing_address":{"countryId":self.country,"regionCode":self.rid,"region":self.region,"street":[self.address],"company":"","telephone":self.phone,"postcode":self.zipcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":[{"attribute_code":"gender","value":"1"}],"saveInAddressBook":0},"shipping_method_code":self.rate,"shipping_carrier_code":self.carrier},"customerAttributes":{"gender":"1"},"additionInformation":{"register":False,"same_as_shipping":True}}
                else:
                    payload = {"addressInformation":{"shipping_address":{"countryId":self.country,"region":self.region,"street":[self.address],"company":"","telephone":self.phone,"postcode":self.zipcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":[{"attribute_code":"gender","value":"1"}],"extension_attributes":{}},"billing_address":{"countryId":self.country,"region":self.region,"street":[self.address],"company":"","telephone":self.phone,"postcode":self.zipcode,"city":self.city,"firstname":self.name,"lastname":self.surname,"customAttributes":[{"attribute_code":"gender","value":"1"}],"saveInAddressBook":0},"shipping_method_code":self.rate,"shipping_carrier_code":self.carrier},"customerAttributes":{"gender":"1"},"additionInformation":{"register":False,"same_as_shipping":True}}

                while True:
                    r = self.s.post(f'https://www.sugar.it/rest/default/V1/guest-carts/{self.entity}/checkout-information', json = payload, headers = h)

                    if r.status_code == 200:
                        if 'true' in r.text:
                            info(f'[TASK {self.threadID}] [SUGAR] - Successfully submitted info!')
                            break
                        else:
                            error(f'[TASK {self.threadID}] [SUGAR] - Failed subimtting info')
                            time.sleep(self.delay)
                            continue


                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [SUGAR] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code >= 500 and r.status_code < 600:
                        error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue
                        
                    elif r.status_code == 400:
                        error(f'[TASK {self.threadID}] [SUGAR] - Error submitting shipping, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SUGAR] - Error while submitting info {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                if self.payment == 'CC':
                    self.cc2()
                elif self.payment == 'PP':
                    self.pp1()
                else:
                    error(f'[TASK {self.threadID}] [SUGAR] - Something is wrong in your csv!')

            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                    self.prox = self.selected_proxies['http']
                error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
                time.sleep(self.delay)
                self.check3()

            except TimeoutError:
                error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
                time.sleep(self.delay)
                self.check3()

            except Exception as e:
                warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while submitting info, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.check3()

        except:
            pass

    def pp1(self):


        global carted, failed, checkoutnum

        try:
            warn(f'[TASK {self.threadID}] [SUGAR] - Submitting payment method...')

            h = {
                'accept': '*/*',
                'x-requested-with': 'XMLHttpRequest',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
                'content-type': 'application/json',
                'referer': 'https://www.sugar.it/onestepcheckout/',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6'
            }

            h2 = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'referer': 'https://www.sugar.it/onestepcheckout/',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'en'
            }


            payload = {"cartId": self.entity,"email":self.mail,"paymentMethod":{"method":"paypal_express","po_number":0,"additional_data":None}}
            
            while True:
                r = self.s.post(f'https://www.sugar.it/rest/default/V1/guest-carts/{self.entity}/set-payment-information', json=payload, headers = h)

                if r.status_code == 200:  
                    x = self.s.get('https://www.sugar.it/paypal/express/start/', headers = h2, allow_redirects = False)
                    self.pp = x.headers['Location']
                    info(f'[TASK {self.threadID}] [SUGAR] - Successfully checked out!')
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break

                elif r.status_code == 403:
                    error(f'[TASK {self.threadID}] [SUGAR] - Forbidden access, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    continue


                elif r.status_code >= 500 and r.status_code < 600:
                    error(f'[TASK {self.threadID}] [SUGAR] - Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                    
                else:
                    error(f'[TASK {self.threadID}] [SUGAR] - Error while getting paypal {r.status_code}, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    continue
            
            self.passCookies()

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
                self.prox = self.selected_proxies['http']
            error(f'[TASK {self.threadID}] [SUGAR] - Connection error, retrying...')
            time.sleep(self.delay)
            self.pp1()

        except TimeoutError:
            error(f'[TASK {self.threadID}] [SUGAR] - Timeout reached, retrying...')
            time.sleep(self.delay)
            self.pp1()

        except Exception as e:
            warn(f'[TASK {self.threadID}] [SUGAR] - Exception error while getting paypal {e}, retrying...')
            time.sleep(self.delay)
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            time.sleep(self.delay)
            self.pp1()


    def passCookies(self):

        try:

            global carted, failed, checkoutnum

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
                url = urllib.parse.quote(base64.b64encode(bytes(self.pp, 'utf-8')).decode())
                self.token = f"https://api.phoenixbot.io/exploits/?cookie={cookieStr}&redirect={url}"
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
                        writer.writerow({'SITE':'SUGAR','SIZE':f'{self.saiz}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})

                else:
                    self.expToken = self.token
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'SUGAR','SIZE':f'{self.saiz}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})

                        
                self.SuccessPP()
                
            except Exception as e: 
                error(f'[TASK {self.threadID}] [SUGAR] - Exception passing cookies, retrying...') 
                failed = failed + 1
                self.bar()
                time.sleep(self.delay)
                self.SuccessPP()
            
        except:
            pass

    def Pubblic_Webhook(self):
        if self.payment == 'CC':
            self.payment = 'CC'
        else:
            self.payment = 'PP'
        try:
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO Cooked!', color = 40703)
            embed.add_embed_field(name=f'**SUGAR**', value = f'{self.title}', inline = False)
            embed.add_embed_field(name='**LINK**', value = f"[LINK]({self.link})", inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.saiz, inline = True)
            embed.add_embed_field(name='**MODE**', value = self.payment, inline = True)  
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url = self.image) 
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
            if self.payment == 'CC':
                self.payment = 'CC'
            else:
                self.payment = 'PP'

            if self.selected_proxies == None:
                self.proxi = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**SUGAR**', value =f'{self.title}', inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.saiz, inline = True)
            embed.add_embed_field(name='**MODE**', value = self.payment, inline = True)
            embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = True)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)   
            embed.set_thumbnail(url = self.image) 
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass

    def SuccessCC(self):
        try:
            if self.payment == 'CC':
                self.payment = 'CC'
            else:
                self.payment = 'PP'

            if self.selected_proxies == None:
                self.proxi = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Succesfully checked out!', color = 4437377)
            embed.add_embed_field(name=f'**SUGAR**', value =f'{self.title}', inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.saiz, inline = True)
            embed.add_embed_field(name='**MODE**', value = self.payment, inline = True)
            embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = True)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)   
            embed.set_thumbnail(url = self.image) 
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass

    def declined(self):
        if self.payment == 'CC':
            self.payment = 'CC'
        else:
            self.payment = 'PP'
        if self.selected_proxies == None:
            self.proxi = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Payment declined!', color = 15746887)
        embed.add_embed_field(name=f'**SUGAR**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.saiz, inline = True)
        embed.add_embed_field(name='**MODE**', value = self.payment, inline = True)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = True)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
        embed.add_embed_field(name='**ERROR**', value = f"{self.messerr}", inline = False)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()