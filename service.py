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

from tools.xbmc_helpers import localize
from tools import xbmc_helpers

# import web_pdb;

WINDOW_FULLSCREEN_VIDEO = 12005
DISPLAY_TIME_SECS = 5
REFRESH_TIME_SECS = 2
SOCKET_TIMEOUT = 0.5
DEBUG = 0

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
    if screen_height == "": screen_height = xbmcgui.getScreenHeight()
    
    screen_width = __addon__.getSetting('screen_width')
    if screen_width == "": screen_width = xbmcgui.getScreenWidth()
    
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
            
            try:
                file = open(twpath, "r")
                self.id_chat = int(file.read())
                file.close()
            except:
                self.id_chat = -1
                
            params = {'idt':self.id_twitter, 'idc':self.id_chat, 'twid':self.id_teamwatch, 'pcid':self.id_playerctl, 'nickname':self.nickname}
            if self.feed_name: 
                params['q'] = ":".join(self.feed_name)
            else:
                params['q'] = "#teamwatch"
                
            if self.twitter_enabled:
                params['tqp'] = "&lang=%s&result_type=%s" % (self.twitter_language, self.twitter_result_type)
                params['tl'] = self.twitter_language
            else:
                params['    notweet'] = 1
                
            url = 'https://www.teamwatch.it/get.php?%s' % urllib.urlencode(params)
            
            if DEBUG > 1: 
                self._log("id_chat: " + str(self.id_chat))
                self._log(url)

            try:
                jresult = {}
                jresult = json.loads(urllib.urlopen(url).read())
            except:
                self._log("error opening %s" % url)
            finally:
                if 'id' in jresult:
                    if 'is_twitter' in jresult and jresult['is_twitter'] == 1:
                        self.id_twitter = jresult['id']
                    else:
                        self.id_chat = jresult['id']

                    file = open(twpath, "w+")
                    file.write(str(self.id_chat))
                    file.close()
                    
            if jresult['status'] == 'ok' and  self.show_enable:
                file = open(twpath, "w")
                file.write(str(self.id_chat))
                file.close()

                user = jresult['user'].encode('utf-8')
                text = jresult['text'].encode('utf-8')
                
                if self.show_allways or xbmcgui.getCurrentWindowId() == WINDOW_FULLSCREEN_VIDEO:
                    if DEBUG > 1:
                        self.show_message(user, text, [ICON_CHAT, ICON_TWITTER][jresult['is_twitter']]) #, jresult['id'])
                    else:
                        self.show_message(user, text, [ICON_CHAT, ICON_TWITTER][jresult['is_twitter']])
            elif jresult['status'] == 'settings':
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

                    file = open(twpath, "w")
                    file.write(str(self.id_chat))
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
                            # dialog = xbmcgui.Dialog()
                            # res = dialog.yesno(localize(32004), localize(32005, (invite[1], movie["title"])))
                            if DEBUG: self._log("invite received for movie: %s" % movie["title"])
                            
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
                        pass
                else:
                    pass
            else:
                if DEBUG and jresult['status'] == "fail" and jresult['reason'] != "no feeds" and not jresult['reason'].startswith('waiting'): 
                    self._log(jresult)
                    
                if DEBUG and jresult['reason'].startswith('json parse error'):
                    self.id_twitter = -1
                    self.id_chat = -1
                   
    def show_message (self, user, text, icon = ICON_CHAT, id=-1):
        if DEBUG: self._log(user + " " + text)
        
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
