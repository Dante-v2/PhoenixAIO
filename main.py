import json, requests, threading, ssl, socket, hashlib, psutil, tempfile, csv, urllib3, sys, time, platform, ctypes, logging, webbrowser, os, uuid, htmllistparse, re, wget, datetime, importlib
from mods.logger import info, warn, error, cyan
from flask import Flask, request, jsonify, render_template
from pypresence import Presence
from colorama import Fore
from discord_webhook import DiscordWebhook, DiscordEmbed
from pkg_resources import parse_version
import traceback

urllib3.disable_warnings()
logging.disable(logging.CRITICAL)
sys.dont_write_bytecode = True

logging.getLogger('werkzeug').setLevel(logging.ERROR)
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

HOST = 'api.phoenixbot.io'
VERSION = '1.9.40'
AUTH_1 = 'Basic cGhvZW5peGJvdDpwaHV2S0RmdVNuQk10NkIyUzNuWQ=='
AUTH_2 = 'Basic cGhvZW5peGJvdDI6V0lrbEhZQ0lYM1VOaGZDV29Va0w='

MACHINE_OS = platform.system()
if not MACHINE_OS in ['Windows', 'Darwin']:
    sys.exit()
IP_ADDRESS = ''
HWID = str(uuid.getnode())
MACHINE_ID = platform.node()

DISCORD_USER = None
DISCORD_ID = None

BANNED_IDs = ['384659757572554752', '604001435339849738', '457998799705735180','768445240587059210']
BANNED_USERS = ['asd#0001', 'Bot Supply#0001', 'xxxmourn#4466','SneakerPirate#6666']

SITES = [
    { 'name': 'ACCOUNTS GENERATOR', 'status': 0, 'id': 'accgen' },
    { 'name': 'WAIT FOR QUICKTASKS', 'status': 0, 'id': 'quicktask' },
    { 'name': '43EINHALB', 'status': 0, 'id': 'einhalb', 'folder': '43einhalb' },
    { 'name': 'ALLIKE', 'status': 0, 'id': 'allike', 'folder': 'Allike' },
    { 'name': 'AMBUSH', 'status': 0, 'id': 'ambush', 'folder': 'ambush' },
    #{ 'name': 'ANTONIOLI', 'status': 0, 'id': 'antonioli', 'folder': 'antonioli' },
    { 'name': 'AWLAB', 'status': 0, 'id': 'awlab', 'folder': 'Awlab' },
    { 'name': 'BASKET4BALLERS', 'status': 0, 'id': 'b4b', 'folder': 'basket4ballers' },
    { 'name': 'BSTN', 'status': 1, 'id': 'bstn', 'folder': 'bstn' },
    { 'name': 'CORNERSTREET', 'status': 1, 'id': 'cornerstreet', 'folder': 'cornerstreet' },
    #{ 'name': 'COURIR', 'status': 0, 'id': 'courir', 'folder': 'courir' },
    { 'name': 'FOOTLOCKER', 'status': 1, 'id': 'footlocker', 'folder': 'footlocker' },
    { 'name': 'GALERIESLAFAYETTE', 'status': 0, 'id': 'galeries', 'folder': 'galeries' },
    { 'name': 'HERE', 'status': 0, 'id': 'here', 'folder': 'here' },
    #{ 'name': 'NAKED', 'status': 0, 'id': 'naked', 'folder': 'naked' },
    { 'name': 'OFF-WHITE', 'status': 1, 'id': 'offwhite', 'folder': 'offwhite' },
    #{ 'name': 'OFF-WHITE', 'status': 1, 'id': 'kith_eu', 'folder': 'kitheu' },
    #{ 'name': 'REVOLVE', 'status': 0, 'id':'genoffwhite', 'folder': 'genoffwhite' },
    #{ 'name': 'REVOLVE', 'status': 0, 'id':'offorder', 'folder': 'offorder' },
    { 'name': 'REVOLVE', 'status': 0, 'id': 'revolve', 'folder': 'revolve' },
    { 'name': 'SLAMJAM', 'status': 0, 'id': 'slamjam', 'folder': 'slamjam' },
    #{ 'name': 'SOTF', 'status': 0, 'id': 'snipesapp', 'folder': 'snipesapp' },
    { 'name': 'SNS', 'status': 0, 'id': 'sns', 'folder': 'Sns' },
    { 'name': 'SOTF', 'status': 0, 'id': 'sotf', 'folder': 'Sotf' },
    { 'name': 'STARCOW', 'status': 0, 'id': 'starcow', 'folder': 'starcow' },
    { 'name': 'SUGAR', 'status': 0, 'id': 'sugar', 'folder': 'sugar' },
    { 'name': 'SUPPA', 'status': 0, 'id': 'suppastore', 'folder': 'suppa' },
    { 'name': 'SUSI', 'status': 0, 'id': 'susi', 'folder': 'susi' },
    { 'name': 'THE BROKEN ARM', 'status': 0, 'id': 'tba', 'folder': 'thebrokenarm' },
    { 'name' : 'TITOLO', 'status': 0, 'id': 'titolo', 'folder': 'titolo' },
    #{ 'name' : 'TITOLO', 'status': 0, 'id': 'zalando', 'folder': 'zalando' },
]

