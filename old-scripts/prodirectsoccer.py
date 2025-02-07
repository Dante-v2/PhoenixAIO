import json, requests, threading, csv, urllib3, sys, random, base64, platform, random, ctypes, logging, os, time, re, urllib, cloudscraper, names, lxml
from mods.logger import info, warn, error
from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup as bs
from playsound import playsound
from twocaptcha import TwoCaptcha
from helheim import helheim, isChallenge
from card_identifier.card_type import identify_card_type
from hawk_cf_api.hawk_cf import CF_2, Cf_challenge_3
from selenium import webdriver

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


checkoutnum = 0
carted = 0
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

def balancefunc():
    try:
        solver = TwoCaptcha(config['2captcha'])
        balance = solver.get_balance()
        return balance
    except:
        balance = 'Unkown'
        return balance

class PRODIRECTSOCCER():

    def __init__(self, name, surname, address1, address2, zipcode, city, region, country, phone, link, size, account, password, mode, webhook, version, threadID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'prodirectsoccer/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "prodirectsoccer/proxies.txt")
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
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'anticaptcha','api_key':config['anticaptcha']},doubleDown=False)
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha']},doubleDown=False)
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)
        
        self.s.proxies = self.selected_proxies

        self.name = name
        self.surname = surname
        self.address = address1
        self.address2 = address2
        self.zipcode = zipcode
        self.city = city
        self.region = region
        self.country = country
        self.phone = phone
        self.link = link
        self.size = size
        self.account = account
        self.password = password
        self.completename = name + surname
        self.version = version
        self.mode = mode
        self.listsuccess = ["https://discordapp.com/api/webhooks/730177494187114596/FCPah-cGJhjbQyt5FbWuZhpCR2OLZsTrLShcE7q2HXmyXelGr761kxJ3JIXAtXi2FfMc","https://discordapp.com/api/webhooks/755037630219157574/zoPCs3ErtJ7WZz7eP22wJ7a-tAnA32kzIrRnboK16s6Qhil_KakjGCEOUWqs7cXPZSm5","https://discordapp.com/api/webhooks/755037802860642405/8HyHFdLWSomeA-JFe-U7sTTD4esgpCKp-70G-fVC3QbNnLagnd2enaVpRfwIhQFJpRrS","https://discordapp.com/api/webhooks/755037905747050560/DfoCcB70DOfkUhvGQD29uLrCIs_SSlqW2SXUpi9MTqsOjJ__EZGpf9AiyhxwiGvr-D6V","https://discordapp.com/api/webhooks/755037940090011690/S-2DDh3p0Mq13TP1PN4nm7Z83_joit-PrckZys7y6V41fhYnBLQF_PIajBFrAIgsqAli","https://discordapp.com/api/webhooks/755038042632486992/5NWWB5q6gHhqwabkbalbF8fl5MAWjJEE71jUosx1LuGlarNt9rSEW-fKVkXtqHiu95Fe","https://discordapp.com/api/webhooks/755038092410355772/SpJY1WSSOfrfnOqjL2UsWh37aw1VV_0N3DL65AfZyEbuhyU6s6X7YOyF69E8616AeSCr","https://discordapp.com/api/webhooks/755038142083629086/p8V3SySf12YYouVgnXNZHBD8GM3F72SX04OsTnul18cHFfL3eVj1EbkarI7dneVU0r2F","https://discordapp.com/api/webhooks/755038187893686332/82CGeubI6jRfmwdjgMibm3gPxhmx6586x-E_2YgGtTYRzzW0JNCvpjh29FqXIA-d50nn","https://discordapp.com/api/webhooks/755038218931667065/IzMJ7tdqym65A5GXjDFzAwLvV8UhFE4AwO9tVQ7EujJBaQVFPIq73teI7b8YU0YYcPbC"]

        try:
            if self.name.upper() == "RANDOM":
                self.name = names.get_first_name(gender='male')
            if self.surname.upper() == "RANDOM":
                self.surname = names.get_last_name()
            if self.phone.upper() == "RANDOM":
                self.phone = str("0"+str(random.randint(7400000000,7999990000)))
            if self.account[:6].upper() == "RANDOM":
                self.account = "{}{}{}@{}".format(self.name, self.surname[0], str(random.randint(1000,9999)), self.account.split("@")[1]).lower()
        except Exception as e:
            error("FAILED CSV")

        if config['timeout-prodirect'] == "":
            self.timeout = 25

        else:
            self.timeout = int(config['timeout-prodirect'])
 
        self.webhook_url = webhook
        self.threadID = '%03d' % threadID

        if self.country == 'Afghanistan':
            self.country= "4"
        if self.country == 'Albania':
            self.country= "8"
        if self.country == 'Algeria':
            self.country = "12"
        if self.country == 'American Samoa':
            self.country = "16"
        if self.country == 'Andorra':
            self.country = "20"
        if self.country == 'Angola':
            self.country = "24"
        if self.country == 'Antarctica':
            self.country = "10"
        if self.country == 'Antigua and Barbuda':
            self.country = "28"
        if self.country == 'Argentina':
            self.country = "32"
        if self.country == 'Armenia':
            self.country = "51"
        if self.country == 'Australia':
            self.country = "36"
        if self.country == 'Austria':
            self.country = "40"
        if self.country == 'Azerbaijan':
            self.country = "31"
        if self.country == 'Bahamas':
            self.country = "44"
        if self.country == 'Bahrain':
            self.country = "48"
        if self.country == 'Bangladesh':
            self.country = "50"
        if self.country == 'Barbados':
            self.country = "52"
        if self.country == 'Belgium':
            self.country = "56"
        if self.country == 'Belize':
            self.country = "84"
        if self.country == '"Benin':
            self.country = "204"
        if self.country == 'Bermuda':
            self.country = "60"
        if self.country == 'Bhutan':
            self.country = "64"
        if self.country == 'Bolivia':
            self.country = "68"
        if self.country == 'Bosnia and Herzegovina':
            self.country = "70"
        if self.country == 'Botswana':
            self.country = "72"
        if self.country == 'Bouvet Island':
            self.country = "74"
        if self.country == 'Brazil':
            self.country = "76"
        if self.country == 'British Indian Ocean Territory':
            self.country = "86"
        if self.country == 'British Virgin Islands':
            self.country = "92"
        if self.country == 'Brunei':
            self.country = "96"
        if self.country == 'Belarus':
            self.country = "112"
        if self.country == 'Bulgaria':
            self.country =  "100"
        if self.country == 'Burkina Faso':
            self.country =  "854"
        if self.country == 'Burundi':
            self.country =  "108"
        if self.country == 'Cambodia':
            self.country =  "116"
        if self.country == 'Cameroon':
            self.country =  "120"
        if self.country == 'Canada':
            self.country =  "124"
        if self.country == 'Cape Verde':
            self.country =  "132"
        if self.country == 'Cayman Islands':
            self.country =  "136"
        if self.country == 'Central African Republic':
            self.country =  "140"
        if self.country == 'Chad':
            self.country =  "148"
        if self.country == 'Chile':
            self.country =  "152"
        if self.country == 'China':
            self.country =  "156"
        if self.country == 'Colombia':
            self.country =  "170"
        if self.country == 'Comoros':
            self.country =  "174"
        if self.country == 'Costa Rica':
            self.country =  "188"
        if self.country == 'Cote D’Ivoire':
            self.country =  "384"
        if self.country == 'Croatia':
            self.country =  "191"
        if self.country == 'Cuba':
            self.country =  "192"
        if self.country == 'Curaçao':
            self.country =  "531"
        if self.country == 'Cyprus':
            self.country =  "196"
        if self.country == 'Czech Republic':
            self.country =  "203"
        if self.country == 'Denmark':
            self.country =  "208"
        if self.country == 'Djibouti':
            self.country =  "262"
        if self.country == 'Dominica':
            self.country =  "212"
        if self.country == 'Dominican Republic':
            self.country =  "214"
        if self.country == 'East Timor':
            self.country =  "626"
        if self.country == 'Ecuador':
            self.country =  "218"
        if self.country == 'Egypt':
            self.country =  "818"
        if self.country == 'El Salvador':
            self.country =  "222"
        if self.country == 'Equatorial Guinea':
            self.country =  "226"
        if self.country == 'Eritrea':
            self.country =  "232"
        if self.country == 'Estonia':
            self.country =  "233"
        if self.country == 'Ethiopia':
            self.country =  "231"
        if self.country == 'Falkland Islands':
            self.country =  "238"
        if self.country == 'Faroe Islands':
            self.country =  "234"
        if self.country == 'Federated States of Micronesia':
            self.country =  "583"
        if self.country == 'France':
            self.country = '250'
        if self.country == 'Fiji':
            self.country =  "242"
        if self.country == 'Finland':
            self.country =  "246"
        if self.country == 'Gabon':
            self.country =  "266"
        if self.country == 'Gambia':
            self.country =  "270"
        if self.country == 'Georgia':
            self.country =  "268"
        if self.country == 'Germany':
            self.country =  "276"
        if self.country == 'Ghana':
            self.country =  "288"
        if self.country == 'Gibraltar':
            self.country =  "292"
        if self.country == 'Greece':
            self.country =  "300"
        if self.country == 'Greenland':
            self.country =  "304"
        if self.country == 'Grenada':
            self.country =  "308"
        if self.country == 'Guam':
            self.country =  "316"
        if self.country == 'Guatemala':
            self.country =  "320"
        if self.country == 'Guernsey':
            self.country =  "831"
        if self.country == 'Guinea':
            self.country =  "324"
        if self.country == 'Guinea-Bissau':
            self.country =  "624"
        if self.country == 'Guyana':
            self.country =  "328"
        if self.country == 'Haiti':
            self.country =  "332"
        if self.country == 'Heard Island and McDonald Islands':
            self.country =  "334"
        if self.country == 'Honduras':
            self.country =  "340"
        if self.country == 'Hong Kong':
            self.country =  "344"
        if self.country == 'Hungary':
            self.country =  "348"
        if self.country == 'Iceland':
            self.country =  "352"
        if self.country == 'India':
            self.country =  "356"
        if self.country == 'Indonesia':
            self.country =  "360"
        if self.country == 'Iran':
            self.country =  "364"
        if self.country == 'Iraq':
            self.country =  "368"
        if self.country == 'Ireland':
            self.country =  "372"
        if self.country == 'Isle of Man':
            self.country =  "833"
        if self.country == 'Israel':
            self.country =  "376"
        if self.country == 'Italy':
            self.country =  "380"
        if self.country == 'Jamaica':
            self.country =  "388"
        if self.country == 'Japan':
            self.country =  "392"
        if self.country == 'Jersey':
            self.country =  "832"
        if self.country == 'Jordan':
            self.country =  "400"
        if self.country == 'Kazakhstan':
            self.country =  "398"
        if self.country == 'Kenya':
            self.country =  "404"
        if self.country == 'Kiribat':
            self.country =  "296"
        if self.country == 'Kuwait':
            self.country =  "414"
        if self.country == 'Kyrgyzstan':
            self.country =  "417"
        if self.country == 'Laos':
            self.country =  "418"
        if self.country == 'Latvia':
            self.country =  "428"
        if self.country == 'Lebanon':
            self.country =  "422"
        if self.country == 'Lesotho':
            self.country =  "426"
        if self.country == 'Liberia':
            self.country =  "430"
        if self.country == 'Libya':
            self.country =  "434"
        if self.country == 'Liechtenstein':
            self.country =  "438"
        if self.country == 'Lithuania':
            self.country =  "440"
        if self.country == 'Luxembourg':
            self.country =  "442"
        if self.country == 'Macau':
            self.country =  "446"
        if self.country == 'Macedonia':
            self.country =  "807"
        if self.country == 'Madagascar':
            self.country =  "450"
        if self.country == 'Malawi':
            self.country =  "454"
        if self.country == 'Malaysia':
            self.country =  "458"
        if self.country == 'Maldives':
            self.country =  "462"
        if self.country == 'Mali':
            self.country =  "466"
        if self.country == 'Malta':
            self.country =  "470"
        if self.country == 'Marshall Islands':
            self.country =  "584"
        if self.country == 'Mauritania':
            self.country =  "478"
        if self.country == 'Mauritius':
            self.country =  "480"
        if self.country == 'Mexico':
            self.country =  "484"
        if self.country == 'Moldova':
            self.country =  "498"
        if self.country == 'Monaco':
            self.country =  "492"
        if self.country == 'Mongolia':
            self.country =  "496"
        if self.country == 'Montenegro':
            self.country =  "499"
        if self.country == 'Montserrat':
            self.country =  "500"
        if self.country == 'Morocco':
            self.country =  "504"
        if self.country == 'Mozambique':
            self.country =  "508"
        if self.country == 'Myanmar':
            self.country =  "104"
        if self.country == 'Namibia':
            self.country =  "516"
        if self.country == 'Nauru':
            self.country =  "520"
        if self.country == 'Nepal':
            self.country =  "524"
        if self.country == 'Netherlands':
            self.country =  "528"
        if self.country == 'New Zealand':
            self.country =  "554"
        if self.country == 'Nicaragua':
            self.country =  "558"
        if self.country == 'Niger':
            self.country =  "562"
        if self.country == 'Nigeria':
            self.country =  "566"
        if self.country == 'Niue':
            self.country =  "570"
        if self.country == 'Norfolk Island':
            self.country =  "574"
        if self.country == 'North Korea':
            self.country =  "408"
        if self.country == 'Northern Mariana Islands':
            self.country =  "580"
        if self.country == 'Norway':
            self.country =  "578"
        if self.country == 'Oman':
            self.country =  "512"
        if self.country == 'Pakistan':
            self.country =  "586"
        if self.country == 'Palau':
            self.country =  "585"
        if self.country == 'Palestine, State of':
            self.country =  "275"
        if self.country == 'Panama':
            self.country =  "591"
        if self.country == 'Papua New Guinea':
            self.country =  "598"
        if self.country == 'Paraguay':
            self.country =  "600"
        if self.country == 'Peru':
            self.country =  "604"
        if self.country == 'Philippines':
            self.country =  "608"
        if self.country == 'Pitcairn':
            self.country =  "612"
        if self.country == 'Poland':
            self.country =  "616"
        if self.country == 'Portugal':
            self.country =  "620"
        if self.country == 'Puerto Rico':
            self.country =  "630"
        if self.country == 'Qatar':
            self.country =  "634"
        if self.country == 'Romania':
            self.country =  "642"
        if self.country == 'Russia':
            self.country =  "643"
        if self.country == 'Rwanda':
            self.country =  "646"
        if self.country == 'Samoa':
            self.country =  "882"
        if self.country == 'San Marino':
            self.country =  "674"
        if self.country == 'Sao Tome and Principe':
            self.country =  "678"
        if self.country == 'Saudi Arabia':
            self.country =  "682"
        if self.country == 'Senegal':
            self.country =  "686"
        if self.country == 'Serbia':
            self.country =  "688"
        if self.country == 'Seychelles':
            self.country =  "690"
        if self.country == 'Sierra Leone':
            self.country =  "694"
        if self.country == 'Singapore':
            self.country =  "702"
        if self.country == 'Sint Maarten':
            self.country =  "534"
        if self.country == 'Slovakia':
            self.country =  "703"
        if self.country == 'Slovenia':
            self.country =  "705"
        if self.country == 'olomon Islands':
            self.country =  "90"
        if self.country == 'Somalia':
            self.country =  "706"
        if self.country == 'South Africa':
            self.country =  "710"
        if self.country == 'South Georgia and the South Sandwich Islands':
            self.country =  "239"
        if self.country == 'South Korea':
            self.country =  "410"
        if self.country == 'South Sudan':
            self.country =  "728"
        if self.country == 'Spain':
            self.country =  "724"
        if self.country == 'Sri Lanka':
            self.country =  "144"
        if self.country == 'St. Helena':
            self.country =  "654"
        if self.country == 'St. Kitts and Nevis':
            self.country =  "659"
        if self.country == 'St. Lucia':
            self.country =  "662"
        if self.country == 'St. Vincent and the Grenadines':
            self.country =  "670"
        if self.country == 'Sudan':
            self.country =  "729"
        if self.country == 'Suriname':
            self.country =  "740"
        if self.country == 'Swaziland':
            self.country =  "748"
        if self.country == 'Sweden':
            self.country =  "752"
        if self.country == 'Switzerland':
            self.country =  "756"
        if self.country == 'Syria':
            self.country =  "760"
        if self.country == 'Taiwan':
            self.country =  "158"
        if self.country == 'Tajikistan':
            self.country =  "762"
        if self.country == 'Tanzania':
            self.country =  "834"
        if self.country == 'Thailand':
            self.country =  "764"
        if self.country == 'Togo':
            self.country =  "768"
        if self.country == 'Tokelau':
            self.country =  "772"
        if self.country == 'Tonga':
            self.country =  "776"
        if self.country == 'Trinidad and Tobago':
            self.country =  "780"
        if self.country == 'Tunisia':
            self.country =  "788"
        if self.country == 'Turkey':
            self.country =  "792"
        if self.country == 'Turkmenistan':
            self.country =  "795"
        if self.country == 'Turks and Caicos Islands':
            self.country =  "796"
        if self.country == 'Tuvalu':
            self.country =  "798"
        if self.country == 'U.S. Virgin Islands':
            self.country =  "850"
        if self.country == 'Uganda':
            self.country =  "800"
        if self.country == 'Ukraine':
            self.country =  "804"
        if self.country == 'United Arab Emirates':
            self.country =  "784"
        if self.country == 'United Kingdom':
            self.country =  "826"
        if self.country == 'United States':
            self.country =  "840"
        if self.country == 'United States Minor Outlying Islands':
            self.country =  "581"
        if self.country == 'Uruguay':
            self.country =  "858"
        if self.country == 'Uzbekistan':
            self.country =  "860"
        if self.country == 'Vanuatu':
            self.country =  "548"
        if self.country == 'Vatican City':
            self.country =  "336"
        if self.country == 'Venezuela':
            self.country =  "862"
        if self.country == 'Vietnam':
            self.country =  "704"
        if self.country == 'Western Sahara':
            self.country =  "732"
        if self.country == 'Yemen':
            self.country =  "887"
        if self.country == 'Zambia':
            self.country =  "894"
        if self.country == 'Zimbabwe':
            self.country =  "716"

        self.balance = balancefunc()

        self.bar()


        self.delay = int(config['delay'])

        warn(f'[TASK {self.threadID}] [PRODIRECT] - Task started!')


        if self.mode == 'LOGIN':
            self.login()
        else:
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
                f'Phoenix AIO {self.version} - PRODIRECT Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO {self.version} - PRODIRECT Running | 2cap Balance: {self.balance} | Checkout: {checkoutnum} | Carted: {carted} | Failed: {failed}\x07')

    def akamai(self):
        try:

            try:

                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "prodirectsoccer")
                file_to_open = os.path.join(path, "akamai.txt")
                with open (file_to_open, 'r') as f:
                    captchalist = f.read().splitlines()       
                    self.abck = captchalist[0]     
                with open (file_to_open, 'w') as f:
                    for line in captchalist:
                        if line != self.abck:
                            f.write(line + "\n")
                f.close()

                return info(f'[TASK {self.threadID}] [PRODIRECT] - Got akamai from txt, proceeding!')

            except Exception as e:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Exception getting akamai, retrying...')
                time.sleep(self.delay)
                self.akamai()
        except:
            pass
    
    def getprod(self):

        try:
            global carted, failed, checkoutnum

            try:

                headers = {
                    'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding' : 'utf-8',
                    'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'sec-fetch-dest' : 'document',
                    'sec-fetch-mode' : 'navigate',
                    'upgrade-insecure-requests' : '1',
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
                }

                while True:

                    r = self.s.get(self.link, proxies = self.selected_proxies, headers = headers)

                    if r.status_code == 200:


                        self.akamai()
                        
                        try:

                            self.pidlungo = r.text.split('data-product-id="')[1].split('"')[0]

                            json1 = r.text.split('<script type="application/ld+json">')[1].split('</script>')[0]

                            json1 = json1.strip()

                            json1 = json.loads(json1)
                            self.title = json1['name']
                            self.pid = json1['sku']
                            num = len(self.pid)

                            variantsinstock = []

                            instroecks = json1['offers']
                            for element in instroecks:
                                sku = element['sku'][num:]
                                variantsinstock.append(sku)

                            if len(variantsinstock) < 1:
                                warn(f'[TASK {self.threadID}] [PRODIRECT] - Product OOS, monitoring...')
                                time.sleep(self.delay)
                                continue

                            else:
                                warn(f'[TASK {self.threadID}] [PRODIRECT] - {self.title} in stock!')
                                self.varianti = variantsinstock
                                break

                        except:
                            warn(f'[TASK {self.threadID}] [PRODIRECT] - Product OOS, monitoring...')
                            time.sleep(self.delay)
                            continue

                    
                    elif r.status_code == 404:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Page is not loaded, retrying...')
                        time.sleep(self.delay)
                        continue
                        
                        
                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, farming akamai...')
                        self.akamai()
                        continue
                        
                    else:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Error {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                self.atc()

            except Exception as e:

                error(f'[TASK {self.threadID}] [PRODIRECT] - Exception getting product, retrying...')
                time.sleep(self.delay)

                self.getprod()

        except:
            pass

    def atc(self):

        try:

            global carted, failed, checkoutnum

            try:

                while True:

                    self.headers = {
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                        'Connection': 'keep-alive',
                        'Content-Type': 'application/json;charset=UTF-8',
                        'Referer': self.link,
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
                        'X-NewRelic-ID': 'VQQBV1dTABACUlZUAAACV1Q='
                    }
                    
                    payload = {"productId":self.pidlungo,"variantId":random.choice(self.varianti),"locale":"GB","quantity":1,"personalisation":[],"updateDeliveryInfo":False,"kitData":'none'}
                    print(payload)

                    self.cookie_obj = requests.cookies.create_cookie(domain='.prodirectsoccer.com',name='_abck',value=self.abck)
                    self.s.cookies.set_cookie(self.cookie_obj)

                    r = self.s.post('https://www.prodirectsoccer.com/client/api/basket/addBasketLine', headers = self.headers, data = payload)
                    print(r.status_code)
                    print(r.text)

                    if r.status_code == 200:
                        info(f'[TASK {self.threadID}] [PRODIRECT] - Added to cart!')
                        carted = carted + 1
                        self.bar()
                        break

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, farming akamai...')
                        self.akamai()
                        continue
                    
                    elif r.status_code >= 500 and r.status_code <= 600:
                            warn(f'[TASK {self.threadID}] [PRODIRECT] - Site down, retrying...')
                            time.sleep(self.delay)
                            continue

                    elif r.status_code == 429:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Error {r.status_code}, retrying...')
                        time.sleep(self.delay)
                        self.getprod()

                sys.exit(1)
            except Exception as e:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Atc failed, monitoring...')
                self.getprod()

        except:
            pass

    def cart(self):

        try:

            warn(f'[TASK {self.threadID}] [PRODIRECT] - Checking cart...')
            try:

                headers = {
                    'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding' :'gzip, deflate, br',
                    'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'cache-control' : 'max-age=0',
                    'content-type' : 'application/x-www-form-urlencoded',
                    'origin' : 'https://www.prodirectbasketball.com',
                    'referer' : self.link,
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
                }


                while True:

                    r = self.s.get("https://www.prodirectbasketball.com/V3_1/V3_1_Basket.aspx", proxies = self.selected_proxies, headers = headers)

                    if r.status_code == 200:

                        if "Sorry, the highlighted item" in r.text:
                            warn(f'[TASK {self.threadID}] [PRODIRECT] - Cart OOS, clearing...')

                            payload = {
                                "__EVENTTARGET": "dlw100$Remove$1",
                                "dlw100$Update$1": "1",
                                "dlwl00$Voucher$txt": ""
                            }

                            while r.status_code not in (200,201):
                                warn(f'[TASK {self.threadID}] [PRODIRECT] - Cart not cleared, retrying...')
                                time.sleep(self.delay)
                                r = self.s.post("https://www.prodirectbasketball.com/V3_1/V3_1_Basket.aspx", data = payload, proxies = self.selected_proxies, headers = headers)


                            info(f'[TASK {self.threadID}] [PRODIRECT] - Cart cleared, back to monitoring...')
                            time.sleep(self.delay)
                            self.getprod()

                            

                        elif "Your basket is empty" in r.text:
                            warn(f'[TASK {self.threadID}] [PRODIRECT] - Cart empty, back to monitoring...')
                            self.getprod()

                        else:
                            
                            soup = bs(r.text, "html.parser")
                            img = soup.find("div", {"class":"img-holder"})
                            img2 = img.find("img")["src"]
                            self.img = f"https://www.prodirectbasketball.com{img2}"
                            title = soup.find("div", {"class":"text-holder"})
                            self.title = title.find("a").text
                            break


                    elif r.status_code >= 500 and r.status_code <= 600:
                            warn(f'[TASK {self.threadID}] [PRODIRECT] - Site down, retrying...')
                            time.sleep(self.delay)
                            continue

                    elif r.status_code == 429:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        continue

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, changing akamai...')
                        self.akamai()
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Error {r.status_code}, retrying...')

                        time.sleep(self.delay)
                        continue
                
                warn(f'[TASK {self.threadID}] [PRODIRECT] - Cart checked, proceding...')
                if self.mode == "LOGIN":
                    self.ship()
                elif self.mode == 'REGISTER':
                    self.register()
                else:
                    self.login()

            except Exception as e:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Exception checking cart, retrying...')
                time.sleep(self.delay)
                self.cart()

        except:
            pass

    def login(self):

        try:

            warn(f'[TASK {self.threadID}] [PRODIRECT] - Logging in...')

            self.akamai()

            try:

                headers = {
                    'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding' :'gzip, deflate, br',
                    'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'cache-control' : 'max-age=0',
                    'content-type' : 'application/x-www-form-urlencoded',
                    'origin' : 'https://www.prodirectbasketball.com',
                    'referer' : 'https://www.prodirectbasketball.com/accounts/MyAccount.aspx',
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
                }

                while True:

                    try:
                        t = requests.get("http://phoenix.prodirectbasketball.com:5000/api/token")
                        resp=t.text
                        if '"success":true}' in resp:
                            info(f'[TASK {self.threadID}] [PRODIRECT] - Token ready from harvester!')
                            self.captcha = resp.split('"results":"')[1].split('","success"')[0]
                            info(f'[TASK {self.threadID}] [PRODIRECT] - Captcha solved!')

                        else:
                            warn(f'[TASK {self.threadID}] [PRODIRECT] - Waiting for captcha...')
                            api = TwoCaptcha(str(config['2captcha']), sleep_time=0.1)
                            self.captcha = api.solve_captcha(page_url="https://www.prodirectbasketball.com/accounts/MyAccount.aspx", site_key='6LdXsbwUAAAAAMe1vJVElW1JpeizmksakCUkLL8g')
                            if self.captcha == 'list index out of range':
                                error(f'[TASK {self.threadID}] [PRODIRECT]- Captcha failed, retrying...')
                                continue
                            else:
                                info(f'[TASK {self.threadID}] [PRODIRECT] - Captcha solved!')

                    except:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Waiting for captcha...')
                        api = TwoCaptcha(str(config['2captcha']))
                        self.captcha = api.solve_captcha(page_url="https://www.prodirectbasketball.com/accounts/MyAccount.aspx", site_key='6LdXsbwUAAAAAMe1vJVElW1JpeizmksakCUkLL8g')
                        if self.captcha == 'list index out of range':
                            error(f'[TASK {self.threadID}] [PRODIRECT]- Captcha failed, retrying...')
                            continue
                        else:
                            info(f'[TASK {self.threadID}] [PRODIRECT] - Captcha solved!')
                            

                    payload = {
                        'loginemail' : self.account,
                        'loginpassword' : self.password,
                        'g-recaptcha-response': self.captcha,
                        '__EVENTTARGET' : 'LogIn'
                    }

                    self.cookie_obj = requests.cookies.create_cookie(domain='.prodirectbasketball.com',name='_abck',value=self.abck)
                    self.s.cookies.set_cookie(self.cookie_obj)

                    r = self.s.post("https://www.prodirectbasketball.com/accounts/MyAccount.aspx", headers = headers, proxies = self.selected_proxies, data = payload, allow_redirects = False)

                    if r.status_code == 302:
                        info(f'[TASK {self.threadID}] [PRODIRECT] - Logged in!')
                        break

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, changing akamai...')
                        self.akamai()
                        continue

                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Site down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        continue
                    
                    elif 'Email address or password specified was incorrect' in r.text:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Invalid credentials, check your information in csv')
                        exit(1)

                    else:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Error {r.status_code}, retrying')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                
                if "RANDOM" in self.account:
                    self.register()
                else:
                    if self.mode == "LOGIN":
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Getting product...')
                        self.getprod()                
                    else:
                        self.ship()

            except Exception as e:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Exception during login, retrying...')
                time.sleep(5)

                self.login()
        
        except:
            pass

    def register(self):

        try:

            warn(f'[TASK {self.threadID}] [PRODIRECT] - Creating account...')

            try:

                headers = {
                    'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding' :'gzip, deflate, br',
                    'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'cache-control' : 'max-age=0',
                    'content-type' : 'application/x-www-form-urlencoded',
                    'origin' : 'https://www.prodirectbasketball.com',
                    'referer' : self.link,
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
                }

                while True:

                    try:
                        t = requests.get("http://phoenix.prodirectbasketball.com:5000/api/token")
                        resp=t.text
                        if '"success":true}' in resp:
                            info(f'[TASK {self.threadID}] [PRODIRECT] - Token ready from harvester!')
                            self.captcha = resp.split('"results":"')[1].split('","success"')[0]
                            info(f'[TASK {self.threadID}] [PRODIRECT] - Captcha solved!')

                        else:
                            warn(f'[TASK {self.threadID}] [PRODIRECT] - Waiting for captcha...')
                            api = TwoCaptcha(str(config['2captcha']), sleep_time=0.1)
                            self.captcha = api.solve_captcha(page_url="https://www.prodirectbasketball.com/accounts/MyAccount.aspx", site_key='6LdXsbwUAAAAAMe1vJVElW1JpeizmksakCUkLL8g')
                            if self.captcha == 'list index out of range':
                                error(f'[TASK {self.threadID}] [PRODIRECT]- Captcha failed, retrying...')
                                continue
                            else:
                                info(f'[TASK {self.threadID}] [PRODIRECT] - Captcha solved!')

                    except:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Waiting for captcha...')
                        api = TwoCaptcha(str(config['2captcha']))
                        self.captcha = api.solve_captcha(page_url="https://www.prodirectbasketball.com/accounts/MyAccount.aspx", site_key='6LdXsbwUAAAAAMe1vJVElW1JpeizmksakCUkLL8g')
                        if self.captcha == 'list index out of range':
                            error(f'[TASK {self.threadID}] [PRODIRECT]- Captcha failed, retrying...')
                            continue
                        else:
                            info(f'[TASK {self.threadID}] [PRODIRECT] - Captcha solved!')
                            

                    payload = {
                        'registeremail' : self.account,
                        'registerpassword' : self.password,
                        'g-recaptcha-response': self.captcha,
                        '__EVENTTARGET' : 'Register'
                    }
            
                    self.cookie_obj = requests.cookies.create_cookie(domain='.prodirectbasketball.com',name='_abck',value=self.abck)
                    self.s.cookies.set_cookie(self.cookie_obj)

                    r = self.s.post("https://www.prodirectbasketball.com/accounts/MyAccount.aspx?Return=Checkout", headers = headers, proxies = self.selected_proxies, data = payload, allow_redirects = True)

                    if r.status_code == 200:
                        info(f'[TASK {self.threadID}] [PRODIRECT] - Account created!')
                        break

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, changing akamai...')
                        self.akamai()
                        continue

                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Site down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Error {r.status_code}, retrying')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        continue

                

                self.registership()

            except Exception as e:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Exception during login, retrying...')
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.register()

        except:
            pass

    def registership(self):

        try:

            warn(f'[TASK {self.threadID}] [PRODIRECT] - Submitting shipping...')

            headers = {
                'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding' :'gzip, deflate, br',
                'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                'cache-control' : 'max-age=0',
                'content-type' : 'application/x-www-form-urlencoded',
                'origin' : 'https://www.prodirectbasketball.com',
                'referer' : self.link,
                'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
            }

            payload = {
                'firstname':self.name,
                'lastname':self.surname,
                'defaultlookupprop':self.address,
                'defaultlookuppostcode':self.zipcode,
                'defaultAddressLine1':self.address,
                'defaultAddressLine2':self.address2,
                'defaulttown':self.city,
                'defaultcounty':self.region,
                'defaultpostcode':self.zipcode,
                'txtAddressID':'0',
                'defaultCountryCode':self.country,
                'defaultStateCode':'',
                'phonenumber':self.phone,
                '__EVENTTARGET':'MDSave'
            }

            try:

                while True:

                    #self.cookie_obj = requests.cookies.create_cookie(domain='.prodirectbasketball.com',name='_abck',value=self.abck)
                    #self.s.cookies.set_cookie(self.cookie_obj)

                    r = self.s.post("https://www.prodirectbasketball.com/accounts/checkout.aspx?acc=completecustomer&return=addr", data = payload, proxies = self.selected_proxies, headers = headers)

                    if r.status_code == 200:
                        
                        resp = r.text
                        self.addid = resp.split('txtAddressID" value="')[1].split('"')[0]
                        info(f'[TASK {self.threadID}] [PRODIRECT] - Succesfully submitted ship')
                        break

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, changing akamai...')
                        self.akamai()
                        continue

                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Site down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Error {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        self.cart()

                self.ship2()

            except Exception as e:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Error while getting shipping, retrying...')
                self.registership()

        except:
            pass

    def ship(self):

        try:   
            warn(f'[TASK {self.threadID}] [PRODIRECT] - Getting checkout page...')

            try:
                
                headers = {
                    'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding' :'gzip, deflate, br',
                    'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'cache-control' : 'max-age=0',
                    'content-type' : 'application/x-www-form-urlencoded',
                    'origin' : 'https://www.prodirectbasketball.com',
                    'referer' : self.link,
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
                }

                while True:
                    r = self.s.get("https://www.prodirectbasketball.com/accounts/checkout.aspx?acc=addr", proxies = self.selected_proxies, headers = headers)

                    if r.status_code == 200:
                        
                        resp = r.text
                        self.addid = resp.split('txtAddressID" value="')[1].split('"')[0]
                        #id4 = id3.find("input", {"name":"txtAddressID"})
                        #self.addid = id4["value"]
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Submitting shipping...')
                        break

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, changing akamai...')
                        self.akamai()
                        continue

                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Site down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Error {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        self.cart()

                self.ship2()
            except Exception as e:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Error while getting shipping, retrying...')
                self.ship()

        except:
            pass

    def ship2(self):

        try:

            warn(f'[TASK {self.threadID}] [PRODIRECT] - Submitting billing...')

            try:

                headers = {
                    'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding' :'gzip, deflate, br',
                    'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'cache-control' : 'max-age=0',
                    'content-type' : 'application/x-www-form-urlencoded',
                    'origin' : 'https://www.prodirectbasketball.com',
                    'referer' : 'https://www.prodirectbasketball.com/accounts/Checkout.aspx?ACC=PAYD',
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
                }

                payload = {
                    'myName' : self.completename,
                    'txtAddressID' : self.addid,
                    'txtAddressID' : self.addid,
                    '__EVENTTARGET' : 'fw100$btnProceedPayment'
                }

                while True:

                    self.cookie_obj = requests.cookies.create_cookie(domain='.prodirectbasketball.com',name='_abck',value=self.abck)
                    self.s.cookies.set_cookie(self.cookie_obj)

                    r = self.s.post("https://www.prodirectbasketball.com/accounts/Checkout.aspx?ACC=PAYD", proxies = self.selected_proxies, headers = headers, data = payload)

                    if r.status_code == 200:

                        if "CheckOut Payment Details" in r.text:

                            

                            break

                        else:
                            error(f'[TASK {self.threadID}] [PRODIRECT] - Error placing order, retrying...')
                            time.sleep(self.delay)
                            self.cart()

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, changing akamai...')
                        self.akamai()
                        continue

                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Site down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        continue

                    else:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Error {r.status_code}, retrying...')
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        time.sleep(self.delay)
                        self.ship2()

                self.checkout()
            except:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Exception while placing order, retrying...')
                time.sleep(self.delay)
                self.ship()

        except:
            pass

    def checkout(self):

        try:

            warn(f'[TASK {self.threadID}] [PRODIRECT] - Placing order...')

            global carted, failed, checkoutnum

            try:

                headers = {
                    'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'accept-encoding' :'gzip, deflate, br',
                    'accept-language' : 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
                    'cache-control' : 'max-age=0',
                    'content-type' : 'application/x-www-form-urlencoded',
                    'origin' : 'https://www.prodirectbasketball.com',
                    'referer' : 'https://www.prodirectbasketball.com/accounts/Checkout.aspx?ACC=PAYD',
                    'sec-fetch-dest' : 'document',
                    'sec-fetch-mode' : 'navigate',
                    'sec-fetch-site' : 'same-origin',
                    'sec-fetch-user' : '?1',
                    'upgrade-insecure-requests' : '1',
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
                }

                payload = {
                    'deliveryOptionInfo' : 'STANDARD',
                    'paymentOption' : 'paypal',
                    'rbCard' : 'newcard',
                    'CardType' : 'Adyen',
                    'tbxIagree' : 'agree',
                    '__EVENTTARGET' : 'fw100$btnGoToPayNow'
                }

                while True:

                    r = self.s.post("https://www.prodirectbasketball.com/accounts/Checkout.aspx?ACC=PAYD", proxies = self.selected_proxies, data = payload, headers = headers)

                    if r.status_code == 200:

                        html = r.text
                        path = os.path.dirname(__file__).rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), "prodirect")   
                        file_to_open = os.path.join(path, f"checkout{self.threadID}.html")
                        

                        with open(file_to_open, 'w') as f:
                            f.write(html)
                        
                        chrome_options = webdriver.ChromeOptions()


                        aaa = os.path.abspath(f"prodirect/checkout{self.threadID}.html")
                        url = 'file://' + aaa
                        chrome_options.headless = True
                        
                        chrome_options.add_argument("--disable-gpu")
                        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
                        pathchrome = os.path.join(os.path.dirname(sys.argv[0]), "chromedriver")
                        driver = webdriver.Chrome(pathchrome, chrome_options=chrome_options)
                        driver.get(url)
                        info(f'[TASK {self.threadID}] [PRODIRECT] - Successfully checked out!')
                        checkoutnum = checkoutnum + 1
                        self.bar()
                        self.pp = driver.current_url                
                        break

                    elif r.status_code == 403:
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Access denied, changing akamai...')
                        self.akamai()
                        continue

                    elif r.status_code >= 500 and r.status_code <= 600:
                        warn(f'[TASK {self.threadID}] [PRODIRECT] - Site down, retrying...')
                        time.sleep(self.delay)
                        continue

                    elif r.status_code == 429:
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        error(f'[TASK {self.threadID}] [PRODIRECT] - Rate limit, retrying...')
                        time.sleep(self.delay)
                        self.s.cookies.clear()
                        continue

                self.pass_cookies()

            except Exception as e:
                error(f'[TASK {self.threadID}] [PRODIRECT] - Checkout failed, retrying...')
                failed = failed + 1
                self.bar()
                if self.all_proxies != None:
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    self.s.proxies = self.selected_proxies
                time.sleep(self.delay)
                self.cart()
        except:
            pass
        
    def webhook(self):
        try:
            if self.mode == "":
                self.mode = "EMPTY"
            if self.selected_proxies == None:
                self.proxi = 'LOCAL'
            info(f'[TASK {self.threadID}] [PRODIRECT] - Sending webhook')
            webhook = DiscordWebhook(url=self.webhook_url, content = "")
            embed = DiscordEmbed(title='Phoenix AIO Success - Click to complete the checkout!', url = self.expToken, color = 0x715aff)
            embed.add_embed_field(name='**PRODIRECT**', value = f'{self.title}', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizechosen}', inline = True)
            embed.add_embed_field(name='**MODE**', value = f'{self.mode}', inline = False)
            embed.add_embed_field(name='**ACCOUNT**', value = f'||{self.account}||', inline = False)
            embed.add_embed_field(name='**PASSWORD**', value = f'||{self.password}||', inline = False)
            embed.add_embed_field(name='**PROXY**', value = f"||{self.proxi}||", inline = False)
            embed.add_embed_field(name='Checkout Mobile', value = f"[LINK]({self.expToken2})", inline = False)
            embed.set_thumbnail(url = self.img)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            self.Pubblic_Webhook()
        except:
            pass


    
    def Pubblic_Webhook(self):
        try:
            webhook = DiscordWebhook(url=random.choice(self.listsuccess), content = "")
            embed = DiscordEmbed(title='Phoenix AIO - Successfully checked out!', color = 40703)
            embed.add_embed_field(name='**PRODIRECT**', value = f'{self.title}', inline = False)
            embed.add_embed_field(name='**PRODUCT**', value = f'[LINK]({self.link})', inline = True)
            embed.add_embed_field(name='**SIZE**', value = f'{self.sizechosen}', inline = True)
            embed.add_embed_field(name='**MODE**', value = f'{self.mode}', inline = False)
            embed.add_embed_field(name='Delay', value = self.delay, inline = True)
            embed.add_embed_field(name='Timeout', value = self.timeout, inline = True)
            embed.set_thumbnail(url = self.img)   
            embed.set_footer(text = f"Phoenix AIO v{self.version}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()

            try:
                playsound('checkout.wav')
                warn("")
            except:
                warn("")
        except:
            pass


    def pass_cookies(self):
        try:

            try:
                cookieStr = ""
                cookies = [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path, 'url': ''} for c in self.s.cookies]
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
                        writer.writerow({'SITE':'PRODIRECT','SIZE':f'{self.sizechosen}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                        

                else:
                    self.expToken = self.token
                    with open(path,'a',newline='') as f:
                        fieldnames = ["SITE","SIZE","PAYLINK","PRODUCT"]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow({'SITE':'PRODIRECT','SIZE':f'{self.sizechosen}','PAYLINK':f'{self.token}','PRODUCT':f'{self.title}'})
                
                self.webhook()


            except Exception as e: 
                error(f'[TASK {self.threadID}] [PRODIRECT] - Exception while passing cookies, retrying...') 
                time.sleep(self.delay)
                self.pass_cookies()
            
        except:
            pass





