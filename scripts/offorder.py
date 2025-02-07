import json, requests, threading, certifi, ssl, socket, hashlib, psutil, tempfile, csv, urllib3, sys, random, base64, platform, hashlib, random, atexit, ctypes, logging, webbrowser, signal, os, uuid, string
from mods.logger import info, warn, error
from random import randint
import requests
import cloudscraper
from discord_webhook import DiscordWebhook, DiscordEmbed
import lxml
from bs4 import BeautifulSoup as bs
import logging
import time, datetime
import re
import urllib.parse
import names
from card_identifier.card_type import identify_card_type
import uuid
from requests_html import HTMLSession
from twocaptcha import TwoCaptcha
from hawk_cf_api.hawk_cf import CF_2
from helheim import helheim


urllib3.disable_warnings()
machineOS = platform.system()
sys.dont_write_bytecode = True

threads = {}
ipaddr = None

cnum = 0

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

    error("FAILED TO READ CONFIG")
    pass



class OFFORDER():

    def __init__(self, row, webhook, version, i, DISCORD_ID):

        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), 'offorder/proxies.txt')
            elif machineOS == "Windows": 
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "offorder/proxies.txt")
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

        discord = DISCORD_ID
        
        if config['anticaptcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'anticaptcha','api_key':config['anticaptcha'], 'no_proxy':True},doubleDown=False,requestPostHook=self.injection,debug=False)
        elif config['2captcha'] != "":
            self.s = cloudscraper.create_scraper(browser={'browser': 'chrome','mobile': False,'platform': 'windows'},captcha={'provider':'2captcha','api_key':config['2captcha'], 'no_proxy':True},doubleDown=False,requestPostHook=self.injection,debug=False)
        else:
            error('2CAPTCHA OR ANTICAPTCHA NEEDED')
            time.sleep(5)
            sys.exit(1)
        
        self.email = row['MAIL']
        self.password = row['PASSWORD']
        self.country = 'IT'

        if self.country == "UK":
            self.country = "GB"

        if self.country == "UK" or self.country == "GB":
            self.currency = "GBP"
        elif self.country == "RU":
            self.currency = "RUB"
        elif self.country == "US":
            self.currency = "USD"
        else:
            self.currency = "EUR"

        self.threadID = '%03d' % i
        self.twoCaptcha = str(config['2captcha'])

        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
            self.s.proxies = self.selected_proxies
        self.bar()

        warn(f'[TASK {self.threadID}] [GEN_OFF] - Starting tasks...')
        self.register()


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
            return ctypes.windll.kernel32.SetConsoleTitleW(
                f'Phoenix AIO - OFF WHITE ACC Running | Generated: {cnum}')

        else:
            sys.stdout.write(f'\x1b]2;Phoenix AIO - OFF WHITE ACC Running | Generated: {cnum}\x07')

    def injection(self, session, response):
        self.bar()
        try:
            if session.is_New_IUAM_Challenge(response) \
            or session.is_New_Captcha_Challenge(response) \
            or session.is_BFM_Challenge(response):
                warn('Solving Cloudflare v2')
                return helheim('a9a8428e-d8b9-4f9d-b4bf-54fd3b6ae693', session, response)
            else:
                return response
        except Exception as e:
            print(e)
            if self.all_proxies != None:
                self.selected_proxies = self.choose_proxy(self.all_proxies)
                self.s.proxies = self.selected_proxies
            self.register()
            #if session.is_New_IUAM_Challenge(response):
            #    warn('Solving Cloudflare v2 api 2')
            #    return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=False,debug=False).solve() 
            #elif session.is_New_Captcha_Challenge(response):
            #    warn('Solving Cloudflare v2 api 2')
            #    return CF_2(session,response,key="4c2075db-9f9f-4395-83e6-ec0c6dd6940b",captcha=True,debug=True).solve() 
            #else:
            #    return response
   
    def register(self):

        self.mom = False

        global cnum


        try:

            if self.country == 'IT':
                self.countrynum = '101'

            if self.country == 'FR':
                self.countrynum = "70"
#
            if self.country == 'CH':
                self.countrynum = "197"
#
            if self.country == 'ES':
                self.countrynum = "187"
#
            if self.country == 'DE':
                self.countrynum = "77"
#
            if self.country == 'DK':
                self.countrynum = "54"
#
            if self.country == 'GB':
                self.countrynum = "215"
#
            if self.country == 'AT':
                self.countrynum = "13"
#
            if self.country == 'GR':
                self.countrynum = "80"
#
            if self.country == 'RU':
                self.countrynum = "170"
#
            if self.country == 'FI':
                self.countrynum = "69"
            
            if self.country == 'SK':
                self.countrynum = "182"
#
            if self.country == 'CZ':
                self.countrynum = "53"
            
            if self.country == 'NL':
                self.countrynum = "144"
#
            if self.country == 'SI':
                self.countrynum = "183"
#
            if self.country == 'PL':
                self.countrynum = "164"
            
            while True:
#
                self.stop = False
                headers = {
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-GB",
                    'Accept-Encoding': 'utf-8',
                    'content-type': 'application/json',
                    'ff-country': self.country,
                    'ff-currency': self.currency,
                    'referer': 'https://www.emiliopucci.com/',
                    "cookie": "ss=sdjfpdsjfjkdspfds-fds-fdsfdsfdsjifdspjofd",
                    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1'
                }
                self.s.headers.update(headers)
                x = self.s.get('https://www.emiliopucci.com/it-it/account/login')
                print(x.status_code)
                payload = {"username":self.email,"password":self.password,"rememberMe":True}
                r = self.s.post(f"https://www.emiliopucci.com/en-{self.country}/api/account/login", json = payload)
                if r.status_code == 200:
                    self.bagid = r.text.split('{"bagId":"')[1].split('"')[0]   
                    info(f'[TASK {self.threadID}] [OFF--WHITE] - Successfully logged in!')
                    del self.s.headers['cookie']
                    head = {
                        'x-newrelic-id': 'VQUCV1ZUGwIFVlBRDgcA'
                    }
                    self.s.headers.update(head)
                    warn('checking')
                    x = self.s.get('https://www.emiliopucci.com/it-it/api/orders')
                    print(x.status_code)
                    if x.status_code == 200:
                        jsonc = json.loads(x.text)
                        a = jsonc['items']['entries']
                        self.order = []
                        self.status = []
                        if a:
                            for i in a:
                                #self.order = i['id']
                                #if self.order in orderlist:
                                self.order.append(i['status'])
                                self.status.append(i['id'])
                                
                            tot = zip(self.order, self.status)
                            self.connecto = list(tot)
                            break

                            

                                
                        else:
                            error('No orders on this acccount')
                            self.stop = True
                            break
                    else:
                        error(x.status_code)
                        if self.all_proxies != None:
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            self.s.proxies = self.selected_proxies
                        continue
                else:
                    error(r.status_code)
                    if self.all_proxies != None:
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        self.s.proxies = self.selected_proxies
                    continue
            
            if self.stop:
                print('a')
                sys.exit()
#
            self.csvsave()
#
#
#
        except Exception as e:
            error(f'[TASK {self.threadID}] [GEN_OFF] - Exception generating account: {e}')

    #def webhook(self):
    #    webh = ['https://discord.com/api/webhooks/832992942679392307/5_Ky6VGcXDelcQjKvqRbHqb0LOansRy8iBJ5jmXh_WHUBy88fl9EOoI8K_GpEGF6txpm', 'https://discord.com/api/webhooks/826587759174352918/PyCvmbfnu-nkqdsWXCkn3r38vJZonzSi7jDkp5rZ4FcunUgDb7eQhmhq7YKz-ZvXYQiW','https://discord.com/api/webhooks/832992941520715827/jGsyfVb8tAnzUq394nvIAyiFqviqfsOPpGfUmm1sG67BOA1HMcCvcpVPrTbDfJCZ44mR','https://discord.com/api/webhooks/832992935317340220/LyKhs9uRnvwxqNj9mqmqWjP0zjmVeNOjUl-5nC0AY3X37M-VPPrZnb7_hAVRbu0rXpeR','https://discord.com/api/webhooks/832992934671548477/ikjwuZ62SjrYmL1YdfO2rDXiHK3_MxeyKvs9YPfJgHJXTEDRGFzPChj_qQ2CQHiJzkcg','https://discord.com/api/webhooks/832992933535416341/IjyskKQRJQlO5sPIbh7oUdFh1WD9N8Bd7XR_qYxkhfxyRcLCKd7I00y7JEWxxR6VhETx','https://discord.com/api/webhooks/832992928954712065/aHJvWp0bI63fA1UE-MRieDQuHT0lA5fZANBmBMvWxmbO5-5dEJ_RftsEuYXE5kRuIDzP']
    #    webhook = DiscordWebhook(url=random.choice(webh), content = "")
    #    embed = DiscordEmbed(title='OFF WHITE - Order Found!', color = 0x715aff)
    #    embed.add_embed_field(name=f'**EMAIL**', value = f'||{self.email}||', inline = True)
    #    embed.add_embed_field(name=f'**PASSWORD**', value = f'||{self.password}||', inline = True)
    #    embed.add_embed_field(name='**ORDER**', value = f'||{self.order}||', inline = False)
    #    embed.add_embed_field(name='**STATUS**', value = self.status, inline = False)
    #    embed.set_footer(text = f"Phoenix AIO v PORCODIO", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
    #    webhook.add_embed(embed)
    #    webhook.execute()
    #    self.SavingAccount()


    def csvsave(self):
        global cnum
        path = os.path.dirname(__file__).rsplit('/', 1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), "offorder")
        file_to_open = os.path.join(path, "success.csv")
        with open(file_to_open,'a',newline='') as f:
            fieldnames = ["MAIL","PASSWORD","ORDER","STATUS"]
            for i in self.connecto:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow({'MAIL':self.email,'PASSWORD':f'{self.password}','ORDER':f'{i[0]}','STATUS':f'{i[1]}'})
        cnum = cnum + 1
        self.bar()

    #def SavingAccount(self):
