# -*- coding: utf-8 -*-
from cStringIO import StringIO
import re
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

SERVER = "maxxam.tk"
WINDOW_FULLSCREEN_VIDEO = 12005
DISPLAY_TIME_SECS = 5
REFRESH_TIME_SECS = 2
SOCKET_TIMEOUT = 2.0
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
    
    twitter_enabled = __addon__.getSetting('twitter_enabled')
    twitter_language = __addon__.getSetting('language')
    twitter_language = xbmc.convertLanguage(twitter_language, xbmc.ISO_639_1)
    twitter_result_type = __addon__.getSetting('result_type')
    
    show_allways = not (__addon__.getSetting('showallways') == "true")
    
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
        self.background = xbmcgui.ControlImage(0, 600, 1280, 50, os.path.join(self.__resources__, '1280_settings.png'))
        self.background.setVisible(True)
        self.feedtext = xbmcgui.ControlLabel(70, 605, 1200, 50, '', font='font30', textColor='0xFFFFFFFF')
        self.feedtext.setVisible(True)
        
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
        
        # player_type = xbmc.PLAYER_CORE_DVDPLAYER
        # player_type = xbmc.PLAYER_CORE_MPLAYER
        player_type = xbmc.PLAYER_CORE_AUTO
        
        self.player = xbmc.Player(player_type)
        self._log("start [" + ":".join(self.feed_name) + "]")
        self._log(self.show_allways)
        
    def _log(self, text):
        xbmc.log ('%d service.maxxam.teamwatch: %s' % (self.log_prog, text))
        self.log_prog = self.log_prog + 1
        
    def loop(self):
        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(REFRESH_TIME_SECS):
                self.hide_message()
                self._log("stop")
                break
            
            # after DISPLAY_TIME_SECS elapsed hide the message bar
            if self.feed_is_shown and time.time() - self.feed_show_time > DISPLAY_TIME_SECS:
                self.hide_message()
                
                if self.show_disable_after:
                    self.hide_message()
                    self.show_enable = False
                    self.show_disable_after = False

            if (time.time() - self.start_time) < REFRESH_TIME_SECS or self.feed_is_shown:
                continue
            
            self.start_time = time.time()
            
            jresult = self.get_feed(SOCKET_TIMEOUT)
            if jresult['status'] != 'fail' and DEBUG: self._log(str(jresult))
            
            if jresult['status'] == 'ok' and  self.show_enable:
                user = jresult['user'].encode('utf-8')
                text = jresult['text'].encode('utf-8')
                
                if self.show_allways or xbmcgui.getCurrentWindowId() == WINDOW_FULLSCREEN_VIDEO:
                    if DEBUG > 1:
                        self.show_message(user, text, [ICON_CHAT, ICON_TWITTER][jresult['is_twitter']], jresult['id'])
                    else:
                        self.show_message(user, text, [ICON_CHAT, ICON_TWITTER][jresult['is_twitter']])
                    
                if jresult['is_twitter']:
                    self.id_twitter = jresult['id']
                else:
                    self.id_chat = jresult['id']
            elif jresult['status'] == 'settings':
                param = jresult['param'].encode('utf-8')
                
                if param.startswith("#tw:addfeed:"):
                    if not param[12:] in self.feed_name: 
                        self.feed_name.append(param[12:])
                        self.__addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32000, param[12:]), ICON_SETTING)
                    self.id_chat = jresult['id']
                elif param.startswith("#tw:removefeed:"):
                    if param[15:] in self.feed_name: 
                        self.feed_name.remove(param[15:])
                        self.__addon__.setSetting('feed', ":".join(self.feed_name))
                        self.show_message('TeamWatch', localize(32001, param[15:]), ICON_SETTING)
                    self.id_chat = jresult['id']
                elif param == "#tw:off":
                    self.show_message('TeamWatch', localize(32002), ICON_SETTING)
                    self.show_disable_after = True
                    self.id_chat = jresult['id']
                elif param == "#tw:on":
                    self.show_enable = True
                    self.show_message('TeamWatch', localize(32003), ICON_SETTING)
                    self.id_chat = jresult['id']
                elif param == "#tw:id":
                    self.id_chat = jresult['idc']
                    self.id_twitter = jresult['idt']
                elif param == "#tw:playerctl:playpause":
                    xbmc.executebuiltin("Action(PlayPause)")
                    self.id_chat = jresult['id']
                elif param == "#tw:playerctl:sshot":
                    xbmc.executebuiltin("TakeScreenshot")
                    self.id_chat = jresult['id']
                elif param.startswith("#tw:playerctl:seek:"):
                    t = [int("0"+filter(str.isdigit, x)) for x in param[19:].split(":")]
                    if len(t) == 4:
                        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Seek", "params": {"playerid":1, "value": {"hours":%d, "minutes":%d, "seconds":%d, "milliseconds":%d}}, "id": 1 }' % tuple(t))
                    elif DEBUG:
                        self._log('#tw:playerctl:seek invalid time')
                        
                    self.id_chat = jresult['id']
                elif param.startswith("#tw:playstream:"):
                    self._log('*** playstream received ***')
                    self._log(param[15:])
                    
                    url = param[15:]
                    
                    if "&#tw_title#=" in url:
                        pos = url.find("&#tw_title#=")
                        title = url[pos + len("&#tw_title#="):]
                        url = url[:pos]

                        if "&#tw_poster#=" in title:
                            pos = title.find("&#tw_poster#=")
                            thumb = title[pos + len("&#tw_poster#="):]
                            title = title[:pos]
                        else:
                            thumb = ""
                            
                        title = urllib.unquote(urllib.unquote(title)).replace('+',' ')
                        thumb = urllib.unquote(urllib.unquote(thumb)).replace('+',' ')
                    else:
                        title = "[TeamWatch] %s" % url
                        thumb = ""
                            
                    video_url = '';
                    
                    self._log('Title     : %s' % title)
                    self._log('Poster    : %s' % thumb)
                    self._log('Url       : %s' % url)
                    
                    if 'abysstream' in url or 'akstream' in url:
                        self._log("abysstream scrape: %s" % url)
                        
                        from scrapers.abysstream import get_video_url
                        status, result = get_video_url(url)
                        
                        if status:
                            video_url = result
                        else:
                            scraper_error = '[abysstream] ' + result
                            self._log("abysstream scraper result: %s" % result)
                    elif 'backin' in url:
                        self._log("backin scrape: %s" % url)
                        
                        from scrapers.backin import get_video_url
                        status, result = get_video_url(url)
                        
                        if status:
                            video_url = result
                        else:
                            scraper_error = '[backin] ' + result
                            self._log("backin scraper result: %s" % result)
                    elif 'speedvideo' in url:
                        self._log("speedvideo scrape: %s" % url)
                        
                        from scrapers.speedvideo import get_video_url
                        status, result = get_video_url(url)
                        
                        if status:
                            video_url = result
                        else:
                            scraper_error = '[speedvideo] ' + result
                            self._log("speedvideo scraper result: %s" % result)
                    elif 'nowvideo' in url:
                        self._log("nowvideo scrape: %s" % url)
                        
                        from scrapers.nowvideo import get_video_url
                        status, result = get_video_url(url)
                        
                        if status:
                            video_url = result
                        else:
                            scraper_error = '[nowvideo] ' + result
                            self._log("nowvideo scraper result: %s" % result)
                    elif 'megahd' in url:
                        self._log("megahd scrape: %s" % url)
                        
                        from scrapers.megahd import get_video_url
                        status, result = get_video_url(url)
                        
                        if status:
                            video_url = result
                        else:
                            scraper_error = '[megahd] ' + result
                            self._log("megahd scraper result: %s" % result)
                    elif 'fastvideo' in url:
                        self._log("fastvideo scrape: %s" % url)
                        
                        from scrapers.fastvideo import get_video_url
                        status, result = get_video_url(url)
                        
                        if status:
                            video_url = result
                        else:
                            scraper_error = '[fastvideo] ' + result
                            self._log("fastvideo scraper result: %s" % result)
                
                    if video_url == '': ### no video_url from scrapers try youtube_dl
                        try:
                            sys.path.append('/usr/local/lib/python2.7/dist-packages/')
                            import youtube_dl
                        except:
                            self._log('youtube_dl import error')

                        if youtube_dl:
                            self._log("youtube_dl scrape: %s" % url)
                            
                            old_stdout = sys.stdout
                            old_stderr = sys.stderr

                            redirected_output = sys.stdout = StringIO()
                            redirected_error = sys.stderr = StringIO()
                            
                            try:
                                ydl = youtube_dl.YoutubeDL({'ignoreerrors': True, 'no_color': True})
                            except:
                                self._log('youtube_dl error creating object')

                            if ydl:
                                try:
                                    result = ydl.extract_info(url, download=False)
                                    
                                    if 'url' in result:
                                        video_url = result['url']
                                    else:
                                        self._log('youtube_dl: no url in result')
                                        scraper_error = '[youtube_dl] no url in result'
                                        video_url = url
                                except:
                                    scraper_error = '[youtube_dl] ' + redirected_error.getvalue()
                                    self._log('youtube_dl error: ' + redirected_error.getvalue())
                                    self._log('youtube_dl output: ' + redirected_output.getvalue())
                                    
                    # tutti i campi che si possono mettere nella listitem
                    # http://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem
                    
                    listitem = xbmcgui.ListItem(title, thumbnailImage=thumb, path=video_url)
                    listitem.setInfo('video', {'Title': title})
                    
                    if video_url:
                        self.player.play(video_url, listitem, False)
                    elif scraper_error:
                        dialog = xbmcgui.Dialog()
                        dialog.notification('TeamViewer', 'Scrape error: %s.' % scraper_error, xbmcgui.NOTIFICATION_ERROR, 5000)
                        self._log('Scrape error: %s.' % scraper_error)
                    else:        
                        self._log('No scraper found... trying to play url')
                        self.player.play(url, listitem, False)
                        
                    self.id_chat = jresult['id']
                elif param.startswith("#tw:invite:"):
                    if DEBUG: self._log("#tw:invite")
                    invite = param[11:].split(":")
                    
                    if invite[1] == "m":
                        movie = xbmc_helpers.search_movie(invite[2])
                        
                        if movie:
                            dialog = xbmcgui.Dialog()
                            res = dialog.yesno(localize(32004), localize(32005, (invite[0], movie["title"])))
                            if DEBUG: self._log("invite received for movie id: %d" % movie["movieid"])
                        else:
                            if DEBUG: self._log("invite received for non existent movie %s" % invite[2])
                            
                    elif invite[1] == "e":
                        episode = xbmc_helpers.search_episode(invite[2], invite[3], invite[4])
                        
                        if episode:
                            dialog = xbmcgui.Dialog()
                            s_ep = "S[COLOR green][B]%02d[/B][/COLOR]E[COLOR green][B]%02d[/B][/COLOR]" % (int(episode["season"]), int(episode["episode"]))
                            res = dialog.yesno(localize(32004), localize(32006, (invite[0], episode["showtitle"], s_ep)))
                            if DEBUG: self._log("invite received for movie id: %d" % episode["episodeid"])
                        else:
                            if DEBUG: self._log("invite received for non existent episode %s %s %s" % (invite[2], invite[3], invite[4]))
                    else:
                        pass
                        
                    self.id_chat = jresult['id']
                else:
                    if 'id' in jresult:
                        self.id_chat = jresult['id']
                    else:
                        self.id_chat = self.id_chat + 1
            else:
                if DEBUG and jresult['status'] == "fail" and jresult['reason'] not in ["no feeds", "recv timeout"] and not jresult['reason'].startswith('waiting'): 
                    self._log(jresult)
                    
                if DEBUG and jresult['reason'].startswith('json parse error'):
                    self._log(jresult)
                    self.id_twitter = -1
                    self.id_chat = -1
                    
                
    def get_feed(self, timeout=0.5):
        start = time.time()
        
        params = {'idt':self.id_twitter, 'idc':self.id_chat, 'twid':self.id_teamwatch, 'pcid':self.id_playerctl}
        if self.feed_name: 
            params['q'] = ":".join(self.feed_name)
        else:
            params['q'] = "#teamwatch"
            
        if self.twitter_enabled:
            params['tqp'] = "&lang=%s&result_type=%s" % (self.twitter_language, self.twitter_result_type)
            params['tl'] = self.twitter_language
        else:
            params['notweet'] = 1
            
        server = SERVER
        args = '/teamwatch/get.php?%s' % urllib.urlencode(params)
        
        if DEBUG > 1: self._log(args)
        
        returndata = str()
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        
        try:
            s.connect((server, 80)) #lets connect :p
        except:
            s.close()
            if DEBUG > 1: self._log('elapsed time: %.2f' % (time.time()-start))
            return {"status":"fail", "reason":"connect timeout"}
 
        s.send("GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (args, server)) #simple http request
        while 1:
            try:
                data = s.recv(1024) #buffer
            except:
                s.close()
                if DEBUG > 1: self._log('elapsed time: %.2f' % (time.time()-start))
                return {"status":"fail", "reason":"recv timeout"}
                
            if not data: break
            returndata = returndata + data
            
        s.close()
        if returndata:
            tmp = returndata.split("\n\r")[1].replace('\r','').replace('\n','').replace('\\','\\\\')
            if DEBUG > 1:
                self._log('returndata: ' + tmp)
                self._log('elapsed time: %.2f' % (time.time()-start))
            
            try:
                return json.loads(tmp)
            except:
                return {'status':'fail', 'reason':'json parse error (%s)' % args, 'json':'%s' % tmp}
        else:
            return {'status':'fail', 'reason':'result is empty ' + args}
        
    def show_message (self, user, text, icon = ICON_CHAT, id=-1):
        if DEBUG: self._log(user + " " + text)
        
        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        self.window.addControls([self.background, self.feedtext])
        
        if icon == ICON_TWITTER:
            self.background.setImage(os.path.join(self.__resources__, '1280_tweet.png'))
        elif icon == ICON_SETTING:
            self.background.setImage(os.path.join(self.__resources__, '1280_settings.png'))
        elif icon == ICON_CHAT:
            self.background.setImage(os.path.join(self.__resources__, '1280_chat.png'))
        else:
            self.background.setImage(os.path.join(self.__resources__, '1280_chat.png'))
            
        if id!=-1:
            self.feedtext.setLabel('[COLOR yellow][B]%s[/B][/COLOR]: [%d] %s' % (user, id, text))
        else:
            self.feedtext.setLabel('[COLOR yellow][B]%s[/B][/COLOR]: %s' % (user, text))
        
        self.feed_is_shown = True
        self.feed_show_time = time.time()
    
    def hide_message(self):
        if self.feed_is_shown:
            self.window.removeControls([self.background, self.feedtext])
            self.feed_is_shown = False
    
if __name__ == '__main__':
    tw = TeamWatch()
    tw.loop()
