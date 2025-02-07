import threading, ctypes, zlib
from ctypes import (
              cdll
            , c_int
            , Structure
            , c_char_p
            , c_void_p
            , c_uint32
            , CFUNCTYPE
            , pythonapi
            , sizeof
            , pointer
            , POINTER
            , cast
            , c_bool
            , c_uint8
    )
from enum import Enum, IntEnum
import json as ujson, base64
from asyncio import get_running_loop
import platform
from datetime import datetime
from collections import OrderedDict
from urllib import parse as urlparse


class FPType(IntEnum):
    HID = 1
    JA3 = 2
    PKT = 3

class HeaderDict(OrderedDict):
    def realkey(self, key):
        return key.lower()

    def __setitem__(self, key, value):
        k = self.realkey(key)
        return super(HeaderDict, self).__setitem__(k, (key, value))


    def __getitem__(self, key):
        k = self.realkey(key)
        return super(HeaderDict, self).__getitem__(k)[1]

    def items(self):
        return self._values()

    def values(self):
        return map(lambda x: x[1], self._values())

    def _values(self):
        return super(HeaderDict, self).values()

def utc_timestamp():
    return datetime.utcnow().timestamp()

def synchronized(fn):
    lock = threading.Lock()
    def func(*args, **kw):
        with lock:
            return fn(*args, **kw)
    return func

class ClientError(Exception):
    pass

class GoClient(Structure):
    _fields_ = [("r1", c_int), ("r2", c_char_p)]

class GoString(Structure):
    _fields_ = [("p", c_char_p), ("n", c_int)]

# class GoCookie(Structure):
#     _fields_ = [
#         ("name", c_char_p),
#         ("value", c_char_p),
#         ("expiry", c_int),
#     ]

#     def __init__(self, name, value, expiry=None):
#         expiry = expiry or utc_timestamp()+(100*3600)
#         super(GoCookie, self).__init__(name, value, expiry)

#     def __repr__(self):
#         return f'<Cookie(name={self.name}, value="{self.value}", expiry={self.expiry})>'

# class SessionCookies(Structure):
#     _fields_ = [
#         ("size", c_int),
#         ("cks", pointer(GoCookie)),
#     ]
#     cookies = {}
#     def add_cookie(self, **cdict):
#         for k, v in cdict.items():
#             self._add_cookie(k, v)
        
#     def update(self):
#         cks = list(self.cookies.values())


#     def _add_cookie(self, name, value, expiry=None):
#         expiry = expiry or utc_timestamp()+(100*3600)
#         ck = GoCookie(name, value, expiry)
#         self.cookies[name] = ck



def gzip_decompress(data):
    return zlib.decompress(data, 16+zlib.MAX_WBITS)

class GoResponse(Structure):
    _fields_ = [
        ("url_", c_char_p),
        ("headers_", c_char_p),
        ("cookies_", c_char_p),
        ("body_", c_void_p),
        ("error", c_char_p),
        ("status", c_int),
        ("length", c_uint32)
    ]
    _headers = None
    _cookies = None

    def check_error(self):
        if self.error:
            raise ClientError(self.error.decode())

    def __del__(self):
        Lib.lib.free_fetch_result(self)

    @property
    def headers(self):
        self._headers = self._headers or ujson.loads(self.headers_)
        return self._headers

    @property
    def cookies(self):
        self._cookies = self._cookies or ujson.loads(self.cookies_)
        return self._cookies

    @property
    def text(self):
        return self.body.decode("utf-8", errors='replace')
        
    @property
    def url(self):
        return self.url_.decode("utf-8")

    def json(self):
        return ujson.loads(self.text)

    @property
    def body(self):
        body = cast(self.body_, POINTER(c_uint8))
        body = bytes(body[:self.length])
        return body

def convert_string(string):
    gstring = bytes(string, encoding="utf-8")
    return GoString(gstring, len(gstring))



def get_library_path():
    p = platform.system()
    filepath = './req/ghttp'
    if p == 'Windows':
        filepath += '_win.dll'
    elif p == 'Darwin':
        filepath += '_mac.so'
    else:
        filepath += '_linux.so'
    return filepath


class client_params:
    proxy = None
    fingerprint = None
    verify_ssl = True
    settings = None
    def __init__(self, proxy, fingerprint, verify_ssl, settings):
        self.proxy = proxy
        self.fingerprint = fingerprint
        self.verify_ssl = verify_ssl
        self.settings = settings


