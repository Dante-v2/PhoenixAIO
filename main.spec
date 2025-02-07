block_cipher = None

a = Analysis(['entry.py'],
             pathex=['.'],
             binaries=[],
             datas=[('pytransform/_pytransform.dll', 'pytransform/.'), ('C:/Users/Dany/AppData/Local/Programs/Python/Python38/lib/site-packages/Cryptodome','./Cryptodome'), ('C:/Users/Dany/AppData/Local/Programs/Python/Python38/Lib/site-packages/pyppeteer_stealth', './pyppeteer_stealth'), ('helheim/pytransform.pyd', 'helheim/.'), ('cloudscraper/user_agent/browsers.json', 'cloudscraper/user_agent'), ('cloudscraper/interpreters/native.py', 'cloudscraper/interpreters'), ('cloudscraper/interpreters/nodejs.py', 'cloudscraper/interpreters'), ('cloudscraper/interpreters/js2py.py', 'cloudscraper/interpreters'), ('cloudscraper/captcha/2captcha.py', 'cloudscraper/captcha'), ('cloudscraper/captcha/9kw.py', 'cloudscraper/captcha'), ('cloudscraper/captcha/anticaptcha.py', 'cloudscraper/captcha'), ('cloudscraper/captcha/deathbycaptcha.py', 'cloudscraper/captcha'), ('hawk_cf_api/hawk_cf.py', 'hawk_cf_api/.'), ('hawk_cf_api/utils.py', 'hawk_cf_api/.'), ('hawk_cf_api/exceptions.py', 'hawk_cf_api/.')],
             hiddenimports=['load', 'pyppeteer.errors', 'pyppeteer.__init__', 'Cryptodome', 'Crypto', 'pycryptodomex','pyppeteer.launch','pyppeteer.connection', 'threadpoolctl', 'pyppeteer.command', 'pyppeteer.helper', 'pyppeteer.execution_context', 'pyppeteer.chromium_downloader', 'pyppeteer.options', 'pyppeteer.util', 'pyppeteer.coverage', 'pyppeteer.dialog', 'pyppeteer.element_handle', 'pyppeteer.emulation_manager', 'pyppeteer.frame_manager', 'pyppeteer.us_keyboard_layout', 'pyppeteer.input', 'pyppeteer.navigator_watcher', 'pyppeteer.multimap', 'pyppeteer.network_manager', 'pyppeteer.tracing', 'pyppeteer.worker', 'pyppeteer.page', 'pyppeteer.target', 'pyppeteer.browser', 'pyppeteer.launcher', 'pyppeteer', 'pyppeteer_stealth', 'pyppeteer_stealth.js', 'asyncio', 'scripts.here', 'scripts.naked', 'scripts.here', 'main', 'json', 'requests', 'threading', 'csv', 'brotli', 'requests_html', 'js2py', 'scripts.gen.gengaleries', 'scripts.genoffwhite', 'dns.resolver', 'scripts.gen', 'urllib3', 'sys', 'colorlog', 'dhooks', 'polling2','scripts.pokemoncenterjp','websocket', 'random', 'base64', 'autosolveclient', 'autosolveclient.autosolve', 'scripts.gen.galeries', 'pycryptodome', 'platform', 'Crypto', 'random', 'ctypes', 'logging', 'os', 'time', 're', 'urllib', 'cloudscraper', 'names', 'lxml', 'cloudscraper', 'names', 'string', 'pytz', 'datetime', 'mods', 'mods.logger', 'mods.errorHandler', 'discord_webhook', 'bs4', 'playsound', 'twocaptcha', 'helheim', 'card_identifier.card_type', 'hawk_cf_api.hawk_cf', 'cryptography.hazmat.primitives.asymmetric', 'cryptography.hazmat.primitives.ciphers.aead', 'AES','cryptography.hazmat.backends', 'dns', 'resolver', 'selenium.webdriver', 'numpy', 'copy', 'webdriver', 'Crypto.Cipher', 'PIL.Image', 'binascii', 'PIL', 'selenium', 'requests.packages.urllib3.util.ssl_','Crypto.Cipher.AES', 'Pillow', 'requests.adapters', 'helheim.kasada', 'helheim.detection', 'helheim.core', 'helheim.lzstring', 'helheim.packer', 'helheim.msgpack', 'helheim.config', 'helheim.exceptions', 'helheim.obfuscation', 'helheim.hCaptcha', 'helheim.sns','helheim.slowAES', 'helheim.wokou', 'helheim.vanaheim', 'helheim.packer', 'helheim.saas', 'helheim.bfm', 'helheim.utils', 'helheim.pytransform', 'helheim.jsch', 'helheim.__init__', 'cloudscraper.user_agent', 'scripts.sns', 'scripts.cCleaned', 'scripts.curlDecode', 'scripts.ambush', 'scripts.tba', 'scripts.gen.gencorner', 'scripts.mobile', 'scripts.footlocker', 'scripts.emiliopucci', 'scripts.titolo', 'scripts.workingclassheroes', 'scripts.revolve', 'scripts.galeries', 'scripts.susi', 'scripts.offwhite', 'scripts.slamjam', 'scripts.cornerstreet', 'scripts.b4b', 'scripts.sav', 'scripts.sneakers76', 'scripts.sugar', 'scripts.einhalb', 'scripts.starcow', 'scripts.prodirect', 'scripts.bstn', 'scripts.suppastore', 'scripts.footdistrict', 'scripts.gen.genb4b', 'scripts.gen.genemilio', 'scripts.susi', 'scripts.awlab', 'scripts.allike', 'scripts.gen.gensotf', 'scripts.sotf', 'htmllistparse', 'pkg_resources', 'colorama', 'colorama.Fore', 'pypresence', 'pypresence.Presence', 'flask', 'flask.Flask', 'flask.request', 'flask.jsonify', 'flask.render_template', 'ssl', 'socket', 'hashlib', 'psutil', 'tempfile', 'uuid', 'wget', 'importlib', 'requests_toolbelt', 'traceback', 'requests_toolbelt.utils.dump', 'cloudscraper.interpreters.js2py', 'cloudscraper.interpreters.native', 'cloudscraper.interpreters.nodejs', 'cloudscraper.user_agent', 'cloudscraper.exceptions', 'python3_anticaptcha.NoCaptchaTask', 'python3_anticaptcha.CallbackClient', 'python3_anticaptcha.ReCaptchaV3TaskProxyless', 'python3_anticaptcha.NoCaptchaTaskProxyless', 'cloudscraper.captcha', 'msgpack', 'pyparsing', 'lzstring', 'zerorpc', 'cryptography'],
             hookspath = [],
             runtime_hooks = [],
             excludes = [],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles, 
          a.datas,
          [],
          name='Phoenix',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True,
          icon='C:\\Users\\Dany\\Desktop\\Scrapers_pids\\3logo.ico')