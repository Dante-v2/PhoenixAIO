import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from autosolveclient.autosolve import AutoSolve
import helheim
from pyppeteer import launch
import asyncio

helheim.auth('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693')

html = '''document.write("<!DOCTYPE html><html><body><form action='{}' method='POST'><input type='hidden' name='PaReq' value='{}'><input type='hidden' name='TermUrl' value='{}'><input type='hidden' name='MD' value='{}'></form><script>document.forms[0].submit()</script></body></html>")'''

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

UNIQUE_ID = int(time.time() * 1000) * 2**random.randint(10,16)
AUTO_SOLVE = None
CAPTCHA_TOKENS = []
CAPTCHA = None

carted = 0
failed = 0
checkoutnum = 0
generated = 0

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

class STARCOW():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            self.logs_path = os.path.join(os.path.dirname(sys.argv[0]), 'starcow/exceptions.log')
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'starcow/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "starcow/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()
        except:
            self.error("Failed reading proxies, running localhost")
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
            self.error('2Captcha or AntiCaptcha needed. Stopping task.')
            time.sleep(5)
            sys.exit(1)

        self.s = cloudscraper.create_scraper(
            browser= {
                'browser': 'chrome',
                'mobile': False,
                'platform': 'windows'
            },
            captcha=self.captcha,
            doubleDown=False,
            requestPostHook=self.injection
        )

        self.link = row['LINK']
        self.size = row['SIZE']
        self.account = row['ACCOUNT']
        self.password = row['PASSWORD']
        self.mode = row['MODE']
        self.country = row['COUNTRY']
        #self.payment = row['PAYMENT']
        #self.cardnumber = row['CARD NUMBER']
        #self.month = row['EXP MONTH']
        #self.year = row['EXP YEAR']
        #self.cvv = row['CVV']
        self.discord = DISCORD_ID
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.delay = int(config['delay'])
        self.version = version
        self.twocaptcha = config['2captcha']
        
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.timeout = 120
        self.balance = balancefunc()
        self.build_proxy()
        self.bar()

        self.warn('Task started!')

        self.mom = False
        
        if self.mode == "LOGIN":
            self.getlogin()
        elif self.mode == "CREATE":
            self.session()
        elif self.mode == "SESSION":
            self.usesession()
        else:
            self.mode = "LOGIN"
            self.getlogin()
        #self.getprod()
    

    def error(self, text):
        message = f'[TASK {self.threadID}] - [STARCOW] - {text}'
        error(message)

    def success(self, text):
        message = f'[TASK {self.threadID}] - [STARCOW] - {text}'
        info(message)

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [STARCOW] - {text}'
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
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO {self.version} - STARCOW Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')
        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - STARCOW Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')



    def injection(self, session, response):
        self.bar()
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
        #        return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
        #    else:
        #        return response

    def usesession(self):
        self.warn('Loading session...')
        while True:
            try:
                if machineOS == "Darwin":
                    path = os.path.dirname(__file__).rsplit('/', 1)[0]
                else:
                    path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "starcow/sessions.txt")   
                with open (path, 'r') as f:
                    sessionlist = f.read().splitlines()
                    self.sessione = sessionlist[-1]
                with open (f'{path}', 'w') as f:
                    for line in sessionlist:
                        if line != self.sessione:
                            f.write(line + "\n")
                jsonsessione = json.loads(self.sessione)
                t1 = jsonsessione['session']
                self.account = jsonsessione['account']
                self.password = jsonsessione['password']
                t = urllib.parse.unquote(t1)
                jsoncookies = str(base64.b64decode(t))
                jsoncookies = jsoncookies.split("b'")[1].split("'")[0]
                jsonporcodio = json.loads(jsoncookies)
                for c in jsonporcodio:
                    cookie_obj = requests.cookies.create_cookie(domain=c['domain'],name=c['name'],value=c['value'])
                    self.s.cookies.set_cookie(cookie_obj)
                try:
                    self.s.delete_cookie('datadome')
                except:
                    pass
                self.success('Session created!')
                break

            except Exception as e:
                self.error('No sessions available, switching to login mode...')
                self.getlogin()
                break
        self.getprod()
                

    def session(self):
        self.warn('Creating session...')
        while True:
            try:
                self.getlogin()
                cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]  
                for cookie in cookies:
                    try:
                        if cookie['domain'][0] == ".":
                            cookie['url'] = cookie['domain'][1:]
                        else:
                            cookie['url'] = cookie['domain']
                        cookie['url'] = "https://"+cookie['url']
                    except:
                        pass
                cookies = json.dumps(cookies)
                self.cookieStr = urllib.parse.quote(base64.b64encode(bytes(cookies, 'utf-8')).decode())
                if machineOS == "Darwin":
                    path = os.path.dirname(__file__).rsplit('/', 1)[0]
                else:
                    path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "starcow/sessions.txt")   
                with open(path, 'a') as output:
                    jsonda = '''{"account":"self.account","password":"self.password","session":"self.cookieStr"}\n'''.replace("self.account", self.account).replace("self.password", self.password).replace("self.cookieStr", self.cookieStr)
                    output.writelines(jsonda)
                    output.close()
                self.success('Session saved!')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception creating session: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                self.session()

    #def solvegeetest(self):
    #    try:
    #        print('a')
    #        payload = {
    #            'gt':self.gt,
    #            'challenge':self.challenge
    #        }
#
    #        self.cookie_obj = requests.cookies.create_cookie(name='token',value='FOZon2MBI9RDO2nDrcF')
    #        self.s.cookies.set_cookie(self.cookie_obj)
