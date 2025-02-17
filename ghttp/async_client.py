import functools
from .utils import (
            Lib,
            CFUNCTYPE,
            GoString,
            c_char_p,
            Fingerprint,
            synchronized,
            GoResponse,
            Structure,
            client_params
    )
import asyncio
from concurrent.futures import ThreadPoolExecutor

class Session:
    lib = None
    executor = False
    client_params = None

    @classmethod
    @synchronized
    def set_executor(cls):
        if cls.executor:
            return cls.executor
        cls.executor = ThreadPoolExecutor(max_workers=500)
        return cls.executor
        
    def __init__(self, proxy=None, fingerprint=Fingerprint.CHROME, timeout=20, redirect=True, verify_ssl=True, settings=None):
        self.lib = Lib()
        self.client_params = client_params(proxy, fingerprint, verify_ssl, settings)
        self.client_id = self.lib.new_client(self.client_params, timeout=timeout, redirect=redirect)

        self.executor = self.set_executor()
        self.request = self.request2

    def switch_proxy(self, proxy, fingerprint=None):
        if proxy:
            self.client_params.proxy = proxy
        if fingerprint:
            self.client_params.fingerprint = fingerprint
        self.lib.switch_proxy(self.client_id, self.client_params)

    def get_cb(self, loop, future):
        def callback(out):
            try:
                out = self.lib.parse_response(out)
                loop.call_soon_threadsafe(future.set_result, out)
            except BaseException as e:
                loop.call_soon_threadsafe(future.set_exception, e)
        return callback

    def get_cb2(self, loop, future):
        def callback(out):
            try:
                out.check_error()
                loop.call_soon_threadsafe(future.set_result, out)
            except BaseException as e:
                loop.call_soon_threadsafe(future.set_exception, e)
            return 0
        return callback

    async def request2(self, method, url, **kw) -> GoResponse:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        functype = CFUNCTYPE(None, c_char_p)
        # callback = functype(self.get_cb(loop, future))
        # self.lib.request_with_cb(self.client_id, callback, method, url, **kw)
        functype = CFUNCTYPE(None, GoResponse)
        callback = functype(self.get_cb2(loop, future))
        self.lib.request_with_cb2(self.client_id, callback, method, url, **kw)
        return await future

    async def request1(self, method, url, **kw) -> GoResponse:
        loop = asyncio.get_running_loop()
        #return await loop.run_in_executor(self.executor, self.lib.request, self.client_id, url, method, **kw)
        return await loop.run_in_executor(self.executor, functools.partial(self.lib.request, **kw), self.client_id, url, method) #, **kw)
        
    async def get(self, url, **kw) -> GoResponse:
        return await self.request('GET', url, **kw)

    async def post(self, url, **kw):
        return await self.request('POST', url, **kw)

    async def head(self, url, **kw):
        return await self.request('HEAD', url, **kw)

    async def put(self, url, **kw):
        return await self.request('PUT', url, **kw)

    async def patch(self, url, **kw):
        return await self.request('PATCH', url, **kw)

    async def delete(self, url, **kw):
        return await self.request('DELETE', url, **kw)
    
def main():
    pass