#
    #    global cnum
    #    txt = self.email + ':' + self.password
    #    warn(f'[TASK {self.threadID}] [GEN_OFF] - Saving account...')
    #    try:
    #        path = os.path.dirname(__file__).rsplit('/', 1)[0]
    #        path = os.path.join(os.path.dirname(sys.argv[0]), "offorder")
    #        file_to_open = os.path.join(path, "output.txt")
    #        with open(file_to_open, 'a') as output:
    #            output.writelines(f'{txt}\n')
    #            output.close()
    #            info(f'[TASK {self.threadID}] [GEN_OFF] - Accoutn saved in txt!')
    #            cnum = cnum + 1
    #            self.bar()
    #    except Exception as e:
    #        error(f'[TASK {self.threadID}] [GEN_OFF] - Failed saving account {e}')


    #def converse(self):
    #    
    #    header = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9','cookie': '_abck=0E66606B49739759B81BAEB913ADEF93~-1~YAAQ38gWw19+cN54AQAAZFZj6gUMZnVsu+h9jl+a6JnZ/aozG6JMR40KJHPM2+MUsEehGDDpsVv71EeHaAdZYqfqpaCCDe3tazpHzMNe/q9NLg0LLYhqGQJc/sOchv6TkyPDHgw0HYrhnBR5fRylyfV8D9btFrOO6m+1+9/aKQmtGjHkopSJczt7c9aHWqHJLbLQ4hJOriDC8KJ+RkLB0LFn9UR4VuMncSaGNn8oaWE2EZw02rl8qWEiRsJ73o4TivtVSl6Qe+F6RT7tpl/BR15VWuuiZMu+VSJvqDg2Tq1K4mUk7D90HmPfKvoRgY1HZdXziTIIng2SX+u92+RX2dVQqcd7IRJr156BakxwsyNZdXV9zNj7DsYIahW5Wt70ptcMfk5IFZcN+nOAtKYvTq7BDkmL~-1~-1~-1'}
    #    self.s.headers.update(header)
