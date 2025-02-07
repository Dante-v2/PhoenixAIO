from ctypes import (
              cdll
            , c_int
            , Structure
            , c_int32
            , c_char_p
            , c_uint32
            , CFUNCTYPE
            , pythonapi
            , sizeof
    )

import base64
import json
import time
from enum import Enum
from .utils import ClientError, GoString, GoClient
from .utils import Fingerprint, Lib, Response, client_params

class Session:
    loaded = False
    is_listening = False
    lib = None
    client_id = 0

    def switch_proxy(self, proxy="", fingerprint=None):
        if proxy:
            self.client_params.proxy = proxy
        if fingerprint:
            self.client_params.fingerprint = fingerprint
        self.lib.switch_proxy(self.client_id, self.client_params)


    @classmethod
    def _get_clients(cls):
        return

    def __del__(self):
        if not self.client_id:
            return
        self.lib.lib.delete_client(self.client_id)

    def __init__(self, proxy=None, fingerprint=Fingerprint.CHROME, timeout=20, redirect=True, verify_ssl=True, settings=None):
        self.cookies = {}
        self.cookieString = {}
        self.lib = Lib()
        self.client_params = client_params(proxy, fingerprint, verify_ssl, settings)
        self.client_id = self.lib.new_client(self.client_params, timeout=timeout, redirect=redirect)

    def get_cookie_header(self, domain):
        if len(self.cookies[domain]) == 0:
            return ""
        cookiesVal = ['%s=%s' % (name,value) for (name,value) in self.cookies[domain].items()]
        cookie_header = '; '.join(cookiesVal)
        return cookie_header

    def set_cookie(self, cookies, domain):
        if not domain in self.cookies.keys():
            self.cookies[domain] = {}
        for key,value in cookies.items():
            self.cookies[domain][key] = value
        self.cookieString[domain] = self.get_cookie_header(domain)

    def remove_cookie(self, domain, *args):
        for key in args:
            self.cookies[domain].pop(key)
        self.cookieString[domain] = self.get_cookie_header(domain)
        
    def request(self, method, url, **kw):
        return self.lib.request(self.client_id, method, url, **kw)
        
    def get(self, url, **kw):
        domain = url.split('://')[1].split('/')[0]
        headers = kw.get('headers', None)
        if domain in self.cookies.keys() and not domain in self.cookieString.keys():
            self.cookieString[domain] = self.get_cookie_header(domain)
        if headers and domain in self.cookieString.keys():
            headers['Cookie'] = self.cookieString[domain]
        r = self.request(url, "GET", **kw)
        self.set_cookie(r.cookies, domain)
        return r
    
    def post(self, url, **kw):
        domain = url.split('://')[1].split('/')[0]
        headers = kw.get('headers', None)
        if domain in self.cookies.keys() and not domain in self.cookieString.keys():
            self.cookieString[domain] = self.get_cookie_header(domain)
        if headers and domain in self.cookieString.keys():
            headers['Cookie'] = self.cookieString[domain]
        r = self.request(url, "POST", **kw)
        self.set_cookie(r.cookies, domain)
        return r

    def patch(self, url, **kw):
        domain = url.split('://')[1].split('/')[0]
        headers = kw.get('headers', None)
        if headers and domain in self.cookieString.keys():
            headers['Cookie'] = self.cookieString[domain]
        r = self.request(url, "PATCH", **kw)
        self.set_cookie(r.cookies, domain)
        return r

    def delete(self, url, **kw):
        domain = url.split('://')[1].split('/')[0]
        headers = kw.get('headers', None)
        if headers and domain in self.cookieString.keys():
            headers['Cookie'] = self.cookieString[domain]
        r = self.request(url, "DELETE", **kw)
        self.set_cookie(r.cookies, domain)
        return r
    
    def put(self, url, **kw):
        domain = url.split('://')[1].split('/')[0]
        headers = kw.get('headers', None)
        if headers and domain in self.cookieString.keys():
            headers['Cookie'] = self.cookieString[domain]
        r = self.request(url, "PUT", **kw)
        self.set_cookie(r.cookies, domain)
        return r
    
