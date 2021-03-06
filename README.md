service.maxxam.teamwatch
========================

[Leggilo in italiano](README-IT.md)

TeamWatch is a Kodi add-on that will change the way you watch TV,
TV becomes 'social' allowing you to comment live with friends
what you see on the screen. TeamWatch also gives you the opportunity to
display on the TV screen tweets regarding the program you are watching!

Configuration options
---------------------

- **Feed**: feeds you want to follow separated by colon.
- **TeamWatch ID**: identifies your addon, allowing you to send commands to it via the web page. (you should keep this secret)
- **Player control ID**: allows to send commands (play, pause, seek) to the player of all the addons that share the some id.

Send message and manage
-----------------------

You can send message and commands throught the web page at www.teamwatch.it

Commands
--------

``#tw:off`` - stop displaying messages

``#tw:on`` - restart displaying messages

``#tw:playerctl:sshot`` - take a screenshot

``#tw:bar:top`` - the bar will be displayed in the top of the screen

``#tw:bar:bottom`` - the bar will be displayed in the bottom of the screen

``#tw[pc]:addfeed:<feed>`` - add a new feed to follow
  
``#tw[pc]:removefeed:<feed>`` - remove a feed from your followed feeds
  
``#tw[pc]:playerctl:playpause`` - pause/resume the current playing video

``#tw[pc]:playerctl:stop`` - stop the current playing video

``#tw[pc]:rss:[on|off]`` - enable/disable rss feeds

``#tw[pc]:tweet:[on|off]`` - enable/disable twitter feeds

``#tw[pc]:playerctl:seek:<hh>:<mm>:<ss>:<cent>`` - seek the current video to the time hh:mm:ss:cent
  
``#tw[pc]:playstream:<url>[&m_title=<title>`` - start playing video stream from url 

**url** can be to 'open stream' or to wstream, backin, akvideo, openload, verystream, streamango

``#tw[pc]:playstream:<site>#<title>[#<streaming-site>, ...]`` - search title and start playing

**site** can be 'cb01' (italian language site) or 'olm' (english language site openload dot org)

**title** is a series of search words separated by spaces or plus sign (like 'hunger+games')

**stream-site** (optional) is one ore more of wstream, backin, akvideo, openload, verystream, streamango

If the command is used with "``#twpc:``" instead of "``#tw:``" it will be sent to all the users sharing the some "Player control ID" with you.
