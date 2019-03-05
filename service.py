# -*- coding: utf-8 -*-
import os
import time
import socket
import urllib
import urllib2
import json
import httplib
import xbmc
import xbmcgui
import xbmcaddon
import pastebin
import random

from tools.xbmc_helpers import localize
from tools import xbmc_helpers

from datetime import datetime
import time

# import web_pdb;

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
        
VERSION = "0.0.6"
WINDOW_FULLSCREEN_VIDEO = 12005
DISPLAY_TIME_SECS = 5
REFRESH_TIME_SECS = 2
SOCKET_TIMEOUT = 0.5
DEBUG = 1

ICON_CHAT = 1
ICON_TWITTER = 2
ICON_SETTING = 3

class TeamWatch():
    __addon__ = xbmcaddon.Addon()
    __resources__ = os.path.join(__addon__.getAddonInfo('path'),'resources')

    monitor = xbmc.Monitor()

    window = None
    background = None
    feedtext = None
    
    id_teamwatch = __addon__.getSetting('twid')
    id_playerctl = __addon__.getSetting('pcid')
    nickname = __addon__.getSetting('nickname')
	
    twitter_enabled = __addon__.getSetting('twitter_enabled')
    twitter_language = __addon__.getSetting('language')
    twitter_language = xbmc.convertLanguage(twitter_language, xbmc.ISO_639_1)
    twitter_result_type = __addon__.getSetting('result_type')
    
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
    id_invite = ""
    
    show_enable = True
    feed_show_time = None
    feed_name = ['#teamwatch']
    feed_is_shown = False;
    show_disable_after = False
    start_time = time.time()
    player = None
    
    log_prog = 1
    
    def __init__(self):
        self.id_teamwatch = self.__addon__.getSetting('twid')
        
        for feed in self.__addon__.getSetting('feed').split(":"):
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
        self._log("start [" + ":".join(self.feed_name) + "]")
        self._log(self.show_allways)
        
        self.bartop = self.screen_height - 75
        self.background = xbmcgui.ControlImage(0, self.bartop, self.screen_width, 75, os.path.join(self.__resources__, '1280_settings.png'))
        self.background.setVisible(False)
        self.feedtext = xbmcgui.ControlLabel(80, self.bartop + 5, self.screen_width-90, 75, '', font='font45', textColor='0xFFFFFFFF')
        self.feedtext.setVisible(False)
        
    def _log(self, text):
        xbmc.log ('%d service.maxxam.teamwatch: %s' % (self.log_prog, text))
        self.log_prog = self.log_prog + 1
        
    def loop(self):        
        twpath = os.path.join(xbmc.translatePath('special://home'), 'userdata', 'addon_data', 'service.maxxam.teamwatch', 'tw.ini')
        
        while not self.monitor.abortRequested():
            # after DISPLAY_TIME_SECS elapsed hide the message bar
            if self.monitor.waitForAbort(REFRESH_TIME_SECS):
                self.hide_message()
                self._log("stop")
                break
            
            if self.feed_is_shown and time.time() - self.feed_show_time > DISPLAY_TIME_SECS:
                self.hide_message()
                
                if self.show_disable_after:
                    self.hide_message()
                    self.show_enable = False
                    self.show_disable_after = False
                    
            if (time.time() - self.start_time) < REFRESH_TIME_SECS or self.feed_is_shown:
                continue
            
            self.start_time = time.time()
            
            if self.id_chat != -1:
                try:
                    file = open(twpath, "r")
                    tmp = file.read().split(":")
                    self.id_chat = int(tmp[0])
                    if len(tmp) == 2: self.id_twitter = int(tmp[1])
                    file.close()
                except:
                    self.id_chat = -1
                    self.id_twitter = -1
                    
            params = {'idt':self.id_twitter, 'idc':self.id_chat, 'twid':self.id_teamwatch, 'pcid':self.id_playerctl, 'nickname':self.nickname}
            if self.feed_name: 
                params['q'] = ":".join(self.feed_name)
            else:
                params['q'] = "#teamwatch"
                
            if self.twitter_enabled:
                params['tqp'] = "&lang=%s&result_type=%s" % (self.twitter_language, self.twitter_result_type)
                params['tl'] = self.twitter_language
            else:
                params['notweet'] = 1
                
            url = 'https://www.teamwatch.it/get.php?%s' % urllib.urlencode(params)
            
            if DEBUG > 0: 
                self._log("id_chat: " + str(self.id_chat))
                self._log("id_twitter: " + str(self.id_twitter))
                self._log(url)

            jresult = {}
            try:
                tmp = urllib.urlopen(url).read()
            except:
                tmp = None
                pass
                
            if tmp == None: 
                jresult = {"status":"fail", "reason": "error opening %s" % url, "time":""}
            else:
                json_response = tmp.replace('\n', ' ').replace('\r', '')
                if DEBUG: self._log("json_response: " + json_response)
                jresult = json.loads(json_response)
                if 'id' in jresult:
                    if 'is_twitter' in jresult and jresult['is_twitter'] == 1:
                        self.id_twitter = jresult['id']
                    else:
                        self.id_chat = jresult['id']

                    file = open(twpath, "w+")
                    file.write(str(self.id_chat) + ":" + str(self.id_twitter))
                    file.close()
                
            """
            try:
                jresult = {}
                jresult = json.loads(urllib.urlopen(url).read())
            except:
                self._log("error opening %s" % url)
                jresult = {"status":"fail", "reason": "error opening %s" % url, "time":""}
            finally:
                if 'id' in jresult:
                    if 'is_twitter' in jresult and jresult['is_twitter'] == 1:
                        self.id_twitter = jresult['id']
                    else:
                        self.id_chat = jresult['id']

                    file = open(twpath, "w+")
                    file.write(str(self.id_chat) + ":" + str(self.id_twitter))
                    file.close()
            """
            # self._log(jresult)        
            if 'status' in jresult and jresult['status'] == 'ok' and  self.show_enable:
                file = open(twpath, "w")
                file.write(str(self.id_chat) + ":" + str(self.id_twitter))
                file.close()

                user = jresult['user'].encode('utf-8')[:15]
                text = jresult['text'].encode('utf-8')
        
                self._log('messaggio ricevuto da %s: %s' % (user, text))
                
                if self.show_allways or xbmcgui.getCurrentWindowId() == WINDOW_FULLSCREEN_VIDEO:
                    if DEBUG > 0:
                        self.show_message(user, text, [ICON_CHAT, ICON_TWITTER][jresult['is_twitter']]) #, jresult['id'])
                    else:
                        self.show_message(user, text, [ICON_CHAT, ICON_TWITTER][jresult['is_twitter']])
            elif 'status' in jresult and jresult['status'] == 'settings':
                param = jresult['param'].encode('utf-8')
                if param.startswith("#tw:addfeed:"):
                    if not param[12:] in self.feed_name: 
                        self.feed_name.append(param[12:])
                        self.__addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32000, param[12:]), ICON_SETTING)
                elif param.startswith("#tw:removefeed:"):
                    if param[15:] in self.feed_name: 
                        self.feed_name.remove(param[15:])
                        self.__addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32001, param[15:]), ICON_SETTING)
                elif param == "#tw:off":
                    self.show_message('TeamWatch', localize(32002), ICON_SETTING)
                    self.show_disable_after = True
                elif param == "#tw:on":
                    self.show_enable = True
                    self.show_message('TeamWatch', localize(32003), ICON_SETTING)
                elif param == "#tw:bar:top":
                    self.bartop = 0
                    self.show_message('TeamWatch', "Bar position set to top", ICON_SETTING)
                elif param == "#tw:bar:bottom":
                    self.bartop = self.screen_height - 75
                    self.show_message('TeamWatch', "Bar position set to bottom", ICON_SETTING)
                elif param == "#tw:id":
                    self.id_chat = jresult['idc']
                    self.id_twitter = jresult['idt']

                    file = open(twpath, "w+")
                    file.write(str(self.id_chat) + ":" + str(self.id_twitter))
                    file.close()
                elif param == "#tw:playerctl:playpause":
                    self._log('esecuzione #tw:playerctl:playpause')
                    xbmc.executebuiltin("Action(PlayPause)")
                    self._log('playpause terminated id_chat: ' + str(self.id_chat))
                elif param == "#tw:playerctl:sshot":
                    xbmc.executebuiltin("TakeScreenshot")
                elif param.startswith("#tw:playerctl:seek:"):
                    t = [int("0"+filter(str.isdigit, x)) for x in param[19:].split(":")]
                    if len(t) == 4:
                        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Seek", "params": {"playerid":1, "value": {"hours":%d, "minutes":%d, "seconds":%d, "milliseconds":%d}}, "id": 1 }' % tuple(t))
                    elif DEBUG:
                        self._log('#tw:playerctl:seek invalid time')
                elif param.startswith("#tw:playstream:"):
                    self._log('*** playstream received ***')
                    self._log(param[15:])
                    player = xbmc.Player()
                    player.play(param[15:])
                elif param.startswith("#tw:invite:"):
                    # web_pdb.set_trace()
                    if DEBUG: self._log("#tw:invite")
                    invite = param[11:].split(":")
                    
                    if invite[0] == "m":
                        self._log("#tw:invite:m: %s" % invite[1])
                        movie = xbmc_helpers.search_movie(invite[1])
                        self._log("after movie search")

                        if movie:
                            if DEBUG: self._log("invite received for movie: %s" % movie["title"])
                            
                            dialog = xbmcgui.Dialog()
                            res = dialog.yesno(localize(32004), localize(32005, (invite[1], movie["title"])))
                            
                            if res:
                                player = xbmc.Player()
                                player.play(movie["file"])
                                
                                if player.isPlaying():
                                    self._log('playing...')
                                else:
                                    self._log('not playing...')
                        else:
                            if DEBUG: self._log("invite received for non existent movie %s" % invite[1])
                            
                    elif invite[0] == "e":
                        episode = xbmc_helpers.search_episode(invite[1], invite[2], invite[3])
                        
                        if episode:
                            dialog = xbmcgui.Dialog()
                            s_ep = "S[COLOR green][B]%02d[/B][/COLOR]E[COLOR green][B]%02d[/B][/COLOR]" % (int(episode["season"]), int(episode["episode"]))
                            res = dialog.yesno(localize(32004), localize(32006, (invite[1], episode["showtitle"], s_ep)))
                            if DEBUG: self._log("invite received for episode id: %d" % episode["episodeid"])
                        else:
                            if DEBUG: self._log("invite received for non existent episode %s %s %s" % (invite[1], invite[2], invite[3]))
                    else:
                        if DEBUG: self._log("invite received invalid param %s" % invite[0])
                elif param.startswith("#tw:sendlog"):
                    # API Settings
                    api_dev_key  = '8ad7b020994f2abf1d8631bf4ea3de6c' # please don't steal these passwords!
                    api_user_key = '764fa208bd3ab14806273da932daf68e' # make a new account it's free

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
                    data = "TeamWatch version: %s from: %s\r\n" % (VERSION, self.nickname)
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
                    else:
                        self._log(result)
                        
                    url = 'https://www.teamwatch.it/add.php?%s' % urllib.urlencode({'user':self.nickname, 'text':result.replace("https://pastebin.com/", ""), 'feed':'#tw:' + ''.join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(20))})
                    tmp = urllib.urlopen(url)
                    
    def show_message (self, user, text, icon = ICON_CHAT, id=-1):
        if DEBUG > 0: 
            self._log("show_message: " + user + " " + text)
            self._log("bartop: " + str(self.bartop))
            
        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        self.background.setPosition(0, self.bartop)
        self.background.setVisible(False)
        self.window.addControl(self.background)
        
        self.feedtext.setPosition(80, self.bartop + 5)
        self.feedtext.setLabel('')
        self.feedtext.setVisible(False)        
        self.window.addControl(self.feedtext)
        
        if icon == ICON_TWITTER:
            self.background.setImage(os.path.join(self.__resources__, '1280_tweet.png'))
        elif icon == ICON_SETTING:
            self.background.setImage(os.path.join(self.__resources__, '1280_settings.png'))
        elif icon == ICON_CHAT:
            self.background.setImage(os.path.join(self.__resources__, '1280_chat.png'))
        else:
            self.background.setImage(os.path.join(self.__resources__, '1280_chat.png'))
            
        if DEBUG:
            self.feedtext.setLabel('[COLOR yellow][B]%s[/B][/COLOR]: [%d] %s' % (user, id, text))
        else:
            self.feedtext.setLabel('[COLOR yellow][B]%s[/B][/COLOR]: %s' % (user, text))
        
        self.background.setVisible(True)
        self.feedtext.setVisible(True)
        
        self.feed_is_shown = True
        self.feed_show_time = time.time()
    
    def hide_message(self):
        if self.feed_is_shown:
            self.window.removeControls([self.feedtext, self.background])
            self.feed_is_shown = False
    
if __name__ == '__main__':
    tw = TeamWatch()
    tw.loop()
