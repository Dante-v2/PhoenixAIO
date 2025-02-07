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
checkoutnum = 0
failed = 0


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

class WORKINGCLASSHEROES():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
        

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'workingclassheroes/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "workingclassheroes/proxies.txt")
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
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': True,'platform': 'windows'},captcha={'provider':'anticaptcha','api_key':config['anticaptcha']},doubleDown=False,requestPostHook=self.injection)
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': True,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha']},doubleDown=False,requestPostHook=self.injection)
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)
        
        self.s.proxies = self.selected_proxies
        self.discord = DISCORD_ID
        self.link = row['LINK']
        self.size = row['SIZE']	
        self.mail = row['MAIL']
        self.country = row['COUNTRY']
        self.zipcode = row['ZIPCODE']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.city = row['CITY']
        self.phone = row['PHONE']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.cardnumber = row['CARDNUMBER']
        self.expmonth = row['EXPMONTH']
        self.expyear = row['EXPYEAR']
        self.cvc = row['CVC']
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]


        self.version = version
        self.delay = int(config['delay'])

        if config['timeout-workingclassheroes'] == "":
            self.timeout = 25

        else:
            self.timeout = int(config['timeout-workingclassheroes'])


        self.balance = balancefunc()

        self.bar()




        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Task started!')
        

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
        except Exception as e:
            error("FAILED CSV")



        self.getprod()


