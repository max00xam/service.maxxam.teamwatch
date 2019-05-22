# -*- coding: utf-8 -*-
import os, re, sys
import base64
import sha
import time
import urllib
import urllib2
import hashlib
import json
import xbmc
import xbmcgui
import xbmcaddon
import pastebin
import random
import HTMLParser
import xml.etree.ElementTree as xml
from datetime import datetime, date, timedelta

#         ___________                                                     #
#         \__    ___/___ _____   _____                                    #
#           |    |_/ __ \\__  \  /     \                                  #
#           |    |\  ___/ / __ \|  Y Y  \                                 #
#           |____| \___  >____  /__|_|  /                                 #
#                      \/     \/      \/                                  #
#                 __      __         __         .__                       #
#                /  \    /  \_____ _/  |_  ____ |  |__                    #
#                \   \/\/   /\__  \\   __\/ ___\|  |  \                   #
#                 \        /  / __ \|  | \  \___|   Y  \                  #
#                  \__/\  /  (____  /__|  \___  >___|  /                  #
#                       \/        \/          \/     \/  by maxxam        #


__version__     = "0.0.15"
__addon__       = xbmcaddon.Addon()
__resources__   = os.path.join(__addon__.getAddonInfo('path'),'resources')
__pylib__       = os.path.join(__addon__.getAddonInfo('path'), 'lib')

ADDONID = __addon__.getAddonInfo('id')

sys.path.append(__pylib__)
sys.path.append(os.path.join(__pylib__, 'maxxam_imdb'))
sys.path.append(os.path.join(__pylib__, 'PIL'))
sys.path.append(os.path.join(__addon__.getAddonInfo('path'), 'scrapers'))
sys.path.append(os.path.join(__addon__.getAddonInfo('path'), 'scrapers', 'requests'))

import betterimap
import xbmc_helpers
from iinfo import get_image_info as img_info
from facebook import facebook
from bs4 import BeautifulSoup
# from PIL import Image
from xbmc_helpers import localize
from gsearch import search as google
import maxxam_imdb as imdb
import maxxam_scraper as scraper

class KodiEvents(xbmc.Monitor):    
    def __init__(self, tw):
        self.teamwatch = tw
    
    def onSettingsChanged(self):
        xbmc.Monitor.onSettingsChanged(self)
        xml_path = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch', 'settings.xml')
        root = xml.parse(xml_path).getroot().findall('setting')
        settings = {}
        for value in [(x.get('id'),  x.text) for x in root]: settings[value[0]]=value[1]
        self.teamwatch.settings(settings)

    """    
    def onNotification(self, sender, method, data):
        xbmc.Monitor.onNotification(self, sender, method, data)
        xbmc.log('%s: service.maxxam.teamwatch Notification %s from %s, params: %s' % (ADDONID, method, sender, str(data)))
    """
               
