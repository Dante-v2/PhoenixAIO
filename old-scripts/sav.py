import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from helheim import helheim, isChallenge
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from selectolax.parser import HTMLParser

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


checkoutnum = 0
failed = 0
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

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance


class SAV():

    def __init__(self, row, webhook, version, i):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'sneakavenue/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "sneakavenue/proxies.txt")
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
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'anticaptcha','api_key':config['anticaptcha']},doubleDown=False,requestPostHook=self.injection)
            self.providerCap = True
            self.twoCaptcha = config['2captcha']
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha']},doubleDown=False,requestPostHook=self.injection)
            self.providerCap = True
            self.twoCaptcha = config['2captcha']
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)

        self.link = row['LINK']
        self.pid = row['PID']
        self.bsid = row['BSID']
        self.size = row['SIZE']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.mail = row['MAIL']
        self.address = row['ADDRESS']
        self.address2 = row['ADDRESS2']
        self.housenumber = row['HOUSENUMBER']
        self.region = row['REGION']
        self.zip = row['ZIPCODE']
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.city = row['CITY']
        self.webhook_url = webhook
        self.version = version
        self.threadID = '%03d' % i
        self.delay = int(config['delay'])
        self.iscookiesfucked = False
        self.cfchl = False
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]


        self.balance = balancefunc()

        self.bar()  

        if config['timeout-sneakeravenue'] == "":
            self.timeout = 25

        else:
            self.timeout = int(config['timeout-sneakeravenue'])

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


        try:
            self.pid = self.pid
            self.bsid = self.bsid
        except:
            self.pid = ""
            self.bsid = ""

        self.UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'


        if '.de/' in self.link:
            self.host = 'https://www.sneak-a-venue.de'
            self.atc_url = 'https://www.sneak-a-venue.de/warenkorb/hinzugefuegen?'
            self.address_url = 'https://www.sneak-a-venue.de/warenkorb/adresse'
            self.payment_url = 'https://www.sneak-a-venue.de/warenkorb/zahlungsart'
            self.check_url = 'https://www.sneak-a-venue.de/warenkorb/pruefen'
            self.atcStep = 'In den Warenkorb'
            self.atcText = 'In+den+Warenkorb'
            self.addressStep = 'Weiter zu Zahlung'
            self.paymentStep = 'Weiter zur Zusammenfassung'
            self.paypalStep = 'Kostenpflichtig bestellen'
            self.countryno = '1'
            self.headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
                'referer': self.link,
                'x-requested-with':	'XMLHttpRequest',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en-GB;q=0.9,en;q=0.8,it;q=0.7',
            }

        elif '.cz/' in self.link:
            self.host = 'https://www.sneak-a-venue.cz'
            self.atc_url = 'https://www.sneak-a-venue.cz/cart/add?'
            self.address_url = 'https://www.sneak-a-venue.cz/cart/address'
            self.payment_url = 'https://www.sneak-a-venue.cz/cart/paymentmethod'
            self.check_url = 'https://www.sneak-a-venue.cz/cart/last-check'
            self.atcStep = 'Přidat do košíku'
            self.atcText = 'Přidat+do+košíku'
            self.addressStep = 'Pokračovat k platbě'
            self.paymentStep = 'Pokračovat'
            self.paypalStep = 'Koupit'
            self.countryno = '1'
            self.headers = {
                'user-agent': self.UA,
                'host': 'www.sneak-a-venue.cz',
                'referer': 'https:/www.sneak-a-venue.cz/',
                'x-requested-with':	'XMLHttpRequest',
                'cache-control':'max-age=0',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }

        else:
            self.host = 'https://www.sneak-a-venue.com'
            self.atc_url = 'https://www.sneak-a-venue.com/cart/add?'
            self.address_url = 'https://www.sneak-a-venue.com/cart/address'
            self.payment_url = 'https://www.sneak-a-venue.com/cart/paymentmethod'
            self.check_url = 'https://www.sneak-a-venue.com/cart/last-check'
            self.atcStep = 'Add to cart'
            self.atcText = 'Add+to+cart'
            self.addressStep = 'Continue to payment'
            self.paymentStep = 'Continue to summary'
            self.paypalStep = 'Buy now'
            self.headers = {
                'user-agent': self.UA,
                'host': 'www.sneak-a-venue.com',
                'referer': 'https:/www.sneak-a-venue.com/',
                'x-requested-with':	'XMLHttpRequest',
                'cache-control':'max-age=0',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }


        if self.country == "DE":
                self.countryno = 1
        if self.country == "UK":
                self.countryno = 6
        if self.country == "NL":
                self.countryno = 9
        if self.country == "HR":
                self.countryno = 20
        if self.country == "DK":
                self.countryno = 24
        if self.country == "EE":
                self.countryno = 68
        if self.country == "BE":
                self.countryno = 5
        if self.country == "AT":
                self.countryno = 22
        if self.country == "FI":
                self.countryno = 19
        if self.country == "FR":
                self.countryno = 1
        if self.country == "GR":
                self.countryno = 12
        if self.country == "HU":
                self.countryno = 20
        if self.country == "IE":
                self.countryno = 13
        if self.country == "IL":
                self.countryno = 67
        if self.country == "IT":
                self.countryno = 2
        if self.country == "HK":
                self.countryno = 42
        if self.country == "LV":
                self.countryno = 63
        if self.country == "LI":
                self.countryno = 49
        if self.country == "LT":
                self.countryno = 56
        if self.country == "LU":
                self.countryno = 15
        if self.country == "SE":
                self.countryno = 18
        if self.country == "ES":
                self.countryno = 11
        if self.country == "CH":
                self.countryno = 1
        if self.country == "PL":
                self.countryno = 10
        if self.country == "SI":
                self.countryno = 8
        if self.country == "UA":
                self.countryno = 70
        if self.country == "NO":
                self.countryno = 17


        if '?' in self.link:
            
            self.link = self.link.split('?',1)[0]

        if '#' in self.link:
            self.link = self.link.split('#',1)[0]


        countries = ['/fr', '/sk', '/sl', '/hr', '/nl', '/it']

        for country in countries:
            if country in self.link:

                self.link = self.link.replace(country, '')

            if '?' in self.link:
                self.link = self.link('?',1)[0]

            else:
                pass

        
        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Starting task...')
        self.connection()


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
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running SNEAKAVENUE | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running SNEAKAVENUE | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')

    def injection(self, session, response):

        self.balance = balancefunc()
        self.bar()

        try:
            if session.is_New_IUAM_Challenge(response) \
            or session.is_New_Captcha_Challenge(response) \
            or session.is_BFM_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Solving Cloudflare v2 api 2')
                return helheim('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693', session, response)
            else:
                return response

        except:
            if session.is_New_IUAM_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Solving Cloudflare v2')
                return CF_2(session,response,key="a6077c8d-a15f-4293-93b7-c854d3a2a3e6",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Solving Cloudflare v2')
                return CF_2(session,response,key="a6077c8d-a15f-4293-93b7-c854d3a2a3e6",captcha=True,debug=False).solve() 
            else:
                return response



    def connection(self):

        try:
            self.mom = False


            try:

                proxyGet = self.s.get(self.host, proxies = self.selected_proxies, timeout = 15)



                if proxyGet.status_code == 200 or proxyGet.status_code == 503:

                    info(f'[TASK {self.threadID}] [SNEAKAVENUE] - Connected to SAV!')

                    if self.bsid == '' or self.pid == '':
                        self.getproduct()
                        

                    else:

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Pid and Bsid given, proceding...')

                        self.pid = self.pid
                        self.bsId = self.bsid
                        self.img = "https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcQSIpx14joZrN-z0sj3GMwa62-Rbimrkw1Cfg&usqp=CAU"
                        self.atc()
                        

                if proxyGet.status_code == 403:
                    

                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Proxy banned, rotating...')

                        self.connection()

                    else:

                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Local ip banned, use proxies!')
                        sys.exit(1)

                else:
                    
                    warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Error {proxyGet.status_code}, retrying...')

                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies

                    time.sleep(self.delay)

                    self.connection()


            

            except Exception as e:

                error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Exception during connection, retrying...')
                if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                time.sleep(self.delay)

                self.connection()
        except:
            pass

    def getproduct(self):

        try:

            try:
                
                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Getting product...')

                while True:

                    if self.mom:
                        prod = self.s.get(self.link, proxies=self.selected_proxies, timeout = self.timeout)
                    else:
                        prod = self.s.get(self.link, headers = self.headers, proxies=self.selected_proxies, timeout = self.timeout)


                    if "Please complete the security check" in prod.text or 'solve the security check' in prod.text:

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Catpcha found!')


                        for node in HTMLParser(prod.text).css("script"):
                            if "/cdn-cgi/scripts/cf.challenge.js" == node.attributes.get('src'):
                                datara = node.attributes.get('data-ray')
                                break

                        for node in HTMLParser(prod.text).css("input"):
                            if "s" == node.attributes.get('name'):
                                s = node.attributes.get('value')
                                break


                        host = self.host.replace('https://www.', '') 
                        solver = TwoCaptcha(config['2captcha'])
                        captcha = solver.recaptcha(url=self.link, sitekey="6LfBixYUAAAAABhdHynFUIMA_sa4s-XsJvnjtgB0")
                        params = (('s', s),('id', datara),('g-recaptcha-response', captcha))
                        prod = self.s.get(f'https://{host}/cdn-cgi/l/chk_captcha', headers=self.headers, proxies = self.selected_proxies, params=params)

                        if prod.status_code == 200:
                            pass

                    elif 'ERROR 404' in prod.text:

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Page not loaded...')
                        time.sleep(self.delay)
                        
                        continue

                    elif prod.status_code == 503:

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Site dead, retrying...')
                        time.sleep(self.delay)
                        
                        continue


                    elif prod.status_code == 429:

                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)

                        continue


                    elif prod.status_code == 403:

                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)

                        continue

                    elif prod.status_code == 200:

                        pass


                    
                    sizeRow = self.size
                    oneSize = False

                    if sizeRow.upper() == 'RANDOM':
                        sizeRow = "1,50"
                        

                    if sizeRow == '' or sizeRow == 'OS':
                        
                        oneSize = True

                    if ',' in sizeRow:
                        sizeRange = sizeRow.replace(" ", '').split(',')

                    else:
                        self.size = sizeRow.replace(" ", '')
                        
                        sizeRange = []
                        sizeRange.append(self.size)
                        sizeRange.append(self.size)

                    if oneSize == False:
                        sizeRange = [float(i) for i in sizeRange]

                    

                    try:

                        
                        prod_xml = bs(prod.text, features='lxml')

                        

                        self.prodName = prod_xml.find("span",{"class":"productname"}).text

                        
                        img_raw = prod_xml.select_one('a.demo-gallery__img--main img[src]')['src']
                        img_final = '{}{}'.format(self.host, img_raw)

                        
                    

                        if oneSize == False:

                            valuesList = []
                            sizeList = []
                            rangedSizes = []
                            divList2 = prod_xml.find('div', attrs = {'class': 'selectVariants clear'})

                            for option in divList2:
                                divList = divList2.findAll('option', {'class': ''})
                            divList.pop(0)

                            for div in divList:
                                sizes = div.text.strip()
                                sizes = re.sub(r'.*-.\w+' , '', sizes, flags=re.I)
                                sizes = sizes.replace(',','.').strip()
                                sizes = sizes.split('· ',1)[1].split(' US',1)[0]
                                sizes = sizes.split('(')[0]
                                sizes = sizes.replace('US','').strip()

                                if 'Y' in sizes:
                                    sizes = sizes.replace('Y', '')

                                sizes = float(sizes)
                                sizeList.append(sizes)

                                if sizeRange[0] <= sizes <= sizeRange[1]:
                                    rangedSizes.append(sizes)
                                    values = div.get('value')
                                    valuesList.append(values)

                            if valuesList == []:

                                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - No available sizes found, retrying...')
                                time.sleep(self.delay)
                                continue

                            else:
                                sizeValue = random.choice(valuesList)
                                product_data = {
                                    'chosen_attribute_value': sizeValue,
                                    'returnHtmlSnippets[partials][0][module]': 'product',
                                    'returnHtmlSnippets[partials][0][path]': '_productDetail',
                                    'returnHtmlSnippets[partials][0][partialName]': 'buybox'
                                }

                                if self.mom:
                                    prodPost = self.s.post(self.link, data = product_data, proxies=self.selected_proxies, timeout = self.timeout)
                                else:
                                    prodPost = self.s.post(self.link, data = product_data, headers = self.headers, proxies=self.selected_proxies, timeout = self.timeout)


                                while prodPost.status_code != 200:

                                    error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Failed getting size info, retrying...')
                                    time.sleep(self.delay)
                                    product_data = {
                                        'chosen_attribute_value': random.choice(valuesList),
                                        'returnHtmlSnippets[partials][0][module]': 'product',
                                        'returnHtmlSnippets[partials][0][path]': '_productDetail',
                                        'returnHtmlSnippets[partials][0][partialName]': 'buybox'
                                    }
                                    if self.mom:
                                        prodPost = self.s.post(self.link, data = product_data, proxies=self.selected_proxies, timeout = self.timeout)
                                    else:
                                        prodPost = self.s.post(self.link, data = product_data, headers = self.headers, proxies=self.selected_proxies, timeout = self.timeout)

                                resp_xml = bs(prodPost.text, features='lxml')
                                pid = re.findall('"id":\w+', resp_xml.text, flags=re.I)[:1]
                                bsId = re.findall('"bsid":\w+', resp_xml.text, flags=re.I)[:1]
                                self.pid = str(pid[0]).replace('"id":','')
                                self.bsId = str(bsId[0]).replace('"bsId":','')
                                self.img = img_final

                                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Got Pid and Bsid, proceding...')

                                break


                        if oneSize == True:
                            self.pid = prod_xml.find('input', {'name': 'product_id'})['value']
                            self.bsId = prod_xml.find('input', {'name': 'product_bs_id'})['value']



                    except:
                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Exception while scraping, retrying...')
                        if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                self.atc()



            except Exception as e:

                error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Exception while scraping, retrying...')
                if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                time.sleep(self.delay)

                self.getproduct()

        except:
            pass


    def atc(self):

        try:

            global carted, checkoutnum, failed

            try:
                

                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Adding to cart...')
                atc_data = {
                    'product_id': self.pid,
                    'product_bsid': self.bsId,
                    'amount': '1',
                    'ajax': 'true',
                    'addToCart': self.atcStep,
                    'forward[module]': 'cart',
                    'forward[action]': 'wasadded'
                }

                cart_url = self.atc_url + 'product_bs_id={0}&product_id={1}&amount=1&addToCart={2}&ajax=true'.format(self.bsId, self.pid, self.atcText)

                while True:
                    
                    if self.mom:
                        cartPost = self.s.post(cart_url, data = atc_data, proxies = self.selected_proxies, allow_redirects=False)
                    else:
                        cartPost = self.s.post(cart_url, data = atc_data, headers = self.headers, proxies = self.selected_proxies, allow_redirects=False)

                    try:
                        self.prodName = str(cartPost.text).split('<p>',1)[1].split(' <span',1)[0]

                    except:
                        self.prod_name = 'Product'


                    if cartPost.status_code == 503 or cartPost.status_code == 500:

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Site is overcrowded, retrying...')

                        time.sleep(self.delay)

                        continue


                    if 'not available' in cartPost.text:

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Product OOS, retrying...')
                        time.sleep(self.delay)
                        continue
                    
                    if 'nicht' in cartPost.text:
                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Product OOS, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif '1x' in cartPost.text:
                        xml = bs(cartPost.text,  features='lxml')
                        self.cartSize = str(xml.find('p').getText()).split('·',1)[1].split('(',1)[0]
                        
                        info(f'[TASK {self.threadID}] [SNEAKAVENUE] - Added to cart size {self.cartSize}')
                        carted = carted + 1
                        self.bar()
                        break

                    elif cartPost.status_code == 403:

                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)

                        continue
                

                self.shipping()

            except Exception as e:

                error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Exception while adding to cart, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)

                self.atc()
        except:
            pass           

    def shipping(self):

        try:

            try:

                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Submitting shipping...')

                guest_data = {
                        'billAddressId': '-1',
                        'guestdata[email]': self.mail,
                        'guestdata[email_repeat]': self.mail,
                        'billaddress[salutation]': '1',
                        'billaddress[forename]': self.name,
                        'billaddress[lastname]': self.surname,
                        'billaddress[street]': self.address,
                        'billaddress[street_number]': self.housenumber,
                        'billaddress[addition]': self.address2,
                        'billaddress[zipcode]': self.zip,
                        'billaddress[city]': self.city,
                        'billaddress[country]': self.countryno,
                        'billaddress[phone]': self.phone,
                        'guestdata[date_of_birth]': '',
                        'shippingaddress[use_shipping_address]': '0',
                        'shippingAddressId': '-1',
                        'shippingaddress[salutation]': '1',
                        'shippingaddress[forename]': self.name,
                        'shippingaddress[lastname]': self.surname,
                        'shippingaddress[street]': self.address,
                        'shippingaddress[street_number]': self.housenumber,
                        'shippingaddress[addition]': self.address2,
                        'shippingaddress[zipcode]': self.zip,
                        'shippingaddress[city]': self.zip,
                        'shippingaddress[country]': self.countryno,
                        'registerguest[password]': '',
                        'registerguest[password_repeat]': '',
                        'back_x_value': '@cart',
                        'next_x': self.addressStep,
                        'next_x_value': '@cart_payment'
                    }

                while True:
                    
                    if self.mom:
                        addressPost = self.s.post(self.address_url, data = guest_data, proxies = self.selected_proxies, timeout = self.timeout)
                    else:
                        addressPost = self.s.post(self.address_url, data = guest_data, headers = self.headers, proxies = self.selected_proxies, timeout = self.timeout)


                    if addressPost.status_code == 403:
                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Proxy banned, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)

                        continue

                    if addressPost.status_code == 503:

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Site is overcrowded, retrying...')

                        time.sleep(self.delay)

                        continue
                    
                    if addressPost.status_code == 200 and addressPost.url.split('/')[-1] != 'cart':
                        info(f'[TASK {self.threadID}] [SNEAKAVENUE] - Shipping submitted, retrying...')
                        self.payment_xml = bs(addressPost.text, features='lxml')
                        break

                    elif addressPost.url.split('/')[-1] == 'cart':
                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - OOS on shipping, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        self.connection()

                    else:
                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Error {addressPost.status_code}, retrying...')
                        time.sleep(self.delay)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue


                self.pagamento()


            except Exception as e:

                error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Exception while submitting shipping, retrying...')

                time.sleep(self.delay)

                self.shipping()   

        except:
            pass

    def pagamento(self):

        try:
            try:

                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Submitting payment...')

                while True:
                    
                    shipping_method = self.payment_xml.find('input', {'name': 'shipping_method_id'})['value']

                    if '.cz' in self.host:
                        payment_data = {
                            'payment_method_id': '7',
                            'shipping_method_id': shipping_method,
                            'back_x_value': '@cart_address',
                            'next_x': self.paymentStep,
                            'next_x_value': '@cart_check'
                        }

                    else:
                        payment_data = {
                            'payment_method_id': '5',
                            'shipping_method_id': shipping_method,
                            'back_x_value': '@cart_address',
                            'next_x': self.paymentStep,
                            'next_x_value': '@cart_check'
                        }

                    if self.mom:
                        paymentPost = self.s.post(self.payment_url, data = payment_data, proxies = self.selected_proxies, timeout = 15)
                    else:
                        paymentPost = self.s.post(self.payment_url, data = payment_data, headers = self.headers, proxies = self.selected_proxies, timeout = 15)


                    if 'payment' in paymentPost.url:

                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Error submitting payment, retrying...')
                        time.sleep(self.delay)
                        continue

                    if paymentPost.status_code == 503 or paymentPost.status_code == 500:

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Site is overcrowded...')
                        time.sleep(self.delay)
                        continue

                    if paymentPost.status_code == 200:

                        info(f'[TASK {self.threadID}] [SNEAKAVENUE] - Payment sumbmitted!')
                        break
                    
                    else:

                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Error {paymentPost.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                            time.sleep(self.delay)
                        continue
                
                self.checkfinale()

            except Exception as e:

                error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Exception submitting payment, retrying...')
                time.sleep(self.delay)
                self.pagamento()

        except:
            pass

    def checkfinale(self):

        try:

            global checkoutnum, failed, carted

            try:

                warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Checking out...')

                check_data = {
                    'next_x': self.paypalStep,
                    'next_x_value': '@order_finished'
                }

                cookies = self.s.cookies

                while True:

                    if self.mom:
                        checkPost = self.s.post(self.check_url, data = check_data, proxies = self.selected_proxies, timeout = 50, allow_redirects = False)
                    else:
                        checkPost = self.s.post(self.check_url, data = check_data, headers = self.headers, proxies = self.selected_proxies, timeout = 50, allow_redirects = False)

                    if checkPost.status_code == 503 or checkPost.status_code == 500:

                        url = checkPost.url

                        warn(f'[TASK {self.threadID}] [SNEAKAVENUE] - Site is overcrowded, retrying...')
                        time.sleep(self.delay)

                        while checkPost.status_code == 503 or checkPost.status_code == 500:

                            checkPost = self.s.get(url, proxies = self.selected_proxies, timeout = 50)


                            

                    if checkPost.status_code == 302:

                        info(f'[TASK {self.threadID}] [SNEAKAVENUE] - Successfully checked out!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        ciao = checkPost.headers
                        self.pp_url = ciao['location']
                        break

                    else:
                        error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Error {checkPost.status_code}, retrying...')
                        failed = failed + 1
                        self.bar()
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        self.s.cookies.clear()

                        time.sleep(self.delay)
                        self.getproduct()


                self.passcookies()

            except Exception as e:

                error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Excpetion while palcing order, retrying...')
                failed = failed + 1
                self.bar()

                time.sleep(self.delay)

                self.checkfinale()

        except:
            pass

    def passcookies(self):

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
                        writer.writerow({'SITE':'SNEAKAVENUE','SIZE':f'{self.cartSize}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})
                        

                else:
                    self.expToken = self.token
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'SNEAKAVENUE','SIZE':f'{self.cartSize}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})
                
                self.SuccessPP()

            except Exception as e: 
                error(f'[TASK {self.threadID}] [SNEAKAVENUE] - Exception while passing cookies, retrying...') 
                time.sleep(self.delay)
                self.passcookies()

        except:
            pass

    def SuccessPP(self):
        try:
            if self.selected_proxies == None:
                self.proxi = 'LOCAL'
            self.prodName = self.prodName.split("item ")[1]
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**SNEAKAVENUE**', value = self.prodName, inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.cartSize, inline = True)
            embed.add_embed_field(name='**PID**', value = self.pid, inline = True)
            embed.add_embed_field(name='**BSID**', value = self.bsId, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = "Paypal", inline = True) 
            embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
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
            embed.add_embed_field(name=f'**SNEAKAVENUE**', value = self.prodName, inline = False)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
            embed.add_embed_field(name='**SIZE**', value = self.cartSize, inline = True)
            embed.add_embed_field(name='**PID**', value = self.pid, inline = True)
            embed.add_embed_field(name='**BSID**', value = self.bsId, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = "Paypal", inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.set_thumbnail(url=self.img)
            embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
                return sys.exit(1)

            except:
                return sys.exit(1)
        except:
            pass