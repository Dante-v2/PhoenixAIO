import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml, pytz
from datetime import datetime
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from helheim import helheim, isChallenge
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from binascii import hexlify, unhexlify
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from cryptography.hazmat.backends import default_backend
from Crypto.Cipher import AES
from os import urandom
from autosolveclient.autosolve import AutoSolve
import copy

urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

UNIQUE_ID = int(time.time() * 1000) * 2**random.randint(10,16)
AUTO_SOLVE = None
CAPTCHA_TOKENS = []
CAPTCHA = None

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

class AutoSolveInitialize():
    def __init__(self):

        global AUTO_SOLVE
        global CAPTCHA

        try:
            if CAPTCHA == 'autosolve':
                if any(x == '' for x in [config['autosolve']['access-token'], config['autosolve']['api-key']]):
                    error('You have chosen AutoSolve for captcha solving but didn\'t enter all credentials.')
                    CAPTCHA = next((x for x in ['2captcha', 'anticaptcha', 'capmonster'] if config[x] != ''), None)
                    if not CAPTCHA:
                        error('Please enter at least one captcha provider.')
                        sys.exit()
                    else:
                        warn(f'Using {CAPTCHA}...')
                        return
            else:
                return

            warn('[AUTOSOLVE] - Connecting...')

            auto_solve_factory = AutoSolve({
                "access_token": config['autosolve']['access-token'],
                "api_key": config['autosolve']['api-key'],
                "client_key": "PheonixAIO-cdfbdc31-ca45-4fc7-9989-0dbbcd6c691b",
                "debug": True,
                "should_alert_on_cancel": True
            })

            AUTO_SOLVE = auto_solve_factory.get_instance()
            AUTO_SOLVE.init()
            AUTO_SOLVE.initialized()
            AUTO_SOLVE.emitter.on('AutoSolveResponse', self.handle_token)
            AUTO_SOLVE.emitter.on('AutoSolveResponse_Cancel', self.handle_token_cancel)
            AUTO_SOLVE.emitter.on('AutoSolveError', self.handle_exception)

            info('[AUTOSOLVE] - Successfully connected!')

        except Exception as e:
            error(f'[AUTOSOLVE] - Error connecting: {e}')
    
    def handle_token(self, message):
        CAPTCHA_TOKENS.append(json.loads(message))
    def handle_token_cancel(self, message):
        CAPTCHA_TOKENS.append({"taskId": json.loads(message)["taskId"], "token": "failed"})
    def handle_exception(self, message):
        error(f'[AUTOSOLVE] - Error connecting: {message}')

try:
    CAPTCHA = config['captcha']['footdistrict']
    config['2captcha']
    config['capmonster']
    config['anticaptcha']
except:
    error('Your config file isn\'t updated. Please download the latest one.')
    sys.exit()
else:
    if CAPTCHA == 'autosolve':
        AutoSolveInitialize()
    elif CAPTCHA == '2captcha' and config['2captcha'] == '':
        error('You have chosen 2captcha for captcha solving but didn\'t enter your API key.')
        CAPTCHA = next((x for x in ['anticaptcha', 'capmonster'] if config[x] != ''), None)
    elif CAPTCHA == 'anticaptcha' and config['anticaptcha'] == '':
        error('You have chosen AntiCaptcha for captcha solving but didn\'t enter your API key.')
        CAPTCHA = next((x for x in ['2captcha', 'capmonster'] if config[x] != ''), None)
    elif CAPTCHA == 'capmonster' and config['capmonster'] == '':
        error('You have chosen CapMonster for captcha solving but didn\'t enter your API key.')
        CAPTCHA = next((x for x in ['2captcha', 'anticaptcha'] if config[x] != ''), None)
    elif CAPTCHA not in ['autosolve', '2captcha', 'capmonster', 'anticaptcha']:
        error('Invalid captcha provider selected.')
        CAPTCHA = next((x for x in ['2captcha', 'anticaptcha', 'capmonster'] if config[x] != ''), None)
    if not CAPTCHA:
        error('Please enter at least one captcha provider.')
        sys.exit()
    else:
        warn(f'Using {CAPTCHA}...')

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

