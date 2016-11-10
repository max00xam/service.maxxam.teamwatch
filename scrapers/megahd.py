import re
from cfscrape import js2py
import cfscrape

def get_video_url(url, DEBUG=0):
    scraper = cfscrape.create_scraper()
    response = scraper.get(url)

    if 'p,a,c,k,e,d' in response.content:
        try:
            packed = re.search(r'<script[^>]+>eval\((function\(p,a,c,k,e,d\).*\)\))\).*?<\/script>', response.content, re.S).group(1)
        except:
            packed = None
            return False, "Packed regex error"

        if packed:
            import jsbeautifier.unpackers.packer as packer
            jwconfig = packer.unpack(packed)
            
            url = re.search('file:"([^"]+)"', jwconfig).group(1)
            
            return True, url
    else:
        return False, "Packed not found"
    
if __name__ == '__main__':
    import sys

    try:
        url = sys.argv[1]
    except:
        print "Please pass url in command line."
        sys.exit()
        
    print get_video_url(url, 1)