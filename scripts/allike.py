import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from mods.errorHandler import errorHandler
import traceback
import helheim

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

HANDLER = errorHandler(__file__)

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None


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


class ALLIKE():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'Allike/exceptions.log')
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'Allike/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "Allike/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()

        except:
            error("Failed reading proxies, running localhost")
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
            time.sleep(5)
            sys.exit(1)

        self.s = cloudscraper.create_scraper(
            browser= {
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
            },
            captcha=self.captcha,
            requestPostHook=self.injection
        )

        

        self.name = row['FIRST NAME']
        self.surname = row['LAST NAME']
        self.mail = row['EMAIL']
        self.address = row['ADDRESS LINE 1']
        self.city = row['CITY']
        self.zip = row['ZIP']
        self.region = row['REGION']
        self.country = row['COUNTRY']
        self.phone = row['PHONE NUMBER']
        self.link = row['LINK']
        self.size = row['SIZE']
        self.payment = row['PAYMENT']
        self.cardnumber = row['CARD NUMBER']
        self.expmonth = row['EXP MONTH']
        self.expyear = row['EXP YEAR']
        self.cvc = row['CVC']

        self.discord = DISCORD_ID

        self.delay = int(config['delay'])
        self.timeout = 120

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
            error(e)


        try:
            if len(self.expyear) == 2:
                self.expyear = "20{}".format(self.expyear)
        except:
            pass

        self.webhook_url = webhook
        self.version = version
        self.threadID = '%03d' % i
        self.build_proxy()
        self.balance = balancefunc()

        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        if self.country == 'US':

            if self.region == 'Alabama':
                self.region = '1'
            if self.region == 'Alaska':
                self.region = '2'
            if self.region == 'American Samoa':
                self.region = '3'
            if self.region == 'Arizona':
                self.region = '4'
            if self.region == 'Arkansas':
                self.region = '5'
            if self.region == 'Armed Forces Africa':
                self.region = '6'
            if self.region == 'Armed Forces Americas':
                self.region = '7'
            if self.region == 'Armed Forces Canada':
                self.region = '8'
            if self.region == 'Armed Forces Europe':
                self.region = '9'
            if self.region == 'Armed Forces Middle East':
                self.region = '10'
            if self.region == 'Armed Forces Pacific':
                self.region = '11'
            if self.region == 'California':
                self.region = '12'
            if self.region == 'Colorado':
                self.region = '13'
            if self.region == 'Connecticut':
                self.region = '14'
            if self.region == 'Delaware':
                self.region = '15'
            if self.region == 'District of Columbia':
                self.region = '16'
            if self.region == 'Federated States Of Micronesia':
                self.region = '17'
            if self.region == 'Florida':
                self.region = '18'
            if self.region == 'Georgia':
                self.region = '19'
            if self.region == 'Guam':
                self.region = '20'
            if self.region == 'Hawaii':
                self.region = '21'
            if self.region == 'Idaho':
                self.region = '22'
            if self.region == 'Illinois':
                self.region = '23'
            if self.region == 'Indiana':
                self.region = '24'
            if self.region == 'Iowa':
                self.region = '25'
            if self.region == 'Kansas':
                self.region = '26'
            if self.region == 'Kentucky':
                self.region = '27'
            if self.region == 'Louisiana':
                self.region = '28'
            if self.region == 'Maine':
                self.region = '29'
            if self.region == 'Marshall Islands':
                self.region = '30'
            if self.region == 'Maryland':
                self.region = '31'
            if self.region == 'Massachusetts':
                self.region = '32'
            if self.region == 'Michigan':
                self.region = '33'
            if self.region == 'Minnesota':
                self.region = '34'
            if self.region == 'Mississippi':
                self.region = '35'
            if self.region == 'Missouri':
                self.region = '36'
            if self.region == 'Montana':
                self.region = '37'
            if self.region == 'Nebraska':
                self.region = '38'
            if self.region == 'Nevada':
                self.region = '39'
            if self.region == 'New Hampshire':
                self.region = '40'
            if self.region == 'New Jersey':
                self.region = '41'
            if self.region == 'New Mexico':
                self.region = '42'
            if self.region == 'New York':
                self.region = '43'
            if self.region == 'North Carolina':
                self.region = '44'
            if self.region == 'North Dakota':
                self.region = '45'
            if self.region == 'Northern Mariana Islands':
                self.region = '46'
            if self.region == 'Ohio':
                self.region = '47'
            if self.region == 'Oklahoma':
                self.region = '48'
            if self.region == 'Oregon':
                self.region = '49'
            if self.region == 'Palau':
                self.region = '50'
            if self.region == 'Pennsylvania':
                self.region = '51'
            if self.region == 'Puerto Rico':
                self.region = '52'
            if self.region == 'Rhode Island':
                self.region = '53'
            if self.region == 'South Carolina':
                self.region = '54'
            if self.region == 'South Dakota':
                self.region = '55'
            if self.region == 'Tennessee':
                self.region = '56'
            if self.region == 'Texas':
                self.region = '57'
            if self.region == 'Utah':
                self.region = '58'
            if self.region == 'Vermont':
                self.region = '59'
            if self.region == 'Virgin Islands':
                self.region = '60'
            if self.region == 'Virginia':
                self.region = '61'
            if self.region == 'Washington':
                self.region = '62'
            if self.region == 'West Virginia':
                self.region = '63'
            if self.region == 'Wisconsin':
                self.region = '64'
            if self.region == 'Wyoming':
                self.region = '65'


        if self.payment == "PP/CC":
            error(f'[TASK {self.threadID}] [ALLIKE] - PLEASE CHECK CSV PAYMENT MODE (PP OR CC)')
            sys.exit(1)

        self.bar()

        self.warn('Task started!')
        self.scraperPid()

    # Red logging

    def error(self, text):
        if 'exception' in text.lower():
            HANDLER.log_exception(traceback.format_exc())
        message = f'[TASK {self.threadID}] - [ALLIKE] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [ALLIKE] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [ALLIKE] - {text}'
        warn(message)

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
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running ALLIKE | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running ALLIKE | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')


    def injection(self, session, response):
        #self.bar()
        #try:
        if helheim.isChallenge(session, response):
            self.warn('Solving Cloudflare v2')
            return helheim.solve(session, response)
        else:
            return response
        #except:
        #    if session.is_New_IUAM_Challenge(response):
        #        self.warn('Solving Cloudflare v2 api 2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
        #    elif session.is_New_Captcha_Challenge(response):
        #        self.warn('Solving Cloudflare v2 api 2')
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
        #    else:
        #        return response

    def solve_v3(self, url):
        try:
            solver = TwoCaptcha(config['2captcha'])
            result = solver.recaptcha(sitekey='6LfMDQEaAAAAAK2OeOZtpVHc4gTPjAdZ8kHcXHCR', url=url, version='v3')
            code = result['code']
            return code
        except Exception as e:
            self.error(f'Exception solving captcha: {e.__class__.__name__}')
            open(self.logs_path, 'a+').write(f'Exception solving captcha: {e}\n')
            return self.solve_v3(url)

    def scraperPid(self):
        self.warn('Getting product page...')
        while True:
            try:
                r = self.s.get(
                    self.link,
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    if "var spConfig" not in r.text:
                        self.warn('Product OOS, retrying...')
                        time.sleep(self.delay)
                        continue
                    else:
                        self.success('Parsing product')
                        soup = bs(r.text, "lxml")
                        formkeyurl = soup.find('form', {'id': 'product_addtocart_form'})['action']
                        image = soup.find("meta",  property="og:image")
                        if image["content"] != None:
                            self.image = image["content"]
                        else:
                            self.image = None
                        self.form_key = str(formkeyurl).split('/form_key/')[1].replace('/', '')
                        self.pid = soup.find('input', {'name': 'product'})['value']
                        self.product_page = r.text
                        break
                elif r.status_code == 404:
                    self.warn('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error getting product: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting product: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue

        self.sizegetter()

    def sizegetter(self):
        try:
            self.warn('Getting sizes...')
            try:
                aec = self.product_page.split('AEC.SUPER = [')[1].split(']')[0]
                r_js = json.loads(aec)
                self.superattribute = r_js['id']
            except:
                self.superattribute = '502'
            
            j = self.product_page.split('var spConfig = new Product.Config(')[1].split(')')[0]
            sizejson = json.loads(j)

            attribute = sizejson['attributes'][self.superattribute]

            idvar = []
            sizes = []

            for i in attribute['options']:
                idvar.append(i['id'])
                sizes.append(i['label'])

            tot = zip(idvar, sizes)
            connect = list(tot)

            self.sizerange = []

            if self.size == "RANDOM":
                scelta = random.choice(connect)
                ciao3 = scelta[0]
                self.AttributeValue = "".join(ciao3)
                ciao2 = scelta[1]
                self.sizeweb = "".join(ciao2)
                self.warn(f'Adding to cart size {self.sizeweb}')

            elif '-' in self.size:
                self.size1 = str(self.size.split('-')[0])
                self.size2 = str(self.size.split('-')[1])
                for x in connect:
                    if self.size1 <= str(x[1]) <= self.size2:
                        self.sizerange.append(x[1])     
                self.sizerandom = random.choice(self.sizerange)  
                for t in connect:
                    if self.sizerandom in t:
                        ciao3 = t[0]
                        self.AttributeValue = "".join(ciao3)
                        ciao = t[1]
                        self.sizeweb = "".join(ciao)
                self.warn(f'Adding to cart size {self.sizeweb}')
    
            elif ',' in self.size:
                self.size1 = str(self.size.split(',')[0])
                self.size2 = str(self.size.split(',')[1])
                for x in connect:
                    if self.size1 <= str(x[1]) <= self.size2:
                        self.sizerange.append(x[1])     
                self.sizerandom = random.choice(self.sizerange)   
                for t in connect:
                    if self.sizerandom in t:
                        ciao3 = t[0]
                        self.AttributeValue = "".join(ciao3)
                        ciao = t[1]
                        self.sizeweb = "".join(ciao)   
                self.warn(f'Adding to cart size {self.sizeweb}')

            else:
                for t in connect:
                    if self.size not in sizes:
                        self.warn('No selected sizes available, monitoring...')
                        return self.scraperPid()
                    elif self.size in t:
                        ciao3 = t[0]
                        self.AttributeValue = "".join(ciao3)
                        ciao = t[1]
                        self.sizeweb = "".join(ciao)
                self.warn(f'Adding to cart size {self.sizeweb}')

            if "new AwCountdown" in self.product_page:
                self.timeleft = str(self.product_page).split("'DHMS','")[1].split("','aw")[0]
                self.warn(f'Timer found: {self.timeleft}, waiting for timer...')
                time.sleep(int(self.timeleft)-15)

        except Exception as e:
            self.error(f'Exception while getting sizes {e.__class__.__name__}, retrying...')
            open(self.logs_path, 'a+').write(f'Exception getting sizes: {e}\n')
            return self.scraperPid()
        else:
            return self.ATC()

    def ATC(self):

        global carted, failed, checkoutnum
        data = {
            "isAjax": 1,
            "form_key": self.form_key,
            f"super_attribute[{self.superattribute}]": self.AttributeValue,
            "parent_id": self.pid,
            "product_id":"",
            "related_product":"",
            "email_notification":"",
        }

        headers = {
            'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'referer': self.link
        }

        encoded = (base64.b64encode(self.link.encode('utf-8'))).decode()
        encoded = encoded.replace("=", ",")

        carting_URL = f'https://www.allikestore.com/default/oxajax/cart/add/uenc/{encoded}/product/{self.pid}/form_key/{self.form_key}/?callback=jQuery111004426187163784743_{int(time.time() * 1000)}'

        while True:
            try:
                r = self.s.post(
                    carting_URL, 
                    data = data,
                    headers = headers,
                    timeout = self.timeout, 
                    allow_redirects = False
                )

                if '"status":"SUCCESS"' in r.text:
                    resp1 = r.text.replace('\\n', '').replace("\\t",'')
                    resp = resp1.replace('\\','')
                    data = bs(resp, 'lxml')
                    try:
                        self.prodName = data.find('p', {'class': 'product-name'}).text
                    except:
                        self.prodName = "Product"
                    try:
                        self.addedSize = data.find('dl', {'class':'item-options'}).find('dd').text.strip()
                    except:
                        self.addedSize = self.size

                    self.success('Successfully added to cart!')
                    carted = carted + 1
                    self.bar()
                    err = False
                    break

                elif 'This product is currently out of stock' in r.text:
                    self.warn('Product OOS while adding to cart')
                    err = True
                    break
                    
                elif r.status_code == 403:
                    self.error('Access denied, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn(f'Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    self.error(f'Error adding to cart: {r.status_code} retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception adding to cart: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception adding to cart: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue

        if not err:
            if self.payment == "CC":
                self.checkoutpa()
            else:
                self.fetchPaypal()
        else:
            self.scraperPid()

    def fetchPaypal(self):
        global carted, failed, checkoutnum

        headers = {
            'Referer': 'https://www.allikestore.com/default/checkout/cart/'
        }

        self.warn('Getting PayPal link...')

        while True:
            try:
                r = self.s.get(
                    "https://www.allikestore.com/default/paypal/express/start/button/1/", 
                    headers=headers,
                    timeout=self.timeout, 
                    allow_redirects = False
                )

                if r.status_code == 302:
                    try:
                        pp_url = r.headers["Location"]
                    except:
                        pp_url = None

                    if not pp_url or 'paypal' not in pp_url:
                        self.error('Product OOS while checking out')
                        self.s.cookies.clear()
                        self.build_proxy()
                        oos = True
                        break
                    else:
                        self.paypalTok = pp_url
                        self.t1 = time.time()
                        self.success('PayPal link fetched!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
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
                        url = urllib.parse.quote(base64.b64encode(bytes(self.paypalTok, 'utf-8')).decode())
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
                                writer.writerow({'SITE':'ALLIKE','SIZE':f'{self.sizeweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})


                        else:
                            self.expToken = self.token
                            with open(path,'a',newline='') as f:
                                fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writerow({'SITE':'ALLIKE','SIZE':f'{self.sizeweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})
                        oos = False
                        break

                elif r.status_code == 403:
                    self.error(f'Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    self.fetchPaypal()

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error fetching PayPal link: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception fetching PayPal link: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception fetching PayPal: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue

        if oos:
            self.scraperPid()
        else:
            self.webhook()
        
    def checkoutpa(self):

        self.warn('Getting checkout page...')

        while True:
            try:
                r = self.s.get(
                    "https://www.allikestore.com/default/checkout/onepage/", 
                    timeout=self.timeout
                )

                if r.status_code == 200:
                    self.success('Successfully got checkout page!')
                    try:
                        soup = bs(r.text, 'lxml')
                        self.form_key = soup.find('input', {'name': 'form_key'})['value']
                    except:
                        pass
                    break

                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue

                elif r.status_code == 429:
                    self.error(f'Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error getting checkout page: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting checkout page: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting checkout: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        self.guest()

    def guest(self):

        self.warn('Submitting guest checkout...')

        headers = {
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.allikestore.com/default/checkout/onepage/'
        }

        data = {"method": "guest"}

        while True:
            try:
                r = self.s.post(
                    "https://www.allikestore.com/default/checkout/onepage/saveMethod/", 
                    data=data,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=False
                )

                if r.status_code == 200:
                    try:
                        rj = r.json()
                        if type(rj) == list and len(rj) == 0:
                            self.success('Successfully submitted guest!')
                            err = False
                            break
                        else:
                            self.error(f'Something went wrong while submitting guest, retrying...')
                            time.sleep(self.delay)
                            continue
                    except:
                        self.error(f'Something went wrong while submitting guest, retrying...')
                        time.sleep(self.delay)
                        continue

                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn(f'Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    error(f'Error submitting guest: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception submitting guest: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting guest: {e}\n')
                open('allike/')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if not err:
            self.ship()
        else:
            self.checkoutpa()

    def ship(self):

        self.warn(f'Getting shipping rates...')

        headers = {
            'accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'x-requested-with': 'XMLHttpRequest',
            'referer': 'https://www.allikestore.com/default/checkout/onepage/'
        }

        payload = {
            'billing[address_id]':'',
            'billing[firstname]':self.name,
            'billing[lastname]':self.surname,
            'billing[company]':'',
            'billing[email]':self.mail,
            'billing[street][]':self.address,
            'billing[city]':self.city,
            'billing[region_id]':self.region,
            'billing[region]':'',
            'billing[postcode]':self.zip,
            'billing[country_id]':self.country,
            'billing[telephone]':self.phone,
            'billing[fax]':'',
            'billing[day]':'',
            'billing[month]':'',
            'billing[year]':'',
            'billing[dob]':'',
            'billing[customer_password]':'',	
            'billing[confirm_password]':'',
            'billing[save_in_address_book]':'1',
            'billing[use_for_shipping]':'1',
            'form_key': self.form_key
        }

        while True:
            self.warn('Solving captcha...')
            code = self.solve_v3('https://www.allikestore.com/default/checkout/onepage/')
            payload['g-recaptcha-response'] = code
            self.success('Successfully solved captcha!')
            try:
                r = self.s.post(
                    "https://www.allikestore.com/default/checkout/onepage/saveBilling/", 
                    headers=headers,
                    data=payload,
                    timeout=self.timeout,
                    allow_redirects=False
                )

                if r.status_code == 200:
                    if 'shipping_method' in r.text:
                        if self.country == "DE":
                            self.smethod = "premiumrate_DHL_GoGreen"
                        elif self.country == 'US':
                            self.smethod = 'premiumrate_UPS_Express_Saver_(excl._Customs_and_Duties)'
                        else:
                            self.smethod = "premiumrate_UPS_Standard"
                        self.success(f'Successfully got shipping rates!')
                        err = False
                        break
                    else:
                        self.error(f'Something went wrong while getting shipping rates, retrying...')
                        err = True
                        break
#
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    continue

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    continue

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    self.error(f'Error while getting shipping rates: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    time.sleep()

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception getting shipping rates: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception getting shipping rates: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if not err:
            self.ship2()
        else:
            self.checkoutpa()

    def ship2(self):

        self.warn('Submitting shipping...')

        headers = {
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.allikestore.com/default/checkout/onepage/',
        }

        payload = {
            'shipping_method':self.smethod,
            'form_key':self.form_key
        }

        while True:
            try:
                r = self.s.post(
                    "https://www.allikestore.com/default/checkout/onepage/saveShippingMethod/",
                    headers=headers,
                    data=payload
                )

                if r.status_code == 200:
                    if 'creditcard' in r.text:
                        self.success('Successfully submitted shipping!')
                        c = r.text.replace('\\','').replace('&quot;','').split('name="payment[payone_config]"n')[1]
                        self.aid = c.split('aid:')[1].split(',')[0]
                        self.encodi = c.split('encoding:')[1].split(',')[0]
                        self.has = c.split('hash:')[1].split(',')[0]
                        self.mid = c.split('mid:')[1].split(',')[0]
                        self.portalid = c.split('portalid:')[1].split(',')[0]
                        err = False
                        break
                    else:
                        self.error('Something went wrong while submitting shipping, retrying...')
                        time.sleep(self.delay)
                        continue

                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    self.error(f'Error submitting shipping: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception submitting shipping: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception submitting shipping: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if not err:
            self.cc()
        else:
            self.checkoutpa()

    def cc(self):

        self.warn('Verifying card...')

        global carted, failed, checkoutnum

        headers = {
            'Accept': '*/*',
            'Referer': 'https://secure.pay1.de/client-api/js/v1/payone_iframe.html'
        }

        cardtype = identify_card_type(self.cardnumber)
        if cardtype == "MasterCard":
            card_type = "M"
        elif cardtype == "Visa":
            card_type = "V"

        while True:
            try:
                r = self.s.get(
                    f"https://secure.pay1.de/client-api/?aid={self.aid}&encoding={self.encodi}&errorurl=&hash={self.has}&integrator_name=&integrator_version=&key=&language=&mid={self.mid}&mode=live&portalid={self.portalid}&request=creditcardcheck&responsetype=JSON&solution_name=&solution_version=&storecarddata=yes&successurl=&cardpan={self.cardnumber}&cardexpiremonth={self.expmonth}&cardexpireyear={self.expyear}&cardtype={card_type}&channelDetail=payoneHosted&cardcvc2={self.cvc}&callback_method=PayoneGlobals.callback", 
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=False
                )
                if r.status_code == 200:
                    try:
                        z = json.loads(r.text.split('PayoneGlobals.callback(')[1].split(');')[0])
                        if z['status'] == 'VALID':
                            self.pseudocardpan = z['pseudocardpan']
                            self.cardtype = z['cardtype']
                            self.truncatedcardpan = z['truncatedcardpan']
                            self.cardexpiredate = z['cardexpiredate']
                            self.success('Card Successfully verified!')
                            break
                        else:
                            self.error('Something went wrong veryfing card')
                            time.sleep(self.delay)
                            continue
                    except:
                        self.error('Something went wrong veryfing card')
                        time.sleep(self.delay)
                        continue
                else:
                    self.error(f'Error while verifying card: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception verifying card: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception verifying card: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue

        self.submitorder()

    def submitorder(self):

        self.warn('Submitting order...')

        global carted, failed, checkoutnum

        headers = {
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.allikestore.com/default/checkout/onepage/'
        }

        payload = {
            'payment[method]':'payone_creditcard',
            'payone_creditcard_cc_type_select':f'4_{self.cardtype}',
            'payment[cc_type]':self.cardtype,
            'payment[payone_pseudocardpan]':self.pseudocardpan,
            'payment[payone_cardexpiredate]':self.cardexpiredate,
            'payment[cc_number_enc]':self.truncatedcardpan,
            'payment[payone_config_payment_method_id]':'4',
            'payment[payone_config]':{
                "gateway": {
                    "4": {
                        "aid": { self.aid },
                        "encoding": { self.encodi },
                        "errorurl":"",
                        "hash": { self.has },
                        "integrator_name":"",
                        "integrator_version":"",
                        "key":"",
                        "language":"",
                        "mid": { self.mid },
                        "mode":"live",
                        "portalid": { self.portalid },
                        "request":"creditcardcheck",
                        "responsetype":"JSON",
                        "solution_name":"",
                        "solution_version":"",
                        "storecarddata":"yes",
                        "successurl":""
                    }
                }
            },
            'payment[payone_config_cvc]':'{"4_V":"always","4_M":"always"}',
            'form_key':self.form_key,
            'agreement[2]':'1',
            'agreement[4]':'1',
            'customer_order_comment':''
        }

        while True:
            try:
                r = self.s.post(
                    f"https://www.allikestore.com/default/checkout/onepage/saveOrder/", 
                    data=payload, 
                    headers=headers
                )

                if r.status_code == 200:
                    try:
                        z = json.loads(r.text)
                        if z['success'] == True:
                            self.redirect = z['redirect']
                            self.success('Successfully checked out!')
                            checkoutnum += 1
                            self.bar()
                            err = False
                            break
                        else:
                            self.error(f'Payment failed, card was probably declined.')
                            failed +=1
                            self.bar()
                            self.declined()
                            err = True
                            break
                    except:
                        self.error('Something went wrong submitting order, card was probably declined.')
                        failed +=1
                        self.bar()
                        self.declined()
                        err = True
                        break

                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    err = True
                    break

                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue

                else:
                    self.error(f'Error checking out: {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue

            except Exception as e:
                self.error(f'Exception checking out: {e.__class__.__name__}, retrying...')
                open(self.logs_path, 'a+').write(f'Exception checking out: {e}\n')
                self.build_proxy()
                time.sleep(self.delay)
                continue
        if not err:
            self.passCookies2()
        else:
            self.s.cookies.clear()
            self.build_proxy()
            self.scraperPid()

    def passCookies2(self):

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
        url = urllib.parse.quote(base64.b64encode(bytes(self.redirect, 'utf-8')).decode())
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
                writer.writerow({'SITE':'ALLIKE','SIZE':f'{self.sizeweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})

        else:
            self.expToken = self.token
            with open(path,'a',newline='') as f:
                fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow({'SITE':'ALLIKE','SIZE':f'{self.sizeweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.prodName}'})

        self.webhook2()

    def declined(self):
        try:
            if self.all_proxies == None:
                self.proxi = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Payment Declined', color = 15746887)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
        except:
            pass


    def webhook2(self):

        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Wating 3d Secure!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass


    def Pubblic_Webhook2(self):
        try:
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = False)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = False)
            embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = True)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
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


    def webhook(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO SUCCESS- PAYPAL READY!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='**PROXY**', value = f'||{self.px}||', inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.image)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()

        except:
            pass

    
    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Success', color = 40703)
            embed.add_embed_field(name='**ALLIKE STORE**', value = f'{self.prodName}', inline = False)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizeweb}', inline = True)
            embed.add_embed_field(name='Payment method', value = self.payment, inline = True)
            embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = True)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
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