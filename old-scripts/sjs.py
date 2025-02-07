import requests, random, time, uuid, hashlib, hmac, base64, json, csv, threading ,sys, re, string, os, platform, logging, names
import urllib.parse
import urllib3
from mods.logger import info, warn, error
from random import randrange
from random import randint
from bs4 import BeautifulSoup as bs
import cloudscraper
from datetime import datetime
from os import urandom
import pytz
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask
from discord_webhook import DiscordEmbed, DiscordWebhook
from threading import Lock
from colorama import Fore, init
machineOS = platform.system()
#disable logging
#sys.tracebacklimit=0
# logging.getLogger('socketio').setLevel(logging.ERROR)
# logging.getLogger('engineio').setLevel(logging.ERROR)
# logging.getLogger('requests').setLevel(logging.ERROR)


def configWriter(json_obj, w_file):
    if machineOS == "Darwin":
        path = os.path.dirname(__file__).rsplit('/',1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), w_file)
    elif machineOS == "Windows":
        path = os.path.dirname(__file__).rsplit('\\',1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), w_file)
    with open(f'{path}', 'w') as f:
        json.dump(json_obj, f, indent=4)
        f.close()

try:
    if machineOS == "Darwin":
        path = os.path.dirname(__file__).rsplit('/',1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), "config.json")
    elif machineOS == "Windows":
        path = os.path.dirname(__file__).rsplit('\\',1)[0]
        path = os.path.join(os.path.dirname(sys.argv[0]), "config.json")
    with open(f'{path}', 'r') as f:
        config = json.load(f)
        f.close()
except Exception as e:
    
    print(f" Failed To Read Config File - [{e}]")
    pass

