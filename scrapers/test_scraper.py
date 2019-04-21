from maxxam_scraper import scrape
import sys

if len(sys.argv) > 1:
    for url in sys.argv[1:]:
        print ("===================================================================================")
        print (scrape(url))
        print ("===================================================================================")
else:
    urls = [
        'https://streamango.com/f/acepaknpacbrntkk/Justice_League_-_Il_Trono_di_Atlantide_HD_2015_Bluray_1080p_mp4', 
        'https://wstream.video/video/thmr6kd1s77v', 
        'https://akvideo.stream/video/dorslg415apl', 
        'http://backin.net/3k7q2oti0hk2', 
        'https://oload.site/f/a9eTGowlkAQ/']

    for url in urls:
        print ("===================================================================================")
        print (scrape(url))
        print ("===================================================================================")
