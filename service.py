# -*- coding: utf-8 -*-
from cStringIO import StringIO
import re
import os
import time
import socket
import urllib
import urllib2
import urlparse
import httplib
import json
import base64
import xbmc
import xbmcgui
import xbmcaddon

from tools.xbmc_helpers import localize
from tools import xbmc_helpers

DEBUG = 1
SERVER = "maxxam.tk"
WINDOW_FULLSCREEN_VIDEO = 12005
DISPLAY_TIME_SECS = 5
REFRESH_TIME_SECS = 2
SOCKET_TIMEOUT = 2.0

ICON_CHAT = 1
ICON_TWITTER = 2
ICON_SETTING = 3

class YtdlLogger(object):
    def debug(self, msg):
        xbmc.log ('youtube_dl D %s' % msg)

    def warning(self, msg):
        xbmc.log ('youtube_dl W %s' % msg)

    def error(self, msg):
        xbmc.log ('youtube_dl E %s' % msg)

class myPlayer(xbmc.Player):
    _totalTime = 0
    _lastPos = 0
    
    def __init__(self, player_type):
        xbmc.Player.__init__(self, player_type)
        self._totalTime = 0
        self._lastPos = 0
        
    def setLastPos(self):
        self._lastPos = self.getTime()
        
    def onPlayBackStarted(self):
        self._totalTime = self.getTotalTime()
        xbmc.log ('service.maxxam.teamwatch: onPlayBackStarted')
        
    def onPlayBackEnded(self):
        xbmc.log ('service.maxxam.teamwatch: onPlayBackEnded [%d:%d]' % (self._lastPos, self._totalTime))
        
        playedTime = int(self._lastPos)
        if self._totalTime == 0 or (playedTime == 0 and self._totalTime == 999999):
            dialog = xbmcgui.Dialog()
            dialog.notification('TeamViewer', 'Playback error.', xbmcgui.NOTIFICATION_ERROR, 5000)

    def onPlayBackStopped(self):
        xbmc.log ('service.maxxam.teamwatch: onPlayBackStopped [%d:%d]' % (self._lastPos, self._totalTime))

        playedTime = int(self._lastPos)
        if self._totalTime == 0 or (playedTime == 0 and self._totalTime == 999999):
            dialog = xbmcgui.Dialog()
            dialog.notification('TeamViewer', 'Playback error.', xbmcgui.NOTIFICATION_ERROR, 5000)
        