class SJS:
    def __init__(self, row, webhook, version, i, DISCORD_ID):
        
        try:
            if machineOS == "Darwin":
                path = os.path.dirname(__file__).rsplit('/', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "sjs/proxies.txt")
            elif machineOS == "Windows":
                path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                path = os.path.join(os.path.dirname(sys.argv[0]), "sjs/proxies.txt")
            with open(f'{path}', 'r') as f:
                proxylist = f.read()
                if proxylist == '':
                    self.all_proxies = None
                else:
                    self.all_proxies = proxylist.split('\n')
                f.close()
        except Exception as e:
            error("Failed To Read Proxies File - using no proxies ")
            self.all_proxies = None

        self.threadID = '%03d' % i
        self.delay = int(config['delay'])
        self.webhook = config['webhook']
        self.session = requests.Session()

        self.name = names.get_first_name(gender='male')
        self.surname = names.get_last_name()
        self.codice = f'{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.randint(000000,999999)}'
        print(self.codice)
        self.link = row['LINK']
        self.color = (random.choice(['Sesame Blue (DD1875-200)','Dark Iris (DD1875-500)']))
        self.webhook = 'https://discord.com/api/webhooks/674397216563265537/SGnI3BAwERaI22DFDJSxpdzWdD-UWVsJ0lyHI6k5saEJCqLEYinojrTRGftIzPuBFYYn'
        self.mail = row['MAIL']

        size_air = ['US 4 (EU 36)', 'US 4.5 (EU 36.5)','US 5 (EU 37.5)','US 5.5 (EU 38)','US 6 (EU 38.5)','US 6.5 (EU 39)','US 7 (EU 40)','US 7.5 (EU 40.5)','US 8 (EU 41)','US 8.5 (EU 42)','US 9 (EU 42.5)','US 9.5 (EU 43)','US 10 (EU 44)','US 10.5 (EU 44.5)','US 11 (EU 45)','US 11.5 (EU 45.5)','US 12 (EU 46)','US 12.5 (EU 47)','US 13 (EU 47.5)']
        
        self.size = random.choice(size_air)
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36'
        self.failCount = 0
        if self.all_proxies != None:
            self.selected_proxies = self.choose_proxy(self.all_proxies)
        else:
            self.selected_proxies = None

        self.session.proxies = self.selected_proxies
        self.getTokens()
        

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
                'https': 'https://{0}:{1}@{2}:{3}'.format(splitted[2], splitted[3], splitted[0], splitted[1])
            }
    
    def getTokens(self):
        
        try:
            self.jiggy1 = str(random.randint(100000,900000))
            self.jiggy2 = str(random.randint(1,9))
            self.jiggy3 = str(random.randint(10,99))
            self.jiggy4 = str(random.randint(1,9))
            self.jiggy5 = str(random.randint(1,9))
            self.jiggy6 = str(random.randint(10,99))
            self.jiggy7 = random.choice(string.ascii_letters) + str(random.randint(10,99))
            self.jiggy8 = str(random.randint(1000000000,9000000000))


            self.headers = {
                'user-agent': self.ua,
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding': 'gzip, deflate, br',
                'x-chrome-connected': f'id=117{self.jiggy1}98{self.jiggy8},mode=0,enable_account_consistency=false,consistency_enabled_by_default=false',
                'x-client-data': f'CI62yQEIo{self.jiggy2}bJAQjBtskBCKmdygIy{self.jiggy3}KAQ{self.jiggy7}sMoBCPe0ygEIl{self.jiggy4}XKAQjtuyoBCI{self.jiggy6}ygEYq{self.jiggy5}TKAQ='
            }
            print(f'{self.link}/viewform')
            r = self.session.get(f'{self.link}/viewform', headers = self.headers, proxies = self.selected_proxies, verify = True)
            print(r.status_code)
            if r.status_code == 200:
                print('a')
                try:

                    soup = bs(r.text, 'lxml')
                    if 'If you select the shipping option' in r.text:
                        self.shippingOption = True
                    else:
                        self.shippingOption = False
                    self.fbzx = soup.find('input', {'name': 'fbzx'}).get('value').replace('-','')
                    self.IDTag = re.findall(r',\d\,(\[\[\d+\,)', str(r.text))
                    info(f"[Task {self.threadID}] Successfully got tokens..")
                    delay = randrange(3, 15)
                    info(f'[Task {self.threadID}] Waiting {str(delay)} seconds before starting task') 
                    time.sleep(delay)
                    return self.register()

                except Exception as e:
                    self.failCount += 1
                    if self.failCount == 3:
                        error(f"[Task {self.threadID}] Task failed, skipping..")
                    else:
                        error(f"[Task {self.threadID}] Proxy banned, switching and retrying..")
                        
                        if self.selected_proxies != '':
                            self.selected_proxies = self.choose_proxy(self.all_proxies)
                            return self.getTokens()
                        else:
                            error(f"[Task {self.threadID}] Probably IP Banned..")
                            #self.taskStatus("Error handling queue!", self.threadID)
                            sys.exit(1)
              
            
            else:
                self.failCount += 1
                if self.failCount == 3:
                    error(f"[Task {self.threadID}] Task failed, skipping..")
                else:
                    error(f"[Task {self.threadID}] Proxy banned, switching and retrying..")
                    
                    if self.selected_proxies != '':
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        return self.getTokens()
                    else:
                        error(f"[Task {self.threadID}] Probably IP Banned..")
                        #self.taskStatus("Error handling queue!", self.threadID)
                        sys.exit(1)
                    

        except Exception as e:
            self.failCount += 1
            if self.failCount == 3:
                error(f"[Task {self.threadID}] Task failed, skipping..")
            else:
                error(f"[Task {self.threadID}] Proxy banned {e}, switching and retrying..")
                
                if self.selected_proxies != '':
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    return self.getTokens()
                else:
                    error(f"[Task {self.threadID}] Probably IP Banned..")
                    #self.taskStatus("Error handling queue!", self.threadID)
                    sys.exit(1)
              

    def register(self):

    
        self.submitLink = f'{self.link}/formResponse'

        try:

            warn(f"[Task {self.threadID}] Registering account..")
         
        
            self.final_headers = {
                'authority': 'docs.google.com',
                'scheme': 'https',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://docs.google.com',
                'referer': f'{self.link}viewform?fbzx=-{self.fbzx}',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'user-agent': self.ua,
                'x-chrome-connected': f'id=117{self.jiggy1}98{self.jiggy8},mode=0,enable_account_consistency=false,consistency_enabled_by_default=false',
                'x-client-data': f'CI62yQEIo{self.jiggy2}bJAQjBtskBCKmdygIy{self.jiggy3}KAQ{self.jiggy7}sMoBCPe0ygEIl{self.jiggy4}XKAQjtuyoBCI{self.jiggy6}ygEYq{self.jiggy5}TKAQ='
            }

            tags = [i.replace('[[','').replace(',','') for i in self.IDTag]

            payload = {
            f'entry.{tags[0]}': self.name,
            f'entry.{tags[1]}': self.surname,
            f'entry.{tags[2]}': self.mail,
            f'entry.{tags[4]}': self.codice,
            f'entry.{tags[3]}': self.size,
            f'entry.{tags[5]}': 'In-store pick-up',
            f'entry.{tags[3]}_sentinel': '',
            'fvv': 1,
            'draftResponse': f'[null,null,"{self.fbzx}"]',
            'pageHistory': 0,
            'fbzx': self.fbzx
            }


        
            try:
                r = self.session.post(self.submitLink, headers = self.final_headers, data = payload, proxies = self.selected_proxies, verify = True)

            except Exception as e:
                self.failCount += 1
                if self.failCount == 3:
                    error(f"[Task {self.threadID}] Task failed, skipping..")
                else:
                    error(f"[Task {self.threadID}] Proxy banned, switching and retrying..")
                    
                    if self.selected_proxies != '':
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        return self.getTokens()
                    else:
                        error(f"[Task {self.threadID}] Probably IP Banned..")
                        #self.taskStatus("Error handling queue!", self.threadID)
                        sys.exit(1)

                        

            if 'We have received your registration.' in r.text:
                info(f"[Task {self.threadID}] - Entry successfull!")
                try:
                    info(f"[Task {self.threadID}] - Saving entry info..")
                    if machineOS == "Darwin":
                        path = os.path.dirname(__file__).rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), "sjs/entered.txt")
                    elif machineOS == "Windows":
                        path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), "sjs/entered.txt")
                    with open(f'{path}', 'a+') as f:
                        f.write('\n'+self.mail+'|'+self.size+'|'+self.mail+'|'+self.name+'|'+self.surname+'|'+self.codice)
                        f.close()
                        info(f"[Task {self.threadID}] - Account entry saved...")
                        return self.sendHook()
                except Exception as e:
                    error(f" Failed to write to file - [{e}]")
                    pass 

            elif 'freebirdFormviewerViewResponseConfirmationMessage' in r.text:
                info(f"[Task {self.threadID}] - Entry successfull!")
                try:
                    info(f"[Task {self.threadID}] - Saving entry info..")
                    if machineOS == "Darwin":
                        path = os.path.dirname(__file__).rsplit('/', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), "sjs/entered.txt")
                    elif machineOS == "Windows":
                        path = os.path.dirname(__file__).rsplit('\\', 1)[0]
                        path = os.path.join(os.path.dirname(sys.argv[0]), "sjs/entered.txt")
                    with open(f'{path}', 'a+') as f:
                        f.write('\n'+self.mail+'|'+self.size+'|'+self.mail+'|'+self.name+'|'+self.surname+'|'+self.codice)
                        f.close()
                        info(f"[Task {self.threadID}] - Account entry saved...")
                        return self.sendHook()
                except Exception as e:
                    error(f" Failed to write to file - [{e}]")
                    pass 
                            
            else:
                self.failCount += 1
                if self.failCount == 3:
                    error(f"[Task {self.threadID}] Task failed, skipping..")
                else:
                    error(f"[Task {self.threadID}] Proxy banned, switching and retrying..")
                    
                    if self.selected_proxies != '':
                        self.selected_proxies = self.choose_proxy(self.all_proxies)
                        return self.getTokens()
                    else:
                        error(f"[Task {self.threadID}] Probably IP Banned..")
                        #self.taskStatus("Error handling queue!", self.threadID)
                        sys.exit(1)

        except Exception as e:
            self.failCount += 1 
            if self.failCount == 3:
                error(f"[Task {self.threadID}] Task failed, skipping..")
            else:
                error(f"[Task {self.threadID}] Proxy banned, switching and retrying..")
                
                if self.selected_proxies != '':
                    self.selected_proxies = self.choose_proxy(self.all_proxies)
                    return self.getTokens()
                else:
                    error(f"[Task {self.threadID}] Probably IP Banned..")
                    #self.taskStatus("Error handling queue!", self.threadID)
                    sys.exit(1)



    def sendHook(self):
        info(f"[Task {self.threadID}] - Sending Webhook...") 
        webhook = DiscordWebhook(url=self.webhook, content="")
        embed=DiscordEmbed(title="Chameleon Success", url="https://twitter.com/ChameleonIO", color=0x715aff)
        embed.add_embed_field(name="**Website**", value="SJS Instore Entry", inline=False)
        embed.add_embed_field(name="**Email**", value=f"{self.mail}", inline = False)
        embed.add_embed_field(name="**Size**", value=f"{self.size}", inline = False)
        embed.add_embed_field(name="**Name**", value=f"{self.name} \n {self.surname}", inline = False)
        embed.add_embed_field(name="**Codice**", value=f"{self.codice}", inline = False)
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/514031700444184628/765208653086720040/download_16.png")
        embed.set_footer(text="ChameleonIO", icon_url="https://media.discordapp.net/attachments/654451500038488078/658596291114303528/def.jpg")
        webhook.add_embed(embed)
        webhook.execute()
        info(f"[Task {self.threadID}] - Webhook Sent...")