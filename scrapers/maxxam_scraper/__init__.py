# -*- coding: utf-8 -*-
import cfscrape
import requests
import re, random, sys
import jsunpack
from bs4 import BeautifulSoup

import traceback

try:
    import xbmc
    NO_XBMC = False
except:
    NO_XBMC = True

STATUS = ['START']
DEBUG = False

_vars = {}
_vars['for_idx'] = -1
_vars['if_status'] = True
_vars['headers'] = {}
_vars['cookies'] = {}

def _debug(data):
    if DEBUG and NO_XBMC:
        fout = open('debug.out', 'w+')
        fout.write(data)
        fout.close()
    
def _log(tag, data):    
    if DEBUG:
        log_text = 'maxxam {}: {}'.format(tag, str(data))
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

    try:
        _log('_get url', _vars['url'])
        
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

        _log('_get headers', _vars['headers'])
        _log('_get cookies', _vars['cookies'])

        if 'allow_redirects' in _vars:
            response = scraper.get(_vars['url'], headers=_vars['headers'], cookies=_vars['cookies'], allow_redirects=_vars['allow_redirects'])
            # response = requests.get(_vars['url'], proxies='', headers=_vars['headers'], cookies=_vars['cookies'], allow_redirects=False)
        else:
            response = scraper.get(_vars['url'], headers=_vars['headers'], cookies=_vars['cookies'])
        
        _log('_get response', str(response))
        _log('_get response headers', response.headers)
        _setcookies(response, _vars['cookies'])
        _vars['headers']['Referer'] = _vars['url']
        _vars[params[0]] = response.text
        _vars['get_response'] = response
        _vars['soup'] = BeautifulSoup(response.text, 'html.parser')
        
        _debug(str(response) + '\n' + (response.text).encode('utf8'))
    except:
        global STATUS
        STATUS = ['ERROR', '{}'.format(sys.exc_info()), '_get', params]
        
def _re_findall(params): 
    # params = ['var name', 'regex', 'page' [, 'flags=0']]
    #
    # regex flags = 0
    # The expression’s behaviour can be modified by specifying a flags value. Values can be any of the following variables, 
    # combined using bitwise OR (the | operator).   
    #
    # re.DEBUG
    # re.I re.IGNORECASE
    # re.L re.LOCALE
    # re.M re.MULTILINE
    # re.S re.DOTALL
    # re.U re.UNICODE
    # re.X re.VERBOSE
    
    result_var_name, pattern, text_var_name = params[:3]
    
    if len(params) == 3:
        flags = 0
    else:
        flags = eval(params[3])
    
    
    try:
        _vars[result_var_name] = [x for x in re.findall(pattern, _vars[text_var_name], flags=flags)]
        _log('_re_findall', '>>> _re_findall result: {}'.format(_vars[result_var_name]))
    except:
        global STATUS
        STATUS = ['ERROR', '{} {}'.format(sys.exc_info()[1][0], traceback.print_stack()), '_re_findall', params]
        
def _re_search(params):
    # params = ['var_name', 'regex', 'page' [, 'flags=0']]
    #
    # regex flags = 0
    # The expression’s behaviour can be modified by specifying a flags value. Values can be any of the following variables, 
    # combined using bitwise OR (the | operator).   
    #
    # re.DEBUG
    # re.I re.IGNORECASE
    # re.L re.LOCALE
    # re.M re.MULTILINE
    # re.S re.DOTALL
    # re.U re.UNICODE
    # re.X re.VERBOSE
    
    result_var_name, pattern, text_var_name = params[:3]
    
    if len(params) == 3:
        flags = 0
    else:
        flags = eval(params[3])
    
    try:
        match = re.search(pattern, _vars[text_var_name], flags=flags)
        if match:
            if match.groupdict():
                for key in match.groupdict().keys(): _vars[key] = match.groupdict()[key]

            _vars[result_var_name] = match.groups()
        else:
            _vars[result_var_name] = None
            
        _log('_re_search', '>>> _re_search result: {}'.format(_vars[result_var_name]))
    except:
        global STATUS
        STATUS = ['ERROR', '{} {}'.format(sys.exc_info()[1][0], traceback.print_stack()), '_re_search', params]
    
def _python(params):
    try:
        exec('global _vars' + '\n' + params[0])
    except:
        global STATUS
        STATUS = ['ERROR', '{} {}'.format(sys.exc_info()[1][0], traceback.print_stack()), '_python', params]
    
def _eval(params):
    try:
        _vars[params[0]] = eval(params[1])
    except:
        global STATUS
        STATUS = ['ERROR', '{} {}'.format(sys.exc_info()[1][0], traceback.print_stack()), '_eval', params]

def _if(params):
    _vars['if_status'] = bool(eval(params))
    
def _endif():
    _vars['if_status'] = True
    
def _for_in(params):
    _log('for_in params', params)
    _log('for_in idx', _vars['for_idx'])
    
    _vars[params[0]] = eval(params[1])[_vars['for_idx']]
    
    _log('{}'.format(params[0]), _vars[params[0]])
        
def _end_for():
    pass

