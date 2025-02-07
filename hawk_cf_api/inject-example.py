#!/usr/bin/python3
import cloudscraper
from cf_cloudscraper.hawk_cf import CF_2,Cf_challenge_3
import re

# ------------------------------------------------------------------------------ cloudscraper is not passing proxies to the requests module, thus we need to monkey
def perform_request(self, method, url, *args, **kwargs):
    if "proxies" in kwargs or "proxy"  in kwargs:
        return super(cloudscraper.CloudScraper, self).request(method, url, *args, **kwargs)
    else:
        return super(cloudscraper.CloudScraper, self).request(method, url, *args, **kwargs,proxies=self.proxies)
# monkey patch the method in
cloudscraper.CloudScraper.perform_request = perform_request
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------ SNS updated theire challenge strings leading to defualt cloudscraper regex not matching anymore thus monkey these as well
#cap challenge
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
# ------------------------------------------------------------------------------

# injection of our api
# ------------------------------------------------------------------------------- #

def injection(session, response):
    if session.is_New_IUAM_Challenge(response):
        return CF_2(session,response,key="your-key",captcha=False,debug=True).solve() # FALSE is actually the default value but is displayed here to show that you need to have it true for captcha handling
                                                    # note that currently no captcha token getter is provided you can edit the file and add your solution
    elif session.is_New_Captcha_Challenge(response):
        return CF_2(session, response, key="your-key", captcha=True,
                    debug=True).solve()
    elif is_fingerprint_challenge(response):
        return Cf_challenge_3(session,response,key="your-key",debug=True).solve()



    else:
        return response

# ------------------------------------------------------------------------------- #





# for using anticaptcha just replace 2captcha with "anticaptcha"
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'mobile': False,
        'platform': 'windows'
        #'platform': 'darwin'
    },captcha={'provider':'anticaptcha','api_key':"", 'no_proxy':True},
    doubleDown=False,
    requestPostHook=injection,
    debug=False
)
proxies = {"your proxies"}
# in case the site presents you a captcha challenge make sure to have you 2cap key assigned above
print(scraper.get('https://www.bstn.com/eu_de/men.html',proxies=None).status_code)
