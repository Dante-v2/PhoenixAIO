import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from helheim import helheim, isChallenge
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3

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

class SNEAKERS76():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'sneakers76/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "sneakers76/proxies.txt")
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
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha']},doubleDown=False,requestPostHook=self.injection)
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)
        
        self.discord = DISCORD_ID
        self.name = row['NAME']
        self.surname = row['SURNAME']
        self.mail = row['MAIL']
        self.address = row['ADDRESS']
        self.region = row['REGION']
        self.zip = row['ZIPCODE']
        self.country = row['COUNTRY']
        self.phone = row['PHONE']
        self.city = row['CITY']
        self.link = row['LINK']
        self.size = row['SIZE']
        self.payment = row['PAYMENT']
        self.webhook_url = webhook
        self.mode = row['MODE']
        self.threadID = '%03d' % i
        self.version = version
        self.delay = int(config["delay"])
        self.iscookiesfucked = False
        self.cfchl = False
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        if config['timeout-sneakers76'] == "":
            self.timeout = 25

        else:
            self.timeout = int(config['timeout-sneakers76'])


        self.balance = balancefunc()

        self.bar()

        self.regionid = ''
        self.countryid = ''

        if self.country == 'AT':
            self.countryid = '12'
        if self.country == 'BE':
            self.countryid = '20'
        if self.country == 'BG':
            self.countryid = '22'
        if self.country == 'HR':
            self.countryid = '98'
        if self.country == 'CZ':
            self.countryid = '56'
        if self.country == 'DE':
            self.countryid = '59'
        if self.country == 'EST':
            self.countryid = '64'
        if self.country == 'FI':
            self.countryid = '70'
        if self.country == 'FR':
            self.countryid = '75'
        if self.country == 'DE':
            self.countryid = '57'
        if self.country == 'GR':
            self.countryid = '89'
        if self.country == 'HU':
            self.countryid = '100'
        if self.country == 'IR':
            self.countryid = '102'
        if self.country == 'IT':
            self.countryid = '110'
        if self.country == 'LTV':
            self.countryid = '135'
        if self.country == 'LTU':
            self.countryid = '133'
        if self.country == 'NL':
            self.countryid = '166'
        if self.country == 'PL':
            self.countryid = '179'
        if self.country == 'PT':
            self.countryid = '184'
        if self.country == 'RO':
            self.countryid = '189'
        if self.country == 'ES':
            self.countryid = '68'
        if self.country == 'SE':
            self.countryid = '197'
        if self.country == 'UK':
            self.countryid = '77'

        if self.country == 'IT':
            if self.region == 'AG':
                self.regionid = '13975'
            if self.region == 'AL':
                self.regionid = '14057'
            if self.region == 'AN':
                self.regionid = '14056'
            if self.region == 'AO':
                self.regionid = '14055'
            if self.region == 'AR':
                self.regionid = '14054'
            if self.region == 'AP':
                self.regionid = '14053'
            if self.region == 'AT':
                self.regionid = '14052'
            if self.region == 'AV':
                self.regionid = '14051'
            if self.region == 'AQ':
                self.regionid = '14026'
            if self.region == 'BA':
                self.regionid = '14050'
            if self.region == 'BG':
                self.regionid = '14047'
            if self.region == 'BI':
                self.regionid = '14058'
            if self.region == 'BL':
                self.regionid = '14049'
            if self.region == 'BN':
                self.regionid = '14048'
            if self.region == 'BO':
                self.regionid = '14046'
            if self.region == 'BR':
                self.regionid = '14043'
            if self.region == 'BT':
                self.regionid = '14070'
            if self.region == 'BS':
                self.regionid = '14044'
            if self.region == 'BZ':
                self.regionid = '14045'
            if self.region == 'CA':
                self.regionid = '13974'
            if self.region == 'CB':
                self.regionid = '14042'
            if self.region == 'CE':
                self.regionid = '14041'
            if self.region == 'CH':
                self.regionid = '14040'
            if self.region == 'CI':
                self.regionid = '14059'
            if self.region == 'CL':
                self.regionid = '13973'
            if self.region == 'CN':
                self.regionid = '14037'
            if self.region == 'CO':
                self.regionid = '14039'
            if self.region == 'CR':
                self.regionid = '14038'
            if self.region == 'CS':
                self.regionid = '13970'
            if self.region == 'CT':
                self.regionid = '13972'
            if self.region == 'CZ':
                self.regionid = '13971'
            if self.region == 'EN':
                self.regionid = '13969'
            if self.region == 'FC':
                self.regionid = '14033'
            if self.region == 'FE':
                self.regionid = '14036'
            if self.region == 'FG':
                self.regionid = '14034'
            if self.region == 'FI':
                self.regionid = '14035'
            if self.region == 'FM':
                self.regionid = '14069'
            if self.region == 'FR':
                self.regionid = '14032'
            if self.region == 'GE':
                self.regionid = '14031'
            if self.region == 'GO':
                self.regionid = '14030'
            if self.region == 'GR':
                self.regionid = '14029'
            if self.region == 'IM':
                self.regionid = '14028'
            if self.region == 'IS':
                self.regionid = '14027'
            if self.region == 'KR':
                self.regionid = '14065'
            if self.region == 'LC':
                self.regionid = '14066'
            if self.region == 'LE':
                self.regionid = '14023'
            if self.region == 'LI':
                self.regionid = '14022'
            if self.region == 'LO':
                self.regionid = '14067'
            if self.region == 'LT':
                self.regionid = '14024'
            if self.region == 'LU':
                self.regionid = '14021'
            if self.region == 'MB':
                self.regionid = '14071'
            if self.region == 'MC':
                self.regionid = '14020'
            if self.region == 'ME':
                self.regionid = '13968'
            if self.region == 'MI':
                self.regionid = '14016'
            if self.region == 'MN':
                self.regionid = '14019'
            if self.region == 'MO':
                self.regionid = '14015'
            if self.region == 'MS':
                self.region = '14018'
            if self.regionid == 'MT':
                self.region = '14017'
            if self.regionid == 'NA':
                self.regionid = '14014'
            if self.region == 'NO':
                self.regionid = '14013'
            if self.region == 'NU':
                self.regionid = '14012'
            if self.region == 'OG':
                self.regionid = '14062'
            if self.region == 'OR':
                self.regionid = '13967'
            if self.region == 'OT':
                self.regionid = '14060'
            if self.region == 'PA':
                self.regionid = '13966'
            if self.region == 'PC':
                self.regionid = '14005'
            if self.region == 'PD':
                self.regionid = '14011'
            if self.region == 'PE':
                self.regionid = '14006'
            if self.region == 'PG':
                self.regionid = '14008'
            if self.region == 'PI':
                self.regionid = '14004'
            if self.region == 'PN':
                self.regionid = '14002'
            if self.region == 'PO':
                self.regionid = '14068'
            if self.region == 'PR':
                self.regionid = '14010'
            if self.region == 'PT':
                self.regionid = '14003'
            if self.region == 'PU':
                self.regionid = '14007'
            if self.region == 'PV':
                self.regionid = '14009'
            if self.region == 'PZ':
                self.regionid = '14001'
            if self.region == 'RA':
                self.regionid = '14000'
            if self.region == 'RC':
                self.regionid = '13964'
            if self.region == 'RE':
                self.regionid = '13999'
            if self.region == 'RG':
                self.regionid = '13965'
            if self.region == 'RI':
                self.regionid = '13998'
            if self.region == 'RM':
                self.regionid = '13997'
            if self.region == 'RN':
                self.regionid = '14063'
            if self.region == 'RO':
                self.regionid = '13996'
            if self.region == 'SA':
                self.regionid = '13995'
            if self.region == 'SI':
                self.regionid = '13992'
            if self.region == 'SO':
                self.regionid = '13991'
            if self.region == 'SP':
                self.regionid = '14025'
            if self.region == 'SR':
                self.regionid = '13963'
            if self.region == 'SS':
                self.regionid = '13994'
            if self.region == 'SU':
                self.regionid = '32534'
            if self.region == 'SV':
                self.regionid = '13993'
            if self.region == 'TA':
                self.regionid = '13990'
            if self.region == 'TE':
                self.regionid = '13989'
            if self.region == 'TN':
                self.regionid = '13986'
            if self.region == 'TO':
                self.regionid = '13987'
            if self.region == 'TP':
                self.regionid = '13962'
            if self.region == 'TR':
                self.regionid = '13988'
            if self.region == 'TS':
                self.regionid = '13984'
            if self.region == 'TV':
                self.regionid = '13985'
            if self.region == 'UD':
                self.regionid = '13983'
            if self.region == 'VA':
                self.regionid = '13982'
            if self.region == 'VB':
                self.regionid = '13980'
            if self.region == 'VC':
                self.regionid = '13979'
            if self.region == 'VE':
                self.regionid = '13981'
            if self.region == 'VI':
                self.regionid = '13977'
            if self.region == 'VR':
                self.regionid = '13978'
            if self.region == 'VS':
                self.regionid = '14061'
            if self.region == 'VT':
                self.regionid = '13976'
            if self.region == 'VV':
                self.regionid = '14064'
        elif self.country == 'ES':
            if self.region == 'Albacete':
                self.regionid = '10969'
            if self.region == 'Alicante':
                self.regionid = '10968'
            if self.region == 'Almería':
                self.regionid = '10967'
            if self.region == 'Araba':
                self.regionid = '10993'
            if self.region == 'Asturias':
                self.regionid = '11000'
            if self.region == 'Ávila':
                self.regionid = '10992'
            if self.region == 'Badajoz':
                self.regionid = '10966'
            if self.region == 'Barcelona':
                self.regionid = '10991'
            if self.region == 'Bizkaia':
                self.regionid = '10972'
            if self.region == 'Burgos':
                self.regionid = '10990'
            if self.region == 'Cáceres':
                self.regionid = '10965'
            if self.region == 'Cádiz':
                self.regionid = '10964'
            if self.region == 'Cantabria':
                self.regionid = '10978'
            if self.region == 'Castelló':
                self.regionid = '10989'
            if self.region == 'Ceuta':
                self.regionid = '11002'
            if self.region == 'Ciudad Real':
                self.regionid = '10963'
            if self.region == 'Córdoba':
                self.regionid = '10962'
            if self.region == 'Coruña':
                self.regionid = '10985'
            if self.region == 'Cuenca':
                self.regionid = '10961'
            if self.region == 'Gipuzkoa':
                self.regionid = '10987'
            if self.region == 'Girona':
                self.regionid = '10994'
            if self.region == 'Granada':
                self.regionid = '10960'
            if self.region == 'Guadalajara':
                self.regionid = '10988'
            if self.region == 'Huelva':
                self.regionid = '10959'
            if self.region == 'Huesca':
                self.regionid = '10986'
            if self.region == 'Illes Balears':
                self.regionid = '11001'
            if self.region == 'Jaén':
                self.regionid = '10958'
            if self.region == 'La Rioja':
                self.regionid = '10996'
            if self.region == 'Las Palmas':
                self.regionid = '10957'
            if self.region == 'León':
                self.regionid = '10984'
            if self.region == 'Lleida':
                self.regionid = '10995'
            if self.region == 'Lugo':
                self.regionid = '10983'
            if self.region == 'Madrid':
                self.regionid = '10997'
            if self.region == 'Málaga':
                self.regionid = '10956'
            if self.region == 'Melilla':
                self.regionid = '11003'
            if self.region == 'Murcia':
                self.regionid = '10998'
            if self.region == 'Navarra':
                self.regionid = '10999'
            if self.region == 'Ourense':
                self.regionid = '10982'
            if self.region == 'Palencia':
                self.regionid = '10981'
            if self.region == 'Pontevedra':
                self.regionid = '10980'
            if self.region == 'Salamanca':
                self.regionid = '10979'
            if self.region == 'Santa Cruz de Tenerife':
                self.regionid = '10955'
            if self.region == 'Segovia':
                self.regionid = '10977'
            if self.region == 'Sevilla':
                self.regionid = '10954'
            if self.region == 'Soria':
                self.regionid = '10976'
            if self.region == 'Tarragona':
                self.regionid = '10975'
            if self.region == 'Teruel':
                self.regionid = '10974'
            if self.region == 'Toledo':
                self.regionid = '10953'
            if self.region == 'València':
                self.regionid = '10952'
            if self.region == 'Valladolid':
                self.regionid = '10973'
            if self.region == 'Zamora':
                self.regionid = '10971'
            if self.region == 'Zaragoza':
                self.regionid = '10970'

        elif self.country == 'DE':
            if self.region == 'Baden-Württemberg':
                self.regionid = '734'
            if self.region == 'Berlin':
                self.regionid = '732'
            if self.region == 'Brandenburg':
                self.regionid = '731'
            if self.region == 'Bremen':
                self.region = '730'
            if self.regionid == 'Freistaat Bayern':
                self.region = '733'
            if self.regionid == 'Freistaat Sachsen':
                self.regionid = '722'
            if self.region == 'Hamburg':
                self.regionid = '729'
            if self.region == 'Hessen':
                self.regionid = '728'
            if self.region == 'Mecklenburg-Vorpommern':
                self.regionid = '727'
            if self.region == 'Niedersachsen':
                self.regionid = '726'
            if self.region == 'Nordrhein-Westfalen':
                self.regionid = '725'
            if self.region == 'Rheinland-Pfalz':
                self.regionid = '724'
            if self.region == 'Saarland':
                self.regionid = '723'
            if self.region == 'Sachsen-Anhalt':
                self.regionid = '721'
            if self.region == 'Schleswig-Holstein':
                self.regionid = '720'
            if self.region == 'Thüringen':
                self.regionid = '719'

        else:
            self.regionid = ""

        if "/en/" in self.link:
            self.link = self.link.replace("/en/","/it/")

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

        warn(f'[TASK {self.threadID}] [SNEAKERS76] - Starting tasks...')

        self.getprod()


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
                f'Phoenix AIO {self.version} - SNEAKERS76 Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - SNEAKERS76 Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')

    def injection(self, session, response):

        self.balance = balancefunc()
        self.bar()

        try:
            if session.is_New_IUAM_Challenge(response) \
            or session.is_New_Captcha_Challenge(response) \
            or session.is_BFM_Challenge(response):
                warn(f'[TASK {self.threadID}] [SNEAKERS76] - Solving Cloudflare v2 api2')
                self.mom = True
                return helheim('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693', session, response)
            else:
                return response
        except:
            if session.is_New_IUAM_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [SNEAKERS76] - Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            elif session.is_New_Captcha_Challenge(response):
                self.mom = True
                warn(f'[TASK {self.threadID}] [SNEAKERS76] - Solving Cloudflare v2')
                return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=False).solve() 
            else:
                return response

    def remove_line(self, line):
        return line[:line.rfind('\n')]


    def getprod(self):

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
            self.s.proxies = self.selected_proxies

        try:
        
            while True:

                r = self.s.get(self.link, proxies = self.selected_proxies, timeout = self.timeout)

                if r.status_code == 200:


                    if 'data-toggle="dropdown" data-original-title="Size sneakers" class="dropdown-toggle"' not in r.text:
                        warn(f'[TASK {self.threadID}] [SNEAKERS76] - Product not live yet, retrying...')
                        time.sleep(self.delay)
                        continue

                    else:

                        jsoninit = r.text.split("var preloadedStock = ")[1].split("var preloadedRelatedItems")[0]
    
                        self.title = r.text.split('property="og:title" content="')[1].split('"')[0]
    
                        jsoninit = self.remove_line(jsoninit)[:-1]
                        jsoninit = json.loads(jsoninit)
                        
                        sizeus = []
                        variantatc = []
    
                        for element in jsoninit:
                            if element['isInStock'] == True:
                                sizeus.append((element['variant']).split(" US")[0])
                                variantatc.append(element["stockItemId"])
    
                        connect = zip(sizeus, variantatc)
                        self.connecto = list(connect)
                        if len(self.connecto) >= 1:
                        
                            info(f'[TASK {self.threadID}] [SNEAKERS76] - {self.title} in stock!')
                            break
                        
                        
                        else:
                            warn(f'[TASK {self.threadID}] [SNEAKERS76] - {self.title} OOS, monitoring...')
                            time.sleep(self.delay)
                            continue

                elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [SNEAKERS76] - Site is dead, retrying...')
                        time.sleep(self.delay)
                        continue

                elif r.status_code == 403:
                    error(f"[Task {self.threadID}] [SNEAKERS76] - Proxy banned, retrying...")
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue

                elif r.status_code == 429:
                    error(f"[Task {self.threadID}] [SNEAKERS76] - Rate limit, retrying...")
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue

                elif r.status_code == 404:
                    warn(f'[TASK {self.threadID}] [SNEAKERS76] - Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  

                else:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    error(f'[TASK {self.threadID}] [SNEAKERS76] - Error {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue
            
            self.atc()

                

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SNEAKERS76] - Connection error, retrying...')
            time.sleep(self.delay)
            self.getprod()

        except Exception as e:
            error(f'[TASK {self.threadID}] [SNEAKERS76] - Exception getting product, retrying...')
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            self.getprod()


    def atc(self):

        try:

            warn(f'[TASK {self.threadID}] [SNEAKERS76] - Getting sizes...')
            self.isOOS = False

            while True:

                if self.size == "RANDOM":

                    chosen = random.choice(self.connecto)
                    self.sizeusata = chosen[0]
                    self.varianteusata = chosen[1]

                elif "," in self.size or "-" in self.size:
                    self.sizerange = []
                    try:
                        self.size1 = str(self.size.split(',')[0])
                        self.size2 = str(self.size.split(',')[1])
                    except:
                        self.size1 = str(self.size.split('-')[0])
                        self.size2 = str(self.size.split('-')[1])
                    for x in self.connecto:
                        if float(self.size1) <= float(x[0]) <= float(self.size2):
                            self.sizerange.append(x)

                    if len(self.sizerange) < 1:
                        warn(f'[TASK {self.threadID}] [SNEAKERS76] - {self.title} size {self.size} OOS, monitoring...')
                        time.sleep(self.delay)
                        self.isOOS = True
                        self.getprod()
                    else:
                        self.sizerandom = random.choice(self.sizerange)

                        self.sizeusata = self.sizerandom[0]
                        self.varianteusata = self.sizerandom[1]
                        info(f'[TASK {self.threadID}] [SNEAKERS76] - Adding to cart size {self.sizeusata}...')

                else:
                    for element in self.connecto:
                        if self.size == element[0]:
                            info(f'[TASK {self.threadID}] [SNEAKERS76] - Adding to cart size {self.sizeusata}...')
                            self.sizeusata = element[0]
                            self.varianteusata = element[1]


                payload = {
                    'controller': 'orders',
                    'action': 'addStockItemToBasket',
                    'stockItemId': self.varianteusata,
                    'quantity': '1',
                    'extension': 'sneakers76',
                    'language': 'IT',
                    'version': '84',
                    'cookieVersion': '1'
                }

                headers = {
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://www.sneakers76.com',
                    'referer': self.link,
                    'sec-ch-ua-mobile': '?0',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                r = self.s.post("https://www.sneakers76.com/index.php", data = payload, headers = headers, proxies = self.selected_proxies, timeout = self.timeout)

                if r.status_code == 200:

                    jsonatc = json.loads(r.text)
                    if jsonatc['payload'][0]['addedQuantity'] == "1":
                        info(f'[TASK {self.threadID}] [SNEAKERS76] - {self.title} size {self.sizeusata} added to cart!')
                        self.image = jsonatc['payload'][0]['imageObject']['url']
                        break

                    else:
                        error(f'[TASK {self.threadID}] [SNEAKERS76] - Error adding to cart, retrying...')
                        continue


                elif r.status_code >= 500 and r.status_code <= 600:
                        error(f'[TASK {self.threadID}] [SNEAKERS76] - Error {r.status_code} retrying...')
                        time.sleep(self.delay)
                        continue

                elif r.status_code == 403:
                    error(f"[Task {self.threadID}] [SNEAKERS76] - Proxy banned, retrying...")
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue

                elif r.status_code == 429:
                    error(f"[Task {self.threadID}] [SNEAKERS76] - Rate limit, retrying...")
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue

                elif r.status_code == 404:
                    warn(f'[TASK {self.threadID}] [SNEAKERS76] - Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  

                else:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    error(f'[TASK {self.threadID}] [SNEAKERS76] - Error {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue


            if self.isOOS:
                self.getprod()

            else:
                self.shipfinale()

            
        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SNEAKERS76] - Connection error, retrying...')
            time.sleep(self.delay)
            self.atc()

        except Exception as e:
            error(f'[TASK {self.threadID}] [SNEAKERS76] - Exception adding to cart, retrying...')
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            self.atc()
           


    def shipfinale(self):

        try:
            warn(f'[TASK {self.threadID}] [SNEAKERS76] - Submitting info...')

            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }

            payload = {
                'secretly': 'false',
                'hardErrorize': 'false',
                'billingAddressId': 'n0',
                'shippingAddressId': 'n0',
                'shipmentFlow': 'DELIVERY',
                'newAddresses[0][counter]': 'n0',
                'newAddresses[0][first_name]': self.name,
                'newAddresses[0][last_name]': self.surname,
                'newAddresses[0][full_name]': f'{self.name} {self.surname}',
                'newAddresses[0][street_address]': self.address,
                'newAddresses[0][zipcode]': self.zip,
                'newAddresses[0][cityName]': self.city,
                'newAddresses[0][statecode]': self.region,
                'newAddresses[0][stateId]': self.regionid,
                'newAddresses[0][countryId]': self.countryid,
                'newAddresses[0][countryName]': '',
                'newAddresses[0][phone_number]': self.phone,
                'newAddresses[0][isDefault]': '0',
                'newAddresses[0][email]': self.mail,
                'newAddresses[1][counter]': 'n1',
                'newAddresses[1][first_name]': '',
                'newAddresses[1][last_name]': '',
                'newAddresses[1][full_name]': '',
                'newAddresses[1][street_address]': '',
                'newAddresses[1][zipcode]': '',
                'newAddresses[1][cityName]': '',
                'newAddresses[1][statecode]': '',
                'newAddresses[1][stateId]': '0',
                'newAddresses[1][countryId]': self.countryid,
                'newAddresses[1][countryName]': '',
                'newAddresses[1][phone_number]': '',
                'newAddresses[1][isDefault]': '0',
                'newAddresses[1][email]': self.mail,
                'requestInvoice': '0',
                'notes': '',
                'paymentMethodId': '12',
                'paymentMethodAccountId': '3',
                'shipments[0][shipmentFlow]': 'DELIVERY',
                'shipments[0][addressId]': 'n0',
                'shipments[0][shipperId]': '2',
                'shipments[0][shipperAccountId]': '1',
                'checkoutMethod': 'guest',
                'guestEmail': self.mail,
                'toDisplay': '1',
                'extension': 'sneakers76',
                'controller': 'orders',
                'action': 'review',
                'clearSession': '0',
                'language': 'IT',
                'version': '84',
                'cookieVersion': '1'
            }


            while True:
                
                r = self.s.post("https://www.sneakers76.com/index.php", data = payload, headers = headers, proxies = self.selected_proxies, stream=True)
            
                if r.status_code == 200:

                    if '"success":true' in r.text:
                        
                        info(f'[TASK {self.threadID}] [SNEAKERS76] - Succesfully submitted info!')

                        break

                    else:
                        error(f'[TASK {self.threadID}] [SNEAKERS76] - Error submitting shipping, retrying...')
                        self.s.cookies.clear()
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        self.getprod()


                elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [SNEAKERS76] - Error {r.status_code} retrying...')
                        time.sleep(self.delay)
                        continue

                elif r.status_code == 403:
                    error(f"[Task {self.threadID}] [SNEAKERS76] - Proxy banned, retrying...")
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue

                elif r.status_code == 429:
                    error(f"[Task {self.threadID}] [SNEAKERS76] - Rate limit, retrying...")
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue

                elif r.status_code == 404:
                    warn(f'[TASK {self.threadID}] [SNEAKERS76] - Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  

                else:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    error(f'[TASK {self.threadID}] [SNEAKERS76] - Error {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue


            self.paypal()



        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SNEAKERS76] - Connection error, retrying...')
            time.sleep(self.delay)
            self.shipfinale()

        except Exception as e:
            error(f'[TASK {self.threadID}] [SNEAKERS76] - Exception submitting info, retrying...')
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            self.shipfinale()


    def paypal(self):

        try:

            self.twoCaptcha = config['2captcha']

            warn(f'[TASK {self.threadID}] [SNEAKERS76] - Submitting captcha for checkout...')
            solver = TwoCaptcha(**{
            'apiKey': self.twoCaptcha,
            'softId': 2637
            })
            self.captcha = solver.recaptcha(url='https://www.sneakers76.com/it/orders/review', sitekey='6LfkeOoZAAAAADgN_RiRCrmCTpofE5KoBcAdblr-') 
            info(f'[TASK {self.threadID}] [SNEAKERS76] - Catcha solved!')
            

            payload = {
                'secretly': 'false',
                'hardErrorize': 'true',
                'billingAddressId': 'n0',
                'shippingAddressId': 'n0',
                'shipmentFlow': 'DELIVERY',
                'newAddresses[0][counter]': 'n0',
                'newAddresses[0][first_name]': self.name,
                'newAddresses[0][last_name]': self.surname,
                'newAddresses[0][full_name]': f"{self.name} {self.surname}",
                'newAddresses[0][street_address]': f"{self.address}",
                'newAddresses[0][zipcode]': self.zip,
                'newAddresses[0][cityName]': self.city,
                'newAddresses[0][statecode]': self.region,
                'newAddresses[0][stateId]': self.regionid,
                'newAddresses[0][countryId]': self.countryid,
                'newAddresses[0][countryName]': '',
                'newAddresses[0][phone_number]': self.phone,
                'newAddresses[0][isDefault]': '0',
                'newAddresses[0][email]': self.mail,
                'newAddresses[1][counter]': 'n1',
                'newAddresses[1][first_name]': '',
                'newAddresses[1][last_name]': '',
                'newAddresses[1][full_name]': '',
                'newAddresses[1][street_address]': '',
                'newAddresses[1][zipcode]': '',
                'newAddresses[1][cityName]': '',
                'newAddresses[1][statecode]': 'Provincia',
                'newAddresses[1][stateId]': '0',
                'newAddresses[1][countryId]': self.countryid,
                'newAddresses[1][countryName]': '',
                'newAddresses[1][phone_number]': '',
                'newAddresses[1][isDefault]': '0',
                'newAddresses[1][email]': self.mail,
                'requestInvoice': '0',
                'notes': '',
                'paymentMethodId': '2',
                'paymentMethodAccountId': '1',
                'shipments[0][shipmentFlow]': 'DELIVERY',
                'shipments[0][addressId]': 'n0',
                'shipments[0][shipperId]': '2',
                'shipments[0][shipperAccountId]': '1',
                'checkoutMethod': 'guest',
                'guestEmail': self.mail,
                'recaptcha': self.captcha['code'],
                'toDisplay': '0',
                'extension': 'sneakers76',
                'controller': 'orders',
                'action': 'save',
                'language': 'IT',
                'version': '99',
                'cookieVersion': '1'
            }


            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://www.sneakers76.com',
                'referer': 'https://www.sneakers76.com/it/orders/review',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }

            while True:


                r = self.s.post("https://www.sneakers76.com/index.php", data = payload, headers = headers, timeout = self.timeout)

                if r.status_code == 200:

                    if '"success":true' in r.text:

                        orderid = json.loads(r.text)
                        orderid = orderid['payload']['orderId']

                        headers = {
                            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                            'accept-encoding': 'gzip, deflate, br',
                            'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                            'referer': 'https://www.sneakers76.com/it/orders/review',
                            'upgrade-insecure-requests': '1',
                            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
                        }

                        r = self.s.get(f"https://www.sneakers76.com/it/orders/checkout/{orderid}?paymentMethodId=2&paymentMethodAccountId=1", headers = headers, allow_redirects = False)

                        if "token=" in r.headers['Location']:
                            info(f'[TASK {self.threadID}] [SNEAKERS76] - Successfully checked out!')
                            self.pplink = r.headers['Location']
                            break

                        else:
                            error(f'[TASK {self.threadID}] [SNEAKERS76] - Checkout Failed, restarting...')
                            self.s.cookies.clear()
                            if self.all_proxies != None:
                                self.selected_proxies = self.choose_proxy(self.all_proxies)
                                self.s.proxies = self.selected_proxies
                            self.getprod()


                elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [SNEAKERS76] - Site dead, retrying...')
                        time.sleep(self.delay)
                        continue

                elif r.status_code == 403:
                    error(f"[Task {self.threadID}] [SNEAKERS76] - Proxy banned, retrying...")
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue

                elif r.status_code == 429:
                    error(f"[Task {self.threadID}] [SNEAKERS76] - Rate limit, retrying...")
                    time.sleep(self.delay)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue

                elif r.status_code == 404:
                    warn(f'[TASK {self.threadID}] [SNEAKERS76] - Page not loaded, retrying...')
                    time.sleep(self.delay)
                    continue  

                else:
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    error(f'[TASK {self.threadID}] [SNEAKERS76] - Error {r.status_code}, retrying...')
                    time.sleep(self.delay)
                    continue

            self.passcookies()
                

        except ConnectionError as e:
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            error(f'[TASK {self.threadID}] [SNEAKERS76] - Connection error, retrying...')
            time.sleep(self.delay)
            self.paypal()

        except Exception as e:
            error(f'[TASK {self.threadID}] [SNEAKERS76] - Exception submitting checkout, retrying...')
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            self.paypal()


    def passcookies(self):

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
                url = urllib.parse.quote(base64.b64encode(bytes(self.pplink, 'utf-8')).decode())
                self.tokenn = f"https://api.phoenixbot.io/exploits/?cookie={cookieStr}&redirect={url}"     
                self.token2 = f"https://api.phoenixbot.io/mobile/?cookie={cookieStr}&redirect={url}"
                apiurl2 = "http://tinyurl.com/api-create.php?url="
                tinyasdurl2 = urllib.request.urlopen(apiurl2 + self.token2).read()
                self.expToken2 = str(tinyasdurl2.decode("utf-8"))
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "success.csv")   


                if len(self.tokenn) > 1999:

                    apiurl = "http://tinyurl.com/api-create.php?url="
                    tinyasdurl = urllib.request.urlopen(apiurl + self.tokenn).read()
                    self.expToken = str(tinyasdurl.decode("utf-8"))
                else:
                    self.expToken = self.tokenn

                self.successprivato()
                
            except Exception as e: 
                error(f'[TASK {self.threadID}] [SNEAKERS76] - Error while passing cookies, retrying...')
                time.sleep(self.delay)
                self.shipfinale()
        except:
            pass


    def successprivato(self):
        if self.selected_proxies == None:
            self.proxi = 'LOCAL'
        webhook = DiscordWebhook(url=self.webhook_url, content = "")
        embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
        embed.add_embed_field(name=f'**SNEAKERS76**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizeusata, inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = 'Paypal', inline = True)
        embed.add_embed_field(name='**MAIL**', value = f"||{self.mail}||", inline = False)
        embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
        embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
        embed.set_thumbnail(url=self.image)
        embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        self.Pubblic()


    def Pubblic(self):

        webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
        embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
        embed.add_embed_field(name=f'**SNEAKERS76**', value = self.title, inline = False)
        embed.add_embed_field(name='**SIZE**', value = self.sizeusata, inline = True)
        embed.add_embed_field(name='**PRODUCT**', value = f"[LINK]({self.link})", inline = True)
        embed.add_embed_field(name='PAYMENT METHOD', value = "Paypal", inline = True)
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