class FOOTDISTRICT():

    def __init__(self, row, webhook, version, i, DISCORD_ID):
        
        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'footdistrict/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "footdistrict/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()
        except:
            self.error("Failed To Read Proxies File - using no proxies ")
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
        self.mail = row['MAIL']
        self.name = row['NAME']
        self.password = row['PASSWORD']
        self.surname = row['SURNAME']
        self.country = row['COUNTRY']
        self.address = row['ADDRESS']
        self.zipcode = row['ZIPCODE']
        self.city = row['CITY']
        self.region = row['REGION']
        self.phone = row['PHONE']
        self.webhook_url = webhook
        self.threadID = '%03d' % i
        self.payment = row['PAYMENT']
        self.mode = row['MODE']
        self.cardnumber = row['CARD NUMBER']
        self.month = row['EXP MONTH']
        self.year = row['EXP YEAR']
        self.cvv = row['CVC']
        self.regioncode = ''
        self.regionid = ''

        if self.mode == 'FAST':
            self.warn('Setting up FAST mode...')
            self.harvestedTokens = []
            threading.Thread(target=self.handleHarvester).start()
            for i in range(8):
                threading.Thread(target=self.harvest_v3, args=([self.link, i])).start()
        
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        self.timeout = 120
        self.monster = config['capmonster']
        self.balance = balancefunc()
        self.version = version
        self.bar()
        self.discord = DISCORD_ID
        self.build_proxy()
        

        if ".de" in self.link:
            link = self.link.replace(".de",".com")
            self.link = link
        if ".pt" in self.link:
            link = self.link.replace(".pt",".com")
            self.link = link
        if ".nl" in self.link:
            link = self.link.replace(".nl",".com")
            self.link = link
        if "com/fr" in self.link:
            link = self.link.replace("com/fr","com")
            self.link = link
        if ".it" in self.link:
            self.origin = "https://footdistrict.it"
        else:
            self.origin = "https://footdistrict.com"
        
        self.delay = int(config['delay'])
        
        if self.country == 'DE':
            if self.region == 'Baden-Wurttemberg':
                self.regionid = '80'
                self.regioncode = 'BAW'
            if self.region == 'Bayern':
                self.regionid = '81'
                self.regioncode = 'BAY'
            if self.region == 'Berlin':
                self.regionid = "82"
                self.regioncode = "BER"
            if self.region == 'Brandenburg':
                self.regionid = "83"
                self.regioncode = "BRG"
            if self.region == 'Bremen':
                self.regionid = "84"
                self.regioncode = "BRE"
            if self.region == 'Hamburg':
                self.regionid = '85'
                self.regioncode = 'HAM'
            if self.region == 'Hessen':
                self.regionid = '86'
                self.regioncode = 'HES'
            if self.region == 'Mecklenburg-Vorpommern':
                self.regionid = '87'
                self.regioncode = 'MEC'
            if self.region == 'Niedersachsen':
                self.regionid = '79'
                self.regioncode = 'NDS'
            if self.region == 'Nordrhein-Westfalen':
                self.regionid = '88'
                self.regioncode = 'NRW'
            if self.region == 'Rheinland-Pfalz':
                self.regionid = '89'
                self.regioncode = 'RHE'
            if self.region == 'Saarland':
                self.regioncode = 'SAR'
                self.regionid = '90'
            if self.region == 'Sachsen':
                self.regioncode = 'SAS'
                self.regionid = '91'
            if self.region == 'Sachsen-Anhalt':
                self.regionid = '92'
                self.regioncode = 'SAC'
            if self.region == 'Schleswig-Holstein':
                self.regionid = '93'
                self.regioncode = 'SCN'
            if self.region == 'Thuringen':
                self.regionid = '94'
                self.regioncode = 'THE'

        if self.country == 'FR':
            if self.region == 'Ain':
                self.regioncode = '1'
                self.regionid = '182'
            
            if self.region == 'Aisne':
                self.regioncode = '2'
                self.regionid = '183'

            if self.region == 'Allier':
                self.regioncode = '3'
                self.regionid = '184'

            if self.region == 'Alpes-de-Haute-Provence':
                self.regioncode = '4'
                self.regionid = '185'

            if self.region == 'Alpes-Maritimes':
                self.regioncode = '6'
                self.regionid = '187'

            if self.region == 'Ardeche':
                self.regionid = '7'
                self.regioncode = '188'

            if self.region == 'Ardennes':
                self.regionid = '8'
                self.regioncode = '189'

            if self.region == 'Ariege':
                self.regionid = '9'
                self.regioncode = '190'
            
            if self.region == 'Aube':
                self.regioncode = '191'
                self.regionid = '10'
            
            if self.region == 'Aude':
                self.regionid = '11'
                self.regioncode = '192'

            if self.region == 'Aveyron':
                self.regionid = '12'
                self.regioncode = '193'
            
            if self.region == 'Bas-Rhin':
                self.regionid = '67'
                self.regioncode = '249'
            
            if self.region == 'Bouches-du-Rhone':
                self.regionid = '13'
                self.regioncode = '194'
            
            if self.region == 'Calvados':
                self.regionid = '14'
                self.regioncode = '195'
            
            if self.region == 'Cantal':
                self.regionid = '15'
                self.regioncode = '196'
            
            if self.region == 'Charente':
                self.regionid = '16'
                self.regioncode = '197'
            
            if self.region == 'Charente-Maritime':
                self.regionid = '17'
                self.regioncode = '198'
            
            if self.region == 'Cher':
                self.regionid = '18'
                self.regioncode = '199'
            
            if self.region == 'Correze':
                self.regionid = '19'
                self.regioncode = '200'
            
            if self.region == 'Corse-du-Sud':
                self.regionid = '2A'
                self.regioncode = '201'
            
            if self.region == "Cote-d'Or":
                self.regionid = '21'
                self.regioncode = '203'
            
            if self.region == "Cotes-d'Armor":
                self.regionid = '22'
                self.regioncode = '204'
            
            if self.region == 'Creuse':
                self.regionid = '23'
                self.regioncode = '205'
            
            if self.region == 'Deux-Sevres':
                self.regionid = '79'
                self.regioncode = '261'
            
            if self.region == 'Dordogne':
                self.regionid = '24'
                self.regioncode = '206'
            
            if self.region == 'Doubs':
                self.regionid = '25'
                self.regioncode = '207'
            
            if self.region == 'Drome':
                self.regionid = '26'
                self.regioncode = '208'
            
            if self.region == 'Essonne':
                self.regionid = '91'
                self.regioncode = '273'
            
            if self.region == 'Eure':
                self.regionid = '27'
                self.regioncode = '209'
            
            if self.region == 'Eure-et-Loir':
                self.regionid = '28'
                self.regioncode = '210'
            
            if self.region == 'Finistere':
                self.regionid = '29'
                self.regioncode = '211'
            
            if self.region == 'Gard':
                self.regionid = '30'
                self.regioncode = '212'
            
            if self.region == 'Gers':
                self.regionid = '32'
                self.regioncode = '214'
            
            if self.region == 'Gironde':
                self.regionid = '33'
                self.regioncode = '215'
            
            if self.region == 'Haut-Rhin':
                self.regionid = '68'
                self.regioncode = '250'
            
            if self.region == 'Haute-Corse':
                self.regionid = '2B'
                self.regioncode = '202'
            
            if self.region == 'Haute-Garonne':
                self.regionid = '31'
                self.regioncode = '213'
            
            if self.region == 'Haute-Loire':
                self.regionid = '43'
                self.regioncode = '225'
            
            if self.region == 'Haute-Marne':
                self.regionid = '52'
                self.regioncode = '234'
            
            if self.region == 'Haute-Saone':
                self.regionid = '70'
                self.regioncode = '252'
            
            if self.region == 'Haute-Savoie':
                self.regionid = '74'
                self.regioncode = '256'
            
            if self.region == 'Haute-Vienne':
                self.regionid = '87'
                self.regioncode = '269'
            
            if self.region == 'Hautes-Alpes':
                self.regionid = '5'
                self.regioncode = '186'
            
            if self.region == 'Hauts-de-Seine':
                self.regionid = '92'
                self.regioncode = '274'
            
            if self.region == 'Herault':
                self.regionid = '34'
                self.regioncode = '216'
            
            if self.region == 'Ille-et-Vilaine':
                self.regionid = '35'
                self.regioncode = '217'
            
            if self.region == 'Indre':
                self.regionid = '36'
                self.regioncode = '218'
            
            if self.region == 'Indre-et-Loire':
                self.regionid = '37'
                self.regioncode = '219'
            
            if self.region == 'Isere':
                self.regionid = '38'
                self.regioncode = '220'
            
            if self.region == 'Jura':
                self.regionid = '39'
                self.regioncode = '221'
            
            if self.region == 'Landes':
                self.regionid = '40'
                self.regioncode = '222'
            
            if self.region == 'Loir-et-Cher':
                self.regionid = '41'
                self.regioncode = '223'
            
            if self.region == 'Loire':
                self.regionid = '42'
                self.regioncode = '224'
            
            if self.region == 'Loire-Atlantique':
                self.regionid = '44'
                self.regioncode = '226'
            
            if self.region == 'Loiret':
                self.regionid = '45'
                self.regioncode = '227'
            
            if self.region == 'Lot':
                self.regionid = '46'
                self.regioncode = '228'
            
            if self.region == 'Lot-et-Garonne':
                self.regionid = '47'
                self.regioncode = '229'
            
            if self.region == 'Lozere':
                self.regionid = '48'
                self.regioncode = '230'
            
            if self.region == 'Maine-et-Loire':
                self.regionid = '49'
                self.regioncode = '231'
            
            if self.region == 'Manche':
                self.regionid = '50'
                self.regioncode = '232'
            
            if self.region == 'Marne':
                self.regionid = '51'
                self.regioncode = '233'
            
            if self.region == 'Mayenne':
                self.regionid = '53'
                self.regioncode = '235'
            
            if self.region == 'Meurthe-et-Moselle':
                self.regionid = '54'
                self.regioncode = '236'
            
            if self.region == 'Meuse':
                self.regionid = '55'
                self.regioncode = '237'
            
            if self.region == 'Morbihan':
                self.regionid = '56'
                self.regioncode = '238'
            
            if self.region == 'Moselle':
                self.regionid = '57'
                self.regioncode = '239'
            
            if self.region == 'Nievre':
                self.regionid = '58'
                self.regioncode = '240'
            
            if self.region == 'Nord':
                self.regionid = '59'
                self.regioncode = '241'
            
            if self.region == 'Oise':
                self.regionid = '60'
                self.regioncode = '242'
            
            if self.region == 'Orne':
                self.regionid = '61'
                self.regioncode = '243'
            
            if self.region == 'Paris':
                self.regionid = '75'
                self.regioncode = '257'
            
            if self.region == 'Pas-de-Calais':
                self.regionid = '62'
                self.regioncode = '244'
            
            if self.region == 'puy de dome':
                self.regionid = '63'
                self.regioncode = '245'
            
            if self.region == 'pyrenees-atlantiques':
                self.regionid = '64'
                self.regioncode = '246'
            
            if self.region == 'Pyrenees-Orientales':
                self.regionid = '66'
                self.regioncode = '248'
            
            if self.region == 'Rhone':
                self.regionid = '69'
                self.regioncode = '251'
            
            if self.region == 'Saene-et-Loire':
                self.regionid = '71'
                self.regioncode = '253'
            
            if self.region == 'Sarthe':
                self.regionid = '72'
                self.regioncode = '254'
            
            if self.region == 'Savoie':
                self.regionid = '73'
                self.regioncode = '255'
            
            if self.region == 'Seine-et-Marne':
                self.regionid = '77'
                self.regioncode = '259'
            
            if self.region == 'Seine-Maritime':
                self.regionid = '76'
                self.regioncode = '258'
            
            if self.region == 'Seine-Saint-Denis':
                self.regionid = '93'
                self.regioncode = '275'
            
            if self.region == 'Somme':
                self.regionid = '80'
                self.regioncode = '262'
            
            if self.region == 'Tarn':
                self.regionid = '81'
                self.regioncode = '263'
            
            if self.region == 'Tarn-et-Garonne':
                self.regionid = '82'
                self.regioncode = '264'
            
            if self.region == 'Territoire-de-Belfort':
                self.regionid = '90'
                self.regioncode = '272'
            
            if self.region == "Val-d'Oise":
                self.regionid = '95'
                self.regioncode = '277'
            
            if self.region == 'Val-de-Marne':
                self.regionid = '94'
                self.regioncode = '276'
            
            if self.region == 'Var':
                self.regionid = '83'
                self.regioncode = '265'
            
            if self.region == 'Vaucluse':
                self.regionid = '84'
                self.regioncode = '266'
            
            if self.region == 'vendee':
                self.regionid = '85'
                self.regioncode = '267'
            
            if self.region == 'Vienne':
                self.regionid = '86'
                self.regioncode = '268'
            
            if self.region == 'Vosges':
                self.regionid = '88'
                self.regioncode = '270'
            
            if self.region == 'Yonne':
                self.regionid = '89'
                self.regioncode = '271'
            
            if self.region == 'Yvelines':
                self.regionid = '78'
                self.regioncode = '260'

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
            self.error(e)

        while CAPTCHA == 'autosolve' and not AUTO_SOLVE:
            time.sleep(1)
        self.warn('Starting tasks...')
        self.start()

    def handleHarvester(self):
        while True:
            for token in copy.deepcopy(self.harvestedTokens):
                if int(time.time()) + 5 > token['expiry']:
                    self.harvestedTokens.remove(token)
                    #info(f'[TASK {self.threadID}] [FOOTDISTRICT] - [FAST] - Available tokens: {len(self.harvestedTokens)}')
                    threading.Thread(target=self.harvest_v3, args=([self.link, 0]))
            time.sleep(5)

    def solve_v3(self, url):
        if CAPTCHA == '2captcha':
            try:
                solver = TwoCaptcha(config['2captcha'])
                result = solver.recaptcha(sitekey='6LdzsasUAAAAACSrKEv5nVgCb6LYeL11-5bxBq8N', url=url, version='v3', action='formularios')
                code = result['code']
                return code
            except Exception as e:
                self.error(f' Exception solving captcha: {e}')
                return self.solve_v3(url)
        elif CAPTCHA == 'capmonster':
            try:
                captchaurl = "https://api.capmonster.cloud/createTask"
                payload = {
                    "clientKey": config['capmonster'],
                    "task": {
                        "type":"RecaptchaV3TaskProxyless",
                        "websiteURL": url,
                        "websiteKey":"6LdzsasUAAAAACSrKEv5nVgCb6LYeL11-5bxBq8N",
                        "minScore": 0.5,
                        "pageAction": "formularios"
                    }
                }
                r = requests.post(captchaurl, json = payload)
                taskid = r.text.split('"taskId":')[1].split('}')[0]
                data = {
                    "clientKey": config['capmonster'],
                    "taskId": taskid
                }
                r = requests.post("https://api.capmonster.cloud/getTaskResult", json = data)
                i = 0
                while not "ready" in r.text and i < 30:
                    time.sleep(5)
                    i += 1
                    r = requests.post("https://api.capmonster.cloud/getTaskResult", json = data)
                if "ready" in r.text:
                    self.success('Captcha solved!')
                    code = r.text.split('"gRecaptchaResponse":"')[1].split('"')[0]
                    return code
                else:
                    self.error('Failed solving captcha!')
                    return self.solve_v3(url)
            except Exception as e:
                self.error(f'Exception solving captcha: {e}')
                return self.solve_v3(url)
        elif CAPTCHA == 'autosolve':
            try:
                AUTO_SOLVE.send_token_request({
                    "taskId"  : f'{self.threadID}-{UNIQUE_ID}', 
                    "url"     : url, 
                    "siteKey" : "6LdzsasUAAAAACSrKEv5nVgCb6LYeL11-5bxBq8N", 
                    "version" : '2',
                    "action"  : 'formularios',
                    "minScore": 0.5
                })
                while True:
                    for token in CAPTCHA_TOKENS:
                        if token['taskId'] == f'{self.threadID}-{UNIQUE_ID}':
                            if token['token'] != 'failed':
                                CAPTCHA_TOKENS.remove(token)
                                return token['token']
                            else:
                                self.error('Autosolve captcha solve failed')
                                return self.solve_v3(url)
                    time.sleep(1)
            except Exception as e:
                self.error(f'An error occured solving captcha with Autosolve: {e}')
                return self.solve_v3(url)

    def harvest_v3(self, url, i):
        time.sleep(5 * i)
        code = self.solve_v3(url)
        self.success(f'Token harvested. Available tokens: {len(self.harvestedTokens) + 1}')
        return self.harvestedTokens.append({'token': code, 'expiry': int(time.time()) + 90})

    # Red logging

    def error(self, text):
        message = f'[TASK {self.threadID}] - [FOOTDISTRICT] - {text}'
        error(message)

    # Green logging

    def success(self, text):
        message = f'[TASK {self.threadID}] - [FOOTDISTRICT] - {text}'
        info(message)

    # Yellow logging

    def warn(self, text):
        message = f'[TASK {self.threadID}] - [FOOTDISTRICT] - {text}'
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
                f'Phoenix AIO {self.version} - Running FOOTDISTRICT | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - Running FOOTDISTRICT | 2cap Balance: {self.balance} | Carted: {carted} | Checkout: {checkoutnum} | Failed: {failed}\x07')

    def injection(self, session, response):
        self.bar()
        try:
            if isChallenge(response):
                self.warn('Solving Cloudflare v2')
                return helheim('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693', session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                self.warn('Solving Cloudflare v2 api 2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.warn('Solving Cloudflare v2 api 2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
            else:
                return response


################################################################################################################################# - GET AL PRODOTTO


    def execjs(self):
        self.warn('Getting cookies...')
        a = unhexlify(self.parteA)
        b = unhexlify(self.parteB)
        c = unhexlify(self.parteC)
        mode = int(self.testocookies.split('toHex(slowAES.decrypt(c,')[1].split(',a,b))')[0])
        modes = [AES.MODE_OFB, AES.MODE_CFB, AES.MODE_CBC]
        decipher = AES.new(a, modes[mode], b) #key, mode, iv
        cookie = hexlify(decipher.decrypt(c)).decode() # data
        self.cookiepart2 = cookie
        return self.success('Succesfully got cookies!')

    def cookiesolve(self):
        while True:
            try:
                r = self.s.get(
                    'https://footdistrict.com/',
                    timeout=self.timeout
                )                
                if r.status_code == 307:
                    cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
                    try:
                        for element in cookies:
                            if self.cookiepart1 in element['name']:
                                cookies.remove(element)
                    except:
                        pass
                    self.cookiepart1 = r.text.split('document.cookie="')[1].split('=')[0]
                    self.testocookies = r.text
                    self.parteA = str(r.text.split('a=toNumbers("')[1].split('"')[0])
                    self.parteB = str(r.text.split('b=toNumbers("')[1].split('"')[0])
                    self.parteC = str(r.text.split('c=toNumbers("')[1].split('"')[0])
                    self.execjs()
                    self.cookie_obj = requests.cookies.create_cookie(domain="footdistrict.com",name=self.cookiepart1,value=self.cookiepart2)
                    self.s.cookies.set_cookie(self.cookie_obj)
                    break
                else:
                    break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.build_proxy()
                self.error(f'Exception while getting cookies {e}, retrying...')
                time.sleep(self.delay)
                continue
        return self.success('Got cookies!')

    def start(self):
        self.warn('Connecting to Footdistrict...')
        while True:
            try:
                r = self.s.get(
                    'https://footdistrict.com/',
                    timeout=self.timeout
                )
                if r.status_code == 307:
                    self.cookiepart1 = r.text.split('document.cookie="')[1].split('=')[0]
                    self.testocookies = r.text
                    self.parteA = str(r.text.split('a=toNumbers("')[1].split('"')[0])
                    self.parteB = str(r.text.split('b=toNumbers("')[1].split('"')[0])
                    self.parteC = str(r.text.split('c=toNumbers("')[1].split('"')[0])
                    self.execjs()
                    self.cookie_obj = requests.cookies.create_cookie(domain="footdistrict.com",name=self.cookiepart1,value=self.cookiepart2)
                    self.s.cookies.set_cookie(self.cookie_obj)
                r = self.s.get(
                    'https://footdistrict.com/customer/account/login/',
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    self.formkey = r.text.split('name="form_key" type="hidden" value="')[1].split('"')[0]
                    self.success('Connected to Footdistrict!')
                    break
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while connecting to fd {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while connecting to fd: {e}, retrying...')
                time.sleep(self.delay)
                continue
        self.login()

    def login(self):
        self.warn('Logging in...')
        while True:
            try:
                self.warn('Solving captcha v3...')
                code = self.solve_v3('https://footdistrict.com/customer/account/login/')
                self.success('Captcha solved!')
                payload = {
                    'form_key': self.formkey,
                    'login[username]': self.mail,
                    'login[password]': self.password,
                    'login[accept_gdpr]': '1',
                    'send': '',
                    'v3-recaptcha-response': code
                }
                r = self.s.post(
                    "https://footdistrict.com/customer/account/loginPost/", 
                    data= payload, 
                    allow_redirects=False,
                    timeout=self.timeout
                )
                if r.status_code == 302 and r.headers['location'] == 'https://footdistrict.com/customer/account/':
                    self.success('Successfully logged in!')
                    break
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while logging in {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                continue
            except Exception as e:
                self.error(f'Exception while logging in: {e.__class__.__name__}, retrying...')
                time.sleep(self.delay)
                continue
        self.getprod()

    def getprod(self):
        self.warn('Getting product...')
        self.verifedonly = False
        self.stop = False
        while True:
            try:
                r = self.s.get(
                    self.link,
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    if 'This product can only be viewed from the country where you are verified' in r.text:
                        self.error('This product can only be viewed from the country where you are verified, rotating proxy...')
                        self.build_proxy()
                        continue
                    try:
                        try:
                            self.hash = r.text.split('hash" value="')[1].split('"')[0]
                        except:
                            self.hash = ''
                        if self.hash != '':
                            self.ipp = r.text.split('ip" value="')[1].split('"')[0]
                            self.countryyy = r.text.split('country" value="')[1].split('"')[0]
                            self.addatc = r.text.split('address" value="')[1].split('"')[0]
                            self.telef = r.text.split('phone" value="')[1].split('"')[0]
                            self.countrycode = r.text.split('country_code" value="')[1].split('"')[0]
                            self.custommer = r.text.split('customer" value="')[1].split('"')[0]
                            self.verifedonly = True
                        else:
                            self.warn('Getting customer info...')
                            self.s.headers.update({
                                'Accept': 'application/json, text/javascript, */*; q=0.01'
                            })
                            v = self.s.get(
                                f'https://footdistrict.com/customer/section/load/?sections=customer&force_new_section_timestamp=false&_={int(time.time() * 1000)}',
                                timeout=120
                            )
                            if v.status_code == 200:
                                try:
                                    l = json.loads(v.text)
                                    self.ipp = l['customer']['ip']
                                    self.countryyy = l['customer']['country']
                                    self.addatc = l['customer']['address']
                                    self.telef = l['customer']['phone']
                                    self.countrycode = l['customer']['country_code']
                                    self.custommer = l['customer']['id']
                                    self.hash = l['customer']['hash']
                                    self.status = l['customer']['status']
                                    if self.status == 'approved':
                                        self.verifedonly = True
                                    self.success('Succesfully got customer info!')
                                except:
                                    self.error('Account flagged, cant atc this product...')
                                    self.stop = True
                                    break
                            elif v.status_code == 307:
                                self.cookiesolve()
                                continue
                            elif v.status_code >= 500 and v.status_code <= 600:
                                self.warn('Site dead, retrying...')
                                time.sleep(self.delay)
                                continue
                            elif v.status_code == 403:
                                self.error('Proxy banned, rotating...')
                                self.build_proxy()
                                self.cookiesolve()
                                continue
                            elif v.status_code == 404:
                                self.error('Page not loaded, retrying...')
                                time.sleep(self.delay)
                                continue
                            elif v.status_code == 429:
                                self.error('Rate limit, retrying...')
                                self.build_proxy()
                                self.cookiesolve()
                                time.sleep(self.delay)
                                continue
                            else:
                                self.error(f'Error while logging in {v.status_code}, retrying...')
                                self.build_proxy()
                                self.cookiesolve()
                                time.sleep(self.delay)
                                continue
                        self.success('Succesfully got product page!')
                        json1 = (r.text.split('"data": ')[1].split('}     ')[0]) + "}"
                        pid = json1.split('"items":{"')[1].split('"')[0]
                        self.price = json1.split('final_price":')[1].split(',')[0]
                        soup = bs(r.text, features='lxml')
                        tit = json.loads(json1)
                        title = tit['items'][pid]['name']
                        try:
                            try:
                                self.formkey = soup.find('div',{'class':'product-add-form'}).find('form',{'method':'post'}).find('input',{'name':'form_key'})['value']
                            except:
                                self.formkey = soup.find('div',{'class':'product-add-form'}).find('form',{'id':'product_addtocart_form'}).find('input',{'name':'form_key'})['value']
                        except:
                            self.warn(f'{title} OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        jsonvarianti = r.text.split('AEC.SUPER = [')[1].split('}]}];')[0] + '}]}'
                        jsonvarianti = json.loads(jsonvarianti)
                        jsoninstock = r.text.split('AEC.CONFIGURABLE_SIMPLES = ')[1].split('};')[0] + '}'
                        try:
                            jsoninstock = json.loads(jsoninstock)
                        except:
                            self.warn(f'{title} OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        sizeinstock = []
                        try:
                            for c in jsoninstock.keys():
                                sizeinstockconnome = jsoninstock[c]['id']
                                if '.5' in sizeinstockconnome or '/3' in sizeinstockconnome:
                                    sizeinstockconnome = sizeinstockconnome[-7:]
                                else:
                                    sizeinstockconnome = sizeinstockconnome[-5:]
                                try:
                                    sizeinstockconnome = sizeinstockconnome.split("-")[1]
                                    if 'Ú' in sizeinstockconnome:
                                        sizeinstock.append(sizeinstockconnome.replace('Ú','U'))
                                    else:
                                        sizeinstock.append(sizeinstockconnome)
                                except:
                                    if '-' in sizeinstockconnome:
                                        sizeinstockconnome = sizeinstockconnome.split("-")[1]
                                    else:
                                        if 'Ú' in sizeinstockconnome:
                                            sizeinstock.append(sizeinstockconnome.replace('Ú','U'))
                                        else:
                                            sizeinstock.append(sizeinstockconnome)
                        except:
                            self.warn(f'{title} OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        idboh = jsonvarianti['id']
                        sizes = []
                        values_index = []
                        attributes = []
                        self.sup = idboh
                        for c in sizeinstock:
                            for options in jsonvarianti['options']:
                                if options['label'] == c:
                                    sizes.append(c)
                                    values_index.append(options['value_index'])
                                    attributes.append(options['product_super_attribute_id'])
                        conf = r.text.replace('\n', '').split('"jsonConfig": ')[1].split(',                "jsonSwatchConfig"')[0]
                        k = json.loads(conf)
                        m = k['attributes'][f'{self.sup}']['options']
                        atts = []
                        for i in m:
                            try:
                                atts.append(i['products'][0])
                            except:
                                pass
                        completo = zip(sizes, values_index, attributes, atts)
                        self.fullsizelist = list(completo)
                        if len(sizes) < 1:
                            self.warn(f'{title} OOS, monitoring...')
                            time.sleep(self.delay)
                            continue
                        else:
                            if self.size == "RANDOM":
                                pass
                            elif '-' in self.size:
                                self.sizerange = []
                                self.size1 = str(self.size.split('-')[0])
                                self.size2 = str(self.size.split('-')[1])
                                for x in self.fullsizelist:
                                    if self.size1 <= str(x[0]) <= self.size2:
                                        self.sizerange.append(x)     
                                pass
                            elif ',' in self.size:
                                self.sizerange = []
                                self.size1 = str(self.size.split(',')[0])
                                self.size2 = str(self.size.split(',')[1])
                                for x in self.fullsizelist:
                                    if self.size1 <= str(x[0]) <= self.size2:
                                        self.sizerange.append(x)  
                                pass
                            else:
                                self.sizespecifica = []
                                for x in self.fullsizelist:
                                    if self.size == x[0]:
                                        self.sizespecifica.append(x)
                                if len(self.sizespecifica) < 1:
                                    self.warn(f'{title} {self.size}, monitoring...')
                                    time.sleep(self.delay)
                                    continue
                                else:
                                    pass
                        json1 = json.loads(json1)
                        aoo = json1['items'][pid]['add_to_compare_button']['url']
                        self.uenc = aoo.split('"uenc\":\"')[1].split('"')[0]
                        self.success(f'{title} in stock! {sizeinstock}')
                        self.pid = pid
                        self.title = title
                        break
                    
                    except Exception as e:
                        self.error(f'Exception parsing product: {e}, retrying...')
                        time.sleep(self.delay)
                        continue
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting product: {r.status_code}, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception getting product: {e}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                time.sleep(self.delay)
                continue
        if self.stop:
            sys.exit(1)
        self.atc()

    def atc(self):
        global failed, checkoutnum, carted
        self.cookie_obj = requests.cookies.create_cookie(domain="footdistrict.com",name='form_key',value=self.formkey)
        self.s.cookies.set_cookie(self.cookie_obj)
        if self.size == "RANDOM":
            self.scelto = random.choice(self.fullsizelist)
        elif '-' in self.size:
            self.scelto = random.choice(self.sizerange)
        elif ',' in self.size:
            self.scelto = random.choice(self.sizerange)
        elif self.sizespecifica:
            self.scelto = random.choice(self.sizespecifica)
        while True:
            try:
                if self.mode == 'FAST':
                    if len(self.harvestedTokens) == 0:
                        self.warn('Solving captcha v3...')
                        code = self.solve_v3(self.link)
                        self.success('Captcha solved!')
                        code = self.solve_v3(self.link)
                    else:
                        self.success('Using harvested token')
                        code = self.harvestedTokens.pop(0)['token']
                else:
                    self.warn('Solving captcha v3...')
                    code = self.solve_v3(self.link)
                    self.success('Captcha solved!')
                if self.verifedonly:
                    payload = {
                        'product':self.pid,
                        'selected_configurable_option':'',
                        'related_product':'',
                        'item':self.pid,
                        'product_size':self.scelto[0],
                        'simple_id':self.scelto[3],
                        'release':'1',
                        'customer':self.custommer,
                        'country_code':self.countrycode,
                        'phone':self.telef,
                        'address':self.addatc,
                        'country':self.countryyy,
                        'ip':self.ipp,
                        'hash':self.hash,
                        'form_key':self.formkey,
                        f'super_attribute[{self.sup}]':self.scelto[1],
                        'v3-recaptcha-response':code,
                        'additional_data[java_enabled]':'false',
                        'additional_data[screen_color_depth]':'24',
                        'additional_data[screen_width]':'1920',
                        'additional_data[screen_height]':'1080',
                        'additional_data[timezone_offset]':'-120',
                        'additional_data[language]':'en'
                    }
                else:
                    payload = {
                        'product': self.pid,
                        'selected_configurable_option': '',
                        'related_product': '',
                        'item': self.pid,
                        'form_key': self.formkey,
                        f'super_attribute[{self.sup}]': self.scelto[1],
                        'v3-recaptcha-response': code
                    }
                self.warn(f'Adding to cart size {self.scelto[0]}...')
                if self.verifedonly:
                    r = self.s.post(
                        'https://footdistrict.com/premium/popup/add/',
                        data = payload,
                        timeout = self.timeout
                    )
                else:
                    r = self.s.post(
                        f"https://footdistrict.com/checkout/cart/add/uenc/{self.uenc}/product/{self.pid}/", 
                        data = payload,
                        timeout=self.timeout,
                        allow_redirects=False
                    )
                if r.status_code == 200 and '"success":true' in r.text:
                    oos = False
                    if self.verifedonly:
                        x = json.loads(r.text)
                        self.premium = x['premium']
                    self.success('Added to cart!')
                    carted = carted + 1
                    self.bar()
                    break
                elif r.status_code == 302:
                    try:
                        if 'mage-messages' in r.headers['set-cookie']:
                            if all([x in r.headers['set-cookie'].split('mage-messages=')[1].split('; expires')[0] for x in ['success', 'checkout']]):
                                self.success('Added to cart!')
                                carted = carted + 1
                                self.bar()
                                oos = False
                                break
                            else:
                                self.error('Error adding to cart, product probably OOS')
                                oos = True
                                break
                        else:
                            self.error('Error adding to cart, product probably OOS')
                            oos = True
                            break
                    except:
                        self.error('Error adding to cart, product probably OOS')
                        oos = True
                        break
                elif r.status_code == 200:
                    self.error('Error adding to cart, product probably OOS')
                    oos = True
                    break
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while adding to cart: {r.status_code}, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception adding to cart: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                time.sleep(self.delay)
                continue
        if oos:
            self.getprod()
        else:
            if self.verifedonly:
                self.pay2()
            else:
                if self.payment == 'PP':
                        self.pp()
                else:
                    self.onstep() 

    def onstep(self):
        self.warn('Getting checkout page...')
        self.s.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        })
        while True:
            try:
                r = self.s.get(
                    "https://footdistrict.com/onestepcheckout/",
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    try:
                        self.entity = r.text.split('"entity_id":"')[1].split('"')[0]
                    except:
                        self.error('Product oos while checking out!')
                        self.s.cookies.clear()
                        self.build_proxy()
                        self.start()
                        break
                    self.success('Got checkout page!')
                    break
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting checkout page: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while getting checkout page: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
        if self.verifedonly:
            self.ratesverfiedonly()
        else:
            self.rates()

    def ratesverfiedonly(self):
        self.warn('Getting shipping rates...')
        self.s.headers.update({
                'Accept': '*/*',
                'x-requested-with': 'XMLHttpRequest'
        })
        payload = {"addressId":self.addatc}
        while True:
            try:
                r = self.s.post(
                    f"https://footdistrict.com/rest/es/V1/carts/mine/estimate-shipping-methods-by-address-id", 
                    json = payload,
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    self.success('Succesfully got shipping rates!')
                    self.carrier_code = r.text.split('carrier_code":"')[1].split('"')[0]
                    self.method_code = r.text.split('method_code":"')[1].split('"')[0]
                    break
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    error(f'Error while getting shipping rates: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while getting shipping rates: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
        self.ccverify()

    def rates(self):
        self.s.headers.update({
                'Accept': '*/*',
                'x-requested-with': 'XMLHttpRequest'
        })
        self.warn('Getting shipping rates...')
        payload = {"address":{"street":[self.address],"city":self.city,"region":self.region,"country_id":self.country,"postcode":self.zipcode,"firstname":self.name,"lastname":self.surname,"vat_id":"","telephone":self.phone}}
        while True:
            try:
                r = self.s.post(
                    f"https://footdistrict.com/rest/es/V1/carts/mine/estimate-shipping-methods", 
                    json = payload,
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    self.success('Succesfully got shipping rates!')
                    self.carrier_code = r.text.split('carrier_code":"')[1].split('"')[0]
                    self.method_code = r.text.split('method_code":"')[1].split('"')[0]
                    break
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while getting shipping rates: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while getting shipping rates: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
        self.cc()

    def ppverify(self):

        global failed, checkoutnum, carted
        self.warn('Opening paypal...')
        self.s.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        })
        while True:
            try:
                r = self.s.get(
                    f'https://footdistrict.com/paypal/express/start/', 
                    allow_redirects = False,
                    timeout = self.timeout
                )
                if r.status_code == 302:
                    self.ppurl = r.headers['Location']
                    self.success('Successfully checked out!')
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while opening paypal: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while opening paypal: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
        self.selenium()

    def pp(self):
        self.warn('Opening paypal...')
        self.s.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        })
        global failed, checkoutnum, carted
        while True:
            try:
                r = self.s.get(
                    f'https://footdistrict.com/paypal/express/start/', 
                    allow_redirects = False,
                    timeout=self.timeout
                )
                if r.status_code == 302:
                    self.ppurl = r.headers['Location']
                    self.success('Successfully checked out!')
                    checkoutnum = checkoutnum + 1
                    self.bar()
                    break
                elif r.status_code == 307:
                    self.cookiesolve()
                    continue
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while opening paypal: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while opening paypal: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            
        self.selenium()

    def selenium(self):
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
                    writer.writerow({'SITE':'FOOTDISTRICT','SIZE':f'{self.scelto[0]}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'FOOTDISTRICT','SIZE':f'{self.scelto[0]}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            self.SuccessPP()
        except Exception as e: 
            self.error('Exception while passing cookies: {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.selenium()

    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url =random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**FOOTDISTRICT**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.scelto[0], inline = True)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
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
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name=f'**FOOTDISTRICT**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.scelto[0], inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = False) 
            embed.add_embed_field(name='EMAIL', value = f"||{self.mail}||", inline = True) 
            embed.add_embed_field(name='PASSWORD', value = f"||{self.password}||", inline = True) 
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()

        except:
            pass

    def gnerateCardDataJsoncard(self, pan):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "number": pan,
            "generationtime": generation_time
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

    def maincard(self, pan, key):
        plainCardData = self.gnerateCardDataJsoncard(
            pan=pan
        )
        cardDataJsonString = json.dumps(plainCardData, sort_keys=True)
        aesKey = AESCCM.generate_key(256)
        nonce = urandom(12)
        encryptedCardData = self.encryptWithAesKey(aesKey, nonce, bytes(cardDataJsonString, encoding='utf8'))
        encryptedCardComponent = nonce + encryptedCardData
        adyenPublicKey = key
        publicKey = self.decodeAdyenPublicKey(adyenPublicKey)
        encryptedAesKey = self.encryptWithPublicKey(publicKey, aesKey)
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
        return encryptedAesData


    def gnerateCardDataJsonmonth(self, expiry_month):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "expiryMonth": expiry_month,
            "generationtime": generation_time
        }

    def mainmonth(self, expiry_month, key):
        plainCardData = self.gnerateCardDataJsonmonth(
            expiry_month=expiry_month
        )
        cardDataJsonString = json.dumps(plainCardData, sort_keys=True)
        aesKey = AESCCM.generate_key(256)
        nonce = urandom(12)
        encryptedCardData = self.encryptWithAesKey(aesKey, nonce, bytes(cardDataJsonString, encoding='utf8'))
        encryptedCardComponent = nonce + encryptedCardData
        adyenPublicKey = key
        publicKey = self.decodeAdyenPublicKey(adyenPublicKey)
        encryptedAesKey = self.encryptWithPublicKey(publicKey, aesKey)
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
        return encryptedAesData


    def gnerateCardDataJsonyear(self, expiry_year):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "expiryYear": expiry_year,
            "generationtime": generation_time
        }

    def mainyear(self, expiry_year, key):
        plainCardData = self.gnerateCardDataJsonyear(
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
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
        return encryptedAesData

    def gnerateCardDataJsoncvv(self, cvc):
        generation_time = datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return {
            "generationtime": generation_time,
            "cvc": cvc
        }

    def maincvv(self, cvc, key):
        plainCardData = self.gnerateCardDataJsoncvv(
            cvc=cvc,
        )
        cardDataJsonString = json.dumps(plainCardData, sort_keys=True)
        aesKey = AESCCM.generate_key(256)
        nonce = urandom(12)
        encryptedCardData = self.encryptWithAesKey(aesKey, nonce, bytes(cardDataJsonString, encoding='utf8'))
        encryptedCardComponent = nonce + encryptedCardData
        adyenPublicKey = key
        publicKey = self.decodeAdyenPublicKey(adyenPublicKey)
        encryptedAesKey = self.encryptWithPublicKey(publicKey, aesKey)
        encryptedAesData = "{}_{}${}${}".format("adyenjs","0_1_25", (base64.standard_b64encode(encryptedAesKey)).decode("utf-8") , (base64.standard_b64encode(encryptedCardComponent)).decode("utf-8"))
        return encryptedAesData

    def pay2(self):
        self.warn('Checking out...')
        payload = {
            'aenc5':f'{self.name} {self.surname}',
            'premium':self.premium,
            'aenc1':self.maincard(pan = self.cardnumber, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
            'aenc4':self.mainyear(expiry_year = self.year, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
            'aenc2':self.mainmonth(expiry_month = self.month, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
            'aenc3':self.maincvv(cvc = self.cvv, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33")
        }
        while True:
            try:
                r = self.s.post(
                    'https://footdistrict.com/premium/popup/autpremium/',
                    data = payload,
                    timeout = self.timeout
                )
                if r.status_code == 200:
                    break
                    #p = json.loads(r.text)
                    #if p['success'] == True:
                    #    break
                    #else:
                    #    print(r.text)
                    #    break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting cc: {r.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while submitting cc: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
        
    def cc(self):
        self.stop5 = False
        self.declined = False
        global failed, checkoutnum, carted
        cardtype = identify_card_type(self.cardnumber)
        if cardtype == "MasterCard":
            card_type = "MC"
        elif cardtype == "Visa":
            card_type = "VI"
        payload = {
            "cartId": f"{self.entity}",
            "billingAddress": {
                "countryId": f"{self.country}",
                "region": f"{self.region}",
                "street": [f"{self.address}"],
                "telephone": f"{self.phone}",
                "postcode": f"{self.zipcode}",
                "city": f"{self.city}",
                "firstname": f"{self.name}",
                "lastname": f'{self.surname}',
                "vatId": "",
                "extension_attributes": {},
                "saveInAddressBook": None
            },
            "paymentMethod": {
                "method": "adyen_cc",
                "additional_data": {
                    "guestEmail": f"{self.mail}",
                    "cc_type": f"{card_type}",
                    "number": self.maincard(pan = self.cardnumber, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
                    "cvc": self.maincvv(cvc = self.cvv, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
                    "expiryMonth": self.mainmonth(expiry_month = self.month, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
                    "expiryYear": self.mainyear(expiry_year = self.year, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
                    "holderName": f"{self.name} {self.surname}",
                    "store_cc": False,
                    "number_of_installments": "",
                    "java_enabled": False,
                    "screen_color_depth": 24,
                    "screen_width": 1920,
                    "screen_height": 1080,
                    "timezone_offset": -60,
                    "language": "en",
                    "combo_card_type": "credit"
                }
            },
            "email": f"{self.mail}"
        }
        self.warn('Submitting cc info...')
        while True:    
            try:   
                addressPost = self.s.post(
                    f'https://footdistrict.com/rest/es/V1/carts/mine/payment-information', 
                    json = payload,
                    timeout=self.timeout
                )
                if addressPost.status_code == 200:
                    break
                elif addressPost.status_code >= 500 and addressPost.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif addressPost.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif addressPost.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif addressPost.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting cc: {addressPost.status_code}, retrying...')
                    self.build_proxy()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while submitting cc: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
        if self.stop5:
            sys.exit()
        self.tred()

    def ccverify(self):
        self.stop4 = False
        self.declined = False
        global failed, checkoutnum, carted
        cardtype = identify_card_type(self.cardnumber)
        if cardtype == "MasterCard":
            card_type = "MC"
        elif cardtype == "Visa":
            card_type = "VI"
        payload = {
            "cartId": f"{self.entity}",
            "billingAddress": {
                "customerAddressId":f"{self.addatc}",
                "countryId": f"{self.country}",
                "regionCode":None,
                "region":self.region,
                "customerId":self.custommer,
                "street": [f"{self.address}"],
                "company":None,
                "telephone": f"{self.phone}",
                "fax":None,
                "postcode": f"{self.zipcode}",
                "city": f"{self.city}",
                "firstname": f"{self.name}",
                "lastname": f'{self.surname}',
                "middlename":None,
                "prefix":None,
                "suffix":None,
                "vatId":None,
                "customAttributes": {},
                "saveInAddressBook": None
            },
            "paymentMethod": {
                "method": "adyen_cc",
                "additional_data": {
                    "guestEmail": None,
                    "cc_type": f"{card_type}",
                    "number": self.maincard(pan = self.cardnumber, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
                    "cvc": self.maincvv(cvc = self.cvv, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
                    "expiryMonth": self.mainmonth(expiry_month = self.month, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
                    "expiryYear": self.mainyear(expiry_year = self.year, key = "10001|9F015D44090ED376C40CF4FA0D3D9D60A5CC798131B0EB983C43FB83C0BFC5725707BB312D0ED71269C920D013A68B82F6E616E665A22A43D39E85866AD7508B9837FAC5FFEFBDF428E0F58CFD999E65504FB2EB8E97FE0921BBF08B018FB743EEAF3440F26F0177BA1AB2A84DB27CE7B7306E56AACDDF45E98751525E5CD78A1F04B251F8AA0F7E2E7721518AC07531718AC2E232E9CDCD654B97B9BC2F35BD9384B67F76C5DA9BE324F04B3B133F5908A7B166E717C39DE9E213FA908E20DBB9425249DE6454CBB369A110A29841CF51FD88DBA46C1B0109C1B629495967BB58800E60ED52C77F8216DE8439F89B193D3476834BCEA8B72B87822FC4CA4C33"),
                    "holderName": f"{self.name} {self.surname}",
                    "store_cc": False,
                    "number_of_installments": "",
                    "java_enabled": False,
                    "screen_color_depth": 24,
                    "screen_width": 1920,
                    "screen_height": 1080,
                    "timezone_offset": -60,
                    "language": "en",
                    "combo_card_type": "credit",
                    "is_active_payment_token_enabler":False
                }
            }
        }
        self.warn('Submitting cc info...')
        while True:
            try:   
                addressPost = self.s.post(
                    f'https://footdistrict.com/rest/es/V1/carts/mine/payment-information', 
                    json = payload,
                    timeout=self.timeout
                )
                if addressPost.status_code == 200:
                    break
                elif addressPost.status_code == 400:
                    self.error(f'Something is wrong with your card: {addressPost.text}')
                    continue
                elif addressPost.status_code >= 500 and addressPost.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif addressPost.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif addressPost.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif addressPost.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Error while submitting cc: {addressPost.status_code}, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while submitting cc: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
        if self.stop4:
            sys.exit()
        self.tred()

    def tred(self):
        global failed, checkoutnum, carted
        self.stop2 = False
        self.warn('Processing payment...')
        while True:
            try:
                r = self.s.get(
                    f'https://footdistrict.com/adyen/process/redirect/',
                    timeout=self.timeout
                )
                if r.status_code == 200:
                    if 'PaReq' in r.text:
                        pareq = r.text.split('PaReq" value="')[1].split('"')[0]
                        urlpo = r.text.split('POST" action="')[1].split('"')[0]
                        md = r.text.split('MD" value="')[1].split('"')[0]
                        termur = r.text.split('TermUrl" value="')[1].split('"')[0]
                        payload = {
                            'PaReq':pareq,
                            'MD':md,
                            'TermUrl':termur
                        }
                        x = self.s.post(
                            urlpo,
                            data = payload,
                            timeout=self.timeout
                        )
                        if 'var pares' in x.text:
                            pares = x.text.split('var pares = "')[1].split('"')[0]
                        else:
                            revtoken = x.text.split('token: "')[1].split('"')[0]
                            payload2 = {"transToken": revtoken}
                            self.warn('Getting 3d secure...')
                            k = self.s.post(
                                "https://poll.touchtechpayments.com/poll", 
                                json = payload2,
                                timeout=self.timeout
                            )
                            while "pending" in k.text:
                                self.warn('Waiting 3d secure...')
                                time.sleep(5)
                                k = self.s.post(
                                    "https://poll.touchtechpayments.com/poll", 
                                    json = payload2,
                                    timeout=self.timeout
                                )
                            if "success" in k.text:
                                r_json = json.loads(k.text)
                                authToken = r_json['authToken']
                            payload = {
                                "transToken": revtoken,
                                "authToken": authToken
                            }
                            r = self.s.post(
                                "https://macs.touchtechpayments.com/v1/confirmTransaction", 
                                json = payload,
                                timeout=self.timeout
                            )
                            r_json = json.loads(r.text)
                            pares = r_json['Response']
                        payload = {
                            "MD":md,
                            "PaRes":pares
                        }
                        self.s.headers.update({
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        })
                        z = self.s.post(
                            f'https://footdistrict.com/adyen/transparent/redirect/', 
                            data = payload,
                            timeout=self.timeout
                        )
                        if z.status_code == 200:
                            b = self.s.post(
                                'https://footdistrict.com/adyen/process/redirect/', 
                                data = payload,
                                timeout=self.timeout
                            )
                            if 'success' in b.url:
                                self.success('Succesfully checked out!')
                                checkoutnum = checkoutnum + 1
                                self.bar()
                                break
                            elif b.status_code >= 500 and b.status_code <= 600:
                                self.warn('Site dead, retrying...')
                                time.sleep(self.delay)
                                continue
                            elif b.status_code == 403:
                                self.error('Proxy banned, rotating...')
                                self.build_proxy()
                                self.cookiesolve()
                                continue
                            elif b.status_code == 404:
                                self.error('Page not loaded, retrying...')
                                time.sleep(self.delay)
                                continue
                            elif b.status_code == 429:
                                self.error('Rate limit, retrying...')
                                self.build_proxy()
                                self.cookiesolve()
                                time.sleep(self.delay)
                                continue
                            else:
                                self.error('Payment failed or declined')
                                failed = failed + 1
                                self.bar()
                                self.stop2 = True
                                break
                        elif r.status_code >= 500 and r.status_code <= 600:
                            self.warn('Site dead, retrying...')
                            time.sleep(self.delay)
                            continue
                        elif r.status_code == 403:
                            self.error('Proxy banned, rotating...')
                            self.build_proxy()
                            self.cookiesolve()
                            continue
                        elif r.status_code == 404:
                            self.error('Page not loaded, retrying...')
                            time.sleep(self.delay)
                            continue
                        elif r.status_code == 429:
                            self.error('Rate limit, retrying...')
                            self.build_proxy()
                            self.cookiesolve()
                            time.sleep(self.delay)
                            continue
                        else:
                            self.error('Payment failed or declined')
                            failed = failed + 1
                            self.bar()
                            self.stop2 = True
                            break
                elif r.status_code >= 500 and r.status_code <= 600:
                    self.warn('Site dead, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 403:
                    self.error('Proxy banned, rotating...')
                    self.build_proxy()
                    self.cookiesolve()
                    continue
                elif r.status_code == 404:
                    self.error('Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue
                elif r.status_code == 429:
                    self.error('Rate limit, retrying...')
                    self.build_proxy()
                    self.cookiesolve()
                    time.sleep(self.delay)
                    continue
                else:
                    self.error(f'Unexpected error while processing payment {r.status_code}, retrying...')
                    self.build_proxy()
                    continue
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.error('Connection error, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
            except Exception as e:
                self.error(f'Exception while submitting cc: {e.__class__.__name__}, retrying...')
                self.build_proxy()
                self.cookiesolve()
                continue
        if self.stop2:
            sys.exit()
        self.SuccessCC()

    def selenium2(self):
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
                    writer.writerow({'SITE':'FOOTDISTRICT','SIZE':f'{self.scelto[0]}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            else:
                self.expToken = self.token
                with open(path,'a',newline='') as f:
                    fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow({'SITE':'FOOTDISTRICT','SIZE':f'{self.scelto[0]}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
            self.SuccessCC()
        except Exception as e: 
            self.error(f'Exception while passing cookies: {e.__class__.__name__}, retrying...') 
            time.sleep(self.delay)
            self.selenium2()

    def Pubblic_Webhook2(self):
        try:
            webhook = DiscordWebhook(url =random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name=f'**FOOTDISTRICT**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.scelto[0], inline = True)
            embed.add_embed_field(name=f'**PRODUCT**', value = f"[LINK]({self.link})", inline = False)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
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

    def SuccessCC(self):
        try:
            if self.all_proxies == None:
                self.px = 'LOCAL'
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', color = 4437377)
            embed.add_embed_field(name=f'**FOOTDISTRICT**', value = self.title, inline = True)
            embed.add_embed_field(name='**SIZE**', value = self.scelto[0], inline = True)
            embed.add_embed_field(name='PAYMENT METHOD', value = 'Credit Card', inline = False) 
            embed.add_embed_field(name='EMAIL', value = f"||{self.mail}||", inline = True) 
            embed.add_embed_field(name='PASSWORD', value = f"||{self.password}||", inline = True) 
            embed.add_embed_field(name='**PROXY**', value = f"||{self.px}||", inline = False)
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook2()
        except:
            pass