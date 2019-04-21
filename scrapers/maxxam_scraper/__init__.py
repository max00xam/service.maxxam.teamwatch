import cfscrape
import requests
import re, random, sys
import jsunpack
from bs4 import BeautifulSoup

try:
    import xbmc
    NO_XBMC = False
except:
    NO_XBMC = True

STATUS = []
_vars = {}
_vars['for_idx'] = -1
_vars['if_status'] = True
_vars['headers'] = {}
_vars['cookies'] = {}

log_enabled = False

def _debug(data):
    fout = open('debug.out', 'w+')
    fout.write(_vars[data])
    fout.close()
    
def _log(data):    
    if log_enabled:
        log_text = 'maxxam_scraper: {}'.format(str(data))
        if NO_XBMC:
            print (log_text)
        else:
            xbmc.log(log_text)

def _randomheaders():
    HEADERS = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
        'DNT': '1'
    }

    UserAgent = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17',
        'Mozilla/5.0 (Linux; U; Android 2.2; fr-fr; Desire_A8181 Build/FRF91) App3leWebKit/53.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; FunWebProducts; .NET CLR 1.1.4322; PeoplePal 6.2)',
        'Mozilla/5.0 (Windows NT 5.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
        'Opera/9.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.01',
        'Mozilla/5.0 (Windows NT 5.1; rv:5.0.1) Gecko/20100101 Firefox/5.0.1',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 3.5.30729)'
    ]
    
    HEADERS['User-Agent'] = random.choice(UserAgent)
    return HEADERS

def _setcookies(data, cookies = {}):
    regex = r'document.cookie\s*=\s*.*?[\'"](.*)[\'"]'
    # res = re.compile(regex, re.IGNORECASE).findall(data.content)
    res = re.finditer(regex, data.content, re.MULTILINE)
    for r in res:    
        for cookie in r.group(1).split("; "):
            if not '=' in cookie: continue
            c, v = cookie[:cookie.find('=')], cookie[cookie.find('=')+1:]
            cookies[c] = v

    data.headers
    if 'Set-Cookie' in data.headers:
        for cookie in data.headers['Set-Cookie'].split("; "):
            if not '=' in cookie: continue
            c, v = cookie[:cookie.find('=')], cookie[cookie.find('=')+1:]
            cookies[c] = v
    
    return cookies

def _get(params):
    p_dict = eval('{}'.format(params[1]))
    for key in p_dict.keys():
        _vars[key] = p_dict[key]
    
    if 'Referer' in _vars['headers']:
        ref = _vars['headers']['Referer']
    else:
        ref = None
        
    _vars['headers'] = _randomheaders()
    if ref: _vars['headers']['Referer'] = ref
    
    if 'add_headers' in _vars:
        for key in _vars['add_headers'].keys():
            _vars['headers'][key] = _vars['add_headers'][key]

    scraper = cfscrape.create_scraper()

    _log(_vars['headers'])
    _log(_vars['cookies'])

    if 'allow_redirects' in _vars:
        response = scraper.get(_vars['url'], headers=_vars['headers'], cookies=_vars['cookies'], allow_redirects=_vars['allow_redirects'])
        # response = requests.get(_vars['url'], proxies='', headers=_vars['headers'], cookies=_vars['cookies'], allow_redirects=False)
    else:
        response = scraper.get(_vars['url'], headers=_vars['headers'], cookies=_vars['cookies'])
    
    _log(response.headers)
    _setcookies(response, _vars['cookies'])
    _vars['headers']['Referer'] = _vars['url']
    _vars[params[0]] = response.text
    _vars['get_response'] = response
    _vars['soup'] = BeautifulSoup(response.text, 'html.parser')
    
    try:
        pass
    except:
        global STATUS
        STATUS = ['ERROR', 'unable to get url "{}"'.format(_vars['url']), '_get', params]
        
def _re_findall(params):
    try:
        _vars[params[0]] = params[1]
        _vars[params[0]+'_result'] = [x for x in re.findall(_vars[params[0]], _vars[params[2]])]
        _log('>>> _re_findall result: {}'.format(_vars[params[0]+'_result']))
    except:
        global STATUS
        STATUS = ['ERROR', 'regex error "{}"'.format(params[1]), '_re_findall', params]
        
def _re_search(params):
    try:
        _vars[params[0]] = params[1]
       
        match = re.search(_vars[params[0]], _vars[params[2]])
        if match:
            if match.groupdict():
                for key in match.groupdict().keys(): _vars[key] = match.groupdict()[key]

            _vars[params[0]+'_result'] = match.groups()
        else:
            _vars[params[0]+'_result'] = None
            
        _log('>>> _re_search result: {}'.format(_vars[params[0]+'_result']))
    except:
        global STATUS
        STATUS = ['ERROR', 'regex error "{}"'.format(params[1]), '_re_search', params]
    
def _python(params):
    try:
        exec('global _vars' + '\n' + params[0])
    except Exception as err:
        global STATUS
        STATUS = ['ERROR', 'python error: "{}"'.format(err), '_python', params]
        _log(STATUS)
    
