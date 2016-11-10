import re
import cfscrape

def get_video_url(url, DEBUG=0):
    scraper = cfscrape.create_scraper()
    response = scraper.get(url)

    try:
        stepkey = re.search (r'name="stepkey" value="([^"]+)"', response.content).group(1)
    except:
        return False, "Stepkey not found."
        
    data = {
        'stepkey': stepkey, 
        'submit': 'submit' 
    }

    scraper.headers['Referer'] = url
    response = scraper.post(url, data=data)
    
    url = ''
    try:
        url = re.search(r'<source\s+src="([^"]+)"\s+type=.*?video', response.content).group(1)
    except:
        return False, "Source not found."
    
    return True, url
    
if __name__ == '__main__':
    import sys

    try:
        url = sys.argv[1]
    except:
        print "Please pass url in command line."
        sys.exit()
        
    print get_video_url(url, 1)