class TeamWatch():
    WINDOW_FULLSCREEN_VIDEO = 12005
    DISPLAY_TIME_SECS = 8
    REFRESH_TIME_SECS = 2
    CHECK_EMAIL_SECS = 60
    CHECK_FACEBOOK_SECS = 300
    SOCKET_TIMEOUT = 0.5
    DEBUG = 1 # 0 = HIGH, 1 = MEDIUM, 2 = LOW lasciare a uno! (solo _log <= DEBUG vengono visualizzti)

    ICON_CHAT = 0
    ICON_TWITTER = 1
    ICON_SETTING = 2
    ICON_TELEGRAM = 3
    ICON_RSSFEED = 4
    ICON_FACEBOOK = 5
    ICON_EMAIL = 6
    ICON_ERROR = 7
    
    SKIN_CONFIG = 'default.skin'

    FACEBOOK_USER_LENGTH = 30
    TWEETS_OFF = False
    RSS_OFF = False
    FB_OFF = False

    monitor = None
    
    window = None
    background = None
    icon = None
    feedtext = None
    icon_rss_off = None
    icon_tweet_off = None
    icon_fb_off = None
    
    id_teamwatch = __addon__.getSetting('twid')
    id_playerctl = __addon__.getSetting('pcid')
    nickname = __addon__.getSetting('nickname')
	
    twitter_enabled = __addon__.getSetting('twitter_enabled')
    twitter_language = __addon__.getSetting('language')
    twitter_language = xbmc.convertLanguage(twitter_language, xbmc.ISO_639_1)
    twitter_result_type = __addon__.getSetting('result_type')
    
    facebook_enabled = __addon__.getSetting('facebook_enabled')
    facebook_email = __addon__.getSetting('facebook_email')
    facebook_password = __addon__.getSetting('facebook_password')
    
    email_enabled = __addon__.getSetting('email_enabled')
    email = __addon__.getSetting('email')
    email_password = __addon__.getSetting('email_password')
    email_imap = __addon__.getSetting('email_imap')
    
    if __addon__.getSetting('imdb_lang') == 'Italian':    
        imdb_translate = 'it'
    elif __addon__.getSetting('imdb_lang') == 'French':    
        imdb_translate = 'fr'
    elif __addon__.getSetting('imdb_lang') == 'German':    
        imdb_translate = 'de'
    else:
        imdb_translate = None
        
    show_allways = not (__addon__.getSetting('showallways') == "true")
    
    screen_height = __addon__.getSetting('screen_height')
    if screen_height == "": 
        try:
            screen_height = xbmcgui.getScreenHeight()
        except:
            screen_height = 75
    else:
        screen_height = int(__addon__.getSetting('screen_height'))
        
    screen_width = __addon__.getSetting('screen_width')
    if screen_width == "":
        try:
            screen_width = xbmcgui.getScreenWidth()
        except:
            screen_width = 800
    else:
        screen_width = int(__addon__.getSetting('screen_width'))
    
    bartop = screen_height - 75
    
    session_id = list('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') # !#$%&+-*=@^_|~
    random.shuffle(session_id)
    session_id = ''.join(session_id)[:15]
    
    skin = {}
    skin['text_color'] = '0xff000000'
    skin['nickname_color'] = 'blue'
    skin['margin_left'] = '100'
    skin['font'] = 'font45'
    skin['bar_chat'] = 'default_chat.png'
    skin['bar_settings'] = 'default_settings.png'
    skin['bar_telegram'] = 'default_telegram.png'
    skin['bar_twitter'] = 'default_tweet.png'
    skin['bar_rssfeed'] = 'default_rss.png'
    skin['bar_facebook'] = 'default_chat.png'
    skin['bar_email'] = 'default_chat.png'
    skin['bar_error'] = skin['bar_settings'] # Fare la nuova barra
    skin['icon'] = 'icon.png'
    
    show_enable = True
    feed_show_time = None
    feed_name = ['#teamwatch']
    feed_is_shown = False;
    show_disable_after = False
    start_time = time.time()
    
    email_time = time.time()
    emails_unread = []
    emails_shown = []
    
    facebook_time = time.time()
    facebook_posts = []    
    facebook_posts_shown = []
    facebook_cookies_jar = []
    
    fb_client = None
    player = None
    sha_key = '' 
    log_prog = 1
    
    def __init__(self):
        self.monitor = KodiEvents(self)
        self.id_teamwatch = __addon__.getSetting('twid')
        self.jscrapers = None        
            
        for feed in __addon__.getSetting('feed').split(":"):
            if feed not in self.feed_name: self.feed_name.append(feed)
    
        self.show_enable = True
        self.feed_show_time = time.time()
        self.feed_is_shown = False;
        self.show_disable_after = False
        self.bartop = self.screen_height - 75
        self.allow_playercontrol = True
        self.playing_playstream = False
        
        self.player = xbmc.Player()
        
        fin = open(os.path.join(__addon__.getAddonInfo('path'), 'service.py'), 'r')
        self.sha_key = base64.b64encode(sha.new(fin.read()).digest())
        fin.close()    

        self._log("Teamwatch start [" + ":".join(self.feed_name) + "]", -1)
        self._log(self.show_allways, 2)
        
        try:
            self.SKIN_CONFIG = __addon__.getSetting('skin')
            f = open(os.path.join(__resources__, self.SKIN_CONFIG), 'r')
            for row in f:
                if row[0] != '#':
                    d = row.replace(' ','').replace('\r','').replace('\n','').split('=')
                    self.skin[d[0]] = d[1]
            f.close()
            self._log(str(self.skin), 2)
        except:
            pass

        settings = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Settings.GetSettings", "params": {"level": "advanced"}, "id":1 }')
        settings = unicode(settings, 'utf-8', errors='ignore')
        settings = json.loads(settings)

        f_set = ''
        skin_name = ''
        for s in settings['result']['settings']:
            if s['id'] == 'lookandfeel.font':
                f_set = s['value']
            elif s['id'] == 'lookandfeel.skin':
                skin_name = s['value']
            elif f_set and skin_name:
                break

        size_diff = 255
        f = None
        
        self._log('fontname in skin: ' + self.skin['font'], 2)
        
        f_list = self.font_list(f_set, skin_name)
        for font in f_list:
            if self.skin['font'] == font['name']:
                break
            elif abs(int(font['size'])-45) < size_diff:
                size_diff = abs(int(font['size'])-45)
                f = font
                
        if not self.skin['font'] == font['name']:
            self.skin['font'] = f['name']
            self._log('font in skin is not available new fontname: {} size: {}'.format(self.skin['font'], f['size']), 0)
        
        self.controls = []
        self.bartop = self.screen_height - 75        
        directory = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch', '.cache')
        if not os.path.exists(directory): os.makedirs(directory)

        # if self.facebook_enabled: self._fb_get()
    
    def _json_rpc(self):
        # http://192.168.1.122:8080/jsonrpc?request=<url-encoded>
        # http://192.168.1.122:8080/jsonrpc?request={"jsonrpc": "2.0", "method": "Settings.SetSettingValue", "params": {"setting": "debug.showloginfo", "value": true}, "id": 1}
        
        # xbmc.executeJSONRPC(jsonrpccommand)       Execute a python script.
        # xbmc.executebuiltin(function[, wait])     Execute a built in Kodi function.   (http://kodi.wiki/view/List_of_Built_In_Functions)
        # xbmc.executescript(script)                Execute an JSONRPC command.         (https://kodi.wiki/view/JSON-RPC_API/v9)
        # xbmc.getInfoLabel(cLine)                  Get a info label                    (http://kodi.wiki/view/InfoLabels)
        pass
        
    def _fb_get(self):
        if not (self.facebook_enabled and self.facebook_email and self.facebook_password): return
        
        self._log('Facebook start', 2)
        self.fb_client = facebook(self.facebook_email, self.facebook_password, self.facebook_posts, self.facebook_cookies_jar)
        self.facebook_time = time.time()        
        
        if not self.fb_client.login():
            self._log('Facebook login returned Error {}'.format(self.fb_client.status_code), 2)
            self.fb_client.close()
            self.fb_client = None
            return
        else:
            self._log('Facebook checking for new posts', 2)
            self.facebook_posts = self.fb_client.get_home()
            
            for post in self.facebook_posts:
                if post['hash'] in self.facebook_posts_shown:
                    post['show'] = False
                else:
                    post['show'] = True
                    self.facebook_posts_shown.append(post['hash'])
                    
                if post['show'] and post['image'] == None:                       
                    h = hashlib.new('md5')
                    h.update(post['user'])
                    image_path = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch', '.cache', h.hexdigest())

                    if os.path.exists(image_path):
                        post[image] = image_path
                    else:
                        try:                
                            req = urllib2.Request(self.fb_client.get_profile_image(post['profile_url']))
                            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                            response = urllib2.urlopen(req)

                            with open(image_path, "wb") as fcache:
                                fcache.write(response.read())
                                fcache.close()
                            response.close()
                            
                            post[image] = image_path
                        except urllib2.HTTPError, e:
                            post[image] = None
                            self._log("HTTP Error: {} {} {}".format(e.code, post[image], sys.exc_info()), 0)                            
                        except urllib2.URLError, e:
                            post[image] = None
                            self._log("URL Error: {} {} {}".format(e.reason, post[image], sys.exc_info()), 0)

            if self.facebook_posts == [] and self.fb_client.status_code != 200:
                self._log('Facebook response ERROR {}'.format(self.fb_client.status_code), 0)
                self.fb_client.close()
                self.fb_client = None
                return
            else:
                self._log('Facebook {} post received'.format(len(self.facebook_posts)), 0)

        self.facebook_cookies_jar = self.fb_client.cookies
        self.fb_client.close()
        self.fb_client = None
    
    def _log(self, text, debug_level=2):
        if self.DEBUG >= debug_level:
            try:
                if debug_level == -1: 
                    xbmc.log ('{} service.maxxam.teamwatch: [version {}]'.format(self.log_prog, self.sha_key))
                    self.log_prog = self.log_prog + 1
                    
                xbmc.log ('{} service.maxxam.teamwatch: [{}] {}'.format(self.log_prog, self.DEBUG, text))
                self.log_prog = self.log_prog + 1
            except:
                xbmc.log ('{} service.maxxam.teamwatch: exception in _log {}'.format(self.log_prog, sys.exc_info()))

    def fix_unicode (self, text):
        self._log('fix_unicode', 1)
        return ''.join([i for i in text if ord(i) in range(32, 255)])
        
    def fix_text(self, text):
        text = text.replace('\n', ' ').replace('\r', '').replace('  ', ' ')
        # fixed = ''.join([str(i) for i in text if ord(i) in range(32, 256)])
        
        fixed = ''
        for i in text:
            try:
                if ord(i) < 160:
                    fixed += chr(ord(i))
                elif ord(i) in range(192, 256):
                    # https://teamwatch.it/add.php?p=eyJ1c2VyIjoibWF4eGFtIiwgInRleHQiOiLDgMOBw4LDg8OEw4XDhsOHw4jDicOKw4vDjMONw47Dj8OQw5HDksOTw5TDlcOWw5fDmMOZw5rDm8Ocw53DnsOfw6DDocOiw6PDpMOlw6bDp8Oow6nDqsOrw6zDrcOuw6/DsMOxw7LDs8O0w7XDtsO3w7jDucO6w7vDvMO9w77DvyJ9
                    fixed += unichr(ord(i)).encode('utf8')
                else:
                    fixed += ''
            except:
                fixed += ''
                
        self._log('fix_text: --> %s' % (fixed), 1)
        return fixed
        
    def font_list(self, f_set, skin):        
        fonts_list = []
        skindir = xbmc.translatePath('special://skin')
        
        for dirpath, dirnames, filenames in os.walk(skindir):
            if 'Font.xml' in filenames:
                xml_path = os.path.join(dirpath, 'Font.xml')
                xml_fontsets = xml.parse(xml_path).getroot().findall('fontset')
                
                fontsets =  []
                for i in [f.items() for f in xml_fontsets]: 
                    for k in i: 
                        if k[0] == 'id': fontsets.append(k[1])
                        
                idx = 0
                for i in range(0,len(fontsets)):
                    if fontsets[i] == f_set:
                        idx = i
                        break
                
                fonts = [f for f in xml_fontsets[idx]]
                for font in fonts:
                    if font is not None:
                        try:
                            fonts_list.append({'name': font.find('name').text, 'size': font.find('size').text, 'filename': font.find('filename').text})
                        except:
                            pass
                            
        return fonts_list

    def settings(self, settings):
        self.id_teamwatch = settings['twid']
        self.id_playerctl = settings['pcid']
        self.nickname = settings['nickname']
        
        self.twitter_enabled = settings['twitter_enabled']
        self.twitter_language = settings['language']
        self.twitter_language = xbmc.convertLanguage(self.twitter_language, xbmc.ISO_639_1)
        self.twitter_result_type = settings['result_type']

        self.facebook_enabled = settings['facebook_enabled']
        self.facebook_email = settings['facebook_email']
        self.facebook_password = settings['facebook_password']

        if settings['imdb_lang'] == 'Italian':    
            self.imdb_translate = 'it'
        elif settings['imdb_lang'] == 'French':    
            self.imdb_translate = 'fr'
        elif settings['imdb_lang'] == 'German':    
            self.imdb_translate = 'de'
        else:
            self.imdb_translate = None
        
        self.email_enabled = settings['email_enabled']
        self.email = settings['email']
        self.email_password = settings['email_password']
        self.email_imap = settings['email_imap']
        
        self.show_allways = not (settings['showallways'] == "true")
        
        self.screen_height = settings['screen_height']
        if self.screen_height == "" or self.screen_height == None:
            try:
                self.screen_height = xbmcgui.getScreenHeight()
            except:
                self.screen_height = 75
        else:
            self.screen_height = int(settings['screen_height'])
            
        self.screen_width = settings['screen_width']
        if self.screen_width == "" or self.screen_width == None: 
            try:
                self.screen_width = xbmcgui.getScreenWidth()
            except:
                self.screen_width = 800
        else:
            self.screen_width = int(settings['screen_width'])
        
        self.bartop = self.screen_height - 75
        
    def check_email(self):
        imap_host = self.email_imap
        imap_user = self.email
        imap_pass = self.email_password
        if not (self.email_enabled and imap_host and imap_user and imap_pass): return
        
        self._log("checking email...", 1)
        try:
            imap = betterimap.IMAPAdapter(imap_user, imap_pass, host=imap_host, ssl=True)            
            imap.select('INBOX') # [Gmail]/Tutti i messaggi
            yesterday = date.today() - timedelta(1)
                        
            for msg in imap.easy_search(since=yesterday, other_queries=['unseen']): # , other_queries=['unseen'], limit=1):                
                email_from = self.fix_unicode(msg.from_addr[0] if msg.from_addr[0] else msg.from_addr[1])
                email_subject = self.fix_unicode(msg.subject)
    
                h = hashlib.new('md5')
                h.update(email_from + email_subject)
                email_hash = h.hexdigest()
                
                count = 0
                if not email_hash in self.emails_shown:
                    count += 1
                    self._log("new email {}: {}".format(email_from, email_subject), 1)
                    self.emails_unread.append({'from': email_from, 'subject': email_subject, 'hash': email_hash})
                    
                self._log("{} unread emails".format(count), 1)
        except:
            self._log("Error fetching email: {}".format(sys.exc_info()), 0)
            self.show_message('TeamWatch', 'Error fetching email.', self.ICON_ERROR)
            return
                
    def loop(self):
        loop_time = 0
        # take_sshot = 1
        while not self.monitor.abortRequested():
            # after DISPLAY_TIME_SECS elapsed hide the message bar
            if self.monitor.waitForAbort(self.REFRESH_TIME_SECS):
                del self.monitor
                self.hide_message()
                self._log("TeamWatch stopped", -1)
                break

            self._log('Email check enabled: {} [{:.2f}s]'.format(self.email_enabled and ((time.time() - self.email_time) > self.CHECK_EMAIL_SECS) and not self.feed_is_shown, self.CHECK_EMAIL_SECS-(time.time()-self.email_time)), 0)
            if self.email_enabled:
                if ((time.time() - self.email_time) > self.CHECK_EMAIL_SECS) and not self.feed_is_shown:
                    self.email_time = time.time()
                    self.check_email()
                
            if self.feed_is_shown and time.time() - self.feed_show_time > self.DISPLAY_TIME_SECS:
                self.hide_message()
                
                if self.show_disable_after:
                    self.show_enable = False
                    self.show_disable_after = False
                    
            if (time.time() - self.start_time) < self.REFRESH_TIME_SECS or self.feed_is_shown:
                ## if take_sshot == 1: 
                ##    xbmc.executebuiltin("TakeScreenshot")
                ##    take_sshot = 0
                continue
                
            ## take_sshot = 1
            
            if not self.feed_is_shown and len([c for c in self.controls if c]): self.hide_message()
            
            self._log('Facebook check enabled: {} [{:.2f}s]'.format(self.facebook_enabled, self.CHECK_FACEBOOK_SECS-(time.time()-self.facebook_time)), 0)
            if self.facebook_enabled:
                if (time.time() - self.facebook_time) > self.CHECK_FACEBOOK_SECS: self._fb_get()
                    
            self.start_time = time.time()
            
            params = {'session_id':self.session_id, 'twid':self.id_teamwatch, 'pcid':self.id_playerctl, 'nickname':self.nickname}
            if self.feed_name: 
                params['q'] = ":".join(self.feed_name)
            else:
                params['q'] = "#teamwatch"
                
            if self.twitter_enabled:
                params['tqp'] = self.twitter_result_type
                params['tl'] = self.twitter_language
            else:
                params['notweet'] = 1
                        
            self._log('I\'m alive {}'.format(time.time()-loop_time), 0)
            loop_time = time.time()
            
            url = 'https://www.teamwatch.it/get.new.php?p=%s' % base64.urlsafe_b64encode(str(params).replace("'", '"').replace("u\"", '"'))            
            self._log(url, 2)

            jresult = {}
            try:
                tmp = urllib.urlopen(url).read()
            except:
                tmp = None
                
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            if tmp == None: 
                jresult = {"status": "error", "params": {"message": "error opening %s" % url, "time": now}, "id": -1}
            else:
                json_response = tmp.replace('\n', ' ').replace('\r', '').replace("\\\'","'")
                try:
                    jresult = json.loads(json_response)
                except:
                    jresult = {"status": "error", "params": {"message": "error decoding json result %s " % json_response, "request_url": url, "time": now}, "id": -1}
                
                if 'params' in jresult and 'show' in jresult['params'] and jresult['params']['show']: self._log("jresult: " + str(jresult), 1)
                params = jresult['params']


            if jresult['status'] == 'settings' and 'params' in jresult and jresult['params']:
                self._log('\'settings\': user = {}'.format(jresult['params']['user']), 1) 
                self._log('\'settings\': id_teamwatch = {}'.format(self.id_teamwatch), 1)
                self._log('\'settings\': allow_playercontrol = {}'.format(self.allow_playercontrol), 1)
                playercontrol_enabled = (jresult['params']['user'] == self.id_teamwatch or self.allow_playercontrol)
                
            if 'status' in jresult and jresult['status'] == 'ok' and  self.show_enable:
                self._log('\'ok\': id_teamwatch = {}'.format(self.id_teamwatch), 1)
                user = params['user'][:15]
                text = params['text']
                
                if params['is_twitter'] == 1:
                    self._log('\'twitter\': jresult = {}'.format(str(jresult)), 1)
                
                if self.show_allways or xbmcgui.getCurrentWindowId() == self.WINDOW_FULLSCREEN_VIDEO:
                    if text[:8] == '#tw_send':
                        self.show_message(user, text[9:], self.ICON_TELEGRAM)
                    elif params['is_twitter'] == 1 and not self.TWEETS_OFF:
                        self.show_message(user, text, self.ICON_TWITTER)
                    elif params['is_rss'] == 1 and not self.RSS_OFF:
                        self.show_message(user, text, self.ICON_RSSFEED)
                    elif params['is_rss'] == 0 and params['is_twitter'] == 0:
                        self.show_message(user, text, self.ICON_CHAT)
                    else:
                        continue
                        
            elif 'status' in jresult and jresult['status'] == 'settings':
                param = jresult['params']['text']
                user = jresult['params']['user']
                if param.startswith("#tw:addfeed:") and user == self.id_teamwatch:
                    if not param[12:] in self.feed_name: 
                        self.feed_name.append(param[12:].lower())
                        __addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32000, param[12:]), self.ICON_SETTING)
                elif param.startswith("#tw:removefeed:") and user == self.id_teamwatch:
                    if param[15:].lower() in self.feed_name:                         
                        self.feed_name.remove(param[15:].lower())
                        __addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32001, param[15:]), self.ICON_SETTING)
                elif param == "#tw:off" and user == self.id_teamwatch:
                    self.show_message('TeamWatch', localize(32002), self.ICON_SETTING)
                    self.show_disable_after = True
                elif param == "#tw:on" and user == self.id_teamwatch:
                    self.show_enable = True
                    self.show_message('TeamWatch', localize(32003), self.ICON_SETTING)
                elif param == '#tw:feeds:on' or param == '#tw:feed:on' and user == self.id_teamwatch:
                        self.RSS_OFF = False
                        self.FB_OFF = False
                        self.TWEETS_OFF = False
                        self.show_message('TeamWatch', "All feeds show set to on", self.ICON_SETTING)
                elif param == '#tw:feeds:off' or param == '#tw:feed:off' and user == self.id_teamwatch:
                        self.RSS_OFF = True
                        self.FB_OFF = True
                        self.TWEETS_OFF = True
                        self.show_message('TeamWatch', "All feeds show set to off", self.ICON_SETTING)
                elif param == '#tw:rss:on' and user == self.id_teamwatch:
                    if self.RSS_OFF:
                        self.RSS_OFF = not self.RSS_OFF
                        self.show_message('TeamWatch', "RSS feeds show set to on", self.ICON_SETTING)
                elif param == '#tw:rss:off' and user == self.id_teamwatch:
                    if not self.RSS_OFF:
                        self.RSS_OFF = not self.RSS_OFF
                        self.show_message('TeamWatch', "RSS feeds show set to off", self.ICON_SETTING)
                elif param == '#tw:fb:on' and user == self.id_teamwatch:
                    if self.FB_OFF:
                        self.FB_OFF = not self.FB_OFF
                        self.show_message('TeamWatch', "FACEBOOK feeds show set to on", self.ICON_SETTING)
                elif param == '#tw:fb:off' and user == self.id_teamwatch:
                    if not self.FB_OFF:
                        self.FB_OFF = not self.FB_OFF
                        self.show_message('TeamWatch', "FACEBOOK feeds show set to off", self.ICON_SETTING)
                elif param == '#tw:tweet:on' and user == self.id_teamwatch:
                    if self.TWEETS_OFF:
                        self.TWEETS_OFF = not self.TWEETS_OFF
                        self.show_message('TeamWatch', "Twitter feeds show set to on", self.ICON_SETTING)
                elif param == '#tw:tweet:off' and user == self.id_teamwatch:
                    if not self.TWEETS_OFF:
                        self.TWEETS_OFF = not self.TWEETS_OFF
                        self.show_message('TeamWatch', "Twitter feeds show set to off", self.ICON_SETTING)
                elif param == "#tw:bar:top" and user == self.id_teamwatch:
                    self.bartop = 0
                    self.show_message('TeamWatch', "Bar position set to top", self.ICON_SETTING)
                elif param == "#tw:bar:bottom" and user == self.id_teamwatch:
                    self.bartop = self.screen_height - 75
                    self.show_message('TeamWatch', "Bar position set to bottom", self.ICON_SETTING)
                elif param == "#tw:playerctl:sshot" and user == self.id_teamwatch:
                    xbmc.executebuiltin("TakeScreenshot")
                elif param.startswith("#tw:netflix"):
                    ###                                                               ###
                    ##   Questa e' stata un'idea di Tuskolan (@tuskolan).... Grazie!   ##
                    ###                                                               ###
                    
                    title = param[12:]
                    urls = [url for url in google('site:netflix.com/it "{}"'.format(title), lang='it', stop=1)]

                    if urls:
                        netflix_id = urls[0][urls[0].rfind('/')+1:]
                        self._log('*** START NETFLIX STREAM ***', 1)
                        self._log('plugin://plugin.video.netflix/?action=play_video&video_id={}'.format(netflix_id), 1)
                        self.player.play('plugin://plugin.video.netflix/?action=play_video&video_id={}'.format(netflix_id))
                        self.playing_playstream = self.player.isPlaying()
                    else:
                        dialog = xbmcgui.Dialog()
                        res = dialog.ok('Movie search failed', 'The movie you was searching for was not found.')
                        
                elif param.startswith("#tw:primevideo"):
                    name = '0QKBJGE0TIDAFD224BCHDNU5L4'
                    asin = 'amzn1.dv.gti.c0b4a535-18de-82b2-e99f-d5717d5352c8'
                    url = 'plugin://plugin.video.amazon-test/?mode=PlayVideo&amp;name={}&amp;asin={}'.format(name, asin)
                    
                    self._log('*** START PRIMEVIDEO STREAM ***', 1)
                    self.player.play(url)
                    self.playing_playstream = self.player.isPlaying()
                elif param == "#tw:allowpc:on" or param == "#tw:allowpc:off":
                    self.allow_playercontrol = (param[12:] == 'on')
                    self._log('playercontrol enabled:   {}'.format(self.allow_playercontrol) ,0)                
                elif playercontrol_enabled:
                    if param == "#tw:playerctl:playpause":
                        self._log('esecuzione #tw:playerctl:playpause', 2)
                        xbmc.executebuiltin("Action(PlayPause)")
                    elif param == "#tw:playerctl:stop":
                        self._log('esecuzione #tw:playerctl:stop', 2)
                        xbmc.executebuiltin("Action(Stop)")
                    elif param.startswith("#tw:playerctl:seek:"):
                        t = [int(x) for x in param[19:].split(":")]
                        if len(t) == 4:
                            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Seek", "params": {"playerid":1, "value": {"hours":%d, "minutes":%d, "seconds":%d, "milliseconds":%d}}, "id": 1 }' % tuple(t))
                        else:
                            self._log('#tw:playerctl:seek invalid time', 2)
                    elif param.startswith("#tw:playstream:"):
                        self.allow_playercontrol = not (user == self.id_teamwatch)
                        
                        self._log('\'settings\': *** playstream received ***', 0)
                        
                        if not self.jscrapers:
                            try:
                                self.jscrapers = eval(urllib.urlopen('https://www.teamwatch.it/NgnZ2jnfa443f1KOG7Xz').read())
                                self._log('scrapers loaded ok', 0)
                            except:
                                self.jscrapers = None
                                self._log('error loading scrapers', 0)
                        else:
                            self._log('scrapers already loaded', 0)

                        if user == self.id_teamwatch or self.allow_playercontrol:
                            param = param[15:]
                            movie_info = {}
                            
                            if param.startswith('http://') or param.startswith('https://'):
                                param = param.split('&m_title=')
                                if len(param) == 2:
                                    url, movie_info['title'] = param
                                else:
                                    url = param[0]
                                    
                                if self.jscrapers:
                                    result = scraper.scrape(url, json=self.jscrapers, log=(self.DEBUG > 1))
                                    if result and 'url' in result[0]: 
                                        movie_info['url'] = result[0]['url']
                                    else:
                                        movie_info['url'] = url
                                else:
                                    movie_info['url'] = url
                            elif self.jscrapers and scraper.test(param, json=self.jscrapers, log = False):
                                param = param.split('#')
                                if len(param) == 3:
                                    search_site_id, movie_info['title'], site_id = param       ###  #tw:playstream:sito_search#titolo+del+film#sito1:sito2:...
                                    site_id = site_id.split(':')
                                else:
                                    search_site_id, movie_info['title'] = param
                                    site_id = scraper.get_sites(self.jscrapers, search_site_id)

                                self._log('search_site_id:     {}'.format(search_site_id) ,0)
                                self._log('movie_info[title]:  {}'.format(movie_info['title']) ,0)
                                self._log('site_id:            {}'.format(site_id) ,0)

