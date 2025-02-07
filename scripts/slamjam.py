import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, pytz
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from os import urandom
import js2py
import traceback
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


class SLAMJAM():

    def __init__(self, row, webhook, version, threadID, DISCORD_ID):
        

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'slamjam/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "slamjam/proxies.txt")
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
        
        self.s = requests.Session()
        self.discord = DISCORD_ID
        self.sku = row['VARIANT'] 
        self.preload = row['PRELOAD']
        self.size = row['SIZE']
        self.twocaptcha = config['2captcha']
        self.mail = row['MAIL']
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.country = row['COUNTRY']
        self.address = row['ADDRESS'] + row['HOUSENUMBER']
        self.address2 = row['ADDRESS2']
        self.zipcode = row['ZIPCODE']
        self.city = row['CITY']
        self.region = row['REGION']
        self.phone = row['PHONE']
        self.cardnumber = row['CARDNUMBER']
        self.expmonth = row['EXPMONTH']
        self.expyear = row['EXPYEAR']
        self.cvv = row['CVV']
        self.webhook_url = webhook
        self.threadID = '%03d' % threadID
        self.payment = row['PAYMENT']
        self.version = version
        self.twocaptcha = config['2captcha']
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.skucorto = False
        
        self.lang = f"en_{self.country}"
        self.domain = f"www.slamjam.com/{self.lang}/"
        self.ship_url = f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/CheckoutShippingServices-SubmitShipping"


        self.balance = balancefunc()

        self.bar()

        self.delay = int(config['delay'])


        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Starting tasks...')

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
            self.s.proxies = self.selected_proxies
        
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


        if self.preload == "":
            if len(self.sku) > 8:
                warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Adding to cart...')
                self.atc()
            else:
                self.skuskusku = self.sku
                self.getprod()
        else:
            self.skuskusku = self.sku
            self.atc2()


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
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - Running SLAMJAM | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running SLAMJAM | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')


    def genkey(self):

        self.publickey = "fQXiz4wCHXdXRa434XC4gg=="
        self.privatekey = "as7rlcwKB5ZzRSva9E6ZtUKDmZShuEUPHaULQ47mGtmeRBfX4A/u8i57gPBwAVLw"
        self.companyname = "phoenix"
        result = []
        t = f'{self.publickey}:phoenix:{int(time.time() * 1000)}:{self.privatekey}'
        for i in range(0, len(t), 4):
            result.append((base64.b64encode((t[i : i + 4]).encode("utf-8"))).decode("utf-8"))
        key = (base64.b64encode(("".join(result)).encode("utf-8"))).decode("utf-8")
        return key



    def get_ddCaptchaChallenge(self):

        try:

            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Parsing challenge...')

            js_script = """
            const navigator = {
                userAgent: 'user_agent',
                language: 'singleLangHere',
                languages: 'langListHere'
            }

            ddExecuteCaptchaChallenge = function(r, t) {
                function e(r, t, e) {
                    this.seed = r, this.currentNumber = r % t, this.offsetParameter = t, this.multiplier = e, this.currentNumber <= 0 && (this.currentNumber += t)
                }
                e.prototype.getNext = function() {
                    return this.currentNumber = this.multiplier * this.currentNumber % this.offsetParameter, this.currentNumber
                };
                for (var n = [function(r, t) {
                        var e = 26157,
                            n = 0;
                        if (s = "VEc5dmEybHVaeUJtYjNJZ1lTQnFiMkkvSUVOdmJuUmhZM1FnZFhNZ1lYUWdZWEJ3YkhsQVpHRjBZV1J2YldVdVkyOGdkMmwwYUNCMGFHVWdabTlzYkc5M2FXNW5JR052WkdVNklERTJOMlJ6YUdSb01ITnVhSE0", navigator.userAgent) {
                            for (var a = 0; a < s.length; a += 1 % Math.ceil(1 + 3.1425172 / navigator.userAgent.length)) n += s.charCodeAt(a).toString(2) | e ^ t;
                            return n
                        }
                        return s ^ t
                    }, function(r, t) {
                        for (var e = (navigator.userAgent.length << Math.max(r, 3)).toString(2), n = -42, a = 0; a < e.length; a++) n += e.charCodeAt(a) ^ t << a % 3;
                        return n
                    }, function(r, t) {
                        for (var e = 0, n = (navigator.language ? navigator.language.substr(0, 2) : void 0 !== navigator.languages ? navigator.languages[0].substr(0, 2) : "default").toLocaleLowerCase() + t, a = 0; a < n.length; a++) e = ((e = ((e += n.charCodeAt(a) << Math.min((a + t) % (1 + r), 2)) << 3) - e + n.charCodeAt(a)) & e) >> a;
                        return e
                    }], a = new e(function(r) {
                        for (var t = 126 ^ r.charCodeAt(0), e = 1; e < r.length; e++) t += (r.charCodeAt(e) * e ^ r.charCodeAt(e - 1)) >> e % 2;
                        return t
                    }(r), 1723, 7532), o = a.seed, u = 0; u < t; u++) {
                    o ^= (0, n[a.getNext() % n.length])(u, a.seed)
                }
                ddCaptchaChallenge = o
                return ddCaptchaChallenge
            }
            ddExecuteCaptchaChallenge("putCidHere", 10);
            """.replace("putCidHere",self.cid).replace("user_agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36") \
                .replace("singleLangHere", "en-US").replace("langListHere", "en-US,en;q=0.9,sr;q=0.8")

            self.result = js2py.eval_js(js_script)
            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Got challenge...')
            return self.result

        except:
            pass

    def connection2(self):

        try:
            

            captchalink = f"https://geo.captcha-delivery.com/captcha/?initialCid={self.initialcid}&hash={self.hsh}&cid={self.cid}&t=fe&referer=https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site&s={self.sss}"

            headers = {
                'accept-encoding': 'gzip, deflate, br',
                'pragma': 'no-cache',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-US,en;q=0.9,sr;q=0.8'
            }

            s = requests.Session()

            r = s.get(captchalink, proxies = self.selected_proxies, headers = headers)   

            if r.status_code == 200:

                ciao = r.text
                self.challenge = ciao.split("challenge: '")[1].split("',")[0]
                self.gt = ciao.split("gt: '")[1].split("',")[0]
                self.ip = ciao.split("'&x-forwarded-for=' + encodeURIComponent('")[1].split("'")[0]
                self.initialcid = ciao.split("&icid=' + encodeURIComponent('")[1].split("'")[0]
                self.hsh = ciao.split("&hash=' + encodeURIComponent('")[1].split("'")[0]
                self.ip = ciao.split("(IP ")[1].split(")")[0]
                
                headers2 = {
                    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Connection': 'keep-alive',
                    'Accept-Language': 'en-US,en;q=0.9,sr;q=0.8',
                    'Cache-Control': 'no-cache',
                    'Sec-Fetch-Dest': 'iframe',
                    'Pragma': 'no-cache',
                    'Referer': 'https://www.slamjam.com/',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
                }

                body = {
                    "key": str(self.genkey()),
                    "gt": self.gt,
                    "challenge": self.challenge
                }


                headers2 = {
                    f"x-{self.companyname}-key": f'{self.privatekey}'
                }

                r = requests.post(f'https://curvesolutions.dev/{self.publickey}/geetest', headers=headers2, data=body)
        
                jsonresp = json.loads(r.text)
                self.geetest_challenge = jsonresp['data']['challenge']
                self.geetest_validate = jsonresp['data']['validate']
                self.geetest_seccode = jsonresp['data']['seccode']

                self.proxi2 = self.selected_proxies['http'].split("http://")[1]

                headers = {
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                    'Cache-Control': 'no-cache',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Referer': 'https://geo.captcha-delivery.com/',
                    'Pragma': 'no-cache',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
                }


                dd_url = 'https://geo.captcha-delivery.com/captcha/check?cid=' + self.cid + '&icid=' + self.initialcid +'&ccid=' + 'null' +'&geetest-response-challenge=' + str(self.geetest_challenge) +'&geetest-response-validate=' + str(self.geetest_validate)  +'&geetest-response-seccode=' + str(self.geetest_seccode) +'&hash=' + self.hsh +'&ua=' + 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' +'&referer=' + self.dataurl +'&parent_url=' + f'https://www.slamjam.com/' + '&s=' + str(self.sss)

                r = self.s.get(dd_url, headers=headers)

                if r.status_code == 200:
                
                    jsondd = json.loads(r.text)
                    dd = jsondd['cookie']

                    dd = dd.split('datadome=')[1].split('"')[0]

                    self.cookie_obj = requests.cookies.create_cookie(domain='.slamjam.com',name='datadome',value=dd)
                    self.s.cookies.set_cookie(self.cookie_obj)

                    return info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome done, proceding...')

                else:
                    return error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome failed, retrying...')

            else:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome failed, restarting...')
                self.s.cookies.clear()
                if self.preload == "":
                    if len(self.sku) > 8:
                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Adding to cart...')
                        self.atc()
                    else:
                        self.skuskusku = self.sku
                        self.getprod()
                else:
                    self.atc2()

        except Exception as e:
            return error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome failed, retrying...')
        
    def token(self):

        try:

            self.dataome = 0

            try:
    
                warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Getting token...')
    
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding': 'gzip, deflate',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'referer': f'https://www.slamjam.com/{self.lang}/checkout',
                    'sec-fetch-dest' : 'document',
                    'sec-fetch-mode' : 'navigate',
                    'sec-fetch-site' : 'same-origin',
                    'sec-fetch-user' : '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
                }
         
                i = 0

                while True:
    
                    r = self.s.get(f"https://www.slamjam.com/{self.lang}/checkout-begin", headers = headers, proxies = self.selected_proxies, timeout = 20)
    
                    if 'Please enable JS' in r.text:
                        self.dataurl = r.url                    
                        resp = r.text
                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            continue

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')
                        

                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]

                        self.connection2()

                        i = i + 1

                        continue

                    
    #
                    if r.status_code == 200:
                        soup = bs(r.text, features='lxml')
                        cftokenhtml = r.text
                        try:
                            self.cftoken = cftokenhtml.split('name="csrf_token" value="')[1].split('"')[0]
                        except:
                            self.cftoken = soup.find('input',{'name':'csrf_token'})['value']
                        break
                    
    #
                    else: 
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error retrieving token {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            time.sleep(1)
                        self.token()
    #
                return info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Successfully got token!')         
    #
            except ConnectionError as e:
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Connection error, retrying...')
                self.s.cookies.clear()
                self.token()
    #
            except Exception as e:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Unknown error while getting token {e}, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                self.s.cookies.clear()
                self.token()

        except:
            pass

    def getprod(self):

        try:

            self.skucorto = True
            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Getting product page...')

            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                'dnt': '1',
                'referer': f'https://www.slamjam.com/en_IT/{self.sku}.html',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }

            heac = {
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Referer': 'https://www.slamjam.com/en_IT/home',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en'
            }

            i = 0

            
            while True:

                x = self.s.get(f'https://www.slamjam.com/en_IT/{self.sku}.html', headers = heac)

                if 'Please enable JS' in x.text:
                    self.dataurl = x.url                    
                    resp = x.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        i = 0
                        continue

                    warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')


                    cid = []
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    for cookie in cookies:
                        if cookie['name'] == "datadome":
                            cid.append(cookie)
                    ciddo = cid[-1]
                    self.cid = ciddo["value"]

                    self.connection2()

                    i = i + 1

                    continue

                if x.status_code == 200:

                    self.color = x.text.split('data-attr-value="')[1].split('"')[0]
                    
                    r = self.s.get(f'https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/en_IT/Product-Variation?dwvar_{self.sku}_color={self.color}&dwvar_{self.sku}_size=&pid={self.sku}&quantity=1', headers = headers, timeout = 20)

                    if 'Please enable JS' in r.text:
                        self.dataurl = r.url                    
                        resp = r.text
                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            i = 0
                            continue

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')


                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]

                        self.connection2()

                        i = i + 1

                        continue

                    if r.status_code == 200:
                        r_json = json.loads(r.text)
                        self.title2 = r_json['product']['productName']
                        img = r_json['product']['images']['hi-res'][0]['url']
                        self.immagine = f'https://www.slamjam.com{img}'

                        try:
                            raffle = r_json['product']['isRaffle']
                        except:
                            raffle = False

                        if raffle == True:
                            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Raffle product, monitoring...')
                            time.sleep(self.delay)
                            continue
                        else:
                            
                            self.available = r_json['product']['available']
                            if self.available == True:
                                availability = r_json['product']['availability']['messages'][0]
                                if availability == 'In Stock':
                                    values = r_json['product']['variationAttributes'][1]['values']
                                    self.sizeprint = []
                                    self.variantid = []
                                    for x in values:
                                        if x['selectable'] == True:
                                            self.sizeprint.append(x['displayValue'])
                                            self.variantid.append(x['productID'])

                                    tot = zip(self.sizeprint, self.variantid)
                                    connect = list(tot)
                                    self.sizerange = []

                                    info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Succesfully got product page!')

                                    if self.size == "RANDOM":
                                        scelta = random.choice(connect)
                                        ciao3 = scelta[1]
                                        self.sku = "".join(ciao3)
                                        ciao1 = scelta[0]
                                        self.sizeprinta = "".join(ciao1)
                                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Adding to cart size {self.sizeprinta}')
                                        break

                                    elif '-' in self.size:
                                        self.size1 = str(self.size.split('-')[0])
                                        self.size2 = str(self.size.split('-')[1])
                                        for x in connect:
                                            if self.size1 <= str(x[0]) <= self.size2:
                                                self.sizerange.append(x)        
                                        self.sizerandom = random.choice(self.sizerange)
                                        for i in connect:
                                            if self.sizerandom[0] in i[0]:
                                                self.sku = i[1]
                                                self.sizeprinta = i[0]
                                        info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Adding to cart size {self.sizeprinta}')
                                        break

                                    elif ',' in self.size:
                                        self.size1 = str(self.size.split(',')[0])
                                        self.size2 = str(self.size.split(',')[1])
                                        for x in connect:
                                            if self.size1 <= str(x[0]) <= self.size2:
                                                self.sizerange.append(x)        
                                        self.sizerandom = random.choice(self.sizerange)
                                        for i in connect:
                                            if self.sizerandom[0] in i[0]:
                                                self.sku = i[1]
                                                self.sizeprinta = i[0]
                                        info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Adding to cart size {self.sizeprinta}')
                                        break

                                    else:
                                        for Traian in connect:
                                            if self.size == Traian[0]:
                                                ciao = Traian[0]
                                                ciao1 = Traian[1]
                                                self.sku = "".join(ciao1)
                                                self.sizeprinta = "".join(ciao)

                                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Adding to cart size {self.sizeprinta}')
                                        break

                                else:
                                    warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Product OOS, monitoring...')
                                    time.sleep(self.delay)
                                    continue
                            else:
                                warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Product OOS, monitoring...')
                                time.sleep(self.delay)
                                continue

                        
                    elif r.status_code == 403:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue
                    
                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Page not loaded, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue
                elif x.status_code == 403:

                    warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    continue

                elif x.status_code == 429:

                    warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    continue

                else:
                    error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {x.status_code}, retrying...')
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    time.sleep(self.delay)
                    continue
            
            self.atc()
                
        except Exception as e:
            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception getting product, retrying...')
            self.getprod()


    def atc(self):

        try:
            try:

                headers = {
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://www.slamjam.com',
                    'referer': f'https://www.slamjam.com/{self.lang}/woman/footwear/sneakers/low/puma/kyron-queen-sneakers/J194348.html',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }


                payload = {
                    'pid': self.sku,
                    'quantity': '1',
                    'viewFrom': 'si',
                    'options': '[]'
                }
                
                i = 0

                while True:


                    r = self.s.post(f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/Cart-AddProduct", headers = headers, proxies = self.selected_proxies, data = payload)

                    if 'Please enable JS' in r.text:
                        self.dataurl = r.url                    
                        resp = r.text
                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            i = 0
                            continue
                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')
                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]
                        self.connection2()
                        i = i + 1
                        continue


                    if r.status_code == 200:
                        try:
                            self.shipuuid = r.text.split('"shipmentUUID": "')[1].split('"')[0]
                            info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Successfully added to cart!')
                            image = r.text.split('https://www.slamjam.com/dw/image/')[1].split('"')[0]
                            self.image = f"https://www.slamjam.com/dw/image/{image}"
                            self.title = r.text.split('"title": "')[1].split('"')[0]
                            break 
                        except:
                            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Product is OOS, retrying...')
                            time.sleep(self.delay)
                            continue

                    elif r.status_code == 403:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                if self.preload == "":
                    self.ship()
                else:
                    if self.payment == "PP":
                        self.pagamento2()
                    else:
                        self.placeorder()
                    
            except Exception as e:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception while adding to cart {e}, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.atc()

        except:
            pass

    def atc2(self):

        try:

            self.dataome = 0

            try:

                warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Preload mode...')

                headers = {
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://www.slamjam.com',
                    'referer': f'https://www.slamjam.com/{self.lang}/woman/footwear/sneakers/low/puma/kyron-queen-sneakers/J194348.html',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }


                payload = {
                    'pid': self.preload,
                    'quantity': '1',
                    'category': 'low',
                    'viewFrom': 'si',
                    'options': '[]'
                }

                i = 0

                while True:

                    r = self.s.post(f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/Cart-AddProduct", headers = headers, proxies = self.selected_proxies, data = payload, timeout = 15)


                    if 'Please enable JS' in r.text:
                        self.dataurl = r.url                    
                        resp = r.text

                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            i = 0
                            continue

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')

                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]

                        self.connection2()

                        i = i + 1

                        continue
                    

                    if r.status_code == 200:

                        try:
                            self.shipuuid = r.text.split('"shipmentUUID": "')[1].split('"')[0]
                            jsoncart = json.loads(r.text)
                            image = r.text.split('https://www.slamjam.com/dw/image/')[1].split('"')[0]
                            self.image = f"https://www.slamjam.com/dw/image/{image}"
                            self.title = r.text.split('"title": "')[1].split('"')[0]
                            self.uuid = jsoncart['pliUUID']
                            break 
                        
                        except:
                            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Preload is OOS, please change it')
                            sys.exit(1)

                    elif r.status_code == 403:
                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)

                    elif r.status_code == 429:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                self.ship()
                    
            except Exception as e:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception while adding preload, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.atc2()

        except:
            pass


    def ship(self):

        try:

            self.dataome = 0

            try:

                self.token()

                warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Submitting shipping...')

                headers = {
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://www.slamjam.com',
                    'referer': f'https://www.slamjam.com/{self.lang}/checkout-begin?stage=shipping',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                payload = {
                    'originalShipmentUUID': self.shipuuid,
                    'shipmentUUID': self.shipuuid,
                    'shipmentSelector': 'new',
                    'dwfrm_shipping_shippingAddress_addressFields_firstName': self.name,
                    'dwfrm_shipping_shippingAddress_addressFields_lastName': self.surname,
                    'dwfrm_shipping_shippingAddress_addressFields_states_country': self.country,
                    'dwfrm_shipping_shippingAddress_addressFields_states_stateCode': self.region,
                    'dwfrm_shipping_shippingAddress_addressFields_city': self.city,
                    'dwfrm_shipping_shippingAddress_addressFields_states_postalCode': self.zipcode,
                    'dwfrm_shipping_shippingAddress_addressFields_address1': self.address,
                    'dwfrm_shipping_shippingAddress_addressFields_address2': self.address2,
                    'dwfrm_shipping_shippingAddress_addressFields_prefix': '+39',
                    'dwfrm_shipping_shippingAddress_addressFields_phone': self.phone,
                    'dwfrm_shipping_shippingAddress_shippingMethodID': '001',
                    'csrf_token': self.cftoken
                }

                i = 0

                while True:

                    r = self.s.post(f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/CheckoutShippingServices-SubmitShipping", headers = headers, proxies = self.selected_proxies, data = payload, timeout = 20)

                    if 'Please enable JS' in r.text:
                        self.dataurl = r.url                    
                        resp = r.text

                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            i = 0
                            continue

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')

                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]

                        self.connection2()

                        i = i + 1

                        continue

                    elif r.status_code == 200:

                        info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Successfully shipping submitted!')
                        break

                    elif r.status_code == 403:

                        

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue



                if self.payment == "PP" or self.cardnumber == "":
                    if self.preload == "":
                        self.pagamento2()
                    else:
                        self.clearcart()
                else:
                    self.pagamento()


            except Exception as e:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception while submitting shipping, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.ship()

        except:
            pass

    def gnerateCardDataJson(self, pan, expiry_month, expiry_year, name, cvc):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "number": pan,
            "expiryMonth": expiry_month,
            "expiryYear": expiry_year,
            "generationtime": generation_time,
            "holderName": name,
            "cvc": cvc
        }

    def encryptWithAesKey(self, aes_key, nonce, plaintext):
        cipher = AESCCM(aes_key, tag_length=8)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        return ciphertext

    def decodeAdyenPublicKey(self, encoded_public_key):
        backend = default_backend()
        key_components = encoded_public_key.split("|")
        public_number = rsa.RSAPublicNumbers(int(key_components[0], 16), int(key_components[1], 16))
        return backend.load_rsa_public_numbers(public_number)

    def encryptWithPublicKey(self, public_key, plaintext):
        ciphertext = public_key.encrypt(plaintext, padding.PKCS1v15())
        return ciphertext

    def main(self, pan, expiry_month, expiry_year, name, cvc, key):

        plainCardData = self.gnerateCardDataJson(
            name=name,
            pan=pan,
            cvc=cvc,
            expiry_month=expiry_month,
            expiry_year=expiry_year
        )

        cardDataJsonString = json.dumps(plainCardData, sort_keys=True)
        aesKey = AESCCM.generate_key(256)
        nonce = urandom(12)
        encryptedCardData = self.encryptWithAesKey(aesKey, nonce, bytes(cardDataJsonString, encoding='utf8'))
        encryptedCardComponent = nonce + encryptedCardData
        adyenPublicKey = key
        publicKey = self.decodeAdyenPublicKey(adyenPublicKey)
        encryptedAesKey = self.encryptWithPublicKey(publicKey, aesKey)
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_18", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))

        return encryptedAesData



    def pagamento(self):

        try:

            self.dataome = 0

            try:

                warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Submitting billing...')

                headers = {
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://www.slamjam.com',
                    'referer': f'https://www.slamjam.com/{self.lang}/checkout-begin?stage=payment',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }


                cardnu = self.cardnumber[-4:]
                cardnum = f'************{cardnu}'

                cardtype = identify_card_type(self.cardnumber)
                if cardtype == "MasterCard":
                    card_type = "Master Card"
                elif cardtype == "Visa":
                    card_type = "Visa"


                payload = {
                    'addressSelector': self.shipuuid,
                    'dwfrm_billing_addressFields_firstName': self.name,
                    'dwfrm_billing_addressFields_lastName': self.surname,
                    'dwfrm_billing_addressFields_states_country': self.country,
                    'dwfrm_billing_addressFields_states_stateCode': self.region,
                    'dwfrm_billing_addressFields_city': self.city,
                    'dwfrm_billing_addressFields_states_postalCode': self.zipcode,
                    'dwfrm_billing_addressFields_address1': self.address,
                    'dwfrm_billing_addressFields_address2': self.address2,
                    'dwfrm_billing_paymentMethod': 'CREDIT_CARD',
                    'dwfrm_billing_creditCardFields_email': self.mail,
                    'dwfrm_billing_privacy': True,
                    'dwfrm_billing_paymentMethod': 'CREDIT_CARD',
                    'dwfrm_billing_creditCardFields_cardType': card_type,
                    'dwfrm_billing_creditCardFields_adyenEncryptedData': self.main(name = f"{self.name} {self.surname}",pan = self.cardnumber,cvc = self.cvv,expiry_month = self.expmonth,expiry_year = self.expyear ,key = "10001|9D82A3F3F81509D2638BEB784DBD525FB3156EE4E0742E195E0DCB79354AC45FA5422E36B224EB082B63CF09F8355B7C28C3D1BB4C6E091CC07022CF6FB76194BD2B166B44452624AF7D770D6DD98CF9D1943979C342005A6F6016DB3CF192BD06E2A56AE46552647581B29A07D2A3E7AD32CEFE6FF03BFDEFB51419855BFD209343B60F963B8AEC00E68764B6471B8CDF66585BBCA31584BB35A7660C3B4D4862E7518C4369C5E1E176E3A9FEA76A641442DFA01707098A6E94AF847C1534F6E164427CFCEA92295327431D1B2256A222E4EDBAD7B86EC5931F5529A75977A07EDF441B581EF60C09357227AFAA234824B03AD411DFA1723F4441B5BCA29115"),
                    'dwfrm_billing_creditCardFields_selectedCardID': '',
                    'dwfrm_billing_creditCardFields_cardNumber': cardnum,
                    'dwfrm_billing_creditCardFields_expirationMonth': self.expmonth,
                    'dwfrm_billing_creditCardFields_expirationYear': self.expyear,
                    'csrf_token': self.cftoken
                }

                i = 0

                while True:

                    r = self.s.post(f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/CheckoutServices-SubmitPayment", headers = headers, proxies = self.selected_proxies, data = payload)

                    if 'Please enable JS' in r.text:
                        self.dataurl = r.url                    
                        resp = r.text

                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            i = 0
                            continue

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')

                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]

                        self.connection2()

                        i = i + 1

                        continue


                    elif r.status_code == 200:
                        info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Successfully billing submitted!')
                        break

                    elif r.status_code == 403:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue


                if self.preload == "":
                    self.placeorder()
                else:
                    self.clearcart()

            except Exception as e:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception while submitting billing {e}, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.pagamento()

        except:
            pass

    def clearcart(self):

        try:

            try:

                headers = {
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'referer': f'https://www.slamjam.com/{self.lang}/cart',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                PARAMS = {
                    'pid': self.preload,
                    'uuid': self.uuid
                }

                i = 0

                while True:

                    r = self.s.get(f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/Cart-RemoveProductLineItem", params = PARAMS, allow_redirects = True, headers = headers)

                    if 'Please enable JS' in r.text or 'geo.captcha' in r.text:
                        try:
                            if 'geo.captcha' in r.text:
                                if self.all_proxies != None:
                                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                                    self.s.proxies = self.selected_proxies
                                continue
                        except:
                            self.dataurl = r.url                    
                            resp = r.text
                            self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                            self.hsh = resp.split("hsh':'")[1].split("','")[0]
                            self.sss = resp.split("'s':")[1].split(',')[0]
                            self.ttt = resp.split("'t':'")[1].split("',")[0]
                            if self.ttt == "bv" or i > 1:
                                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                                if self.all_proxies != None:
                                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                                    self.s.proxies = self.selected_proxies
                                i = 0
                                continue
                            
                            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')

                            cid = []
                            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                            
                            for cookie in cookies:
                                if cookie['name'] == "datadome":
                                    cid.append(cookie)
                            ciddo = cid[-1]
                            self.cid = ciddo["value"]

                            self.connection2()

                            i = i + 1

                            continue


                    if r.status_code == 200:
                        jsonpreload = json.loads(r.text)

                        a = str(jsonpreload['basketModelPlus'])

                        total = a.split("'numItems': ")[1].split(",")[0]

                        if "0" in total:

                            info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Preload done!')
                            break

                        if 'captchade':
                            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Cart not clear, preload failed, retrying...')
                            time.sleep(self.delay)
                            continue

                    elif r.status_code == 403:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code >= 500 and r.status_code <= 600:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                
                if len(self.sku) > 8:
                    warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Adding to cart...')
                    self.atc()
                else:
                    self.getprod()


            except Exception as e:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception while clearing cart: {e}, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.clearcart()

        except:
            pass

    def pagamento2(self):

        try:

            self.dataome = 0

            try:

                warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Submitting paypal...')

                headers = {
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://www.slamjam.com',
                    'referer': f'https://www.slamjam.com/{self.lang}/checkout-begin?stage=payment',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }




                payload = {
                    'addressSelector': self.shipuuid,
                    'dwfrm_billing_addressFields_firstName': self.name,
                    'dwfrm_billing_addressFields_lastName': self.surname,
                    'dwfrm_billing_addressFields_states_country': self.country,
                    'dwfrm_billing_addressFields_states_stateCode': self.region,
                    'dwfrm_billing_addressFields_city': self.city,
                    'dwfrm_billing_addressFields_states_postalCode': self.zipcode,
                    'dwfrm_billing_addressFields_address1': self.address,
                    'dwfrm_billing_addressFields_address2': self.address2,
                    'dwfrm_billing_paymentMethod': 'Paypal',
                    'dwfrm_billing_creditCardFields_email': self.mail,
                    'dwfrm_billing_privacy': True,
                    'isPaypal': True,
                    'dwfrm_billing_paymentMethod': 'Paypal',
                    'csrf_token': self.cftoken
                }

                i = 0

                while True:

                    r = self.s.post(f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/CheckoutServices-SubmitPayment", headers = headers, proxies = self.selected_proxies, data = payload)
                    if 'Please enable JS' in r.text:
                        self.dataurl = r.url                    
                        resp = r.text

                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            i = 0
                            continue

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')

                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]

                        self.connection2()

                        i = i + 1

                        continue

                    elif r.status_code == 200 and "paypalToken" in r.text:

                        info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Successfully checked out!')
                        self.pptoken = r.text.split('"paypalToken": "')[1].split('"')[0]
                        break

                    elif r.status_code == 403:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue


                self.paypal()

            except Exception as e:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception while submitting paypal, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.pagamento2()

        except:
            pass

    def paypal(self):
        
        try:

            link = f"https://www.paypal.com/webscr?cmd=_express-checkout&useraction=commit&token={self.pptoken}"

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
                url = urllib.parse.quote(base64.b64encode(bytes(link, 'utf-8')).decode())
                self.token1 = f"https://api.phoenixbot.io/exploits/?cookie={cookieStr}&redirect={url}"
                self.token2 = f"https://api.phoenixbot.io/mobile/?cookie={cookieStr}&redirect={url}"
                apiurl2 = "http://tinyurl.com/api-create.php?url="
                tinyasdurl2 = urllib.request.urlopen(apiurl2 + self.token2).read()
                self.expToken2 = str(tinyasdurl2.decode("utf-8"))
                if machineOS == "Darwin":
                    path = os.path.dirname(__file__).rsplit('/', 1)[0]
                else:
                    path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "success.csv")   

                if len(self.token1) > 1999:

                    try:
                        apiurl = "http://tinyurl.com/api-create.php?url="
                        tinyasdurl = urllib.request.urlopen(apiurl + self.token1).read()
                        self.expToken = str(tinyasdurl.decode("utf-8"))
                    except:
                        self.expToken = "https://twitter.com/PhoenixAI0"
                    
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'SLAMJAM','SIZE':f'{self.sku}','PAYLINK':f'{self.token1}','PRODUCT':f'{self.title}'})

                else:
                    self.expToken = self.token1
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'SLAMJAM','SIZE':f'{self.sku}','PAYLINK':f'{self.token1}','PRODUCT':f'{self.title}'})

                        
                if self.skucorto:
                    self.SuccessPP2()
                else:
                    self.SuccessPP()
                
            except Exception as e: 
                error(f'[TASK {self.threadID}] [SLAMJAM] - Exception while passing cookies {e}, retrying...') 
                time.sleep(self.delay)
                self.ship() 

        except:
            pass

    def placeorder(self):

        try:

            self.dataome = 0

            warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Placing order...')
            try:

                payload = {}

                headers = {
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-length': '0',
                    'origin': 'https://www.slamjam.com',
                    'referer': f'https://www.slamjam.com/{self.lang}/checkout-begin?stage=placeOrder',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                i = 0

                while True:


                    r = self.s.post(f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/CheckoutServices-PlaceOrder", data = payload, headers = headers, proxies = self.selected_proxies, allow_redirects = True)
                    
                    if 'Please enable JS' in r.text:
                        self.dataurl = r.url                    
                        resp = r.text

                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            i = 0
                            continue

                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Datadome found, proceding...')

                        cid = []
                        cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                        for cookie in cookies:
                            if cookie['name'] == "datadome":
                                cid.append(cookie)
                        ciddo = cid[-1]
                        self.cid = ciddo["value"]

                        self.connection2()

                        i = i + 1

                        continue


                    elif r.status_code == 200 and "orderID" in r.text:
                        info(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Successfully checked out!')
                        self.order = r.text.split('"orderID": "')[1].split('"')[0]
                        self.url3d = r.text.split('continueUrl": "')[1].split('"')[0]                                        
                        self.urlfinale = f"https://www.slamjam.com/on/demandware.store/Sites-slamjam-Site/{self.lang}/Adyen-Adyen3D?{self.url3d}"
                        break

                    elif r.status_code == 403:
                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Proxy banned, rotating...')                    
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        warn(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Rate limit, rotating...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                    else:
                        if "not valid" in r.text:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Checkout failed, retrying...')
                            self.declined()
                            sys.exit(1)
                        
                        elif 'cannot be ordered since one or more' in r.text:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Product oos while checking out, retrying...')
                            time.sleep(self.delay)
                            continue

                        else:
                            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Error status {r.status_code}, retrying...')
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            time.sleep(self.delay)
                            continue

                self.passpp()       

            except Exception as e:
                error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception while placing order, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.placeorder()
        except:
            pass

    def passpp(self):
        try:
            cookieStr = ""
            cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
            for element in cookies:
                if 'cf_chl_prog' in element['name']:
                    cookies.remove(element)
            try:
                for element in cookies:
                    if 'cf_chl' in element['name']:
                        cookies.remove(element)
            except:
                pass
            try:
                for element in cookies:
                    if 'KEYCLOAK_ADAPTER_STATE' in element['name']:
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
                    writer.writerow({'SITE':'SLAMJAM','SIZE':f'{self.sku}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'SLAMJAM','SIZE':f'{self.sku}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            if self.payment == 'CC':
                if self.skucorto:
                    self.SuccessCC2()
                else:
                    self.SuccessCC()
            else:
                self.SuccessPP()
        except Exception as e: 
            error(f'[TASK {self.threadID}] [SLAMJAM] [{self.sku}] - Exception sending webhook: {e}, retrying...') 
            self.passpp()

    def SuccessPP(self):
        if self.preload != "":
            mode = "PRELOAD"
        else:
            mode = "SAFE"
        if self.selected_proxies == None:
            self.proxi = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**SLAMJAM**', value = self.title, inline = False)
        embed.add_embed_field(name='**VARIANT**', value = self.sku, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = True)
        embed.add_embed_field(name='**MODE**', value = mode, inline = False)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url=self.image)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic()

    def SuccessPP2(self):
        if self.preload != "":
            mode = "PRELOAD"
        else:
            mode = "SAFE"
        if self.selected_proxies == None:
            self.proxi = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**SLAMJAM**', value = self.title2, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizeprinta, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = True)
        embed.add_embed_field(name='**MODE**', value = mode, inline = False)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        #embed.add_embed_field(name='**ORDER**', value = f"||{self.order}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url=self.immagine)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.PubblicPP2()

    def PubblicPP2(self):
        if self.preload != "":
            mode = "PRELOAD"
        else:
            mode = "SAFE"
        webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'**SLAMJAM**', value = self.title2, inline = False)
        embed.add_embed_field(name='**PID**', value = self.skuskusku, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
        embed.add_embed_field(name='**MODE**', value = mode, inline = False)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_thumbnail(url=self.immagine)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()

    def SuccessCC(self):
        if self.preload != "":
            mode = "PRELOAD"
        else:
            mode = "SAFE"
        if self.selected_proxies == None:
            self.proxi = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**SLAMJAM**', value = self.title, inline = False)
        embed.add_embed_field(name='**VARIANT**', value = self.sku, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = True)
        embed.add_embed_field(name='**MODE**', value = mode, inline = False)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**ORDER**', value = f"||{self.order}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url=self.image)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic()

    def SuccessCC2(self):
        if self.preload != "":
            mode = "PRELOAD"
        else:
            mode = "SAFE"
        if self.selected_proxies == None:
            self.proxi = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**SLAMJAM**', value = self.title2, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizeprinta, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = True)
        embed.add_embed_field(name='**MODE**', value = mode, inline = False)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**ORDER**', value = f"||{self.order}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url=self.immagine)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.PubblicCC2()

    def PubblicCC2(self):
        if self.preload != "":
            mode = "PRELOAD"
        else:
            mode = "SAFE"
        webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'**SLAMJAM**', value = self.title2, inline = False)
        embed.add_embed_field(name='**PID**', value = self.skuskusku, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
        embed.add_embed_field(name='**MODE**', value = mode, inline = False)
        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
        embed.set_thumbnail(url=self.immagine)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        try:
            playsound('checkout.wav')
            sys.exit(1)
        except:
            sys.exit(1)

    def declined(self):
        if self.preload != "":
            mode = "PRELOAD"
        else:
            mode = "SAFE"
        if self.selected_proxies == None:
            self.proxi = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Card declined!', color = 15746887)
        embed.add_embed_field(name=f'**SLAMJAM**', value = self.title, inline = False)
        embed.add_embed_field(name='**VARIANT**', value = self.sku, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = True)
        embed.add_embed_field(name='**MODE**', value = mode, inline = False)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
        embed.set_thumbnail(url=self.image)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()

    def Pubblic(self):
        try:
            if self.preload != "":
                mode = "PRELOAD"
            else:
                mode = "SAFE"
            webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**SLAMJAM**', value = self.title, inline = False)
            embed.add_embed_field(name='**VARIANT**', value = self.sku, inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = self.payment, inline = True)
            embed.add_embed_field(name='**MODE**', value = mode, inline = False)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
            embed.set_thumbnail(url=self.image)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            try:
                playsound('checkout.wav')
                sys.exit(1)
            except:
                sys.exit(1)
        except:
            print(traceback.format_exc())






        



        