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
from PIL import Image

__version__     = "0.0.13"
__addon__       = xbmcaddon.Addon()
__resources__   = os.path.join(__addon__.getAddonInfo('path'),'resources')
__pylib__       = os.path.join(__addon__.getAddonInfo('path'), 'lib')

ADDONID = __addon__.getAddonInfo('id')

sys.path.append(__pylib__)
sys.path.append(os.path.join(__pylib__, 'maxxam_imdb'))
sys.path.append(os.path.join(__addon__.getAddonInfo('path'), 'scrapers'))
sys.path.append(os.path.join(__addon__.getAddonInfo('path'), 'scrapers', 'requests'))

import betterimap
import xbmc_helpers
from facebook import facebook
from bs4 import BeautifulSoup
from xbmc_helpers import localize
import maxxam_imdb as imdb
import maxxam_scraper as scraper
import cineblog

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
    SOCKET_TIMEOUT = 0.5
    DEBUG = 2 # 0 = HIGH, 1 = MEDIUM, 2 = LOW lasciare a uno! (solo _log <= DEBUG vengono visualizzti)

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

    monitor = None
    
    window = None
    background = None
    icon = None
    feedtext = None
    icon_rss_off = None
    icon_tweet_off = None
    
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
    
    facebook = __addon__.getSetting('facebook')
    
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
        screen_height = xbmcgui.getScreenHeight()
    else:
        screen_height = int(__addon__.getSetting('screen_height'))
        
    screen_width = __addon__.getSetting('screen_width')
    if screen_width == "": 
        screen_width = xbmcgui.getScreenWidth()
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
    facebook_time = time.time()
    facebook_posts = []
    facebook_cookies_jar = []
    fb_client = None
    player = None
    sha_key = '' 
    log_prog = 1
    
    def __init__(self):
        self.monitor = KodiEvents(self)
        self.id_teamwatch = __addon__.getSetting('twid')
        
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

        self._log("Teamwatch start [" + ":".join(self.feed_name) + "]", 0)
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
        
        self._log('fontname in skin: ' + self.skin['font'])
        
        f_list = self.font_list(f_set, skin_name)
        for font in f_list:
            # self._log('found font {} comparing to {} result: {}'.format(font['name'], self.skin['font'], self.skin['font'] == font['name']))
            if self.skin['font'] == font['name']:
                break
            elif abs(int(font['size'])-45) < size_diff:
                size_diff = abs(int(font['size'])-45)
                f = font
                
        if not self.skin['font'] == font['name']:
            self.skin['font'] = f['name']
            self._log('font in skin is not available new fontname: {} size: {}'.format(self.skin['font'], f['size']))
        
        self.bartop = self.screen_height - 75        
        directory = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch', '.cache')
        if not os.path.exists(directory): os.makedirs(directory)

        if self.facebook_enabled: self._fb_get()
            
    def _fb_get(self):
        self._log('Facebook start', 1)
        self.fb_client = facebook(self.facebook_email, self.facebook_password, self.facebook_posts, self.facebook_cookies_jar)
        self.facebook_time = time.time()
        self.fb_client.login()
        
        if self.fb_client.status_code != 200:
            self._log('Facebook login returned Error {self.fb_client.status_code}'.format(), 1)
            self.fb_client.close()
            self.fb_client = None
            return
        else:
            self._log('Facebook checking for new posts', 1)
            self.facebook_posts = self.fb_client.get_home()
            if self.facebook_posts == [] and self.fb_client.status_code != 200:
                self._log('Facebook response ERROR {}'.format(self.fb_client.status_code), 1)
                self.fb_client.close()
                self.fb_client = None
                return
            else:
                self._log('Facebook {} post received'.format(len(self.facebook_posts)), 1)

        self.facebook_cookies_jar = self.fb_client.cookies
        self.fb_client.close()
        self.fb_client = None
    
    def _log(self, text, debug_level=2):
        if self.DEBUG >= debug_level:
            if debug_level == 0: 
                xbmc.log ('%d service.maxxam.teamwatch: [version %s]' % (self.log_prog, self.sha_key))
                self.log_prog = self.log_prog + 1
                
            xbmc.log ('%d service.maxxam.teamwatch: %s' % (self.log_prog, text))
            self.log_prog = self.log_prog + 1

    def fix_unicode (self, barray, repl = ''):
        out = ''
        for c in barray:
            try:
                out += str(c)
            except:
                out += repl
                
        return out

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
        self.facebook = settings['facebook']
        
        self.show_allways = not (settings['showallways'] == "true")
        
        self.screen_height = settings['screen_height']
        if self.screen_height == "" or self.screen_height == None: 
            self.screen_height = xbmcgui.getScreenHeight()
        else:
            self.screen_height = int(settings['screen_height'])
            
        self.screen_width = settings['screen_width']
        if self.screen_width == "" or self.screen_width == None: 
            self.screen_width = xbmcgui.getScreenWidth()
        else:
            self.screen_width = int(settings['screen_width'])
        
        self.bartop = self.screen_height - 75
        
    def check_email(self):
        imap_host = self.email_imap
        imap_user = self.email
        imap_pass = self.email_password

        try:
            imap = betterimap.IMAPAdapter(imap_user, imap_pass, host=imap_host, ssl=True)            
            imap.select('INBOX') # [Gmail]/Tutti i messaggi
            
            yesterday = date.today() - timedelta(1)
            for msg in imap.easy_search(since=yesterday, other_queries=['unseen'], limit=1):
                user = self.fix_unicode(msg.from_addr[0] if msg.from_addr[0] else msg.from_addr[1])
                text = self.fix_unicode(msg.subject)
                
                self.show_message(user, text, self.ICON_EMAIL)
        except:
            self.show_message('TeamWatch', 'Error fetching email.', self.ICON_ERROR)
            return
                
    def loop(self):
        while not self.monitor.abortRequested():
            # after DISPLAY_TIME_SECS elapsed hide the message bar
            if self.monitor.waitForAbort(self.REFRESH_TIME_SECS):
                self.hide_message()
                self._log("stop", 0)
                break
            
            self._log('Email check enabled: {}'.format(self.email_enabled), 1)
            if self.email_enabled and time.time() - self.email_time > self.CHECK_EMAIL_SECS and not self.feed_is_shown:
                self.email_time = time.time()
                # self.check_email()
                
            if self.feed_is_shown and time.time() - self.feed_show_time > self.DISPLAY_TIME_SECS:
                self.hide_message()
                
                if self.show_disable_after:
                    self.show_enable = False
                    self.show_disable_after = False
                    
            if (time.time() - self.start_time) < self.REFRESH_TIME_SECS or self.feed_is_shown:
                continue
            
            self._log('Facebook check enabled: {} [{:.2f}s]'.format(self.facebook_enabled, 300-(time.time()-self.facebook_time)), 1)
            if self.facebook_enabled and (time.time() - self.facebook_time) > 300: self._fb_get()
                    
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
                
                if 'params' in jresult and 'show' in jresult['params'] and jresult['params']['show']: self._log("jresult: " + str(jresult), 0)
                params = jresult['params']

            if 'status' in jresult and jresult['status'] == 'ok' and  self.show_enable:
                user = params['user'][:15]
                text = params['text']
                
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
                        self.show_message(user, text, self.ICON_CHAT)
                        
            elif self.facebook_posts:
                fb_post = self.facebook_posts[0]
                self.facebook_posts = self.facebook_posts[1:]
                if len(fb_post['user']) > self.FACEBOOK_USER_LENGTH:
                    user = fb_post['user'][:self.FACEBOOK_USER_LENGTH-3] + '...'
                else:
                    user = fb_post['user']
                self.show_message('{} [{}]'.format(user, fb_post['time']), fb_post['text'], self.ICON_FACEBOOK, image = fb_post['image'])
            
            elif 'status' in jresult and jresult['status'] == 'settings':
                param = jresult['params']['text']
                user = jresult['params']['user']
                if param.startswith("#tw:addfeed:") and user == id_teamwatch:
                    if not param[12:] in self.feed_name: 
                        self.feed_name.append(param[12:].lower())
                        __addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32000, param[12:]), self.ICON_SETTING)
                elif param.startswith("#tw:removefeed:") and user == id_teamwatch:
                    if param[15:].lower() in self.feed_name:                         
                        self.feed_name.remove(param[15:].lower())
                        __addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32001, param[15:]), self.ICON_SETTING)
                elif param == "#tw:off" and user == id_teamwatch:
                    self.show_message('TeamWatch', localize(32002), self.ICON_SETTING)
                    self.show_disable_after = True
                elif param == "#tw:on" and user == id_teamwatch:
                    self.show_enable = True
                    self.show_message('TeamWatch', localize(32003), self.ICON_SETTING)
                elif param == '#tw:rss:on' and user == id_teamwatch:
                    if self.RSS_OFF:
                        self.RSS_OFF = not self.RSS_OFF
                        self.show_message('TeamWatch', "RSS feeds show set to on", self.ICON_SETTING)
                elif param == '#tw:rss:off' and user == id_teamwatch:
                    if not self.RSS_OFF:
                        self.RSS_OFF = not self.RSS_OFF
                        self.show_message('TeamWatch', "RSS feeds show set to off", self.ICON_SETTING)
                elif param == '#tw:tweet:on' and user == id_teamwatch:
                    if self.TWEETS_OFF:
                        self.TWEETS_OFF = not self.TWEETS_OFF
                        self.show_message('TeamWatch', "Twitter feeds show set to on", self.ICON_SETTING)
                elif param == '#tw:tweet:off' and user == id_teamwatch:
                    if not self.TWEETS_OFF:
                        self.TWEETS_OFF = not self.TWEETS_OFF
                        self.show_message('TeamWatch', "Twitter feeds show set to off", self.ICON_SETTING)
                elif param == "#tw:bar:top" and user == id_teamwatch:
                    self.bartop = 0
                    self.show_message('TeamWatch', "Bar position set to top", self.ICON_SETTING)
                elif param == "#tw:bar:bottom" and user == id_teamwatch:
                    self.bartop = self.screen_height - 75
                    self.show_message('TeamWatch', "Bar position set to bottom", self.ICON_SETTING)
                elif param == "#tw:playerctl:sshot" and user == id_teamwatch:
                    xbmc.executebuiltin("TakeScreenshot")                    
                elif user == self.id_teamwatch or self.allow_playercontrol:
                    """
                    se il film in play non è partito con #twpc:playstream rifiuta tutti i comandi #twpc

                    quando si riceve un #twpc:playstream se non c'é niente in play lo fa partire automaticamente
                    se invece c'é qualcosa in play partito con #twpc:playstream mostra una finestra di dialogo

                    se il film è partito con #twpc accetta tutti i comandi #twpc
                    
                    Domanda: se il play è partito da un altro addon il mio self.player lo sa?
                    """
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
                            self._log('#tw:playerctl:seek invalid time', 0)
                    elif param.startswith("#tw:playstream:"): ###
                        self._log('*** playstream received ***', 0)
                        if user == self.id_teamwatch:
                            self.allow_playercontrol = False    # playstream sent by user disallow pcid
                        elif self.player.isPlaying():
                            dialog = xbmcgui.Dialog()           # playing from a previous playstream ask if user want to start a new strem
                            res = dialog.yesno('You have received a request to start a movie by {}, do you want to start playback?'.format(self.id_playerctl))
                            self.allow_playercontrol = res
                        else:                                   # no stream in playback... allow pcid
                            self.allow_playercontrol = True
                        
                        if user == self.id_teamwatch or self.allow_playercontrol:
                            if 'http://' in param[15:] or 'https://' in param[15:]:
                                params = param[15:].split('&m_title=')
                                url = params[0]
                                if len(params) == 2:
                                    title = params[1]
                                else:
                                    title = ''
                                    
                                if scraper.test(url):
                                    streams = scraper.scrape(url)
                                    if streams: url = streams[0]['url']
                            else:
                                search, sites = param[15:].split('#')
                                sites = [s.strip() for s in sites.split(',')]
                                cb01_links = cineblog.search(search)
                                if cb01_links:
                                    streams = cineblog.getstreams(cb01_links[0]['url'], sites)
                                    if streams:
                                        url = streams[0]['strean_info']['url']
                                        title = cb01_links[0]['title'].encode('utf-8')
                                    else:
                                        url = ''
                                        title = search
                                else:
                                    url = ''
                                    title = search
                            
                            self._log('received url: {}'.format(url), 0)
                            self._log('title: {}'.format(title), 0)

                            if url:
                                if title:
                                    title = re.sub('\(\d{4}\)', '', title)   # remove (year)
                                    title = re.sub('\[[^\]]+\]', '', title)  # remove [HD] [SUB-ITA] ecc.
                                    title = ''.join([x for x in title if ord(x) in range(32,127)]).strip()  # remove unicode
                                    search_str = '+'.join(title.strip().lower().split())
                                    
                                    movie = imdb.search(search_str, self.imdb_translate)
                                    if 'error' in movie:
                                        if '+-+' in search_str:
                                            movie = imdb.search(search_str[:search_str.find('+-+')], self.imdb_translate)
                                        else:
                                            movie = imdb.search(search, self.imdb_translate)
                                        
                                    if not 'error' in movie: 
                                        if 'image_url' in movie:
                                            video_info = xbmcgui.ListItem(path=url, iconImage=movie['image_url'], thumbnailImage=movie['image_url'])
                                            video_info.setArt({'cover': movie['image_url']})
                                        else:
                                            video_info = xbmcgui.ListItem(path=url)
                                            
                                        video_info.setInfo('video', imdb._kodiJson(movie))
                                    else:
                                        video_info = xbmcgui.ListItem(path=url)
                                        video_info.setInfo('video', {'Title': title})
                                else:
                                    video_info = xbmcgui.ListItem(path=url)
                                    
                                self._log('start playing url: {}'.format(url), 0)                       
                                self.player.play(url, video_info)
                                
                                self.playing_playstream = self.player.isPlaying()
                            else:
                                dialog = xbmcgui.Dialog()
                                res = dialog.ok('Movie search failed', 'The movie you was searching for was not found.')
                        else:
                            self.show_message('TeamWatch', 'Playstream command from {} rejected.'.format(self.id_playerctl), self.ICON_SETTING)
                            
    def show_message (self, user, text, icon = ICON_CHAT, image = ''):
        try:
            self._log("show_message: {} {} [{}]".format(user, text, icon), 1)
        except:
            pass
            
        self._log("bartop: " + str(self.bartop), 2)
        self._log("text_color: " + self.skin['text_color'], 2)

        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

        self._log("looking for url", 2)
        try:
            url = re.findall('\[(https?://.+)\]', text)[0]
            self._log("url: " + url, 2)
        except:
            url = ""
            
        if image: url = image
            
        icon_file = os.path.join(__resources__, self.skin['icon'])
        if url:
            if url: text = text.replace('[' + url + ']', '').replace('  ',' ')
            
            h = hashlib.new('md5')
            h.update(url)
            icon_file = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch', '.cache', h.hexdigest())
            if not os.path.exists(icon_file):
                try:                
                    req = urllib2.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                    response = urllib2.urlopen(req)

                    with open(icon_file, "wb") as fcache:
                        fcache.write(response.read())
                        fcache.close()
                    response.close()
                    
                except urllib2.HTTPError, e:
                    self._log("HTTP Error: %s %s" % (e.code, url))
                except urllib2.URLError, e:
                    self._log("URL Error: %s %s" % (e.reason, url))

        if xbmcgui.getCurrentWindowId() == self.WINDOW_FULLSCREEN_VIDEO:
            icon_height = 150
        else:
            icon_height = 350

        im = Image.open(icon_file)
        icon_width = icon_height*im.width/im.height
        im.close()
        
        ICON_YPOS = 15
        
        self._log("adding icon", 2)
        self.icon = xbmcgui.ControlImage(0, 0, icon_width, icon_height, os.path.join(__resources__, 'no_image.png'))

        if self.bartop < 50:
            self.icon.setPosition(self.screen_width - (icon_width + 30), self.bartop + ICON_YPOS)
        else:
            self.icon.setPosition(self.screen_width - (icon_width + 30), self.bartop - (icon_height - ICON_YPOS))                
        self.window.addControl(self.icon)
        
        self.icon.setImage(icon_file, useCache=True)  

        self._log("icon file: %s" % icon_file, 2)
        self._log("icon: %s" % icon, 2)
        
        self._log("adding background", 2)
        if icon in range(7):
            self.background = xbmcgui.ControlImage(0, self.bartop, self.screen_width, 75, os.path.join(__resources__, self.skin[
                ['bar_chat', 'bar_twitter', 'bar_settings', 'bar_telegram', 'bar_rssfeed', 'bar_facebook', 'bar_email', 'bar_settings'][icon]
            ]))
        else:
            self.background = xbmcgui.ControlImage(0, self.bartop, self.screen_width, 75, os.path.join(__resources__, self.skin['bar_chat']))

        self.window.addControl(self.background)
        
        icon_top = self.bartop + 4
        if self.RSS_OFF:
            self.icon_rss_off = xbmcgui.ControlImage(85, icon_top, 30, 30, os.path.join(__resources__, self.skin['icon_rss_off']))
            self.window.addControl(self.icon_rss_off)
            icon_top = self.bartop + 41
            
        if self.TWEETS_OFF:
            self.icon_tweet_off = xbmcgui.ControlImage(85, icon_top, 30, 30, os.path.join(__resources__, self.skin['icon_tweet_off']))
            self.window.addControl(self.icon_tweet_off)
        
        self._log("adding feedtext", 2)        
        if self.RSS_OFF or self.TWEETS_OFF:
            self.feedtext = xbmcgui.ControlFadeLabel(int(self.skin['margin_left']) + 50, self.bartop + 5, self.screen_width-140, 75, font=self.skin['font'], textColor=self.skin['text_color'])
        else:
            self.feedtext = xbmcgui.ControlFadeLabel(int(self.skin['margin_left']), self.bartop + 5, self.screen_width-90, 75, font=self.skin['font'], textColor=self.skin['text_color'])
        self.window.addControl(self.feedtext)
        
        text = text.replace('\n', ' ').replace('\r', '').replace('  ', ' ')
        if user == 'rss' or user == '':
            self.feedtext.addLabel(text)
        else:
            self.feedtext.addLabel('[COLOR %s][B]%s[/B][/COLOR]: [B]%s[/B]' % (self.skin['nickname_color'], user, text))
        
        self.feed_is_shown = True
        self.feed_show_time = time.time()
    
    def hide_message(self):
        if self.feed_is_shown:
            self.window.removeControls([self.background, self.feedtext, self.icon])
            del self.feedtext
            del self.background
            del self.icon               
            
            if self.RSS_OFF:
                self.window.removeControl(self.icon_rss_off)
                del self.icon_rss_off
            
            if self.TWEETS_OFF: 
                self.window.removeControl(self.icon_tweet_off)
                del self.icon_tweet_off
            
            del self.window
            self.feed_is_shown = False
    
if __name__ == '__main__':
    tw = TeamWatch()
    tw.loop()
    tw._log('TeamWatch stopped')
