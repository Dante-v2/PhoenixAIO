import json, traceback

PREFETCH_ENDPOINTS = {
    'zalando': '/login?target=/myaccount/',
    'www.nike.com': '/de/w/neu-3n82y'
}

BM_ENDPOINTS = {
    'en.zalando.de': '/clientlibs/fcea3d9f8no195dc6567dbaa4a32b3b',
    'www.zalando.cz': '/staticweb/909abd84a5dti201af97f5a0d0d4603e0',
    'www.zalando.it': '/staticweb/506f337992dti225eeaf339182b00ffec',
    'www.zalando.nl': '/webcontent/70177893ui242e28a4566b95d389a2',
    'www.zalando.fi': '/clientlibs/d1b1571eano1997c9a75a9574dd59b1',
    'www.nike.com': '/staticweb/32838c2af74ti2112d967a1f89f124f0f',
    'www.notebooksbilliger.de': '/webcontent/e060b030ui252e0ec83a2d1653f951',
    'www.converse.com': '/clientlibs/21a44f9c2no2655477d184fd92ea840',
    'www.officelondon.de': '/webcontent/da66e28aui2648ee0cd60939a010df',
    'www.kickz.com': '/webcontent/cc5f0248ui264cf3248bc33b922d78',
    'www.offspring.co.uk': '/DxTcQdHsz/QPv3j/CsJ95/nUUq37hg/1ct1kSzGmY/SWMRIi4B/dC/UHakxFAFE',
    'www.amd.com': '/Fx2nK6/aAFZ/gbj/mtm/ycYdFsJ_CP8/7tk7rbczESf7/BxRDUWU/AhJEI/yMqUE8'
}

ZALANDO_DOMAINS = [
    'en.zalando.de', 'www.zalando.at', 'www.zalando.ch', 'www.zalando.co.uk', 'www.zalando.pl', 'www.zalando.fr',
    'www.zalando.it', 'www.zalando.es', 'www.zalando.nl', 'www.zalando.be', 'www.zalando.cz', 'www.zalando.ie',
    'www.zalando.no', 'www.zalando.se', 'www.zalando.dk', 'www.zalando.fi',
]

"""
Validation rules

    0: accept all
    1: '=' not in cookie
    2: '==' in cookie
    3: '=' in cookie and '==' not in cookie
    
"""
VALIDATION_RULES = {
    'zalando': 0,
    'www.nike.com': 0,
    'www.notebooksbilliger.de': 0,
    'www.converse.com': 0,
    'www.officelondon.de': 0,
    'www.offspring.co.uk': 0,
    'www.kickz.com': 0,
    'www.amd.com': 0
}

API_KEY = ''

