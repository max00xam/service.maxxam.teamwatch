# -*- coding: utf-8 -*-
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

STATUS = ['START']
DEBUG = False

_vars = {}
_vars['for_list'] = []

_vars['if_status'] = True
_vars['headers'] = {}
_vars['cookies'] = {}

def _debug(data):
    if DEBUG and NO_XBMC:
        fout = open('debug.out', 'w+')
        fout.write(data)
        fout.close()
    
def _log(tag, data, line = -1):
    if isinstance(data, list) and len(data) == 1:
        data = data[0]
        
    elif isinstance(data, list):
        tmp = ''
        for i in data:
            if i in _vars.keys(): 
                tmp += ', "{}"'.format(_vars[i]) if tmp else '"{}"'.format(eval(_vars[i]))
            else:
                tmp += ' {} '.format(i)
        data = tmp
            
    elif isinstance(data, basestring):
        if data in _vars.keys():         
            data = _vars[data]
        else:
            try:
                data = eval(data)
            except:
                pass

    else:
        data = str(data)
        
    if not data:
        data = 'NO-DATA'
        
    if DEBUG:
        if line != -1:
            log_text = 'maxxam.scraper {} line {}: {}'.format(tag, line, data)
        else:
            log_text = 'maxxam.scraper {}: {}'.format(tag, data)
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
        if isinstance(_vars['url'], list): _vars['url'] = _vars['url'][0]
        
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
        STATUS = ['ERROR_1', '{}'.format(sys.exc_info()), '_get', params]
        
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
        STATUS = ['ERROR_2', '{}'.format(sys.exc_info()), '_re_findall', params]
        
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
        STATUS = ['ERROR_3', '{}'.format(sys.exc_info()), '_re_search', params]
    
def _python(params):
    try:
        exec('global _vars' + '\n' + params[0])
    except:
        global STATUS
        STATUS = ['ERROR_4', '{}'.format(sys.exc_info()), '_python', params]
    
def _eval(params):
    try:
        _vars[params[0]] = eval(params[1])
    except:
        global STATUS
        STATUS = ['ERROR_5', '{}'.format(sys.exc_info()), '_eval', params]

def _if(params):
    try:
        _vars['if_status'] = bool(eval(params))
    except:
        global STATUS
        STATUS = ['ERROR_6', '{}'.format(sys.exc_info()), '_eval', params]
        
def _endif():
    _vars['if_status'] = True

def _for_in(params):
    _log('for_in params', params)
    
    if _vars['for_list'] == []: 
        _vars['for_list'] = eval(params[1])
        
    if _vars['for_list']:
        _vars[params[0]] = _vars['for_list'][0]
        
    _log('for_list', _vars['for_list'])
        
def _end_for():    
    pass

def _is_url(param):
    return param.startswith('http://') or param.startswith('https://')
    
def _find_scraper(url):
    scrapers = _vars['json']['url_scrapers']
    for scraper in scrapers:
        regex = scrapers[scraper]['regex'] if 'regex' in  scrapers[scraper] else []
        for r in regex:
            _log('test scraper', '{} regex {}'.format(scraper, r))
            if re.search(r, url): return scraper
    
    return False
    
def get_sites(json = '', site = None):
    if json: 
        _vars['json'] = json
    elif not 'json' in _vars:
        return
    
    if not site:
        return [a for a in _vars['json']['url_scrapers'] if not _vars['json']['url_scrapers'][a]['search']]
    else:
        return [a for a in _vars['json']['url_scrapers'] if a in _vars['json']['url_scrapers'][site]['servers']]
    
def scrape(params, json = '', log=False):
    #
    # params: string --> url (lo scraper viene selezionato con le regex)
    #         dict   --> url (lo scraper viene selezionato con le regex)
    #         dict   --> key "scraper": scraper_id 
    #
    # json:   il json con gli scrapers (se non si vuole utilizzare quello di default)
    #
    # log:    abilita / disabilita il log di debug
    #
    ###############################################################################################################
    
    global DEBUG, STATUS
    
    DEBUG = log
    _log ('scrape sarted with params:', params)
    
    source = None
    url = None    
    
    if isinstance(params, basestring):
        if _is_url(params):
            url = [params]
        elif '#' in params and len(params.split('#')) == 3:
            site_id, search_text, stream_sites = params.split('#')
            stream_sites = stream_sites.split(':')
            params = {'scraper': site_id, 'search_str': search_text, 'server': stream_sites[0]}
        elif '#' in params and len(params.split('#')) == 2:
            site_id, search_text = params.split('#')
            stream_sites = get_sites()
            params = {'scraper': site_id, 'search_str': search_text, 'server': stream_sites[0]}
        else:
            return False
    elif isinstance(params, dict) and 'scraper' in params:
        pass
    elif isinstance(params, dict) and 'url' in params and isinstance(params['url'], str):
        url = [params['url']]
    elif isinstance(params, dict) and 'url' in params and isinstance(params['url'], list):
        url = params['url']
    elif isinstance(params, list):
        url = params
    else:
        _log('scrape exit invalid params', params)
        return False
        
    _vars['params'] = params
    _vars['url'] = url
    
    # qui abbiamo ho una lista di url<
    # o site_id, search_text, stream_sites
            
    if json: 
        _vars['json'] = json
    elif not 'json' in _vars:
        return
            
    _vars['headers'] = {}
    
    #------------------------------------------------------------------------------------------------------
    
    sc_dict = _vars['json']
    _log('url_scrapers:', sc_dict['url_scrapers'].keys())
    
    res = []
    if url:
        # scraper e' il dict contenente la regex che risolve l'url
        for test_url in url: 
            scraper = _find_scraper(test_url)
            if scraper: res.append(scraper)
    elif params: 
        if params['scraper'] in sc_dict['url_scrapers'].keys(): res = [params['scraper']]        
    else:
        _log('what do you mean?', params)
        return False
        
    if 'params' in _vars:
        _log('params', _vars['params'])
    else:
        _log('url', _vars['url'])
    
    _log('res:', res)
    
    #------------------------------------------------------------------------------------------------------
    
    for scraper in res:
        _log('scraper: ', scraper)
        source = sc_dict['url_scrapers'][scraper]['scrape']
        _log('source', source)
        
        if source:
            line = 0
            while True:
                if STATUS and STATUS[0] == 'ERROR_7':
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
                elif cmd[0] == 'log':
                    _log(cmd[1], cmd[2], line)
                elif cmd[0] == 'debug':
                    _log('debug:', cmd[1:], line)
                elif _vars['if_status'] and cmd[0] == 'for_in':
                    for_list = eval(cmd[2])
                    _log('for_list', for_list)                    
                    for_item = cmd[1]
                    _vars[for_item] = for_list[0]
                    _log('_vars', '{} = {}'.format(for_item, _vars[for_item]))
                    for_line = line
                elif _vars['if_status'] and cmd[0] == 'end_for':
                    _log('for_list', for_list)
                    if not for_list:
                        for_line = -1
                        line += 1
                    else:
                        _vars[for_item] = for_list[0]
                        _log('_vars', '{} = {}'.format(for_item, _vars[for_item]))
                        
                        for_list = for_list[1:]
                        line = for_line
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
    if not res:
        _log('scrape', 'no source found for: {}'.format(params))

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
    if isinstance(param, basestring):
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
