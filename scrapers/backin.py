import re
import js2py
import cfscrape

def get_video_url(url, DEBUG=0):
    scraper = cfscrape.create_scraper()
    response = scraper.get('http://backin.net/s/streams.php?s=bvawcff4nckk')

    if 'generating' in response.content:
        response = scraper.get('http://backin.net/s/generating.php?code=bvawcff4nckk')
        if 'p,a,c,k,e,d' in response.content:
            try:
                packed = re.search(r'<script[^>]+>(eval\(function\(p,a,c,k,e,d\).*)</script>', response.content, re.S).group(1)
            except:
                return False, "Packed regex error"
                
            jwconfig = js2py.eval_js(packed.replace('eval', 'a='))
            
            url = ''
            try:
                url = re.search('file:"([^"]+)"', jwconfig).group(1)
            except:
                return False, "Url not found in jwconfig."
                if DEBUG: print jwconfig
                
            return True, url
    else:
        return False, "Generating link not found"
    
if __name__ == '__main__':
    import sys

    try:
        url = sys.argv[1]
    except:
        print "Please pass url in command line."
        sys.exit()
        
    print get_video_url(url, 1)