ACC_GENERATORS = [
    #{ 'name': 'AMBUSH ACCOUNT GENERATOR', 'status': 0, 'id': 'genambush' },
    #{ 'name': 'COURIR ACCOUNT GENERATOR', 'status': 0, 'id': 'gencourir' },
    { 'name': 'SOTF ACCOUNT GENERATOR', 'status': 0, 'id': 'gensotf' },
    { 'name': 'CORNESTREET ACCOUNT GENERATOR', 'status': 0, 'id': 'gencorner' },
    { 'name': 'GALERIES ACCOUNT GENERATOR', 'status': 0, 'id': 'gengaleries' },
    { 'name': 'BASKET4BALLERS ACCOUNT GENERATOR', 'status': 0, 'id': 'genb4b' }
]

def getInput(text):
    asctime = str(datetime.datetime.now()).replace('.', ',')[:-3]
    print (f'[{asctime}] {Fore.YELLOW}{text}: ', end='')
def readConfig():
    try:
        path = os.path.join(os.path.dirname(sys.argv[0]), 'config.json')
        return json.load(open(path, 'r'))
    except Exception as e:
        error(f'Failed reading your config file - {e}')
        sys.exit()
def readTasks(site):
    try:
        if MACHINE_OS == 'Darwin':
            path = os.path.dirname('__file__').rsplit('/', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), f'{site}/tasks.csv')
        elif MACHINE_OS == 'Windows':
            path = os.path.dirname('__file__').rsplit('\\', 1)[0]
            path = os.path.join(os.path.dirname(sys.argv[0]), f'{site}/tasks.csv')
        tasks = csv.DictReader(open(f'{path}', 'r'))
        return tasks
    except:
        return None
def getIP():
    try:
        return requests.get('https://myexternalip.com/raw', verify=False).text
    except:
        pass

IP_ADDRESS = getIP()
CONFIG = readConfig()