class Akamai:
    akamai_sensor_ep = "https://ak01-eu.hwkapi.com/akamai/generate"
    akamai_ua_ep = "https://ak01-eu.hwkapi.com/akamai/ua"
    akamai_pixel_ep = "https://ak01-eu.hwkapi.com/akamai/pixel"

    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'

    def __init__(self, domain, session, pixelMode=False):
        self.domain = domain

        # While 'domain' is always the real site domain, 'site' can also be some aggregated name like 'zalando'
        if self.domain in ZALANDO_DOMAINS:
            self.site = 'zalando'
        else:
            self.site = domain

        # Check if we need to pre-fetch a resource before getting an invalid _abck cookie
        if self.site in PREFETCH_ENDPOINTS:
            self.prefetch_ep = f'https://{self.domain}{PREFETCH_ENDPOINTS[self.site]}'
        else:
            self.prefetch_ep = None

        self.bm_ep = f'https://{self.domain}{BM_ENDPOINTS[self.domain]}'

        self.session = session
        self.proxy = None
        self.mouse_events = None
        self.key_events = None

        self.abck = None

        self.apiHeaders = {
            "Accept-Encoding": "gzip, deflate",
            "X-Api-Key": API_KEY,
            "X-Sec": "high" if pixelMode else "low"
        }

    def get_user_agent(self):
        r = None
        while r is None:
            try:
                r = self.session.get(Akamai.akamai_ua_ep, headers=self.apiHeaders)
            except Exception as e:
                print(f'ERROR WHILE GETTING USER-AGENT: {e}')

        return r.text

    def update_user_agent(self, ua):
        Akamai.USER_AGENT = ua

    def solve(self, proxy=None, mouse_events=True, key_events=True, respect_ua=False):
        self.proxy = proxy
        self.mouse_events = mouse_events
        self.key_events = key_events
        self.respect_ua = respect_ua

        success = False
        while not success:
            success = self.get_invalid_abck()

        try:
            for _ in range(2):
                payload = None
                while payload is None:
                    payload = self.get_sensor()

                success = False
                while not success:
                    success = self.post_akamai_payload(payload)

        except:
            return None

        if not self.validate_cookie():
            return None

        return self.abck

    def solve_pixel(self, pixel_url, script_id, script_secret, proxy=None):
        self.proxy = proxy

        payload = None
        while payload is None:
            payload = self.get_pixel(script_id, script_secret)

        success = None
        while not success:
            success = self.post_pixel(payload, pixel_url)

    def get_pixel(self, script_id, script_secret):
        try:
            params = {
                "user_agent": Akamai.USER_AGENT, 
                "script_id": script_id, 
                "script_secret": script_secret
            }

            r = None
            while r is None:
                try:
                    r = self.session.post(Akamai.akamai_pixel_ep, json=params, headers=self.apiHeaders)
                except Exception as e:
                    print(f'ERROR WHILE GETTING PIXEL DATA: {e}')

            return r.text

        except Exception as e:
            print(f'ERROR WHILE GETTING PIXEL DATA: {e}')
            return None

    def post_pixel(self, payload, pixel_url):
        headers = {
            'content-length': '',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': Akamai.USER_AGENT,
            'content-type': 'application/x-www-form-urlencoded',
            'accept': '*/*',
            'origin': f'https://{self.domain}',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'https://{self.domain}/',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en,de-DE;q=0.9,de;q=0.8,en-US;q=0.7'
        }

        try:
            r = None
            while r is None:
                try:
                    r = self.session.post(url=pixel_url, data=payload, headers=headers, proxies=self.proxy)
                except Exception as e:
                    print(f'ERROR WHILE POSTING PIXEL PAYLOAD: {e}')

            return True
        except Exception as e:
            print(f'ERROR WHILE POSTING PIXEL PAYLOAD: {e}')
            return False

    def get_sensor(self):
        try:
            mouse = 1 if self.mouse_events else 0
            key = 1 if self.key_events else 0

            params = {
                "site": self.site,
                "abck": self.abck,
                "type": "sensor",
                "events": f"{mouse},{key}"
            }
            
            if self.respect_ua:
                params["user_agent"] = Akamai.USER_AGENT

            r = None
            while r is None:
                try:
                    r = self.session.post(Akamai.akamai_sensor_ep, json=params, headers=self.apiHeaders)
                except Exception as e:
                    print(f'ERROR WHILE GETTING SENSOR-DATA: {e}')

            sensor = r.text.split('*')[0]
            payload = {"sensor_data": sensor}

            return payload
        except Exception as e:
            print(f'ERROR WHILE GETTING SENSOR-DATA: {e}')
            return None

    def post_akamai_payload(self, payload):
        headers = {
            'content-length': '',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': Akamai.USER_AGENT,
            'content-type': 'text/plain;charset=UTF-8',
            'accept': '*/*',
            'origin': f'https://{self.domain}',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'https://{self.domain}/login',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en,de-DE;q=0.9,de;q=0.8,en-US;q=0.7'
        }

        try:
            r = None
            while r is None:
                try:
                    data = json.dumps(payload)
                    r = self.session.post(url=self.bm_ep, data=data, headers=headers, proxies=self.proxy)
                    print(r.text)
                except Exception as e:
                    print(f'ERROR WHILE POSTING AKAMAI PAYLOAD: {e}')

            self.abck = r.cookies.get('_abck')
            return True
        except Exception as e:
            print(f'ERROR WHILE POSTING AKAMAI PAYLOAD: {e}')
            return False

    def validate_cookie(self):
        """
        Validates the _abck cookie according to the validation rules set for the current site.
        Will return True if the cookie is valid.
        """
        rule = VALIDATION_RULES[self.site]

        if rule == 1:
            if '=' in self.abck:
                return False
        if rule == 2:
            if '==' not in self.abck:
                return False
        if rule == 3:
            if '=' not in self.abck or '==' in self.abck:
                return False

        return True

    def get_invalid_abck(self):
        try:
            r = None
            while r is None:
                try:
                    if self.prefetch_ep is not None:
                        headers = {
                            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                            'sec-ch-ua-mobile': '?0',
                            'upgrade-insecure-requests': '1',
                            'user-agent': Akamai.USER_AGENT,
                            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                            'sec-fetch-site': 'none',
                            'sec-fetch-mode': 'navigate',
                            'sec-fetch-user': '?1',
                            'sec-fetch-dest': 'document',
                            'accept-encoding': 'gzip, deflate, br',
                            'accept-language': 'en,de-DE;q=0.9,de;q=0.8,en-US;q=0.7'
                        }
                        r = self.session.get(self.prefetch_ep, proxies=self.proxy, headers=headers)

                    headers = {
                        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                        'sec-ch-ua-mobile': '?0',
                        'user-agent': Akamai.USER_AGENT,
                        'accept': '*/*',
                        'sec-fetch-site': 'same-origin',
                        'sec-fetch-mode': 'no-cors',
                        'sec-fetch-dest': 'script',
                        'referer': f'https://{self.domain}/login',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'en,de-DE;q=0.9,de;q=0.8,en-US;q=0.7'
                    }
                    r = self.session.get(self.bm_ep, proxies=self.proxy, headers=headers)
                except Exception as e:
                    print(f'ERROR WHILE GETTING AKAMAI COOKIE 1: {e}')
                    print(traceback.format_exc())

            if self.session.cookies.get('_abck', None) is not None:
                self.abck = r.cookies.get('_abck')
                return True
        except Exception as e:
            print(f'ERROR WHILE GETTING AKAMAI COOKIE: {e}')
            return False