#####################################################################################################################  - CHOOSE PROXY


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
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running WORKINGCLASSHEROES | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - WORKINGCLASSHEROES Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')


    def injection(self, session, response):

        self.balance = balancefunc()
        self.bar()

        try:
            if session.is_New_IUAM_Challenge(response) \
            or session.is_New_Captcha_Challenge(response) \
            or session.is_BFM_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Solving Cloudflare v2 api2')
                return helheim('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693', session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
            else:
                return response



    def getprod(self):

        self.mom = False

        try:

            try:

                warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Getting product...')

                while True:


                    r = self.s.get(self.link, proxies = self.selected_proxies)

                    if r.status_code == 200:
                        
                        try:
                            var = r.text.split("var universal_pageType = 'product'; var ")[1].split(";</script>")[0]
                            self.prodid = var.split('"id":')[1].split(',')[0]

                            headers = {
                                'accept': 'application/json, text/javascript, */*; q=0.01',
                                'accept-encoding': "utf-8",
                                'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                                'content-type': 'application/json; charset=UTF-8',
                                'origin': 'https://www.workingclassheroes.co.uk',
                                'referer': self.link,
                                'sec-fetch-dest': 'empty',
                                'sec-fetch-mode': 'cors',
                                'sec-fetch-site': 'same-origin',
                                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
                                'x-requested-with': 'XMLHttpRequest'
                            }
                            
                            payload = {"controlLocation":"/modules/controls/clAttributeControl.ascx", "ProductID":self.prodid, "DetailPage":True, "dollar":"0", "percentage":"0"}
                            t = self.s.post("https://www.workingclassheroes.co.uk/wsCitrusStore.asmx/GetAttributes", json = payload, headers = headers)
                            
                            resp = t.text

                            self.atcid = resp.split(f'Add2BasketAttributeCtrl({self.prodid},')[1].split(',')[0]
                            
                            self.sku = var.split('"sku_code":"')[1].split('",')[0]
                            self.title = var.split('"name":"')[1].split('",')[0]
                            img = var.split('"image":"')[1].split('",')[0]
                            self.img = f"https://www.workingclassheroes.co.uk/{img}"
                            self.price = var.split('"unit_price":"')[1].split('",')[0]
                            attributes = var.split('attributes":')[1].split(',"facets')[0]


                            r_json = json.loads(attributes)
                            variant = []
                            sizes = []
                            qty = []
                            size_id = []
                            for element in r_json:
                                variant.append(element['attribute_ID'])
                                qty.append(element['qty_in_stock'])
                                size_id.append(element['size_term_ID'])
                                if 'UK' in element['name']:
                                    saiz = element['name'].split('UK ')[1]
                                    sizes.append(saiz)

                            connect = zip(variant, sizes, qty, size_id)
                            self.connect = list(connect)

                            info(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Got {self.title}!')

                            break
                            
                            #self.instock = []
                            #print(self.connect)
                            #for traian in self.connect:
    #
                            #    if traian[2] != "0":
                            #        self.instock.append(traian)
                            #
    #
                            #if len(self.instock) != 0:
    #
                            #    info(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - {self.title} IN STOCK')
    #
                            #    self.sizes_instock = []
    #
                            #    for ele in self.instock:
                            #        self.sizes_instock.append(ele[1])
    #
                            #    if self.size != "RANDOM" and self.size in self.sizes_instock:
    #
                            #        info(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - {self.size} AVAILABLE!')
                            #        break
    #
                            #    else:
                            #        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - {self.sizes_instock} AVAILABLE')
                            #        break
                            #        
    #
                            #else:
    #
                            #    warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - {self.title} OOS, MONITORING')
                            #    time.sleep(self.delay)
                            #    continue


                        except Exception as e:
                            warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Product not live, monitoring...')
                            

                    elif r.status_code == 403:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Proxy banned, rotating...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 400:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Bad request, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code >= 500 or r.status_code <= 599:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Site down, retrying...')
                        time.sleep(self.delay)
                        continue

                    else:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue



                self.atc()

            except Exception as e:
                error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Exception getting product, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.getprod()
        
        except:
            pass

    def atc(self):
        
        try:

            try:
                headers = {
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/json; charset=UTF-8',
                    'origin': 'https://www.workingclassheroes.co.uk',
                    'referer': self.link,
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }
                

                while True:
    #   
                    self.sizerange = []
                    if self.size == "RANDOM":

                        scelto = random.choice(self.connect)
                        self.sizescelta = scelto[1]
                        self.attrscelto = scelto[0]

                    elif '-' in self.size:
                        self.size1 = float(self.size.split('-')[0])
                        self.size2 = float(self.size.split('-')[1])
                        for x in self.connect:
                            if self.size1 <= float(x[1]) <= self.size2:
                                self.sizerange.append(x[1])    
                        self.sizerandom = random.choice(self.sizerange)   
                        for element in self.connect:
                            if self.sizerandom in element[1]:
                                self.sizescelta = element[1]
                                self.attrscelto = element[0]
                        
                    elif ',' in self.size:
                        self.size1 = float(self.size.split(',')[0])
                        self.size2 = float(self.size.split(',')[1])
                        for x in self.connect:
                            if self.size1 <= float(x[1]) <= self.size2:
                                self.sizerange.append(x[1])     
                        self.sizerandom = random.choice(self.sizerange)   
                        for element in self.connect:
                            if self.sizerandom in element[1]:
                                self.sizescelta = element[1]
                                self.attrscelto = element[0]

                    else:
                        for element in self.connect:
                            if self.size in element[1]:
                                self.sizescelta = element[1]
                                self.attrscelto = element[0]

                    
                    warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Adding to cart size {self.sizescelta}...')

                    payload = {"iProductID": self.prodid, "iQuantity": 1, "iAttributeID": self.atcid, "iAttributeDetailID": self.attrscelto}


                    r = self.s.post("https://www.workingclassheroes.co.uk/wsCitrusStore.asmx/AddToBasketJSNew", json = payload, proxies = self.selected_proxies)


                    if r.status_code == 200:

                        if "added to basket" in r.text:

                            info(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Added to cart size {self.sizescelta}!')
                            break

                        else:
                            warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Size {self.sizescelta} OOS, retrying...')
                            time.sleep(self.delay)
                            continue

                    elif r.status_code == 403:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Proxy banned, rotating...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 400:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Bad request, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Rate limit, rotating...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code >= 500 or r.status_code <= 599:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue


                    else:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                self.account()

            except Exception as e:
                error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Exception adding to cart, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.atc()
        except:
            pass

    def account(self):

        try:

            try:

                headers = {
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/json; charset=UTF-8',
                    'origin': 'https://www.workingclassheroes.co.uk',
                    'referer': 'https://www.workingclassheroes.co.uk/ssl/secure/',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Setting user informations...')

                payload = {"emailAddress":self.mail , "firstName":self.name , "lastName":self.surname,"GDPRAllowed": False}


                while True:


                    r = self.s.post("https://www.workingclassheroes.co.uk/wsCitrusStore.asmx/WightCreateAnonymousCustomerLogin", json = payload, proxies = self.selected_proxies)


                    if r.status_code == 200 and 'status\\":true,' in r.text:

                        info(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - User info submitted!')
                        break

                    elif r.status_code == 403:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Proxy banned, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue


                    elif r.status_code == 404:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Page not laoded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 400:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Bad request, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code >= 500 or r.status_code <= 599:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    else:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                self.ship()

    
            except Exception as e:
                error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Exception submitting shipping, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.ship()

        except:
            pass


    def ship(self):

        try:

            try:

                headers = {
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/json; charset=UTF-8',
                    'origin': 'https://www.workingclassheroes.co.uk',
                    'referer': 'https://www.workingclassheroes.co.uk/ssl/secure/',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Submitting shipping...')

                while True:
                    
                    payload = {"firstName":self.name, "lastName":self.surname, "company":"", "address1":self.address, "address2":self.address2, "city":self.city, "postcode":self.zipcode, "country":self.country}



                    r = self.s.post("https://www.workingclassheroes.co.uk/wsCitrusStore.asmx/WightLoadShippingOptions", json = payload, proxies = self.selected_proxies)


                    if r.status_code == 200:

                        info(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Shipping submitted!')


                        self.cookies = r.cookies

                        resp = r.text
                        respo = resp.replace('u0026', '')
                        x = respo.replace('u003e','')
                        m = x.replace('\\u0026quot;','')
                        g = m.replace('quot;','')
                        p = g.replace('u003c','')
                        l = p.replace('\\n','')
                        j = l.replace('\\quot','')
                        b = j.replace('\\r','')
                        v = b.replace('\\u0027','')
                        o = v.replace('\\','')
                        a = o.replace('/div','')
                        c = a.replace('/span','')
                        i = c.replace('/form','')
                        d = i.replace('div','')

                        ll = d.split('collectionWindow:')[1].split(',c')[0]
                        self.to = ll.split('to:')[1].split(',')[0]
                        self.from1 = ll.split('from:')[1].split('}')[0]

                        self.cutoff = d.split('cutOffDateTime:')[1].split(',')[0]
                        
                        xx = d.split('deliveryWindow:')[1].split(',g')[0]
                        self.todel = xx.split('to:')[1].split(',')[0]
                        self.from1del = xx.split('from:')[1].split('}')[0]

                        self.booking = d.split('bookingCode:')[1].split(',')[0]
                        self.servicecode = d.split('carrierServiceCode:')[1].split(',')[0]
                        self.carrier = d.split('carrierCode:')[1].split(',')[0]

                        t = d.replace('ttttttt','')
                        self.packname = t.split('metaPackName"')[1].split(' class')[0]
                        
                        self.charge = t.split('shippingCharge:')[1].split(',')[0]
                        self.cost = t.split('shippingCost:')[1].split('.')[0]

                        self.groupcode = t.split('groupCodes:')[1].split(',')[0]
                        if self.groupcode == 'null':
                            self.groupcode = None
                        self.scor = d.split('score:')[1].split(',')[0]
                        if self.scor == 'null':
                            self.scor = None
                        self.senderTimeZone = d.split('senderTimeZone:')[1].split(',')[0]
                        if self.senderTimeZone == 'null':
                            self.senderTimeZone = None
                        self.taxAndDuty = d.split('taxAndDuty:')[1].split(',')[0]
                        if self.taxAndDuty == 'null':
                            self.taxAndDuty = None
                        self.taxAndDutyStatusText = d.split('taxAndDutyStatusText:')[1].split(',')[0]
                        if self.taxAndDutyStatusText == 'null':
                            self.taxAndDutyStatusText = None
                        self.vatRate = d.split('vatRate:')[1].split('},')[0]
                        if self.vatRate == 'null':
                            self.vatRate = None

                        break

                    elif r.status_code == 403:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Proxy banned, rotating...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 400:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Bad request, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code >= 500 or r.status_code <= 599:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    else:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue
                
                self.ship2()

            except Exception as e:
                error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Exception submitting shipping, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.ship()
        except:
            pass
    
    def ship2(self):
#
#
        try:
            try:

                headers = {
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/json; charset=UTF-8',
                    'origin': 'https://www.workingclassheroes.co.uk',
                    'referer': 'https://www.workingclassheroes.co.uk/ssl/secure/',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Getting shippin rates...')
                time.sleep(3)

                payload = {
                    "firstName": self.name,
                    "lastName": self.surname,
                    "company": "",
                    "address1": self.address,
                    "address2": self.address2,
                    "city": self.city,
                    "postcode": self.zipcode,
                    "phone": self.phone,
                    "country": self.country,
                    "selectedShipping": {
                        "IsPremium": False,
                        "bookingCode": self.booking,
                        "carrierCode": self.carrier,
                        "carrierCustom1": "",
                        "carrierCustom2": "",
                        "carrierCustom3": "",
                        "carrierServiceCode": self.servicecode,
                        "carrierServiceTypeCode": "",
                        "collectionSlots": None,
                        "collectionWindow": {
                            "to": self.to,
                            "from": self.from1
                        },
                        "cutOffDateTime": self.cutoff,
                        "deliverySlots": None,
                        "deliveryWindow": {
                            "to": self.todel,
                            "from": self.from1del
                        },
                        "groupCodes": self.groupcode,
                        "name": self.packname,
                        "nominatableCollectionSlot": False,
                        "nominatableDeliverySlot": False,
                        "recipientTimeZone": None,
                        "score": self.scor,
                        "senderTimeZone": self.senderTimeZone,
                        "shippingCharge": self.charge,
                        "shippingCost": self.cost,
                        "taxAndDuty": self.taxAndDuty,
                        "taxAndDutyStatusText": self.taxAndDutyStatusText,
                        "vatRate": self.vatRate
                    },
                    "nickname": ""
                }

                while True:
                    

                    r = self.s.post("https://www.workingclassheroes.co.uk/wsCitrusStore.asmx/WightPostShippingDetails", proxies = self.selected_proxies, json = payload)



                    if r.status_code == 200:

                        info(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Shipping rates submitted!')
                        break


                    elif r.status_code == 403:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Proxy banned, rotating...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code == 404:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 400:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Bad request, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue

                    elif r.status_code >= 500 or r.status_code <= 599:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Site is down, retrying...')
                        time.sleep(self.delay)
                        continue

                    else:
                        warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue
                
                self.checkout()

            except Exception as e:
                error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Exception submitting rates, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.ship2()
        except:
            pass
                
    def checkout(self):

        try:

            try:

                warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Placing order...')

                headers = {
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/json; charset=UTF-8',
                    'origin': 'https://www.workingclassheroes.co.uk',
                    'referer': 'https://www.workingclassheroes.co.uk/ssl/secure/',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                cardtype = identify_card_type(self.cardnumber)
                if cardtype == "MasterCard":
                    card_type = "MasterCard"
                    cardid = 9
                elif cardtype == "Visa":
                    card_type = "Visa"
                    cardid = 8

                payload = {"MethodType":"Standard","SpecialInstructions":"","PaymentMethod":"credit card","cardTypeUid":cardid,"cardType":card_type,"cardNumber":self.cardnumber,"secureCode":self.cvc,"expMonth":self.expmonth,"expYear":self.expyear,"token":"","selectedShipping":{"IsPremium":False,"bookingCode":"","carrierCode":"","carrierCustom1":"","carrierCustom2":"","carrierCustom3":"","carrierServiceCode":"","carrierServiceTypeCode":"","collectionSlots":None,"collectionWindow":{"to":"2019-08-12T00:00:00","from":"2019-08-12T00:00:00"},"cutOffDateTime":"2019-08-12T00:00:00","deliverySlots":None,"deliveryWindow":{"to":"2019-08-13T00:00:00","from":"2019-08-13T00:00:00"},"groupCodes":None,"name":"","nominatableCollectionSlot":False,"nominatableDeliverySlot":False,"recipientTimeZone":None,"score":0,"senderTimeZone":None,"shippingCharge":0,"shippingCost":0,"taxAndDuty":0,"taxAndDutyStatusText":None,"vatRate":0},"paypalToken":"","payPalPayerID":""}


                t = self.s.post("https://www.workingclassheroes.co.uk/wsCitrusStore.asmx/WightHandlePaymentSelector", proxies = self.selected_proxies, json = payload)

                headers2 = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding' : 'gzip, deflate, br',
                    'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'referer': 'https://www.workingclassheroes.co.uk/ssl/secure/',
                    'sec-fetch-dest' : 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
                }

                r = self.s.get("https://www.workingclassheroes.co.uk/ssl/secure/3DValidation.aspx", proxies = self.selected_proxies,  headers = headers2)


                if r.status_code == 200 and "3D" in r.url:

                    info(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Successfully checked out!')
                    self.urlfinale = r.url

                    self.passcookies()


                elif r.status_code == 403:

                    error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Proxy banned, retrying...')
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    self.checkout()

                elif r.status_code == 404:

                    error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Page not laoded, retrying...')
                    time.sleep(self.delay)
                    self.checkout()

                elif r.status_code == 400:

                    error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Bad request, rotating...')
                    time.sleep(self.delay)
                    self.checkout()

                elif r.status_code == 429:

                    error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Rate limit, rotating...')
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    self.checkout()

                elif r.status_code >= 500 or r.status_code <= 599:
                    warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Site is down, retrying...')
                    time.sleep(self.delay)
                    self.checkout()

                else:
                    warn(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Error {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    self.checkout()


            except Exception as e:
                error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Exception submitting order, retrying...')
                time.sleep(self.delay)
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.checkout()
        except:
            pass

    def passcookies(self):

        try:

            try:

                cookieStr = ""
                cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]  
                for cookie in cookies:
                    if cookie['domain'][0] == ".":
                        cookie['url'] = cookie['domain'][1:]
                    else:
                        cookie['url'] = cookie['domain']
                    cookie['url'] = "https://"+cookie['url'] 


                cookies = json.dumps(cookies)
                cookieStr = urllib.parse.quote(base64.b64encode(bytes(cookies, 'utf-8')).decode())
                if not cookieStr: return
                url = urllib.parse.quote(base64.b64encode(bytes(self.urlfinale, 'utf-8')).decode())
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
                        writer.writerow({'SITE':'WORKINGCLASSHEROES','SIZE':f'{self.sizescelta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                        

                else:
                    self.expToken = self.token
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'WORKINGCLASSHEROES','SIZE':f'{self.sizescelta}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                
                self.SuccessPP()

            except Exception as e: 
                error(f'[TASK {self.threadID}] [WORKINGCLASSHEROES] - Exception passing cookies, retrying...') 
                time.sleep(self.delay)
                self.passcookies()
        except:
            pass

    def SuccessPP(self):
        try:
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - 3D is waiting, click to comlete checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**WORKINGCLASSHEROES**', value = self.title, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = "CreditCard", inline = True) 
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url=self.img)
            embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()

            self.Pubblic_Webhook()
        except:
            pass

    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url =random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**WORKINGCLASSHEROES**', value = self.title, inline = False)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.sizescelta, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = "CreditCard", inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url=self.img)
            embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
                return sys.exit(1)
    #
            except:
                return sys.exit(1)
        except:
            pass