class TeamWatch():
    __addon__ = xbmcaddon.Addon()
    __resources__ = os.path.join(__addon__.getAddonInfo('path'),'resources')

    monitor = None

    window = None
    background = None
    feedtext = None
    
    __version__ = __addon__.getAddonInfo('version')
    
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
    playing_url = None
    
    log_prog = 1
    
    def __init__(self):
        self.monitor = xbmc.Monitor()
        
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
        
        self.title = ""
        self.thumb = ""
        self.format = -1
        
        self._log("start [" + ":".join(self.feed_name) + "]")
        self._log("Show allways: " + ["no", "yes"][self.show_allways])
        
    def _log(self, text):
        xbmc.log ('%d service.maxxam.teamwatch: %s' % (self.log_prog, text))
        self.log_prog = self.log_prog + 1
        
    def loop(self):
        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(REFRESH_TIME_SECS):
                self._log("stop")
                
                self.hide_message()
                
                # del self.background
                # del self.feedtext
                del self.monitor
                # del self.player

                break
                
            """    
            if self.player and self.player.isPlaying():
                self.player.setLastPos()
            else:
                self.playing_url = ''
                self.title = ""
                self.thumb = ""
                if self.player: del self.player
            """
            
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
            
            if "version" in jresult and jresult.get('version') != self.__version__:
                self._log('installed version %s differ from server version %s' % (self.__version__, jresult.get('version')))
                
                try:
                    a = int(jresult.get('version').replace('.', '')) 
                except:
                    a=0
                    
                b = int(self.__version__.replace('.', ''))
                if a > b: 
                    self._log('UpdateLocalAddons')
                    xbmc.executebuiltin('UpdateAddonRepos')
                    xbmc.executebuiltin('UpdateLocalAddons')
                    
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
                elif param == "#tw:savestrm":
                    """
                    if self.player and self.player.isPlaying() and self.title:
                        self._log('#tw:savestrm saving: %s' % self.title)
                        
                        path = os.path.join(xbmc.translatePath("special://profile/addon_data/service.maxxam.teamwatch"), 'Movies')
                        if not os.path.isdir(path):
                            os.makedirs(path)
                            
                        fout = open(os.path.join(path, self.title + '.strm'), 'w')
                        fout.write("%s\n" % self.playing_url)
                        fout.close
                        
                        #fout = open(os.path.join(path, self.title + '.nfo'), 'w')
                        #fout.write('<movie>\n')
                        #fout.write('<title>%s</title>\n' % self.title)
                        #fout.write('</movie>\n')
                        #fout.close
                    else:
                        self._log('#tw:savestrm not playing')
                    """    
                    self.id_chat = jresult['id']
                elif param.startswith("#tw:playstream:"):
                    self._log('*** playstream received ***')
                    self._log(param[15:])
                    
                    url = param[15:]
                    no_scrape = 0
                    
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
                            
                        if "&#tw_format#=" in thumb:
                            pos = thumb.find("&#tw_format#=")
                            format = thumb[pos + len("&#tw_format#="):]
                            thumb = thumb[:pos]
                        else:
                            format = ''
                            
                        self.title = urllib.unquote(urllib.unquote(title)).replace('+',' ')
                        self.thumb = urllib.unquote(urllib.unquote(thumb)).replace('+',' ')
                        if format.isdigit():
                            self.format = int(format)
                        else:
                            self.format = -1
                    elif url.startswith("tw_url"):
                        qs = urlparse.parse_qs(param[15:])
                        if 'tw_url' in qs:
                            url = base64.b64decode(qs['tw_url'][0])
                            
                        if 'tw_title' in qs:
                            try:
                               self.title = base64.b64decode(qs['tw_title'][0])
                            except:
                               self.title = qs['tw_title'][0]
                        if 'tw_poster' in qs:
                            self.thumb = base64.b64decode(qs['tw_poster'][0])
                            
                        if 'tw_format' in qs and qs['tw_format'][0].isdigit():
                            self.format = int(qs['tw_format'][0])
                        else:
                            self.format = -1
                            
                        if 'tw_noscrape' in qs and qs['tw_noscrape'][0] == '1':
                            no_scrape = 1
                        else:
                            no_scrape = 0
                    else:
                        self.title = url
                        self.thumb = ""
                        self.format = -1

                    video_url = '';
                    
                    self._log('Title     : %s' % self.title)
                    self._log('Poster    : %s' % self.thumb)
                    self._log('Url       : %s' % url)
                    self._log('Format    : %d' % self.format)
                    
                    scraper_error = None
                    if no_scrape:
                        self._log("no scrape: %s" % url)
                        video_url = url
                    elif 'rapidvideo' in url:
                        self._log("rapidvideo scrape: %s" % url)
                        
                        from scrapers.rapidvideo import get_video_url
                        status, result = get_video_url(url)
                        
                        if status:
                            video_url = result
                        else:
                            scraper_error = '[rapidvideo] ' + result
                            self._log("rapidvideo scraper result: %s" % result)
                    elif 'abysstream' in url or 'akstream' in url:
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
                
                    if video_url == '':
                        try:
                            sys.path.append('/usr/local/lib/python2.7/dist-packages/')
                            import youtube_dl
                        except:
                            self._log('youtube_dl import error')

                        if youtube_dl:
                            self._log("youtube_dl scrape: %s" % url)
                            
                            ydl_opts = {
                                'ignoreerrors': True, 
                                'no_color': True,
                                'skip_download': True,
                                'verbose': True,
                                'logger': YtdlLogger()
                            }
                            
                            if self.format:
                                ydl_opts['format'] = 'bestaudio/best'

                            try:
                                ydl = youtube_dl.YoutubeDL(ydl_opts)
                            except:
                                self._log('youtube_dl error creating object')

                            if ydl:
                                self._log('youtube_dl extract_info %s' % url)
                                try:
                                    result = ydl.extract_info(url, download=False)
                                    
                                    if result:
                                        if self.format:
                                            for fmt in result['formats']:
                                                if int(fmt['format_id']) == self.format:
                                                    video_url = fmt['url']
                                                    break
                                                    
                                            if not video_url:
                                                self._log('youtube_dl: format not found %d' % self.format)
                                                video_url = fmt['url']
                                        else:
                                            if 'url' in result:
                                                video_url = result['url']
                                            elif 'formats' in result:
                                                video_url = result['formats'][-1]['url']
                                            else:
                                                self._log('youtube_dl: no url in result')
                                                scraper_error = '[youtube_dl] no url in result'
                                    else:
                                        self._log('youtube_dl: result is none')
                                        scraper_error = '[youtube_dl] result is none'
                                except:
                                    scraper_error = '[youtube_dl] scraper error'
                                
                    # tutti i campi che si possono mettere nella listitem
                    # http://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem
                    
                    listitem = xbmcgui.ListItem("[TeamWatch] %s" % self.title, thumbnailImage=self.thumb, path=video_url)
                    listitem.setInfo('video', {'Title': "[TeamWatch] %s" % self.title})
                    player = myPlayer(xbmc.PLAYER_CORE_AUTO)
                    
                    if video_url:
                        # player_type = xbmc.PLAYER_CORE_AUTO
                        # self.player = myPlayer(player_type)
                        # self.player.play(video_url, listitem, False)
                        # self.playing_url = video_url
                        
                        # xbmc.executebuiltin('playmedia(%s)' % video_url)
                        player.play(video_url, listitem=listitem)
                    elif scraper_error:
                        # dialog = xbmcgui.Dialog()
                        # dialog.notification('TeamViewer', 'Scrape error: %s.' % scraper_error, xbmcgui.NOTIFICATION_ERROR, 5000)
                        self._log('Scrape error: %s.' % scraper_error)
                        self._log('trying to play url')
                        
                        # xbmc.executebuiltin('playmedia(%s)' % url)
                        player.play(url, listitem=listitem)
                    else:        
                        # self.playing_url = url
                        # self.player.play(url, listitem, False)
                        self._log('No scraper found... trying to play url')
                        
                        # xbmc.executebuiltin('playmedia(%s)' % url)
                        player.play(url, listitem=listitem)
                        
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
                if DEBUG > 1:
                    self._log(jresult)
                elif DEBUG == 1:
                    if jresult['status'] == "fail" and jresult['reason'] not in ["no feeds", "recv timeout", "connect timeout"] and not jresult['reason'].startswith('waiting'): 
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