#
    #        r = self.s.post('https://geetest.stranck.ovh/submit', json = payload)
    #        
    #        r_json = json.loads(r.text)
    #        if r.status_code == 200 and r_json['success'] == True:
    #            print('b')
    #            self.id = r_json['id']
    #            payload2 = {
    #                'gt':self.gt,
    #                'challenge':self.challenge,
    #                'id':self.id
    #            }
    #            x = self.s.post('https://geetest.stranck.ovh/submit', json = payload2)
#
    #            print(x.text)
    #        else:
    #            print(r.text)
#
#
    #    except Exception as e:
    #        error(f'An error occured solving captcha with Autosolve: {e}')
    #        self.build_proxy()
#
    #def connection2(self):
#
    #    try:
    #        
    #        captchalink = f"https://geo.captcha-delivery.com/captcha/?initialCid={self.initialcid}&hash={self.hsh}&cid={self.cid}&t=fe&referer={self.dataurl}&s={self.sss}"
#
    #        headers = {
    #            'accept-encoding': 'gzip, deflate, br',
    #            'pragma': 'no-cache',
    #            'upgrade-insecure-requests': '1',
    #            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    #            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9',
    #            'sec-fetch-site': 'none',
    #            'sec-fetch-mode': 'navigate',
    #            'sec-fetch-user': '?1',
    #            'sec-fetch-dest': 'document',
    #            'accept-language': 'en-US,en;q=0.9,sr;q=0.8'
    #        }
#
    #        s = requests.Session()
    #        s.proxies = self.px
    #        r = s.get(captchalink, headers = headers)   
#
    #        if r.status_code == 200:
    #            ciao = r.text
    #            self.challenge = ciao.split("challenge: '")[1].split("',")[0]
    #            self.gt = ciao.split("gt: '")[1].split("',")[0]
    #            self.apiserver = ciao.split("api_server: '")[1].split("'")[0]
    #            self.ip = ciao.split("'&x-forwarded-for=' + encodeURIComponent('")[1].split("'")[0]
    #            self.initialcid = ciao.split("&icid=' + encodeURIComponent('")[1].split("'")[0]
    #            self.hsh = ciao.split("&hash=' + encodeURIComponent('")[1].split("'")[0]
    #            self.ip = ciao.split("(IP ")[1].split(")")[0]
#
    #            self.solvegeetest()
    #            headers = {
    #                'Accept': '*/*',
    #                'Connection': 'keep-alive',
    #                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    #                'Cache-Control': 'no-cache',
    #                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    #                'Referer': 'https://geo.captcha-delivery.com/',
    #                'Pragma': 'no-cache',
    #                'Sec-Fetch-Dest': 'empty',
    #                'Sec-Fetch-Mode': 'cors',
    #                'Sec-Fetch-Site': 'same-origin',
    #                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
    #            }
#
    #            dd_url = 'https://geo.captcha-delivery.com/captcha/check?cid=' + self.cid + '&icid=' + self.initialcid +'&ccid=' + 'null' +'&geetest-response-challenge=' + str(self.geetest_challenge) +'&geetest-response-validate=' + str(self.geetest_validate)  +'&geetest-response-seccode=' + str(self.geetest_seccode) +'&hash=' + self.hsh +'&ua=' + 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' +'&referer=' + self.dataurl +'&parent_url=' + f'https://www.starcow.com/' + '&s=' + str(self.sss)
#
    #            r = self.s.get(dd_url, headers=headers)
#
    #            if r.status_code == 200:
    #            
    #                jsondd = json.loads(r.text)
    #                dd = jsondd['cookie']
#
    #                dd = dd.split('datadome=')[1].split('"')[0]
#
    #                self.cookie_obj = requests.cookies.create_cookie(name='datadome',value=dd)
    #                self.s.cookies.set_cookie(self.cookie_obj)
#
    #                return self.success('Datadome done, proceding...')
#
    #            else:
    #                return self.error('Datadome failed, retrying...')
#
    #        else:
    #            self.error('Datadome failed, restarting...')
    #            self.s.cookies.clear()
    #            if self.mode == "LOGIN":
    #                self.login()
    #            elif self.mode == "CREATE":
    #                self.session()
    #            elif self.mode == "SESSION":
    #                self.usesession()
    #            else:
    #                self.mode = "LOGIN"
    #                self.login()