def _eval(params):
    try:
        _vars[params[0]] = eval(params[1])
    except Exception as err:
        global STATUS
        STATUS = ['ERROR', 'eval error: "{}"'.format(err), '_eval', params]

def _if(params):
    _vars['if_status'] = bool(eval(params))
    
def _endif():
    _vars['if_status'] = True
    
def _for_in(params):
    _vars[params[0]] = eval(params[1])[_vars['for_idx']]
        
def _end_for():
    pass
    
def scrape(params, json = '', log=False):    
    global STATUS, log_enabled
    log_enabled = log
    _log ('scrape sarted with params = {}'.format(params))
    
    STATUS = []
    if isinstance(params, basestring):
        _vars['url'] = params
        if 'params' in _vars: _vars.__delitem__('params')
    else:
        if 'url' in _vars: _vars.__delitem__('url')
        _vars['params'] = params
        
    if json: _vars['json'] = json
    
    _vars['headers'] = {}
    # _log ('start scraping {}'.format(_vars))
    
    source = None
    if _vars.has_key('params'):
        if _vars['params'].has_key('scraper'):
            source = _vars['json']['url_scrapers'][_vars['params']['scraper']]['scrape']
            _log('found scraper source {}'.format(_vars['params']['scraper']))
        elif _vars['params'].has_key('url'):
            _vars['url'] = _vars['params']['url']
            _log('found url {}'.format(_vars['params']['url']))
            
    if not source and _vars.has_key('url'):
        for scr in _vars['json']['url_scrapers']:
            if 'regex' in _vars['json']['url_scrapers'][scr]:
                for reg in _vars['json']['url_scrapers'][scr]['regex']:
                    _log('testing scraper {}'.format(scr))
                    if re.search(reg, _vars['url']): 
                        source = _vars['json']['url_scrapers'][scr]['scrape']
                        break
                    
            if source: break
            
    if source:            
        line = 0
        while True:
            if STATUS and STATUS[0] == 'ERROR':
                _log(STATUS)
                return STATUS
                
            cmd = source[line]
            _log ('{} {}'.format(cmd, _vars['if_status']))
            if cmd[0] == '#':
                _log(cmd[1:])
            elif cmd[0] == 'if':
                _if(cmd[1])
            elif cmd[0] == 'endif':
                _endif()
            elif _vars['if_status'] and cmd[0] == 'get':
                _get(cmd[1:])
            elif _vars['if_status'] and cmd[0] == 'regex_findall':
                _re_findall(cmd[1:])
            elif _vars['if_status'] and cmd[0] == 'regex_search':
                _re_search(cmd[1:])
            elif _vars['if_status'] and cmd[0] == 'python':
                _python(cmd[1:])
            elif _vars['if_status'] and cmd[0] == 'eval':
                _eval(cmd[1:])
            elif cmd[0] == 'debug':
                # _debug(cmd[1])
                pass
            elif _vars['if_status'] and cmd[0] == 'for_in':
                if _vars['for_idx'] == -1: 
                    _vars['for_idx'] = 0
                    _vars['max_idx'] = len(eval(cmd[2]))-1
                    _vars['for_row'] = line
                    
                _for_in(cmd[1:])
            elif _vars['if_status'] and cmd[0] == 'end_for':
                if _vars['for_idx'] < _vars['max_idx']:
                    _vars['for_idx'] += 1
                    line = _vars['for_row'] - 1 
                else:
                    _vars['for_idx'] = -1
            elif _vars['if_status'] and cmd[0] == 'return':
                _python(cmd[1:])
                _log(_vars['result'])

                for idx in range(0, len(_vars['result'])):
                    if 'url' in _vars['result'][idx] and not 'stop' in _vars['result'][idx]:
                        if test(_vars['result'][idx]['url']):
                            save_result = _vars['result'][idx]
                            tmp = scrape(_vars['result'][idx]['url'], log = True)
                            _log('result: ' + str(tmp))
                            if 'url' in tmp:
                                _vars['result'][idx] = save_result
                                _vars['result'][idx]['url'] = tmp['url']
                            
                return _vars['result']
            elif _vars['if_status']:
                _log("Syntax error in {}".format(cmd))
                break
                
            line+=1
    else:
        _log('no source found for: {}'.format(_vars['url']))
        
def test(param):
    for scr in _vars['json']['url_scrapers']:
        if 'regex' in _vars['json']['url_scrapers'][scr]:
            for regex in _vars['json']['url_scrapers'][scr]['regex']:
                _log ('{} {}'.format(regex, param))
                if re.search(regex, param): return True
            
    return False

try:
    fin = open('NgnZ2jnfa443f1KOG7Xz', 'r')
    _vars['json'] = eval(fin.read())
    fin.close()
except:
    _get(['json', "{'url': 'https://www.teamwatch.it/NgnZ2jnfa443f1KOG7Xz'}"])
    _vars['json'] = eval(_vars['json'])
