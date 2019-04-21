import requests, random, time, re, hashlib, sys
from urlparse import urljoin
from bs4 import BeautifulSoup as bs
from datetime import datetime

try:
    import xbmc
    NO_XBMC = False
except:
    NO_XBMC = True

class facebook():
    def __init__(self, email, password, posts = [], cookies = []):
        self.session = requests.session()
        self.headers = self._random_headers()
        self.status_code = None
        self.fb_login_email = email
        self.fb_login_password = password
        self.soup = None
        self.html = ''
        self.posts = posts
        self.cookies = cookies
        self.base_url = ''
        self.scrape_items = False
            
    def _random_headers(self):
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

    def _relative_url(self, url):
        if url[:4] != 'http':
            return urljoin(self.base_url, url)
        else:
            return url
            
    def _img_scrape(self):
        for el in self.soup.find_all('img'):
            if 'src' in el.attrs:
                self.session.get(self._relative_url(el['src']), headers = self.headers)

    def _iframe_scrape(self):
        for el in self.soup.find_all('iframe'):
            if 'src' in el.attrs:
                self.session.get(self._relative_url(el['src']), headers = self.headers)

    def _time_convert(self, time, months = 'gennaio|febraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre'.split('|')):
        time_re = re.search(r'^(\d{1,2})\s+([^\s]+).+?(\d{2}):(\d{2})$', time)

        if time_re:
            time = '{:0d}/{:0>2d}/{} {:0>2d}:{:0>2d}'.format(int(time_re.group(1)), months.index(time_re.group(2))+1, datetime.now().year, int(time_re.group(3)), int(time_re.group(4)))
            min = (datetime.now()-datetime.strptime(time, '%d/%m/%Y %H:%M')).seconds/60
            if min > 60:
                time = '{}h {}m'.format(int(min/60), min-(int(min/60)*60))
            else:
                time = '{}m'.format(min)
        elif re.search(r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$', time):
            min = (datetime.now()-datetime.strptime(time, '%Y-%m-%d %H:%M:%S')).seconds/60
            if min > 60:
                time = '{}h {}m'.format(int(min/60), min-(int(min/60)*60))
            else:
                time = '{}m'.format(min)
        else:
            time = time.replace(' min', 'm').replace(' h', 'h')

        return time

    def _get(self, url):
        result = self.session.get(url, headers = self.headers, cookies = self.cookies)
        self.headers['Referer'] = url
        self.cookies = result.cookies
        self.base_url = url
        self.html = result.text
        self.status_code = result.status_code
        self._log('_get result: {}, bytes: {}, url: {}'.format(result.status_code, len(self.html), url))
        
        if result.status_code != 200:
            self.soup = None
        else:
            self.soup = bs(result.text, 'html.parser')

    def _post(self, url, data):
        result = self.session.post(url, data = data, headers = self.headers, cookies = self.cookies)
        self.headers['Referer'] = url
        self.cookies = result.cookies
        self.base_url = url
        self.html = result.text
        self.status_code = result.status_code
        self._log('_post result: {}, bytes: {}, url: {}'.format(result.status_code, len(self.html), url))
        
        if result.status_code != 200:
            self.soup = None
        else:
            self.soup = bs(result.text, 'html.parser')
            
    def _debug(self):
        # fout = open('facebook.debug.out', 'w')
        # fout.write(self.html.encode('utf8'))
        # fout.close()
        pass
        
    def _log(self, data, log_enabled = True):
        log_text = 'maxxam facebook: {}'.format(str(data))
        if NO_XBMC:
            print log_text
        else:
            xbmc.log(log_text)
            
    #### FACEBOOK LOGIN ###################################################################################################
    def login(self, scrape_items = True):
        self._log('start login')
        
        login_url = "https://m.facebook.com/"    
        self._get(login_url)
        if (self.status_code != 200) or (self.soup == None): return
        
        if self.soup.select('#root > span:nth-child(3) > img:nth-child(1)'):
            img_url = self._relative_url(self.soup.select('#root > span:nth-child(3) > img:nth-child(1)')[0]['src'])
            self.session.get(img_url, headers = self.headers)
        else:
            self.soup = None
            self.status_code = -1
            return
            
        if not self.soup.select('form input'):
            self.soup = None
            self.status_code = -1
            return
            
        payload = {}
        for i in self.soup.select('form input'):
            if i['type'] != 'submit' and not 'noscript' in i['name']:
                if 'value' in i.attrs:
                    payload[i['name']] = i['value']
                else:
                    payload[i['name']] = ''

        payload['email'] = self.fb_login_email
        payload['pass'] = self.fb_login_password

        if not self.soup.find('form'):
            self.soup = None
            self.status_code = -1
            return
        
        form_action = self._relative_url(self.soup.find('form')['action'])

        self._log('form submit')
        self._post(form_action, payload)
        if (self.status_code != 200) or (self.soup == None): return 
        
        if scrape_items:
            self._img_scrape()
            self._iframe_scrape()
        
    #### GET FACEBOOK HOME PAGE ###########################################################################################
    def get_home(self, scrape_items = True):
        if (self.status_code != 200) or (self.soup == None): return []
        
        self._log('getting home page')
        
        if not self.soup.form or not 'action' in self.soup.form.attrs:
            self.soup = None
            self.status_code = -1
            return
        
        payload = {}
        for input in self.soup.form.find_all('input'):
            if input['type'] == 'hidden':
                try:
                    payload[input['name']] = input['value']
                except:
                    payload[input['name']] = ''
                
        form_action = self._relative_url(self.soup.form['action'])
        self._post(form_action, payload)
        if (self.status_code != 200) or (self.soup == None): return []
        
        self._scrapehome()
        return self.posts
    
    def close(self):
        self.session.close()
        
    #### SCRAPE FACEBOOK HOME PAGE #######################################################################################
    def _scrapehome(self, scrape_items = True):
        if (self.status_code != 200) or (self.soup == None): return
        
        self._log('start scraping page')
    
        self._log('found {} div role="article"'.format(len(self.soup.findAll('div', {'role': 'article'}))))
        if len(self.soup.findAll('div', {'role': 'article'})) == 0:
            ### self._debug()
            self.status_code = -2
            return
            
        for post in self.soup.findAll('div', {'role': 'article'}):
            self._log('*** start for loop ***')
            if 'data-ft' in post.attrs:
                mf_story_key = re.search('["\']mf_story_key["\']\s*:\s*["\']([\-0-9]+)["\']', post.attrs['data-ft'])
                if mf_story_key: 
                    mf_story_key = mf_story_key.group(1)
                    self._log('found mf_story_key = ' + mf_story_key)
            else:
                mf_story_key = '__unknown__'
                
            post_time = ''
            if post.find('abbr'): 
                post_time = post.find('abbr').text
            else:
                for a in post.findAll('a'):
                    href = a['href'].replace('%3A', ':').replace('%22', '"').replace('%2C', ',')
                    post_time = re.search('"publish_time":([0-9]+?),', href)
                    if post_time:
                        post_time = str(datetime.fromtimestamp(int(post_time.group(1))))
                        break
                    else:
                        post_time = re.search(':view_time\.([0-9]+?):', href)
                        if post_time:
                            post_time = str(datetime.fromtimestamp(int(post_time.group(1))))
                            break
            
            if post_time:
                r_post_time = self._time_convert(post_time)
                self._log('post time: {} --> {}'.format(post_time, r_post_time))
                post_time = r_post_time          
            
            if not post.find('h3'): # or not 'dv' in post.find('h3').attrs['class']: 
                self._log('h3 not found')
                continue
            
            if post.find('h3'):
                user = post.find('h3').text.strip()
                user = re.sub('[\n\r\t]',' ', user)
                user = re.sub('\s+',' ', user)
                user = user.encode('utf8')
            else:
                user = '__unknown__'
            
            self._log('user = ' + str(user))
            
            paragraph = post.find('p')
            if paragraph: 
                paragraph = paragraph.text
                paragraph = re.sub('[\r\n\t]+', '', paragraph)
                paragraph = re.sub('\s+', ' ', paragraph)
                paragraph = paragraph.encode('utf8')
            else:
                paragraph = ''

            self._log('paragraph = ' + str(paragraph))
            
            image = ''
            for img in post.findAll(
                        lambda tag:tag.name == "img" and re.search('scontent', tag.attrs['src'])):
                try:
                    image = img.attrs['src'].encode('utf8')
                    break
                except:
                    pass
            
            self._log('image = ' + str(image))
            
            _hash = hashlib.md5(paragraph + image).hexdigest()
            if (paragraph or image) and not _hash in [h['hash'] for h in self.posts]:
                self.posts.append({
                    'story_key': mf_story_key.encode('utf8'),
                    'hash': _hash,
                    'user': user,
                    'time': post_time,
                    'text': paragraph,
                    'image': image})
                
        if scrape_items:
            self._img_scrape()
            self._iframe_scrape()

if __name__ == '__main__':
    fb_email    = '** your email *****'  
    fb_password = '** your password **'
    
    if fb_email == '** your email *****' or fb_password == '** your password **':
        print 'To test the library you must enter (in the code) your email and password to access facebook'
    else:
        fb = facebook(fb_email, fb_password)
        fb.login()
        
        res_posts = fb.get_home()
        if res_posts:
            for post in res_posts:
                print post['story_key'], post['hash']
                if post['text'] and post['image']:
                    print '{} [{}] {} {}'.format(post['user'], post['time'], post['text'], post['image'])
                elif post['text']:
                    print '{} [{}] {}'.format(post['user'], post['time'], post['text'])
                else:
                    print '{} [{}] {}'.format(post['user'], post['time'], post['image'])
                print
        else:
            print 'receiveid {} from facebook'.format(fb.status_code)
            
        fb.close()