#
    #    except Exception as e:
    #        return self.error(f'Datadome failed {e}, retrying...')

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
            self.warn('Parsing challenge...')
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
            self.warn('Succesfully got challenge...')
            return self.result
        except:
            pass

    def connection2(self):
        try:
            captchalink = f"https://geo.captcha-delivery.com/captcha/?initialCid={self.initialcid}&hash={self.hsh}&cid={self.cid}&t=fe&referer=https://www.starcowparis.com/&s={self.sss}"
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
            r = s.get(captchalink, proxies = self.s.proxies, headers = headers)   
            if r.status_code == 200:
                ciao = r.text
                self.challenge = ciao.split("challenge: '")[1].split("',")[0]
                self.gt = ciao.split("gt: '")[1].split("',")[0]
                self.ip = ciao.split("'&x-forwarded-for=' + encodeURIComponent('")[1].split("'")[0]
                self.initialcid = ciao.split("&icid=' + encodeURIComponent('")[1].split("'")[0]
                self.hsh = ciao.split("&hash=' + encodeURIComponent('")[1].split("'")[0]
                self.ip = ciao.split("(IP ")[1].split(")")[0]
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
                dd_url = 'https://geo.captcha-delivery.com/captcha/check?cid=' + self.cid + '&icid=' + self.initialcid +'&ccid=' + 'null' +'&geetest-response-challenge=' + str(self.geetest_challenge) +'&geetest-response-validate=' + str(self.geetest_validate)  +'&geetest-response-seccode=' + str(self.geetest_seccode) +'&hash=' + self.hsh +'&ua=' + 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' +'&referer=' + self.dataurl +'&parent_url=' + 'https://www.starcowparis.com/' + '&s=' + str(self.sss)
                r = self.s.get(dd_url, headers=headers)
                if r.status_code == 200:
                    jsondd = json.loads(r.text)
                    dd = jsondd['cookie']
                    dd = dd.split('datadome=')[1].split('"')[0]
                    self.cookie_obj = requests.cookies.create_cookie(domain='.starcowparis.com',name='datadome',value=dd)
                    self.s.cookies.set_cookie(self.cookie_obj)
                    return self.success('Datadome done, proceding...')
                else:
                    self.build_proxy()
                    return self.error('Datadome failed, retrying...')
            else:
                self.error('Datadome failed, restarting...')
                self.s.cookies.clear()
                self.build_proxy()
                if self.preload == "":
                    if len(self.sku) > 8:
                        self.warn('Adding to cart...')
                        self.atc()
                    else:
                        self.skuskusku = self.sku
                        self.getprod()
                else:
                    self.atc2()
        except Exception as e:
            self.build_proxy()
            return self.error(f'Datadome failed: {e}, retrying...')

    def getlogin(self):
        self.warn('Getting login page...')
        i = 0
        err = 0
        while True:
            try:
                r = self.s.get(
                    "https://www.starcowparis.com/connexion", 
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    self.warn('Datadome found, proceding...')
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
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code == 200:
                    self.success('Succesfully got login page!')
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is down, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Login failed:{r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while logging in, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception logging in: {e}, retrying...')
                self.build_proxy()
                
                continue
        self.login()

    def login(self):
        global carted, failed, checkoutnum
        headers = {
            'upgrade-insecure-requests': '1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self.s.headers.update(headers)
        data = {
            'back': 'my-account',
            'email': self.account,
            'password': self.password,
            'submitLogin': '1'
        }
        self.warn('Logging in...')
        i = 0
        err = 0
        self.restart = False
        while True:
            try:
                r = self.s.post(
                    "https://www.starcowparis.com/connexion?back=my-account", 
                    data = data, 
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    self.warn('Datadome found, proceding...')
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
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                elif "cloudflare.com/5xx-error-landing?" in r.text:
                    self.error('Cloudflare issue, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                elif 'identite' in r.url:
                    self.error('Account not verified, retrying...')
                    sys.exit(1)
                    break
                elif 'mon-compte' in r.url:
                    self.success('Successfully logged in!')
                    html = r.text
                    token = html.split('"static_token":"')[1]
                    self.token = token.split('","token":"')[0]
                    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is down, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Login failed:{r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while logging in, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception logging in: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                if err > 1:
                    self.restart = True
                    break
                else:
                    err = err + 1
                    continue
        if self.restart:
            self.s.cookies.clear()
            self.build_proxy()
            self.getlogin()
        else:
            if self.mode == "CREATE":
                return self.warn('Saving session...')
            else:
                self.getprod()

    def getprod(self):
        self.warn("Getting product...")
        i = 0
        while True:
            try:
                product = self.s.get(
                    self.link, 
                    timeout = self.timeout
                )
                if 'Please enable JS' in product.text:
                    self.dataurl = product.url                    
                    resp = product.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    self.warn('Datadome found, proceding...')
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
                elif product.status_code == 200:
                    prod_xml = bs(product.text, features='lxml')
                    try:
                        self.instock = []
                        self.rangedSizes = []
                        select = prod_xml.find('div', {'class': 'product-actions'})
                        selecto = select.find("div", {"class":"product-variants"})
                        selec = selecto.find("div",{"class":"clearfix product-variants-item"})
                        group = []
                        var = []
                        size = []
                        try:
                            v = product.text.split('<ul id="group')[1].split('class="')[1].split('"')[0]
                            try:
                                sel = selec.find("ul", {"class":"home"})
                                dante = sel.findAll("li",{"class":"input-container float-xs-left"})
                            except:
                                try:
                                    sel = selec.find("ul", {"class":"shoes"})
                                    dante = sel.findAll("li",{"class":"input-container float-xs-left"})
                                except:
                                    try:
                                        sel = selec.find("ul", {"class":"casual"})
                                        dante = sel.findAll("li",{"class":"input-container float-xs-left"})
                                    except:
                                        try:
                                            sel = selec.find("ul", {"class":"sneakers"})
                                            dante = sel.findAll("li",{"class":"input-container float-xs-left"})
                                        except:
                                            sel = selec.find("ul", {"class":v})
                                            dante = sel.findAll("li",{"class":"input-container float-xs-left"})
                            
                            for raffaele in dante:
                                group.append(raffaele.find("input")["name"])
                                var.append(raffaele.find("input")["value"])
                                pop = raffaele.find("span", {"class":"radio-label"}).text
                                poppo = pop.split('US')[0].strip()
                                size.append(poppo.replace(" 1/2",".5"))
                        except:
                            bbb = prod_xml.find('select',{'class':'form-control form-control-select'}).find_all('option')
                            for raffaele in bbb:
                                group.append(prod_xml.find('select',{'class':'form-control form-control-select'})['name'])
                                var.append(raffaele["value"])
                                size.append(raffaele["title"])
                        tot = zip(group, var, size)
                        self.connect = list(tot)
                        self.sizexx = size
                        self.success(f"Successfully found sizes: {size}")
                        self.product = prod_xml.find('h1', {'itemprop': 'name'}).text
                        try:
                            self.price = prod_xml.find("span", {"itemprop":"price"}).text
                        except:
                            self.price = '||undefined||'
                        self.img = prod_xml.find("img", {"class": "js-qv-product-cover"})["src"]
                        self.product_id = prod_xml.find('input', {'name': 'id_product'})['value']
                        self.token = prod_xml.find('input', {'name': 'token'})['value']
                        self.id_costum = prod_xml.find('input', {'name': 'id_customization'})['value']
                        break
                    except Exception as e:
                        self.warn(f"Product not released yet, retrying...")
                        time.sleep(self.delay)
                        continue
                    except Exception as e:
                        if product.url == "https://www.starcowparis.com/2-home":
                            self.warn("Page is not loaded, retrying...")
                            time.sleep(self.delay)
                            continue
                        self.warn("Product page pulled, retrying...")
                        continue
                elif product.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                elif product.status_code >= 500 and product.status_code <= 600:
                    self.warn('Site is down, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed getting product page:{product.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while getting product page, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception getting product page: {e.__class__.__name__}, retrying...')
                continue
        self.atc()

    def atc(self):
        global carted, failed, checkoutnum
        i = 0
        self.sizerange = []
        if self.size == "RANDOM":
            scelta = random.choice(self.connect)
            ciao3 = scelta[0]
            self.group = "".join(ciao3)
            ciao = scelta[1]
            self.var = "".join(ciao)
            ciao2 = scelta[2]
            self.size_chosen = "".join(ciao2)
        elif '-' in self.size:
            self.size1 = self.size.split('-')[0]
            self.size2 = self.size.split('-')[1]
            for x in self.connect:
                taglia = x[2].replace(",", ".")
                if float(self.size1) <= float(taglia) <= float(self.size2):
                    self.sizerange.append(x[2])     
            self.sizerandom = random.choice(self.sizerange)   
            for Traian in self.connect:
                if self.sizerandom in Traian:
                    ciao3 = Traian[0]
                    self.group = "".join(ciao3)
                    ciao = Traian[1]
                    self.var = "".join(ciao)
                    ciao2 = Traian[2]
                    self.size_chosen = "".join(ciao2)  
        elif ',' in self.size:
            self.size1 = self.size.split(',')[0]
            self.size2 = self.size.split(',')[1]
            for x in self.connect:     
                taglia = x[2].replace(",", ".")
                if float(self.size1) <= float(taglia) <= float(self.size2):
                    self.sizerange.append(x[2])    
            self.sizerandom = random.choice(self.sizerange)   
            for Traian in self.connect:
                if self.sizerandom in Traian:
                    ciao3 = Traian[0]
                    self.group = "".join(ciao3)
                    ciao = Traian[1]
                    self.var = "".join(ciao)
                    ciao2 = Traian[2]
                    self.size_chosen = "".join(ciao2)    
        else:
            for Traian in self.connect:
                if self.size in Traian[2]:
                    ciao3 = Traian[0]
                    self.group = "".join(ciao3)
                    ciao = Traian[1]
                    self.var = "".join(ciao)
                    ciao2 = Traian[2]
                    self.size_chosen = "".join(ciao2)
        atc_data = {
            'token': self.token,
            'id_product': self.product_id,
            'id_customization': '0',
            self.group : self.var,
            'qty': '1',
            'add': '1',
            'action': 'update'
        }
        self.warn(f"Adding {self.product} {self.size_chosen} to cart...")
        while True:
            try:   
                r = self.s.post(
                    'https://www.starcowparis.com/panier', 
                    data = atc_data, 
                    allow_redirects = False, 
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    self.warn('Datadome found, proceding...')
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
                    if 'add_to_cart_url' in r.text.lower():
                        self.success(f"Added {self.product} [US {self.size_chosen}] to cart...")
                        carted = carted + 1
                        self.bar()
                        break
                    elif '"Forbidden email address' in r.text:
                        self.warn("Product OOS, retrying...")
                        time.sleep(self.delay)
                        continue
                    elif 'no longer available in this quantity' in r.text.lower():
                        self.warn("Product OOS, retrying...")
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is down, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed getting product page:{r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while preparing session, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue    
            except Exception as e:
                self.error(f'Exception adding to cart: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        if self.country == 'FR':
            self.shipfr()
        else:
            #if self.payment == 'CC':
            #    self.cc()
            #else:
            self.ship()
            
    def shipfr(self):
        global carted, failed, checkoutnum
        self.warn("Getting shipping rates...")
        i = 0
        while True:
            try:
                commandeGet = self.s.get(
                    'https://www.starcowparis.com/commande', 
                    timeout = self.timeout
                )
                if 'Please enable JS' in commandeGet.text:
                    self.dataurl = commandeGet.url                    
                    resp = commandeGet.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    self.warn('Datadome found, proceding...')
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
                elif commandeGet.status_code == 200:
                    prod_xml = bs(commandeGet.text, features='lxml')
                    self.address_id = prod_xml.find('input', {'name': 'id_address_delivery'})['value']
                    address_data = {
                        'id_address_delivery': self.address_id,
                        'confirm-addresses': '1'
                    }
                    addressPost = self.s.post(
                        'https://www.starcowparis.com/commande', 
                        data = address_data, 
                        timeout = self.timeout
                    )
                    if 'Please enable JS' in addressPost.text:
                        self.dataurl = addressPost.url                    
                        resp = addressPost.text
                        self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                        self.hsh = resp.split("hsh':'")[1].split("','")[0]
                        self.sss = resp.split("'s':")[1].split(',')[0]
                        self.ttt = resp.split("'t':'")[1].split("',")[0]
                        if self.ttt == "bv" or i > 1:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()
                            continue
                        self.warn('Datadome found, proceding...')
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
                    elif addressPost.status_code == 200 or 302:
                        shipping_data = {
                            f'delivery_option[{self.address_id}]': '34,',
                            'delivery_message': '',
                            'confirmDeliveryOption': '1'
                        }
                        shippingPost = self.s.post(
                            'https://www.starcowparis.com/commande', 
                            data = shipping_data, 
                            timeout = self.timeout
                        )
                        if 'Please enable JS' in shippingPost.text:
                            self.dataurl = shippingPost.url                    
                            resp = shippingPost.text
                            self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                            self.hsh = resp.split("hsh':'")[1].split("','")[0]
                            self.sss = resp.split("'s':")[1].split(',')[0]
                            self.ttt = resp.split("'t':'")[1].split("',")[0]
                            if self.ttt == "bv" or i > 1:
                                self.error('Proxy banned, rotating...')
                                self.build_proxy()
                                continue
                            self.warn('Datadome found, proceding...')
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
                        elif shippingPost.status_code == 200 or 302:
                            self.success("Successfully got shipping rates...")
                            break
                        elif shippingPost.status_code == 429:
                            self.error('Rate limit, retrying...')
                            self.build_proxy()
                            continue
                        elif shippingPost.status_code >= 500 and shippingPost.status_code <= 600:
                            self.warn('Site is down, retrying...')
                            time.sleep(self.delay)
                            continue
                        else:
                            self.error(f'Failed submitting ship:{shippingPost.status_code}, retrying...')
                            self.build_proxy()
                            time.sleep(self.delay)
                            continue
                    elif addressPost.status_code == 429:
                        self.error('Rate limit, retrying...')
                        self.build_proxy()
                        continue
                    elif addressPost.status_code >= 500 and addressPost.status_code <= 600:
                        self.warn('Site is down, retrying...')
                        time.sleep(self.delay)
                        continue
                    else:
                        self.warn(f"Failed submitting address: {addressPost.status_code}, retrying...")
                        continue
                elif commandeGet.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                elif commandeGet.status_code >= 500 and commandeGet.status_code <= 600:
                    self.warn('Site is down, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.warn(f"Failed submitting address: {commandeGet.status_code}, retrying...")
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while submitting ship, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception submitting ship: {e.__class__.__name__}, retrying...')
                continue   
        #if self.payment == 'CC':
        #    self.cc()
        #else:
        self.ship()

    def ship(self):
        global carted, failed, checkoutnum
        self.warn("Submitting payment...")
        i = 0
        while True:
            try:
                r = self.s.get(
                    'https://www.starcowparis.com/module/ps_checkout/create?credit_card=0&getToken=1', 
                    timeout = self.timeout
                )
                if 'Please enable JS' in r.text:
                    self.dataurl = r.url                    
                    resp = r.text
                    self.initialcid = resp.split("'cid':'")[1].split("','")[0]
                    self.hsh = resp.split("hsh':'")[1].split("','")[0]
                    self.sss = resp.split("'s':")[1].split(',')[0]
                    self.ttt = resp.split("'t':'")[1].split("',")[0]
                    if self.ttt == "bv" or i > 1:
                        self.error('Proxy banned, rotating...')
                        self.build_proxy()
                        continue
                    self.warn('Datadome found, proceding...')
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
                elif r.status_code in (200,302):
                    finaldata = json.loads(r.content)
                    if finaldata['status'] == True:
                        token = finaldata['body']['orderID']
                        self.pp_url = f"https://www.paypal.com/cgi-bin/webscr?useraction=commit&cmd=_express-checkout&token={token}"
                        if 'paypal' in self.pp_url:
                            self.success("Successfully checked out!")
                            checkoutnum = checkoutnum + 1
                            self.bar()
                            break
                    else:
                        self.error("Checkout failed or cart empty, retrying...")
                        failed = failed + 1
                        self.bar()
                        self.getprod()
                        break
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site is down, retrying...')
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Failed getting product page:{r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error while submitting payment, retrying...')
                self.s.cookies.clear()
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while submitting payment: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                continue
        self.pass_cookies()

    def pass_cookies(self):
        try:
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
                    self.accweb = str(self.account)
                    writer.writerow({'SITE':'STARCOW','SIZE':f'{self.size_chosen} {self.accweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.product}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    self.accweb = str(self.account)
                    writer.writerow({'SITE':'STARCOW','SIZE':f'{self.size_chosen} {self.accweb}','PAYLINK':f'{self.token}','PRODUCT':f'{self.product}'})
            self.SuccessPP()
        except Exception as e: 
            self.error(f'Exception error while passing cookies: {e.__class__.__name__}, retrying...') 
            sys.exit(1)

    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name='**STARCOW**', value = self.product, inline = True)
            embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = True)
            embed.add_embed_field(name='**SIZE**', value = str(self.size_chosen), inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = "Paypal", inline = False)    
            embed.add_embed_field(name='**MODE**', value = self.mode, inline = True)
            embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
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
            if self.mode == "SESSION":
                self.accweb = str(self.account)
                self.passweb = "Logged from session"
            else:
                self.accweb = str(self.account)
                self.passweb = str(self.password)
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name='**STARCOW**', value = self.product, inline = True)
            embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = True)
            embed.add_embed_field(name='**SIZE**', value = str(self.size_chosen), inline = True)
            embed.add_embed_field(name='**MODE**', value = self.mode, inline = True)
            embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.accweb}||", inline = False)
            embed.add_embed_field(name='**PASSWORD**', value = f"||{self.passweb}||", inline = True)      
            embed.add_embed_field(name='PAYMENT METHOD', value = "Paypal", inline = False) 
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg") 
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass
    
    #def cc(self):
    #    global carted, failed, checkoutnum
    #    self.warn("Submitting payment...")
    #    i = 0
    #    while True:
    #        try:
    #            r = self.s.get(
    #                'https://www.starcowparis.com/module/ps_checkout/create?credit_card=1&getToken=0', 
    #                timeout = self.timeout
    #            )
    #            if 'Please enable JS' in r.text:
    #                self.dataurl = r.url                    
    #                resp = r.text
    #                self.initialcid = resp.split("'cid':'")[1].split("','")[0]
    #                self.hsh = resp.split("hsh':'")[1].split("','")[0]
    #                self.sss = resp.split("'s':")[1].split(',')[0]
    #                self.ttt = resp.split("'t':'")[1].split("',")[0]
    #                if self.ttt == "bv" or i > 1:
    #                    self.error('Proxy banned, rotating...')
    #                    self.build_proxy()
    #                    continue
    #                self.warn('Datadome found, proceding...')
    #                cid = []
    #                cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
    #                for cookie in cookies:
    #                    if cookie['name'] == "datadome":
    #                        cid.append(cookie)
    #                ciddo = cid[-1]
    #                self.cid = ciddo["value"]
    #                self.connection2()
    #                i = i + 1
    #                continue
    #            elif r.status_code in (200,302):
    #                finaldata = json.loads(r.content)
    #                if finaldata['status'] == True:
    #                    self.orderid = finaldata['body']['orderID']
    #                    self.success('Succesfully submitted payment!')
    #                    break
    #                else:
    #                    self.error("Checkout failed or cart empty, retrying...")
    #                    failed = failed + 1
    #                    self.bar()
    #                    self.getprod()
    #                    break
    #            elif r.status_code == 429:
    #                self.error('Rate limit, retrying...')
    #                self.build_proxy()
    #                continue
    #            elif r.status_code >= 500 and r.status_code <= 600:
    #                self.warn('Site is down, retrying...')
    #                time.sleep(self.delay)
    #                continue
    #            else:
    #                self.error(f'Failed getting product page:{r.status_code}, retrying...')
    #                self.build_proxy()
    #                time.sleep(self.delay)
    #                continue
    #        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    #            self.error('Connection error while submitting payment, retrying...')
    #            self.s.cookies.clear()
    #            self.build_proxy()
    #            continue
    #        except Exception as e:
    #            self.error(f'Exception while submitting payment: {e.__class__.__name__}, retrying...')
    #            self.build_proxy()
    #            continue
    #    self.cc2()
#
    #def cc2(self):
    #    self.decline = False
    #    payload = {
    #        "payment_source": {
    #            "card": {
    #                "number": self.cardnumber,
    #                "expiry": f"{self.year}-{self.month}",
    #                "security_code": f"{self.cvv}",
    #                "attributes": {
    #                    "verification": {
    #                        "method": "SCA_ALWAYS"
    #                    }
    #                }
    #            }
    #        },
    #        "application_context": {
    #            "vault": False
    #        }
    #    }
    #    headers = {
    #        'Braintree-SDK-Version':'3.32.0-payments-sdk-dev',
    #        'Authorization':'Bearer A21AAPb8xlboZKyZvEHxZjSelNgk6fzJhB9VzWTOtqJGsdbCb3RYv0HyyH57sXLSurrmUo4Haj98mnmJlxETPxDTUYr0uUo5g',
    #        #PayPal-Client-Metadata-Id	530d6872954f158cd123a719b3b46d90,
    #        'Content-Type':'application/json',
    #        'Accept':'*/*',
    #        'Origin':'https://assets.braintreegateway.com',
    #        'Referer':'https://assets.braintreegateway.com/'
    #    }
    #    self.warn('Submitting credit card...')
    #    while True:
    #        try:
    #            r = self.s.post(
    #                f'https://cors.api.paypal.com/v2/checkout/orders/{self.orderid}/validate-payment-method',
    #                json = payload,
    #                headers = headers,
    #                timeout = self.timeout
    #            )
    #            if '3ds' in r.text:
    #                break
    #            else:
    #                open(self.logs_path, 'a+').write(f'Submitting credit card - {r.status_code} - {r.text}\n\n')
    #                self.decline = True
    #                break
    #        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    #            self.error('Connection error while submitting payment, retrying...')
    #            self.s.cookies.clear()
    #            self.build_proxy()
    #            continue
    #        except Exception as e:
    #            self.error(f'Exception while submitting credit card: {e.__class__.__name__}, retrying...')
    #            self.build_proxy()
    #            continue
    #    if self.decline: 
    #        self.declined()
    #    else:
    #        self.cc3()
    #
    #def cc3(self):
    #    self.decline = False
    #    headers = {
    #        'Accept':'application/json, text/plain, */*',
    #        'x-requested-with':'XMLHttpRequest'
    #    }
    #    while True:
    #        try:
    #            r = self.s.get(
    #                f'https://www.paypal.com/webapps/helios/payerAction?cart_id={self.orderid}&action_type=THREED_SECURE_ACTION',
    #                timeout = self.timeout
    #            )
    #            if r.status_code == 200:
    #                r_json = json.loads(r.text)
    #                self.acs = r_json['acs_request']
    #                break
    #            else:
    #                open(self.logs_path, 'a+').write(f'Getting 3d info - {r.status_code} - {r.text}\n\n')
    #                self.decline = True
    #                break
    #        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    #            self.error('Connection error while getting 3d info, retrying...')
    #            self.s.cookies.clear()
    #            self.build_proxy()
    #            continue
    #        except Exception as e:
    #            open(self.logs_path, 'a+').write(f'Getting 3d info: {e}\n\n')
    #            self.error(f'Exception while getting 3d info: {e.__class__.__name__}, retrying...')
    #            self.build_proxy()
    #            continue
    #    if self.decline: 
    #        self.declined()
    #    else:
    #        self.cc4()
    #
    #def cc4(self):
    #    self.decline = False
    #    payload = {
    #        'TermUrl':'https://www.paypal.com/webapps/helios/process3DS',
    #        'MD':{"token":f"{self.orderid}"},
    #        'PaReq':self.acs
    #    }
    #    headers = {
    #        'Content-Type':	'application/x-www-form-urlencoded',
    #        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    #    }
    #    while True:
    #        try:
    #            r = self.s.post(
    #                'https://0eaf.cardinalcommerce.com/EAFService/jsp/v1/redirect',
    #                data = payload,
    #                timeout = self.timeout
    #            )
    #            if r.status_code == 200:
    #                self.posturl = r.text.split("action='")[1].split("'")[0]
    #                self.MD = r.text.split("MD' value='")[1].split("'")[0]
    #                self.pareq = r.text.split("PaReq' value='")[1].split("'")[0]
    #                self.termurl = r.text.split("TermUrl' value='")[1].split("'")[0]
    #                break
    #            else:
    #                open(self.logs_path, 'a+').write(f'Getting 3d info - {r.status_code} - {r.text}\n\n')
    #                self.decline = True
    #                break
    #        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    #            self.error('Connection error while getting 3d info, retrying...')
    #            self.s.cookies.clear()
    #            self.build_proxy()
    #            continue
    #        except Exception as e:
    #            open(self.logs_path, 'a+').write(f'Getting 3d info: {e}\n\n')
    #            self.error(f'Exception while getting 3d info: {e.__class__.__name__}, retrying...')
    #            self.build_proxy()
    #            continue
    #    if self.decline: 
    #        self.declined()
    #    else:
    #        self.webhook3d()
    #        asyncio.run(self.main3d())
    #        self.finale()
#
    #async def main3d(self):
#
    #    self.warn("Waiting for 3D secure..")
#
    #    try:
#
    #        chrome = await launch(
    #            handleSIGINT=False,
    #            handleSIGTERM=False,
    #            handleSIGHUP=False,
    #            headless=False,
    #            logLevel='WARNING',
    #            args=[
    #                f'--window-size={750},{750}',
    #                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    #            ]
    #        )
#
    #        page = (await chrome.pages())[0]
    #        await page.setRequestInterception(True)
    #        self._3dsAccepted = False
    #        self._3dsCancelled = False
#
    #        async def intercept(request):
    #            if 'paypal' in request.url:
    #                self._3dsAccepted = True
    #                self.threeddata = request._postData
    #                self.threedheaders = request._headers
    #                self.threedurl = request.url
    #                await request.abort()
    #                await chrome.close()
    #                return True
    #            else:
    #                self._3dsAccepted = False
    #                await request.continue_()
#
    #        page.on('request', lambda req: asyncio.ensure_future(intercept(req)))
    #        script = html.format(self.posturl, self.pareq, self.termurl, self.MD)
    #        await page.evaluate(script)
#
    #        while self._3dsAccepted == False:
    #            try:
    #                dimensions = await page.evaluate('''() => {
    #                    return {
    #                        width: document.documentElement.clientWidth,
    #                        height: document.documentElement.clientHeight,
    #                        deviceScaleFactor: window.devicePixelRatio,
    #                    }
    #                }''')
    #            except Exception as e:
    #                if 'page has been closed' in str(e) and self._3dsAccepted != True:
    #                    self.warn('3DS Window closed.')
    #                    return False
    #            await asyncio.sleep(self.delay)
#
    #    except Exception as e:
    #        self.error(f"Exception while handling 3DS: {e.__class__.__name__}")
    #        return False
    #
    #def finale(self):
    #    self.decline = False
    #    global carted, failed, checkoutnum
    #    self.warn('Finalzing order...')
    #    payload = {
    #        "liabilityShifted": True,
    #        "liabilityShift": "POSSIBLE",
    #        "authenticationStatus": "YES",
    #        "authenticationReason": "SUCCESSFUL",
    #        "orderID": self.orderid,
    #        "fundingSource": "card",
    #        "isHostedFields": True
    #    }
    #    headers = {
    #        'Content-Type':'application/json',
    #        'Accept':'*/*'
    #    }
    #    while True:
    #        try:
    #            r = self.s.post(
    #                'https://www.starcowparis.com/module/ps_checkout/validate',
    #                json = payload,
    #                timeout = self.timeout
    #            )
    #            if 'Please enable JS' in r.text:
    #                self.dataurl = r.url                    
    #                resp = r.text
    #                self.initialcid = resp.split("'cid':'")[1].split("','")[0]
    #                self.hsh = resp.split("hsh':'")[1].split("','")[0]
    #                self.sss = resp.split("'s':")[1].split(',')[0]
    #                self.ttt = resp.split("'t':'")[1].split("',")[0]
    #                if self.ttt == "bv" or i > 1:
    #                    self.error('Proxy banned, rotating...')
    #                    self.build_proxy()
    #                    continue
    #                self.warn('Datadome found, proceding...')
    #                cid = []
    #                cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
    #                for cookie in cookies:
    #                    if cookie['name'] == "datadome":
    #                        cid.append(cookie)
    #                ciddo = cid[-1]
    #                self.cid = ciddo["value"]
    #                self.connection2()
    #                i = i + 1
    #                continue
    #            elif r.status_code == 400:
    #                self.decline = True
    #                r_json = json.loads(r.text)
    #                self.messaggio = r_json['body']['error']['message']
    #                failed = failed + 1
    #                self.bar()
    #                self.error(f'Payment declined! - {self.messaggio}')
    #                break
    #            elif r.status_code == 200:
    #                self.success('Succesfully checked out!')
    #                checkoutnum = checkoutnum + 1
    #                self.bar()
    #                break
    #            else:
    #                open(self.logs_path, 'a+').write(f'Completing checkout - {r.status_code} - {r.text}\n\n')
    #                self.decline = True
    #                break
    #        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    #            self.error('Connection error while completing checkout, retrying...')
    #            self.s.cookies.clear()
    #            self.build_proxy()
    #            continue
    #        except Exception as e:
    #            open(self.logs_path, 'a+').write(f'Completing checkout: {e}\n\n')
    #            self.error(f'Exception while Completing checkout: {e.__class__.__name__}, retrying...')
    #            self.build_proxy()
    #            continue
    #    if self.decline:
    #        self.declined()
    #    else:
    #        self.webhookcc()
#
    #def webhook3d(self):
    #    if self.mode == "SESSION":
    #        self.accweb = str(self.account)
    #        self.passweb = "Logged from session"
    #    else:
    #        self.accweb = str(self.account)
    #        self.passweb = str(self.password)
    #    if self.all_proxies == None:
    #        self.px = 'LOCAL'
    #    webhook = DiscordWebhook(url=self.webhook_url, content = "")
    #    embed = DiscordEmbed(title='Phoenix AIO Success - 3d is waiting for you!', color = 16426522)
    #    embed.add_embed_field(name=f'**STARCOW**', value = self.product, inline = False)
    #    embed.add_embed_field(name='**SIZE**', value = str(self.size_chosen), inline = True)
    #    embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = False) 
    #    embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.accweb}||", inline = True)
    #    embed.add_embed_field(name='**PASSWORD**', value = f"||{self.passweb}||", inline = True)  
    #    embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)    
    #    embed.set_thumbnail(url=self.img)
    #    embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
    #    webhook.add_embed(embed)
    #    webhook.execute()
#
    #def webhookcc(self):
    #    if self.all_proxies == None:
    #        self.px = 'LOCAL'
    #    if self.mode == "SESSION":
    #        self.accweb = str(self.account)
    #        self.passweb = "Logged from session"
    #    else:
    #        self.accweb = str(self.account)
    #        self.passweb = str(self.password)
    #    if self.all_proxies == None:
    #        self.px = 'LOCAL'
    #    webhook = DiscordWebhook(url=self.webhook_url, content = "")
    #    embed = DiscordEmbed(title='Phoenix AIO Success - Succesfully checked out!', color = 4437377)
    #    embed.add_embed_field(name=f'**STARCOW**', value = self.product, inline = False)
    #    embed.add_embed_field(name='**SIZE**', value = str(self.size_chosen), inline = True)
    #    embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = False) 
    #    embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.accweb}||", inline = True)
    #    embed.add_embed_field(name='**PASSWORD**', value = f"||{self.passweb}||", inline = True) 
    #    embed.add_embed_field(name='**ORDER NUMBER**', value = f"||{self.orderid}||", inline = True) 
    #    #embed.add_embed_field(name='**PAYMENT STATUS**', value = f"||{self.statuss}||", inline = True) 
    #    embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)    
    #    embed.set_thumbnail(url=self.img)
    #    embed.set_footer(text = f"Phoenix AIO v {self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
    #    webhook.add_embed(embed)
    #    webhook.execute()
    #    self.Pubblic_WebhookCC()
#
    #def Pubblic_WebhookCC(self):
    #    try:
    #        webhook = DiscordWebhook(url = random.choice(self.listsuccess), content = "")
    #        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
    #        embed.add_embed_field(name='**STARCOW**', value = self.product, inline = True)
    #        embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = True)
    #        embed.add_embed_field(name='**SIZE**', value = str(self.size_chosen), inline = False)
    #        embed.add_embed_field(name='PAYMENT METHOD', value = "Credit Card", inline = True)    
    #        embed.add_embed_field(name='**MODE**', value = self.mode, inline = True)
    #        embed.add_embed_field(name='USER', value = f"<@{self.discord}>", inline = False)
    #        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
    #        webhook.add_embed(embed)
    #        webhook.execute()
    #        try:
    #            playsound('checkout.wav')
    #            sys.exit(1)
    #        except:
    #            sys.exit(1)
    #    except:
    #        pass
#
    #def declined(self):
    #    if self.all_proxies == None:
    #        self.px = 'LOCAL'
    #    if self.mode == "SESSION":
    #        self.accweb = str(self.account)
    #        self.passweb = "Logged from session"
    #    else:
    #        self.accweb = str(self.account)
    #        self.passweb = str(self.password)
    #    if self.all_proxies == None:
    #        self.px = 'LOCAL'
    #    webhook = DiscordWebhook(url=self.webhook_url, content = "")
    #    embed = DiscordEmbed(title='Phoenix AIO - Payment declined!', color = 15746887)
    #    embed.add_embed_field(name=f'**STARCOW**', value = self.product, inline = False)
    #    embed.add_embed_field(name='**SIZE**', value = str(self.size_chosen), inline = True)
    #    embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = False) 
    #    embed.add_embed_field(name='**ACCOUNT**', value = f"||{self.accweb}||", inline = True)
    #    embed.add_embed_field(name='**PASSWORD**', value = f"||{self.passweb}||", inline = True)  
    #    #embed.add_embed_field(name='**ORDER NUMBER**', value = f"||{self.passweb}||", inline = True) 
    #    #embed.add_embed_field(name='**PAYMENT STATUS**', value = f"||{self.messaggio}||", inline = True) 
    #    embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)    
    #    embed.set_thumbnail(url=self.img)  
    #    embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
    #    webhook.add_embed(embed)
    #    webhook.execute()
    #    sys.exit()