if MACHINE_OS == 'Windows':
    try:
        key = CONFIG['key']
        tmp = tempfile.gettempdir()
        tempfiles = []
        for f in os.listdir(tmp):
            tempfiles.append(f)
        if any('.DMP' in f for f in tempfiles):
            webhook = DiscordWebhook(url="https://discordapp.com/api/webhooks/796498076142796801/oKD8Uc3mkzTD-iEPw7s_JYGzfHVYJEQyWGxp0pGvMP55lL-8jBfw8LG1c7vLb22b1flD", content = "")
            embed = DiscordEmbed(title='CRACKING WITH DMP FILE!', color = 16711680)
            embed.add_embed_field(name='KEY', value = f"{key}", inline = True)
            embed.set_footer(text = f"Phoenix AIO Security", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            print("Cracking attemp logged")
            parent_pid = os.getpid()
            time.sleep(2)
            parent = psutil.Process(parent_pid)
            parent.kill()
    except:
        parent_pid = os.getpid()
        time.sleep(2)
        parent = psutil.Process(parent_pid)
        parent.kill()

class Security():
    def log_attempt(self, key, extype):
        url = "https://discordapp.com/api/webhooks/748916983927537715/mAl1tNtYUAOiLmznL6TDm_xoKgWCyHmLqYMJoRpdefleBOkOVnYpQUhi9uaRkYrDPj0T"
        data = {}
        key = key.strip()
        data["embeds"] = []
        embed = {}
        embed["description"] = f"**Key**\n[config: {CONFIG['key']}, live: {key}], \n\n**HWID** {HWID} \n\n**IP** {IP_ADDRESS} \n\n**TYPE**\n {extype}"
        embed["title"] = "Cracking attempt - Version: " + VERSION
        data["embeds"].append(embed)
        try:
            requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"}, verify=True)
            error("Cracking attempt logged")
            self.crackAttempt = True
            parent_pid = os.getpid()
            parent = psutil.Process(parent_pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except:
            error("Cracking attempt logged")
            self.crackAttempt = True
            parent_pid = os.getpid()
            parent = psutil.Process(parent_pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
    def checkIfProcessRunning(self, processName):
        for proc in psutil.process_iter():
            try:
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    def security(self):
        hash = "f6ec9f2b93dc9d2ef96507a2a5546ee523cfc79e0b5bb0774b6e8fca160d6c4f"
        socket.gethostname()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(6)
        wrappedSocket = ssl.wrap_socket(sock)
        thumb_sha256 = ""
        try:
            wrappedSocket.connect(("api.phoenixbot.io", 443))
        except Exception as e:
            error(f"Initialization error - {e}")
            pass
        else:
            der_cert_bin = wrappedSocket.getpeercert(True)
            pem_cert = ssl.DER_cert_to_PEM_cert(wrappedSocket.getpeercert(True))
            cert = tempfile.NamedTemporaryFile(delete=False)
            cert.write(pem_cert.encode())
            cert.close()
            thumb_sha256 = hashlib.sha256(der_cert_bin).hexdigest()
        if thumb_sha256 != "":
            if thumb_sha256 != hash:
                self.log_attempt("",  "Node Mismatch")
                error("Fingerprint mismatch!")
                parent_pid = os.getpid()
                parent = psutil.Process(parent_pid)
                for child in parent.children(recursive=True):
                        child.kill()
                parent.kill()
        else:
            pass
        try:
            if MACHINE_OS == "Windows":
                    hosts = open('C:\Windows\System32\drivers\etc\hosts', 'r')
            elif MACHINE_OS == "Darwin":
                    hosts = open('/etc/hosts')
            hostlist = hosts.readlines()
            hosts.close()
            for entry in hostlist:
                if str(HOST) in entry:
                    error("Hosts tamper detected")
                    self.log_attempt("", "Host tamper")
                    parent_pid = os.getpid()
                    parent = psutil.Process(parent_pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
        except:
            pass
        bannedprocesses = ["Wireshark", "HTTP Debugger", "Burp", "Fiddler 4", "Fiddler", "Charles"]
        for proc in bannedprocesses:
            if self.checkIfProcessRunning(proc):
                error("Disallowed process: %s is running" % (proc))
                self.log_attempt("", f"Dissalowed process: {proc}")
                parent_pid = os.getpid()
                parent = psutil.Process(parent_pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
        return False
    def permSecurity(self):
        while True:
            self.security()
            time.sleep(5)
    def authKey(self):
        global DISCORD_USER, DISCORD_ID
        warn('CHECKING KEY')
        if self.security():
            return
        authorization = AUTH_1
        while True:
            try:
                r = requests.get(
                    f'https://api.tldashboards.com/v1/user?licenseKey={CONFIG["key"]}&hwId={HWID}',
                    headers={
                        'Authorization': authorization,
                        'accept': 'application/json'
                    }
                )
                if r.status_code == 200:
                    rj = r.json()
                    DISCORD_USER = rj['discordUsername']
                    DISCORD_ID = rj['discordId']
                    self.planType = rj['planType']
                    if "https://api.tldashboards.com/" in r.url and rj['userStatus'] == "Active":
                        self.auth = authorization
                        break
                    else:
                        error('UNABLE TO VERIFY KEY, UNAUTHORIZED')
                        time.sleep(3)
                        sys.exit(1)
                elif r.status_code == 401:
                    error('UNABLE TO VERIFY KEY, UNAUTHORIZED')
                    time.sleep(3)
                    sys.exit(1)
                elif r.status_code == 404 and authorization != AUTH_2:
                    authorization = AUTH_2
                    continue
                elif r.status_code == 404:
                    error('UNABLE TO VERIFY KEY, CHECK CONFIG')
                    time.sleep(3)
                    sys.exit(1)
                elif r.status_code == 500:
                    error('SERVER ERROR WHILE CHECKING KEY, RETRYING...')
                    time.sleep(2)
                    continue
                else:
                    error(f'UNKOWN ERROR WHILE CHECKING KEY: {r.status_code}')
                    sys.exit(1)
            except:
                sys.exit(1)
        self.check_machine()
    def check_machine(self):
        while True:
            try:
                headers = {
                    'Accept': '*/*',
                    'Authorization': self.auth
                }

                r = requests.get(
                    f'https://api.tldashboards.com/v1/machine?licenseKey={CONFIG["key"]}&hwId={HWID}',
                    headers=headers
                )

                if r.status_code == 200:
                    rj = r.json()
                    if not rj['deviceName'] and not rj['hwId']:
                        verified = False
                        break
                    if rj['deviceName'] == MACHINE_ID and rj['hwId'] == HWID and rj['userStatus'] == 'Active':
                        if "api.tldashboards.com/v1/" in r.url:
                            info('KEY SUCCESSFULLY ACTIVATED')
                            verified = True
                            break
                        else:
                            error('UNABLE TO VERIFY KEY, UNAUTHORIZED')
                            time.sleep(3)
                            sys.exit(1)
                    else:
                        error('LICENSE KEY IS ALREADY BOUND TO A MACHINE')
                        sys.exit(1)
                elif r.status_code == 404:
                    error('UNABLE TO VERIFY KEY, CHECK CONFIG')
                    time.sleep(3)
                    sys.exit(1)
                elif r.status_code == 500:
                    error('SERVER ERROR WHILE CHECKING KEY, RETRYING...')
                    time.sleep(2)
                    continue
                else:
                    error(f'UNKOWN ERROR WHILE CHECKING KEY: {r.status_code}')
                    sys.exit(1)
            except:
                sys.exit(1)
        if not verified:
            self.bind_machine()
        else:
            self.webhook_key()
    def bind_machine(self):
        while True:
            try:
                payload = {
                    "deviceName": MACHINE_ID,
                    "hwId": HWID
                }

                headers = {
                    'Accept': '*/*',
                    'Authorization': self.auth
                }

                r = requests.post(
                    f'https://api.tldashboards.com/v1/machine/{CONFIG["key"]}',
                    headers=headers,
                    json=payload
                )

                if r.status_code == 201:
                    if "api.tldashboards.com/v1/machine/" in r.url:
                        break
                    else:
                        error('UNABLE TO VERIFY KEY, UNAUTHORIZED')
                        time.sleep(3)
                        sys.exit(1)
                elif r.status_code == 400:
                    error('LICENSE KEY IS ALREADY BOUND TO A MACHINE')
                    sys.exit(1)
                elif r.status_code == 401:
                    error('UNABLE TO VERIFY KEY, UNAUTHORIZED')
                    time.sleep(3)
                    sys.exit(1)
                elif r.status_code == 404:
                    error('UNABLE TO VERIFY KEY, CHECK CONFIG')
                    time.sleep(3)
                    sys.exit(1)
                elif r.status_code == 500:
                    error('SERVER ERROR WHILE CHECKING KEY, RETRYING...')
                    time.sleep(2)
                    continue
                else:
                    error(f'UNKOWN ERROR WHILE CHECKING KEY: {r.status_code}')
                    sys.exit(1)
            except Exception as e:
                sys.exit(1)
        self.webhook_key()
    def webhook_key(self):
        local_ip = socket.gethostbyname(socket.gethostname())
        if DISCORD_ID in BANNED_IDs or DISCORD_USER in BANNED_USERS or self.planType not in ['Renewal', 'Weekly', 'F&F']:
            webhook = DiscordWebhook(url="https://discordapp.com/api/webhooks/803349551720693760/eVFNJiNSJ2WWeaq66Vgo_L0TjfGR1YODGN_5hdM7cc3uCgHEaY6juJKn8P4L69QaXupa", content = "")
            embed = DiscordEmbed(title='User running!', color = 40703)
            embed.add_embed_field(name='USER', value = f"<@{DISCORD_ID}>", inline = True)
            embed.add_embed_field(name='DISCORD NAME', value = DISCORD_USER, inline = True)
            embed.add_embed_field(name='PLANTYPE', value = self.planType, inline = True)
            embed.add_embed_field(name='HWID', value = HWID, inline = True)
            embed.add_embed_field(name='LOCAL IP', value = f'{local_ip} | {IP_ADDRESS}', inline = True)
            embed.add_embed_field(name='KEY', value = CONFIG['key'], inline = True)
            embed.set_footer(text = f"Phoenix AIO v{VERSION}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()
            parent_pid = os.getpid()
            parent = psutil.Process(parent_pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        else:
            local_ip = socket.gethostbyname(socket.gethostname())
            webhook = DiscordWebhook(url="https://discordapp.com/api/webhooks/738755860431372309/TDuMVs4CPESJBsnonD5B5QEmsaw79QxL-meqEvLR3ZJiisvNdU83Xt2IgZ3qVIOPJGlq", content = "")
            embed = DiscordEmbed(title='User running!', color = 40703)
            embed.add_embed_field(name='USER', value = f"<@{DISCORD_ID}>", inline = True)
            embed.add_embed_field(name='DISCORD NAME', value = DISCORD_USER, inline = True)
            embed.add_embed_field(name='PLANTYPE', value = self.planType, inline = True)
            embed.add_embed_field(name='HWID', value = HWID, inline = True)
            embed.add_embed_field(name='LOCAL IP', value = f'{local_ip} | {IP_ADDRESS}', inline = True)
            embed.add_embed_field(name='KEY', value = CONFIG['key'], inline = True)
            embed.set_footer(text = f"Phoenix AIO v{VERSION}", icon_url = "https://cdn.discordapp.com/attachments/732955582989992076/732957353263235092/4Senza-titolo-1.jpg")
            webhook.add_embed(embed)
            webhook.execute()

class MainWrapper(Security):
    try:
        rpc = Presence('738896087359815810')
        rpc.connect()
        rpc.update(state=f'Version {VERSION}', details='Burning sites...', large_image="large", small_image='3logo', start=int(time.time()), instance=False)
    except:
        pass

    def __init__(self):
        self.updateChecker()
    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    def updateChecker(self):
        url = 'https://api.phoenixbot.io/download/exe/'
        currentFile = os.path.abspath(os.path.dirname(sys.argv[0]))
        try:
            cwd, files = htmllistparse.fetch_listing(
                url,
                timeout=30
            )
            for f in files:
                if '.exe' in f.name:
                    windowsVersion = re.findall(r'(?:(\d+\.[.\d]*\d+))', f.name)[0]
                    windowsDL = "{0}{1}".format(url, f.name)
                    windowsFile = f.name
                else:
                    macVersion = re.findall(r'(?:(\d+\.[.\d]*\d+))', f.name)[0]
                    macDL = "{0}{1}".format(url, f.name)
                    macFile = f.name
            if MACHINE_OS == 'Windows':
                latestVersion = windowsVersion
                latestDL = windowsDL
                filename = windowsFile
            else:
                latestVersion = macVersion
                latestDL = macDL
                filename = macFile

            if parse_version(VERSION) < parse_version(latestVersion):
                try:
                    warn("UPDATE AVAILABLE!")
                    warn(wget.download(latestDL, currentFile))
                    warn("")
                except:
                    error(f"ERROR UPDATING, PLEASE DOWNLOAD MANUALLY")
                    sys.exit()
                else:
                    try:
                        if MACHINE_OS == 'Windows':
                            info("Extracted and updated!")
                            os.system('cls')
                            os.startfile("{0}\\{1}".format(currentFile, filename))
                        else:
                            try:
                                newfile = filename.replace(".", "_")
                                os.system("mv {0}/{1} {0}/{2}".format(currentFile, filename, newfile))
                                os.system("chmod 755 {0}/{1}".format(currentFile, newfile))
                            except Exception as e:
                                error(f"Error formatting update.. {e.__class__.__name__}")
                            else:
                                info("Extracted and updated!")
                                os.system('clear')
                                os.system("open {0}/{1}".format(currentFile, newfile))
                        time.sleep(2)
                        parent_pid = os.getpid()
                        parent = psutil.Process(parent_pid)
                        print(f"{parent} killed - updateChecker()")
                        parent.kill()
                    except:
                        error(f"ERROR UPDATING, PLEASE DOWNLOAD MANUALLY")
                        sys.exit()
            else:
                self.scriptmenu()
        except UnboundLocalError:
            self.scriptmenu()
        except Exception as e:
            print(traceback.format_exc())
            error(f"FAILED TO START - {e}")
            sys.exit()

    def timer(self):
        user_time = datetime.datetime.strptime(input(), "%d-%m-%Y %H:%M:%S")
        now = datetime.datetime.now()
        delta = int((user_time-now).total_seconds())
        t = delta - 15
        warn(f'Sleeping for {t} seconds...')
        return t

    def wait_for_qt(self):
        try:
            r = requests.get('http://127.0.0.1:5005/phoenixqt')
        except:
            pass
        else:
            if r.status_code == 400:
                error("You're already waiting for quicktasks on another instance on this machine")
                self.get_scope()
                self.start_bot()
                return None
        app = Flask(__name__)
        app.logger.disabled = True
        @app.route('/phoenixqt')
        def start_qt():
            req_data = request.args
            if not req_data.get('input'):
                return "'input' parameter not specified", 400
            elif not req_data.get('site'):
                return "'site' parameter not specified", 400
            elif req_data.get('site').lower() not in [x['id'] for x in SITES]:
                return "Invalid 'site' parameter", 400
            else:
                site = req_data.get('site').lower()
                inp = req_data.get('input')
                i = 0
                siteData = next(x for x in SITES if x['id'] == site)
                tasks = readTasks(siteData['folder'])
                module = getattr(importlib.import_module(f'scripts.{site}'), site.upper())
                if site == 'awlab':
                    for row in list(tasks)[:20]:
                        i += 1
                        if inp != None:
                            if 'VARIANT' in row.keys():
                                row['VARIANT'] = inp
                            elif 'SKU' in row.keys():
                                row['SKU'] = inp
                            elif 'PID' in row.keys():
                                row['PID'] = inp  
                            else:
                                row['LINK'] = inp
                        threading.Thread(target=module, args=([row, CONFIG['webhook'], VERSION, i, DISCORD_ID])).start()
                if site == 'susi':
                    for row in list(tasks)[:200]:
                        i += 1
                        if inp != None:
                            if 'VARIANT' in row.keys():
                                row['VARIANT'] = inp
                            elif 'SKU' in row.keys():
                                row['SKU'] = inp
                            elif 'PID' in row.keys():
                                row['PID'] = inp  
                            else:
                                row['LINK'] = inp
                        threading.Thread(target=module, args=([row, CONFIG['webhook'], VERSION, i, DISCORD_ID])).start()
                if site == 'sugar':
                    for row in list(tasks)[:10]:
                        i += 1
                        if inp != None:
                            if 'VARIANT' in row.keys():
                                row['VARIANT'] = inp
                            elif 'SKU' in row.keys():
                                row['SKU'] = inp
                            elif 'PID' in row.keys():
                                row['PID'] = inp  
                            else:
                                row['LINK'] = inp
                        threading.Thread(target=module, args=([row, CONFIG['webhook'], VERSION, i, DISCORD_ID])).start()
                else:
                    for row in tasks:
                        i += 1
                        if inp != None:
                            if 'VARIANT' in row.keys():
                                row['VARIANT'] = inp
                            elif 'SKU' in row.keys():
                                row['SKU'] = inp
                            elif 'PID' in row.keys():
                                row['PID'] = inp  
                            else:
                                row['LINK'] = inp
                        threading.Thread(target=module, args=([row, CONFIG['webhook'], VERSION, i, DISCORD_ID])).start()
                return "Quick tasks started", 200
        warn('Waiting for Quicktasks')
        app.run('127.0.0.1', port='5005', debug=True, use_reloader=False)

    def scriptmenu(self):

        request = b'GET /S1T3S4EWKXU/ HTTP/1.0\r\nHost: api.phoenixbot.io\r\n\r\n'
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        wrappedSocket = ssl.wrap_socket(client, ssl_version=ssl.PROTOCOL_TLSv1)
        target = "api.phoenixbot.io"
        port = 443
        wrappedSocket.connect((target,port))    
        wrappedSocket.sendall(request)
        result = wrappedSocket.recv(4096)
        while (len(result) < 1):
            result = wrappedSocket.recv(4096)  
        self.apiData = str(result)
        info(f"Welcome {DISCORD_USER} - PhoenixAIO {VERSION}")
        if 'mobilemode' in CONFIG.keys() and CONFIG['mobilemode'] != '':
            from scripts.mobile import START
            threading.Thread(target=START, args=([CONFIG['webhook'], VERSION])).start()
        else:
            while True:
                for site in SITES:
                    i = str(SITES.index(site))
                    spaces = ' ' * (2 - len(i))
                    if site['status'] == 0:
                        info(f'[{spaces}{i}] {site["name"]}')
                    elif site['status'] == 1:
                        warn(f'[{spaces}{i}] {site["name"]}')
                    elif site['status'] == 2:
                        error(f'[{spaces}{i}] {site["name"]}')
                print("-------------------------------------------------------------------------------------------")
                getInput('-- [Please select]')
                site = input().strip()
                try:
                    site = int(site)
                    site = SITES[site]
                    break
                except:
                    error('Invalid site chosen')
                    continue
            if site['id'] == 'quicktask':
                return self.wait_for_qt()
            if site['id'] == 'accgen':
                while True:
                    for gen in ACC_GENERATORS:
                        i = str(ACC_GENERATORS.index(gen))
                        spaces = ' ' * (2 - len(i))
                        if gen['status'] == 0:
                            info(f'[{spaces}{i}] {gen["name"]}')
                        elif gen['status'] == 1:
                            warn(f'[{spaces}{i}] {gen["name"]}')
                        elif gen['status'] == 2:
                            error(f'[{spaces}{i}] {gen["name"]}')
                    getInput('-- [Please select]')
                    chosen = input().strip()
                    try:
                        chosen = int(chosen)
                        chosen = ACC_GENERATORS[chosen]
                        break
                    except:
                        error('Invalid gen chosen')
                        continue
                gen = getattr(importlib.import_module(f'scripts.gen.{chosen["id"]}'), chosen['id'].upper())
                tasks = readTasks(chosen['id'])
                if not tasks:
                    error('Failed reading tasks. Please check your tasks.csv file.')
                    sys.exit(1)
                else:
                    i = 0
                    for row in tasks:
                        i += 1
                        threading.Thread(target=gen, args=([row, i])).start()
            else:
                if site['name'] in self.apiData:
                    tasks = readTasks(site['folder'])
                    if not tasks:
                        error('Failed reading tasks. Please check your tasks.csv file.')
                        sys.exit(1)
                    else:
                        modes = [1,2,3]
                        username = None
                        password = None
                        while True:
                            warn('[MODE 1]: RUN TASKS')
                            warn('[MODE 2]: INPUT LINK / SKU')
                            warn('[MODE 3]: TIMER')
                            if site['id'] == 'einhalb':
                                modes.append(4)
                                warn('[MODE 4]: START WITH LINK AND CREDENTIALS')
                            elif site['id'] == 'starcow':
                                modes.append(4)
                                warn('[MODE 4]: CREATE SESSIONS')
                            getInput('-- [Please select]')
                            mode = input().strip()
                            try:
                                mode = int(mode)
                                if not mode in modes:
                                    raise Exception
                                else:
                                    break
                            except:
                                error('Invalid mode chosen')
                                continue
                        if mode == 1:
                            inp = None
                        if mode == 2:
                            getInput('[INPUT LINK]')
                            inp = input().strip()
                        elif mode == 3:
                            warn('TIMER NEEDS TO BE IN THIS FORMAT: DD-MM-YYYY HH:MM:SS')
                            t = self.timer()
                            time.sleep(t)
                        elif mode == 4 and site['id'] == 'einhalb':
                            getInput('[INPUT LINK]')
                            inp = input().strip()
                            getInput('[INPUT USERNAME]')
                            username = input().strip()
                            getInput('[INPUT PASSWORD]')
                            password = input().strip()
                        else:
                            inp = None
                        i = 0
                        module = getattr(importlib.import_module(f'scripts.{site["id"]}'), site['id'].upper())
                        if site['id'] == 'awlab':
                            for row in list(tasks)[:20]:
                                i += 1
                                if inp != None:
                                    if 'VARIANT' in row.keys():
                                        row['VARIANT'] = inp
                                    elif 'SKU' in row.keys():
                                        row['SKU'] = inp
                                    elif 'PID' in row.keys():
                                        row['PID'] = inp  
                                    else:
                                        row['LINK'] = inp
                                threading.Thread(target=module, args=([row, CONFIG['webhook'], VERSION, i,DISCORD_ID])).start()
                        if site['id'] == 'susi':
                            for row in list(tasks)[:200]:
                                i += 1
                                if inp != None:
                                    if 'VARIANT' in row.keys():
                                        row['VARIANT'] = inp
                                    elif 'SKU' in row.keys():
                                        row['SKU'] = inp
                                    elif 'PID' in row.keys():
                                        row['PID'] = inp  
                                    else:
                                        row['LINK'] = inp
                                threading.Thread(target=module, args=([row, CONFIG['webhook'], VERSION, i,DISCORD_ID])).start()
                        if site['id'] == 'sugar':
                            for row in list(tasks)[:10]:
                                i += 1
                                if inp != None:
                                    if 'VARIANT' in row.keys():
                                        row['VARIANT'] = inp
                                    elif 'SKU' in row.keys():
                                        row['SKU'] = inp
                                    elif 'PID' in row.keys():
                                        row['PID'] = inp  
                                    else:
                                        row['LINK'] = inp
                                threading.Thread(target=module, args=([row, CONFIG['webhook'], VERSION, i,DISCORD_ID])).start()
                        else:
                            for row in tasks:
                                i += 1
                                if inp != None:
                                    if 'VARIANT' in row.keys():
                                        row['VARIANT'] = inp
                                    elif 'SKU' in row.keys():
                                        row['SKU'] = inp
                                    elif 'PID' in row.keys():
                                        row['PID'] = inp  
                                    else:
                                        row['LINK'] = inp
                                if mode == 4 and site['id'] == 'einhalb':
                                    row['USERNAME'] = username
                                    row['PASSWORD'] = password
                                elif mode == 4 and site['id'] == 'starcow':
                                    row['MODE'] = 'CREATE'
                                threading.Thread(target=module, args=([row, CONFIG['webhook'], VERSION, i,DISCORD_ID])).start()
                else:
                    error('SITE IS LOCKED!')
                    time.sleep(2)
                    self.scriptmenu()

s = Security()
s.authKey()
threading.Thread(target=s.permSecurity).start()
threading.Thread(target=MainWrapper).start()