def scrape(params, json = '', log=False):
    #
    # params: string --> url
    #         dict   --> key "scraper": scraper_id 
    #         dict   --> url (lo scraper viene selezionato con le regex)
    #
    # json:   il json con gli scrapers (se non si vuole utilizzare quello di default)
    #
    # log:    abilita / disabilita il log di debug
    #
    ###############################################################################################################
    
    global DEBUG, STATUS
    
    DEBUG = log
    _log ('scrape', 'scrape sarted with params = {}'.format(params))
    
    if isinstance(params, (basestring, str, unicode)):
        _vars['url'] = params
        if 'params' in _vars: _vars.__delitem__('params')
    else:
        if 'url' in _vars: _vars.__delitem__('url')
        _vars['params'] = params
        
    if json: 
        _vars['json'] = json
    elif not 'json' in _vars:
        return
            
    _vars['headers'] = {}
    
    source = None
    if 'params' in _vars:
        if 'scraper' in _vars['params'] and _vars['params']['scraper'] in _vars['json']['url_scrapers']:
            source = _vars['json']['url_scrapers'][_vars['params']['scraper']]['scrape']
            scraper = _vars['params']['scraper']
            _log('scrape', 'found scraper source {}'.format(_vars['params']['scraper']))
        elif 'url' in _vars['params']:
            _vars['url'] = _vars['params']['url']
            _log('scrape', 'found url {}'.format(_vars['params']['url']))
            
    if not source and 'url' in _vars:
        for scraper in _vars['json']['url_scrapers']:
            if 'regex' in _vars['json']['url_scrapers'][scraper]:
                for reg in _vars['json']['url_scrapers'][scraper]['regex']:
                    _log('scrape', 'testing scraper {}'.format(scraper))
                    if re.search(reg, _vars['url']): 
                        source = _vars['json']['url_scrapers'][scraper]['scrape']
                        break
                    
            if source: break
            
    if source:            
        line = 0
        while True:
            if STATUS and STATUS[0] == 'ERROR':
                _log('scrape.source({}:{})'.format(scraper, line), STATUS)
                return STATUS
                
            cmd = source[line]
            _log('scrape.source({}:{})'.format(scraper, line), '{} {}'.format(cmd, _vars['if_status']))
            if cmd[0][0] == '#':
                _log('scrape.source({}:{})'.format(scraper, line), cmd[1:])
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
                print str(cmd[1:])
            elif _vars['if_status'] and cmd[0] == 'for_in':
                _log('for_idx', _vars['for_idx'])
            
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
                _vars['for_idx'] = -1
                _vars['if_status'] = True

                _python(cmd[1:])
                _log('scrape.source({}:{})'.format(scraper, line), _vars['result'])
                
                for item in _vars['result']:
                    _log('scrape.source result', item)
                    
                    if 'url' in item and 'stop' in item:
                        _log('scrape.source result', str('url' in item and 'stop' in item)) # True
                        return _vars['result']
                    
                    if test(item['url']):
                        return scrape(item['url'], log = True)
                        _log('scrape.source({}:{})'.format(scraper, line), 'result: ' + str(tmp))
                            
                return []
            elif _vars['if_status']:
                _log('scrape.source({}:{})'.format(scraper, line), "Syntax error in {}".format(cmd))
                break
                
            line+=1
    else:
        _log('scrape', 'no source found for: {}'.format(params))

def _is_url(param):
    return param.startswith('http://') or param.startswith('https://')
    
def _find_scraper(url):
    scrapers = _vars['json']['url_scrapers']
    for scraper in scrapers:
        regex = _vars['json']['url_scrapers'][scraper]['regex'] if 'regex' in  _vars['json']['url_scrapers'][scraper] else []
        for r in regex:
            _log('test scraper', '{} regex {}'.format(scraper, r))
            if re.search(r, url): return scraper
    
    return False
    
def get_sites(json = ''):
    if json: 
        _vars['json'] = json
    elif not 'json' in _vars:
        return
    
    return _vars['json']['url_scrapers'].keys()
    
def movie_info():
    res = {}
    for a in ['title', 'genres', 'runtime', 'country']:
        if a in _vars: res[a] = _vars[a]
    return res
    
def test(param, json = '', log=False):
    #
    # param   <stream_url>                                                     -->  test if url can be scraped
    #         [<stream_url>, ... ]
    #         {'url': <stream_url>, ... }
    #         {'url': [<stream_url>, ...], ... }
    #
    #         <site_id>#<search_text>#<stream_site_id>: ... :<stream_site_id>  -->  search site for stream urls
    #
    ################################################################################################################

    global DEBUG, STATUS
    
    DEBUG = log
    
    if json: 
        _vars['json'] = json
    elif not 'json' in _vars:
        return
    
    _log('starting test with param: {}'.format(type(param)), param)
    
    url = None    
    if isinstance(param, (str, unicode, basestring)):
        if _is_url(param): 
            url = [param]
        elif '#' in param and len(param.split('#')) == 3:
            site_id, search_text, stream_sites = param.split('#')
            stream_sites = stream_sites.split(':')
        elif '#' in param and len(param.split('#')) == 2:
            site_id, search_text = param.split('#')
            stream_sites = get_sites()
        else:
            return False
    elif isinstance(param, dict) and 'url' in param and isinstance(param['url'], str):
        url = [param['url']]
    elif isinstance(param, dict) and 'url' in param and isinstance(param['url'], list):
        url = param['url']
    elif isinstance(param, list):
        url = param
    else:
        _log('test exit 2', type(param))
        return False

    if url:        
        for url_test in url: 
            test = _find_scraper(url_test)
            _log('test ({})'.format(url_test), 'result: ' + str(test))
            return bool(test)
    else:
        scrapers = _vars['json']['url_scrapers']
        test = (site_id in scrapers) and bool([site for site in scrapers if site in stream_sites])
        _log('test ({})'.format(site_id), 'result: ' + str(test))
        return test
        
    return False
