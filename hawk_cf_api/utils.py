from urllib.parse import urlparse
import lzstring

def check_for_captcha(soup_string):
    captcha = soup_string.find("input",attrs={
        "name":"cf_captcha_kind"
    })
    if not captcha:
        return False
    if captcha["value"] == "h":
        return True
    else:
        raise Exception("Captcha type not supported: "+captcha["value"])

def compressToEncodedURIComponent(uncompressed,keyStrUriSafe):
    '''A monkeypatched version of lzstring'''
    if uncompressed is None:
        return ""
    return lzstring._compress(uncompressed, 6, lambda a: keyStrUriSafe[a])

def extract_domain(url: str) -> str:
    """:returns domain from given url."""
    parsed_url = urlparse(url)
    return parsed_url.netloc