class Lib:
    loaded = False
    lib = None
    is_listening = False

    @classmethod
    @synchronized
    def load(cls):
        if cls.loaded:
            return
        path = get_library_path()
        cls.lib = cdll.LoadLibrary(path)
        #create client
        cls.lib.new_client.argtypes = [GoString, GoString, c_int, GoString, c_int, c_bool, c_bool]
        cls.lib.new_client.restype = GoClient
        cls.lib.switch_proxy.argtypes = [c_uint32, GoString, GoString, c_int, GoString, c_bool]
        cls.lib.switch_proxy.restype = c_char_p

        # cls.lib.new_client_ja3.argtypes = [GoString, GoString, c_int]
        # cls.lib.new_client_ja3.restype = GoClient
        #gc client
        cls.lib.delete_client.argtypes = [c_uint32]
        
        functype = CFUNCTYPE(None, GoResponse)
        cls.lib.node_fetch.argtypes = [c_uint32, GoString, GoString, GoString, GoString]
        cls.lib.node_fetch.restype = GoResponse
        cls.lib.node_fetch_with_cb.argtypes = [c_uint32, GoString, GoString, GoString, GoString, functype]
        cls.lib.node_fetch_with_cb.restype = None
        cls.lib.free_fetch_result.argtypes = [GoResponse]

        
        cls.loaded = True
        cls.start_signal_listener()
        

    @classmethod
    def switch_proxy(cls, client_id, c :client_params):
        proxy, fingerprint, fptype, settings = cls.parse_client_params(client_params)
        err = cls.lib.switch_proxy(client_id, proxy, fingerprint, fptype, settings, c.verify_ssl)
        if err:
            raise ClientError(err)
        return True

    @classmethod
    def new_client(cls, c:client_params, timeout=20, redirect=True):
        if not cls.loaded:
            cls.load()
        proxy, fingerprint, fptype, settings = cls.parse_client_params(c)
        client = cls.lib.new_client(proxy, fingerprint, fptype, settings, timeout, redirect, c.verify_ssl)
        if client.r2:
            raise ClientError(client.r2)
        return client.r1

    @staticmethod
    def parse_client_params(c : client_params):
        if isinstance(c.settings, dict):
            settings = ujson.dumps(c.settings)
        else:
            settings = ""
        settings = convert_string(settings)
        proxy = str.strip(c.proxy or '')
        proxy2 = convert_string(proxy)
        # fingerprint = c.fingerprint
        fingerprint, fptype = convert_string(str(c.fingerprint)), c.fingerprint.typenum.value
        return proxy2, fingerprint, fptype, settings
    @classmethod
    def start_signal_listener(cls):
        if cls.is_listening:
            return
        cls.is_listening = True
        functype = CFUNCTYPE(c_int)
        cls.lib.start_signal_listener.argtypes = [functype]
        f = functype(pythonapi.PyErr_CheckSignals)
        cls.__signal_checker = f
        cls.lib.start_signal_listener(f)

    @classmethod
    def prepare_request(cls, method, url, params=None, data='', json=None, headers=None, cookies=None, files=None, auth=None):
        headers = headers or []
        url = convert_string(url)
        if isinstance(headers, dict):
            headers = list(headers.items())
        if not isinstance(headers, list):
            raise AttributeError('expected headers to be list or dict')
        headers = HeaderDict(headers)

        if json:
            data = ujson.dumps(json)
            if "json" not in headers.get("Content-Type", ""):
                headers["Content-Type"] = "application/json"

        if isinstance(data, dict) or isinstance(data, list):
            data = urlparse.urlencode(data)
            if headers.get("Content-Type", ""):
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                
        if isinstance(cookies, dict):
            cookie_string = "; ".join([str(x)+"="+str(y) for x,y in cookies.items()])
            headers['Cookie'] = cookie_string

        headers = ujson.dumps(list(headers.items()))
        
        headers = convert_string(headers)
        method = convert_string(method)
        data = convert_string(data)
        return url, headers, method, data

    @classmethod
    def request(cls, client_id, method, url, **kw):
        url, headers, method, data = cls.prepare_request(url, method, **kw)
        # raw_resp = cls.lib.make_request(client_id, url, headers, method, data)
        # return cls.parse_response(raw_resp)
        resp = cls.lib.node_fetch(client_id, url, headers, method, data)
        resp.check_error()
        return resp
    
    @classmethod
    def request_with_cb(cls, client_id, callback, method, url, **kw):
        url, headers, method, data = cls.prepare_request(method, url, **kw)
        cls.lib.make_request_with_cb(client_id, url, headers, method, data, callback)
        return

    @classmethod
    def request_with_cb2(cls, client_id, callback, method, url, **kw):
        url, headers, method, data = cls.prepare_request(method, url, **kw)
        cls.lib.node_fetch_with_cb(client_id, url, headers, method, data, callback)
        return

    @classmethod
    def parse_response(cls, raw_response):
        out = ujson.loads(raw_response)
        if out.get("error"):
            raise ClientError(out["error"])
        body = out["body"]
        url = out["url"]
        headers = ujson.loads(out["headers"])
        status = int(out["status"])
        cookies = out["cookies"]
        new_headers = {}
        
        for header in headers:
            new_headers[header] = headers[header][0]
        
        return Response(url, body, new_headers, status, cookies)
        

class Response:
    def __init__(self, url, text, headers, status, cookies):
        self.text = text
        self.url = url
        self.headers = headers
        self.status = status
        self.cookies = cookies

class Fingerprint(Enum):
    CHROME_83 = 'chrome_83'
    CHROME_72 = 'chrome_72'
    FIREFOX_65 = 'firefox_65'
    FIREFOX_56 = 'firefox_56'
    RANDOM = 'random'
    CHROME = 'chrome'
    CHROME_70 = 'chrome_70'
    IOS_12 = 'ios_12'
    FIREFOX = 'firefox'
    FIREFOX_63 = 'firefox_63'
    FIREFOX_55 = 'firefox_55'
    IOS_11 = 'ios_11'
    CHROME_62 = 'chrome_62'
    IOS = 'ios'
    GOLANG = 'golang'

    def __init__(self, value):
        self.typenum = FPType.HID

    def __str__(self):
        return self.value
    
class PktFingerprint(str):
    typenum = FPType.PKT
    pass

class JA3Fingerprint(str):
    typenum = FPType.JA3
    pass