#
    #    #elf.cookie_obj = requests.cookies.create_cookie(name='_abck',value='0E66606B49739759B81BAEB913ADEF93~-1~YAAQ38gWw19+cN54AQAAZFZj6gUMZnVsu+h9jl+a6JnZ/aozG6JMR40KJHPM2+MUsEehGDDpsVv71EeHaAdZYqfqpaCCDe3tazpHzMNe/q9NLg0LLYhqGQJc/sOchv6TkyPDHgw0HYrhnBR5fRylyfV8D9btFrOO6m+1+9/aKQmtGjHkopSJczt7c9aHWqHJLbLQ4hJOriDC8KJ+RkLB0LFn9UR4VuMncSaGNn8oaWE2EZw02rl8qWEiRsJ73o4TivtVSl6Qe+F6RT7tpl/BR15VWuuiZMu+VSJvqDg2Tq1K4mUk7D90HmPfKvoRgY1HZdXziTIIng2SX+u92+RX2dVQqcd7IRJr156BakxwsyNZdXV9zNj7DsYIahW5Wt70ptcMfk5IFZcN+nOAtKYvTq7BDkmL~-1~-1~-1')
    #    #elf.s.cookies.set_cookie(self.cookie_obj)
    #    try:
    #        r = self.s.get('https://www.converse.com/on/demandware.store/Sites-converse-it-Site/it_IT/Order-ShowCheckStatusPopUp?format=ajax')
#
    #        if r.status_code == 200:
    #            self.token = r.text.split('csrf_token" value="')[1].split('"')[0]
    #            self.link = r.text.split('form action="')[1].split('"')[0]
    #            payload = {
    #                'csrf_token':self.token,
    #                'dwfrm_ordertrack_orderNumber':self.password,
    #                'dwfrm_ordertrack_orderEmail':self.email,
    #                'format':'ajax',
    #                'dwfrm_ordertrack_findorder':"Verifica stato dell'ordine"
    #            }
    #            x = self.s.post(self.link,data=payload)
    #            if x.status_code == 200:
    #                z = self.s.get('https://www.converse.com/on/demandware.store/Sites-converse-it-Site/it_IT/Order-CheckOrderStatus')
    #                if z.status_code == 200:
    #                    self.status = z.text.split('order_status_overall": "')[1].split('"')[0]
    #                    self.csvsave2()
    #                else:
    #                    error(z.status_code)
    #            else:
    #                print(x.status_code)
    #        else:
    #            warn(r.status_code)
    #    except Exception as e:
    #        print(e)
    #    
    #def csvsave2(self):
    #    global cnum
    #    path = os.path.dirname(__file__).rsplit('/', 1)[0]
    #    path = os.path.join(os.path.dirname(sys.argv[0]), "offorder")
    #    file_to_open = os.path.join(path, "success.csv")
    #    with open(file_to_open,'a',newline='') as f:
    #        fieldnames = ["MAIL","ORDER","STATUS"]
    #        writer = csv.DictWriter(f, fieldnames=fieldnames)
    #        writer.writerow({'MAIL':self.email,'ORDER':f'{self.password}','STATUS':f'{self.status}'})
    #    cnum = cnum + 1
    #    self.bar()