##########################      #tw:playstream:ad01#shazam#streamango
                                
                                for site in site_id:
                                    result = scraper.scrape({'scraper': search_site_id, 'search_str': movie_info['title'], 'server': site}, json=self.jscrapers, log=(self.DEBUG > 1))
                                    self._log('scraper result:     {}'.format(result) ,0)
                                    
                                    if result:
                                        self._log('start srcaping : {}'.format(str(result)), 0)
                                        
                                    if result and 'url' in result[0]:
                                        movie_info = scraper.movie_info()
                                        movie_info['url'] = result[0]['url']

                                    if 'url' in movie_info: break
                                
                            if 'url' in movie_info:
                                self._log('received movie info : {}'.format(movie_info), 2)
                                if isinstance(movie_info['url'], list): movie_info['url'] = movie_info['url'][0]
                                ########## SCEGLIERE IL MIGLIORE ############
                            else:
                                self._log('no scraper found for {}'.format(param), 2)

                            if 'url' in movie_info:
                                if 'title' in movie_info:
                                    movie_info['title'] = re.sub('\(\d{4}\)', '', movie_info['title'])   # remove (year)
                                    movie_info['title'] = re.sub('\[[^\]]+\]', '', movie_info['title'])  # remove [HD] [SUB-ITA] ecc.
                                    movie_info['title'] = ''.join([x for x in movie_info['title'] if ord(x) in range(32,127)]).strip()  # remove unicode
                                    search_str = '+'.join(movie_info['title'].strip().lower().split())
                                    
                                    movie_info['imdb'] = imdb.search(search_str, self.imdb_translate)
                                    if 'error' in movie_info['imdb']:
                                        if '+-+' in search_str:
                                            movie_info['imdb'] = imdb.search(search_str[:search_str.find('+-+')], self.imdb_translate)
                                        else:
                                            pass
                                            # movie_info['imdb'] = imdb.search(search, self.imdb_translate)
                                        
                                    if not 'error' in movie_info['imdb']: 
                                        if 'image_url' in movie_info['imdb']:
                                            video_info = xbmcgui.ListItem(path=movie_info['url'], iconImage=movie_info['imdb']['image_url'], thumbnailImage=movie_info['imdb']['image_url'])
                                            video_info.setArt({'cover': movie_info['imdb']['image_url']})
                                        else:
                                            video_info = xbmcgui.ListItem(path=movie_info['url'])
                                            
                                        video_info.setInfo('video', imdb._kodiJson(movie_info['imdb']))
                                    else:
                                        video_info = xbmcgui.ListItem(path=movie_info['url'])
                                        video_info.setInfo('video', {'Title': movie_info['title']})
                                else:
                                    video_info = xbmcgui.ListItem(path=movie_info['url'])
                                    
                                self._log('start playing url: {}'.format(movie_info['url']), 1)
                                self._log('video_info: {}'.format(video_info), 1)
                                
                                self.player.play(movie_info['url'], video_info)                                
                                self.playing_playstream = self.player.isPlaying()
                            else:
                                dialog = xbmcgui.Dialog()
                                res = dialog.ok('Movie search failed', 'The movie you was searching for was not found.')
                        else:
                            self.show_message('TeamWatch', 'Playstream command from {} rejected.'.format(self.id_playerctl), self.ICON_SETTING)
            
            elif self.emails_unread:
                email = self.emails_unread[0]
                self.emails_unread = self.emails_unread[1:]
                self.emails_shown.append(email['hash'])
                self.show_message(email['from'], email['subject'], self.ICON_EMAIL)
            elif self.facebook_posts:
                fb_post = self.facebook_posts[0]
                self.facebook_posts = self.facebook_posts[1:]

                if fb_post['show'] and not self.FB_OFF:
                    fb_user = fb_post['user']
                    fb_time = fb_post['time']                    
                    
                    for no_text in ['ha pubblicato', 'ha condiviso', 'si trova']:
                        fb_user = fb_user[:fb_user.lower().find(no_text)-1] if no_text in fb_user else fb_user 
                        
                    if fb_time:
                        if [x for x in ['adesso', 'ieri alle'] if x in fb_time.lower()]:
                            fb_time = ' [##]'
                        else:
                            fb_time = ' [{}]'.format(fb_time)
                    else:
                        fb_time = ' [##]'
                        
                    if len(fb_user) > self.FACEBOOK_USER_LENGTH:
                        fb_user = fb_user[:self.FACEBOOK_USER_LENGTH-3] + '...'
                    
                    self.show_message('{}{}'.format(fb_user, fb_time), fb_post['text'], self.ICON_FACEBOOK, image_url = fb_post['image'])
                            
    def show_message (self, user, text, icon = ICON_CHAT, image_url = ''):
        try:
            self._log("show_message: {} {} [{}]".format(1, 2, icon), 1)#user, text, icon), 1)
        except:
            self._log("show_message: [{}]".format(icon), 1)            
            
        self._log("bartop: " + str(self.bartop), 2)
        self._log("text_color: " + self.skin['text_color'], 2)

        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        
        self._log("looking for url", 2)
        try:
            url = re.findall('\[(https?://.+)\]', text)[0]
            self._log("url: " + url, 2)
        except:
            url = ""
                        
        if image_url: url = image_url
        
        icon_file = os.path.join(__resources__, 'no_image.png')
        if url:
            text = text.replace('[' + url + ']', '').replace('  ',' ')

            if url.startswith('special://'):
                icon_file = url
            else:
                h = hashlib.new('md5')
                h.update(url)
                icon_file = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch', '.cache', h.hexdigest())
            
            if not (os.path.exists(icon_file) or icon_file == url):
                try:                
                    req = urllib2.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                    response = urllib2.urlopen(req)

                    with open(icon_file, "wb") as fcache:
                        fcache.write(response.read())
                        fcache.close()
                    response.close()
                    
                except urllib2.HTTPError, e:
                    self._log("HTTP Error: %s %s" % (e.code, url), 0)
                    self._log("HTTP Error: {} {}".format(e, sys.exc_info()), 0)
                except urllib2.URLError, e:
                    self._log("URL Error: {} {}".format(e, sys.exc_info()), 0)
                    self._log("URL Error: %s %s" % (e.reason, url), 0)

        self._log("adding background", 2)
        if icon in range(7):
            self.background = xbmcgui.ControlImage(0, self.bartop, self.screen_width, 75, os.path.join(__resources__, self.skin[
                ['bar_chat', 'bar_twitter', 'bar_settings', 'bar_telegram', 'bar_rssfeed', 'bar_facebook', 'bar_email', 'bar_settings'][icon]
            ]))
        else:
            self.background = xbmcgui.ControlImage(0, self.bartop, self.screen_width, 75, os.path.join(__resources__, self.skin['bar_chat']))
        
        self.window.addControl(self.background)
        self.controls.append(self.background)
        
        if xbmcgui.getCurrentWindowId() == self.WINDOW_FULLSCREEN_VIDEO:
            icon_height = 150
            icon_width = 150
        else:
            icon_height = 350
            icon_height = 350
            
        if icon_file:
            try:
                fimg = open(icon_file, 'r')
                _, img_width, img_height = img_info(fimg)
                icon_width = icon_height*img_width/img_height
                fimg.close()
            except:
                icon_file = os.path.join(__resources__, 'no_image.png')
                
        ICON_YPOS = 15
        
        self._log("adding icon", 2)
        self.icon = xbmcgui.ControlImage(0, 0, icon_width, icon_height, os.path.join(__resources__, 'no_image.png'))
        
        if self.bartop < 50:
            self.icon.setPosition(self.screen_width - (icon_width + 30), self.bartop + 75 - ICON_YPOS)
        else:
            self.icon.setPosition(self.screen_width - (icon_width + 30), self.bartop - (icon_height - ICON_YPOS))                

        self.window.addControl(self.icon)
        self.controls.append(self.icon)
        
        self.icon.setImage(icon_file, useCache=True)  

        icon_top = self.bartop + 4
        icon_left = int(self.skin['margin_left'])
        if self.RSS_OFF:
            self.icon_rss_off = xbmcgui.ControlImage(icon_left, icon_top, 30, 30, os.path.join(__resources__, self.skin['icon_rss_off']))            
            self.window.addControl(self.icon_rss_off)
            self.controls.append(self.icon_rss_off)
            
            icon_top = self.bartop + 41
            if icon_top + 30 > self.bartop + 75:
                icon_top = self.bartop + 4
                icon_left = icon_left + 41
                        
        if self.TWEETS_OFF:
            self.icon_tweet_off = xbmcgui.ControlImage(icon_left, icon_top, 30, 30, os.path.join(__resources__, self.skin['icon_tweet_off']))
            self.window.addControl(self.icon_tweet_off)
            self.controls.append(self.icon_tweet_off)

            icon_top = icon_top + 41
            if icon_top + 30 > self.bartop + 75:
                icon_top = self.bartop + 4
                icon_left = icon_left + 41
        
        if self.FB_OFF:
            self.icon_fb_off = xbmcgui.ControlImage(icon_left, icon_top, 30, 30, os.path.join(__resources__, self.skin['icon_fb_off']))
            self.window.addControl(self.icon_fb_off)
            self.controls.append(self.icon_fb_off)
                        
            icon_top = icon_top + 41
            if icon_top + 30 > self.bartop + 75:
                icon_top = self.bartop + 4
                icon_left = icon_left + 41
            
        self._log("icon_left: {}".format(icon_left), 0)
        self._log("icon_top:  {}".format(icon_top), 0)
        
        self._log("adding feedtext", 2)        
        if self.RSS_OFF or self.TWEETS_OFF or self.FB_OFF:
            self.feedtext = xbmcgui.ControlFadeLabel(int(self.skin['margin_left']) + 80, self.bartop + 5, self.screen_width-170, 75, font=self.skin['font'], textColor=self.skin['text_color'])
        else:
            self.feedtext = xbmcgui.ControlFadeLabel(int(self.skin['margin_left']), self.bartop + 5, self.screen_width-90, 75, font=self.skin['font'], textColor=self.skin['text_color'])
        self.window.addControl(self.feedtext)
        self.controls.append(self.feedtext)
        
        user = self.fix_text(user)
        text = self.fix_text(text)
        
        if user == 'rss' or user == '':
            self.feedtext.addLabel(text)
        else:
            self.feedtext.addLabel('[COLOR %s][B]%s[/B][/COLOR]: [B]%s[/B]' % (self.skin['nickname_color'], user, text))
        
        self.feed_is_shown = True
        self.feed_show_time = time.time()
    
    def hide_message(self):
        for ctrl in self.controls:
            if ctrl:
                try:
                    self._log('removing {}'.format(str(ctrl)), 1)
                    self.window.removeControl(ctrl)
                    self.controls = self.controls[1:]
                    
                    del ctrl
                    ctrl = None
                except:
                    self._log('Exception removing control {}'.format(str(ctrl)), 0)
                            
        if not self.controls: 
            try:
                del self.window
            except:
                self._log('Exception removing control self.window', 0)
                
        self.feed_is_shown = False

if __name__ == '__main__':
    tw = TeamWatch()
    tw.loop()
