# -*- coding: utf-8 -*-
import os, re, sys
import base64
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

__version__ = "0.0.11"
__addon__ = xbmcaddon.Addon()
__resources__ = os.path.join(__addon__.getAddonInfo('path'),'resources')
__pylib__ = os.path.join(__addon__.getAddonInfo('path'), 'lib')

ADDONID = __addon__.getAddonInfo('id')

sys.path.append(__pylib__)
sys.path.append('./lib/maxxam_imdb')

import betterimap
import xbmc_helpers
from bs4 import BeautifulSoup
from xbmc_helpers import localize
import maxxam_imdb as imdb

error_lines = False

def checkline(line, time_now):
    global error_lines
    
    try:
        time_line=int(line[:2])*3600 + int(line[3:5])*60+int(line[6:8])
    except:
        return False
        
    if (time_now-time_line) > 5*60: 
        return False
        
    if "ERROR: EXCEPTION Thrown (PythonToCppException)" in line:
        error_lines = True
    elif "-->End of Python script error report<--" in line:
        error_lines = False
    
    return "service.maxxam.teamwatch" in line or error_lines

def fix_unicode (barray, repl = ''):
    out = ''
    for c in barray:
        try:
            out += str(c)
        except:
            out += repl
            
    return out

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
    DEBUG = 2 # 0 = LOW, 1 = MEDIUM, 2 = HIGH lasciare a uno!

    ICON_CHAT = 0
    ICON_TWITTER = 1
    ICON_SETTING = 2
    ICON_TELEGRAM = 3
    ICON_RSSFEED = 4
    ICON_FACEBOOK = 5
    ICON_EMAIL = 6
    ICON_ERROR = 7
    
    SKIN_CONFIG = 'default.skin'

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
    
    email_enabled = __addon__.getSetting('email_enabled')
    email = __addon__.getSetting('email')
    email_password = __addon__.getSetting('email_password')
    email_imap = __addon__.getSetting('email_imap')
    facebook = __addon__.getSetting('facebook')
    
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
    
    id_chat = -1
    id_twitter = -1
    id_rss = -1
    id_invite = ""
    
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
    player = None
    
    log_prog = 1

    def __init__(self):
        self.monitor = KodiEvents(self)
        self.id_teamwatch = __addon__.getSetting('twid')
        
        for feed in __addon__.getSetting('feed').split(":"):
            if feed not in self.feed_name: self.feed_name.append(feed)
    
        self.id_chat = -1
        self.id_twitter = -1
        self.id_invite = ""
        
        self.show_enable = True
        self.feed_show_time = time.time()
        self.feed_is_shown = False;
        self.show_disable_after = False
        self.bartop = self.screen_height - 75
        
        self.player = xbmc.Player()
        self._log("Teamwatch start [" + ":".join(self.feed_name) + "]")
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
            
        self.bartop = self.screen_height - 75        
        directory = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch', '.cache')
        if not os.path.exists(directory): os.makedirs(directory)

    def _log(self, text, debug_level=1):
        if self.DEBUG >= debug_level:
            xbmc.log ('%d service.maxxam.teamwatch: %s' % (self.log_prog, text))
            self.log_prog = self.log_prog + 1

    def settings(self, settings):
        self.id_teamwatch = settings['twid']
        self.id_playerctl = settings['pcid']
        self.nickname = settings['nickname']
        
        self.twitter_enabled = settings['twitter_enabled']
        self.twitter_language = settings['language']
        self.twitter_language = xbmc.convertLanguage(self.twitter_language, xbmc.ISO_639_1)
        self.twitter_result_type = settings['result_type']
        
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

        text = ''
        try:
            imap = betterimap.IMAPAdapter(imap_user, imap_pass, host=imap_host, ssl=True)            
            imap.select('INBOX') # [Gmail]/Tutti i messaggi
            
            icon = None
            yesterday = date.today() - timedelta(1)
            for msg in imap.easy_search(since=yesterday, other_queries=['unseen'], limit=1):
                if msg.from_addr[1] == 'notification@facebookmail.com' and self.facebook:
                    body = fix_unicode(msg.html())
                    
                    regex = r"<span style=\"color:#FFFFFF;font-size:1px;\">([^<]+)<\/span>"
                    matches = re.finditer(regex, body, re.MULTILINE)
                    if matches:
                        text = fix_unicode(msg.subject) + ' ' + [i.group(1) for i in matches][0]
                        text = text.replace('\n', '').replace('\r', '')
                        text = re.sub(r"  Mipiace.*$", "", text)
                        text = re.sub(r"  -  Rispondi.*$", "", text)
                        text = re.sub(r"^\s*", "", text)
                        text = re.sub(r"\s*$", "", text)
                        text = BeautifulSoup(text, features="html.parser")
                        text = '[B]{}[/B]'.format('', text)
                    else:
                        text = fix_unicode(msg.subject)
                        text = '[B]{}[/B]'.format(fix_unicode(msg.subject))
                        
                    self.ICON_FACEBOOK
                else:
                    icon = self.ICON_EMAIL
                    text = '[COLOR {}][B]{}[/B][/COLOR]: [B]{}[/B]'.format(self.skin['nickname_color'], fix_unicode(msg.from_addr[0] if msg.from_addr[0] else msg.from_addr[1]), fix_unicode(msg.subject))
        except:
            self.show_message('', 'Error fetching email.', self.ICON_ERROR)
            return
            
        if text: self.show_message('', text, icon)
        
    def get_ids(self):
        directory = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch')
        twpath = os.path.join(directory, 'tw.ini')

        try:
            file = open(twpath, "r")
            tmp = file.read().split(":")
            file.close()
            while len(tmp) != 3: tmp.append(-1)
        except:
            tmp = [-1, -1, -1]
        
        return tmp
        
    def write_ids(self):
        directory = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch')
        if not os.path.exists(directory): os.makedirs(directory)
        twpath = os.path.join(directory, 'tw.ini')
        
        file = open(twpath, "w+")
        file.write('{}:{}:{}'.format(self.id_chat, self.id_twitter, self.id_rss))
        file.close()
        
    def loop(self):
        while not self.monitor.abortRequested():
            # after DISPLAY_TIME_SECS elapsed hide the message bar
            if self.monitor.waitForAbort(self.REFRESH_TIME_SECS):
                self.hide_message()
                self._log("stop", 2)
                break
            
            self._log('Email check enabled: {}'.format(self.email_enabled))
            if self.email_enabled and time.time() - self.email_time > self.CHECK_EMAIL_SECS and not self.feed_is_shown:
                self.email_time = time.time()
                self.check_email()
                
            if self.feed_is_shown and time.time() - self.feed_show_time > self.DISPLAY_TIME_SECS:
                self.hide_message()
                
                if self.show_disable_after:
                    self.show_enable = False
                    self.show_disable_after = False
                    
            if (time.time() - self.start_time) < self.REFRESH_TIME_SECS or self.feed_is_shown:
                continue
            
            self.start_time = time.time()
            
            if self.id_chat != -1: self.id_chat, self.id_twitter, self.id_rss = self.get_ids()
                    
            params = {'idt':self.id_twitter, 'idc':self.id_chat, 'idr':self.id_rss, 'twid':self.id_teamwatch, 'pcid':self.id_playerctl, 'nickname':self.nickname}
            if self.feed_name: 
                params['q'] = ":".join(self.feed_name)
            else:
                params['q'] = "#teamwatch"
                
            if self.twitter_enabled:
                params['tqp'] = self.twitter_result_type
                params['tl'] = self.twitter_language
            else:
                params['notweet'] = 1
                    
            url = 'https://www.teamwatch.it/get.php?p=%s' % base64.urlsafe_b64encode(str(params).replace("'", '"'))
            
            if self.DEBUG > 0: 
                self._log("id_chat: " + str(self.id_chat), 1)
                self._log("id_twitter: " + str(self.id_twitter), 1)
                self._log("id_rss: " + str(self.id_rss), 1)
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
                    jresult = {"status": "error", "params": {"message": "error decoding json result %s " % json_response, "time": now}, "id": -1}
                    
                if self.DEBUG > 0: self._log("jresult: " + str(jresult), 1)
                params = jresult['params']
                
                if 'status' in jresult:
                    if jresult['status'] == 'ok':
                        if params['is_twitter'] == 1:
                            self.id_twitter = jresult['id']
                        elif params['is_rss'] == 1:
                            self.id_rss = jresult['id']
                        else:
                            self.id_chat = jresult['id']
                    elif jresult['status'] == 'settings':
                        self.id_chat = jresult['id']
                    else:
                        self._log('Error in json message: {}'.format(params))
                        if 'show' in params and params['show']: self.show_message('Error', params['message'], self.ICON_ERROR)
                        
                    self.write_ids()
                else:
                    self._log('Error invalid json message: {}'.format(params))
                    self.show_message('Error', 'Invalid message received', self.ICON_ERROR)
                
            if 'status' in jresult and jresult['status'] == 'ok' and  self.show_enable:
                user = params['user'].encode('utf-8')[:15]
                text = params['text'].encode('utf-8') 
        
                if self.show_allways or xbmcgui.getCurrentWindowId() == self.WINDOW_FULLSCREEN_VIDEO:
                    if text[:8] == '#tw_send':
                        self.show_message(user, text[9:], self.ICON_TELEGRAM)
                    elif params['is_twitter'] == 1 and not self.TWEETS_OFF:
                        self.show_message(user, text, self.ICON_TWITTER)
                    elif params['is_rss'] == 1 and not self.RSS_OFF:
                        self.show_message(user, text, self.ICON_RSSFEED)
                    elif params['is_rss'] == 0 and params['is_twitter'] == 0:
                        self.show_message(user, text, self.ICON_CHAT)
                        
            elif 'status' in jresult and jresult['status'] == 'settings':
                param = params['text']
                if param.startswith("#tw:addfeed:"):
                    if not param[12:] in self.feed_name: 
                        self.feed_name.append(param[12:].lower())
                        __addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32000, param[12:]), self.ICON_SETTING)
                elif param.startswith("#tw:removefeed:"):
                    if param[15:].lower() in self.feed_name:                         
                        self.feed_name.remove(param[15:].lower())
                        __addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32001, param[15:]), self.ICON_SETTING)
                elif param == "#tw:off":
                    self.show_message('TeamWatch', localize(32002), self.ICON_SETTING)
                    self.show_disable_after = True
                elif param == "#tw:on":
                    self.show_enable = True
                    self.show_message('TeamWatch', localize(32003), self.ICON_SETTING)
                elif param == '#tw:rss:on':
                    if self.RSS_OFF:
                        self.RSS_OFF = not self.RSS_OFF
                        self.show_message('TeamWatch', "RSS feeds show set to on", self.ICON_SETTING)
                elif param == '#tw:rss:off':
                    if not self.RSS_OFF:
                        self.RSS_OFF = not self.RSS_OFF
                        self.show_message('TeamWatch', "RSS feeds show set to off", self.ICON_SETTING)
                elif param == '#tw:tweet:on':
                    if self.TWEETS_OFF:
                        self.TWEETS_OFF = not self.TWEETS_OFF
                        self.show_message('TeamWatch', "Twitter feeds show set to on", self.ICON_SETTING)
                elif param == '#tw:tweet:off':
                    if not self.TWEETS_OFF:
                        self.TWEETS_OFF = not self.TWEETS_OFF
                        self.show_message('TeamWatch', "Twitter feeds show set to off", self.ICON_SETTING)
                elif param == "#tw:bar:top":
                    self.bartop = 0
                    self.show_message('TeamWatch', "Bar position set to top", self.ICON_SETTING)
                elif param == "#tw:bar:bottom":
                    self.bartop = self.screen_height - 75
                    self.show_message('TeamWatch', "Bar position set to bottom", self.ICON_SETTING)
                elif param == "#tw:id":
                    self.id_chat = params['idc']
                    self.id_twitter = params['idt']
                    self.id_rss = params['idr']
                    
                    self.write_ids()
                elif param == "#tw:playerctl:playpause":
                    if self.DEBUG > 0: self._log('esecuzione #tw:playerctl:playpause', 2)
                    xbmc.executebuiltin("Action(PlayPause)")
                    if self.DEBUG > 0: self._log('playpause terminated id_chat: ' + str(self.id_chat), 2)
                elif param == "#tw:playerctl:stop":
                    if self.DEBUG > 0: self._log('esecuzione #tw:playerctl:stop', 2)
                    xbmc.executebuiltin("Action(Stop)")
                    if self.DEBUG > 0: self._log('stop terminated id_chat: ' + str(self.id_chat), 2)
                elif param == "#tw:playerctl:sshot":
                    xbmc.executebuiltin("TakeScreenshot")
                elif param.startswith("#tw:playerctl:seek:"):
                    t = [int(x) for x in param[19:].split(":")]
                    if len(t) == 4:
                        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Seek", "params": {"playerid":1, "value": {"hours":%d, "minutes":%d, "seconds":%d, "milliseconds":%d}}, "id": 1 }' % tuple(t))
                    elif self.DEBUG > 0:
                        self._log('#tw:playerctl:seek invalid time')
                elif param.startswith("#tw:playstream:"):
                    self._log('*** playstream received ***', 2)
                    params = param[15:].split('&m_title=')
                    
                    player = xbmc.Player()
                    
                    if len(params) == 2:
                        url, m_title = params
                        movie = imdb.search(m_title)
                        
                        listitem = xbmcgui.ListItem(path=url, thumbnailImage=movie['image_url'])
                        
                        listitem.setInfo('video', imdb._kodiJson(movie))
                        if 'image_url' in movie: listitem.setArt({'cover': movie['image_url']})
                        
                        self._log(url, 2)
                        player.play(url, listitem)
                    else:
                        player.play(url)
                elif param.startswith("#tw:invite:"):
                    # web_pdb.set_trace()
                    if self.DEBUG > 0: self._log("#tw:invite", 2)
                    invite = param[11:].split(":")
                    user = "unknown"
                    
                    if invite[0] == "m":
                        self._log("#tw:invite:m: %s" % invite[1], 2)
                        movie = xbmc_helpers.search_movie(invite[1])
                        self._log("after movie search", 2)

                        if movie:
                            if self.DEBUG > 0: self._log("invite received for movie: %s" % movie["title"], 2)
                            
                            dialog = xbmcgui.Dialog()
                            res = dialog.yesno(localize(32004), localize(32005, (user, movie["title"])))
                            
                            if res:
                                player = xbmc.Player()
                                player.play(movie["file"])
                                
                                if player.isPlaying():
                                    self._log('playing...', 2)
                                else:
                                    self._log('not playing...', 2)
                        else:
                            if self.DEBUG > 0: self._log("invite received for non existent movie %s" % invite[1])
                            self.show_message('TeamWatch', "invite received for non existent movie %s" % invite[1], self.ICON_SETTING)
                    elif invite[0] == "e":
                        episode = xbmc_helpers.search_episode(invite[1], invite[2], invite[3])
                        self._log(str(episode), 2)
                        
                        if episode:
                            dialog = xbmcgui.Dialog()
                            s_ep = "S[B]%02d[/B]E[B]%02d[/B]" % (int(episode["season"]), int(episode["episode"]))
                            res = dialog.yesno(localize(32004), localize(32006, (user, episode["showtitle"], s_ep)))
                            if self.DEBUG > 0: self._log("invite received for episode id: %d" % episode["episodeid"], 2)
                            if res:
                                player = xbmc.Player()
                                player.play(xbmc_helpers.get_episode_details(episode["episodeid"])["file"])
                                
                                if player.isPlaying():
                                    self._log('playing...', 2)
                                else:
                                    self._log('not playing...', 2)
                        else:
                            if self.DEBUG > 0: self._log("invite received for non existent episode %s %s %s" % (invite[1], invite[2], invite[3]))
                            self.show_message('TeamWatch', "invite received for non existent episode %s %s %s" % (invite[1], invite[2], invite[3]), self.ICON_SETTING)
                    else:
                        if self.DEBUG > 0: self._log("invite received invalid param %s" % invite[0])
                        self.show_message('TeamWatch', "invite received invalid param %s" % invite[0], self.ICON_SETTING)
                elif param.startswith("#tw:sendlog"):
                    if self.DEBUG == 0:
                        self.show_message('TeamWatch', "Please activate debug log in Kodi settings", self.ICON_SETTING)
                        continue
                    
                    # API Settings
                    api_dev_key  = '8ad7b020994f2abf1d8631bf4ea3de6c' # please don't steal these passwords!
                    api_user_key = '764fa208bd3ab14806273da932daf68e' # make a new account it's for free

                    # Define API
                    if api_user_key:
                        api = pastebin.PasteBin(api_dev_key, api_user_key)
                    else:
                        api = pastebin.PasteBin(api_dev_key)
                        api_user_key = api.create_user_key('teamwatch', 'n0DPeu2cuhZY7o5JfdRD')
                        if 'Bad API request' not in api_user_key:
                            api = pastebin.PasteBin(api_dev_key, api_user_key)
                        else:
                            raise SystemExit('[!] - Failed to create API user key! ({0})'.format(api_user_key.split(', ')[1]))
                    
                    version_number = xbmc.getInfoLabel("System.BuildVersion")[0:2]
                    if version_number < 12:
                        if xbmc.getCondVisibility("system.platform.osx"):
                            if xbmc.getCondVisibility("system.platform.atv2"):
                                log_path = "/var/mobile/Library/Preferences"
                            else:
                                log_path = os.path.join(os.path.expanduser("~"), "Library/Logs")
                        elif xbmc.getCondVisibility("system.platform.ios"):
                            log_path = "/var/mobile/Library/Preferences"
                        elif xbmc.getCondVisibility("system.platform.windows"):
                            log_path = xbmc.translatePath("special://home")
                        elif xbmc.getCondVisibility("system.platform.linux"):
                            log_path = xbmc.translatePath("special://home/temp")
                        else:
                            log_path = xbmc.translatePath("special://logpath")
                    else:
                        log_path = xbmc.translatePath("special://logpath")

                    if version_number < 14:
                        filename = "xbmc.log"
                    else:
                        filename = "kodi.log"

                    if not os.path.exists(os.path.join(log_path, filename)):
                        if os.path.exists(os.path.join(log_path, "spmc.log")):
                            filename = "spmc.log"

                    log_path = os.path.join(log_path, filename)
                    # Create a Paste
                    t = time.strftime('%H:%M:%S', time.localtime())
                    time_now=int(t[:2])*3600 + int(t[3:5])*60+int(t[6:])
                    data = "TeamWatch version: %s from: %s\r\n" % (__version__, self.nickname)
                    filepath = log_path.decode("utf-8")
                    with open(filepath) as fp:  
                        line = fp.readline()
                        if checkline(line, time_now): data += line
                        
                        while line:
                            line = fp.readline()
                            if checkline(line, time_now): data += line
                            
                    result = api.paste(data, guest=False, name='kodi teamwatch log', format='text', private='2', expire='10M')
                    if 'Bad API request' in result: 
                        self._log('[!] - Failed to create paste! ({0})'.format(api_user_key.split(', ')[1]))
                        self.show_message('TeamWatch', '[!] - Failed to create paste! ({0})'.format(api_user_key.split(', ')[1]), self.ICON_SETTING)
                    else:
                        self._log(result, 2)
                        self.show_message('TeamWatch', result, self.ICON_SETTING)
                        
                    url = 'https://www.teamwatch.it/add.php?%s' % urllib.urlencode({'user':self.nickname, 'text':result.replace("https://pastebin.com/", ""), 'feed':'#tw:' + ''.join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(20))})
                    tmp = urllib.urlopen(url)
                    
    def show_message (self, user, text, icon = ICON_CHAT, id=-1):
        if self.DEBUG > 0: 
            self._log("show_message: {} {} [{}]".format(user, text, icon), 1)
            self._log("bartop: " + str(self.bartop), 2)
            self._log("text_color: " + self.skin['text_color'], 2)

        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        
        if self.DEBUG > 0: self._log("adding background", 2)
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
        
        if self.DEBUG > 0: self._log("adding feedtext", 2)        
        if self.RSS_OFF or self.TWEETS_OFF:
            self.feedtext = xbmcgui.ControlFadeLabel(int(self.skin['margin_left']) + 50, self.bartop + 5, self.screen_width-140, 75, font=self.skin['font'], textColor=self.skin['text_color'])
        else:
            self.feedtext = xbmcgui.ControlFadeLabel(int(self.skin['margin_left']), self.bartop + 5, self.screen_width-90, 75, font=self.skin['font'], textColor=self.skin['text_color'])
        self.window.addControl(self.feedtext)
        
        if self.DEBUG > 0: self._log("adding icon", 2)
        self.icon = xbmcgui.ControlImage(0, 0, 150, 150, os.path.join(__resources__, self.skin['icon']))
        if self.bartop < 50:
            self.icon.setPosition(self.screen_width - 180, self.bartop + 30)
        else:
            self.icon.setPosition(self.screen_width - 180, self.bartop - 130)        
        self.icon.setImage(os.path.join(__resources__, self.skin['icon']), useCache=True)
        self.window.addControl(self.icon)
        
        if self.DEBUG > 0: self._log("looking for url", 2)
        try:
            url = re.findall('\[(https?://.+)\]', text)[0]
            if self.DEBUG > 0: self._log("url: " + url, 2)
        except:
            url = ""
            
        icon_file = os.path.join(__resources__, self.skin['icon'])
        if url:
            text = text.replace('[' + url + ']', '').replace('  ',' ')
        
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
                    
        self.icon.setImage(icon_file, useCache=True)  
        
        if self.DEBUG > 0: self._log("icon file: %s" % icon_file, 2)
        if self.DEBUG > 0: self._log("icon: %s" % icon, 2)
        
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
