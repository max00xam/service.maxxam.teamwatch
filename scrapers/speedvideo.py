import re
import base64
import cfscrape

def get_video_url(url, DEBUG=0):
    scraper = cfscrape.create_scraper()
    response = scraper.get(url)

    data = {
        'op': 'download1', 
        'usr_login': '', 
        'id': '', 
        'fname': '', 
        'referer': '', 
        'hash': '',
        'imhuman': ''
    }

    txtout = ''
    for field in ['hash', 'id', 'fname', 'imhuman']:
        try:
            data[field] = re.search('name="%s" value="([^<]+)"' % field, response.content).group(1)
        except:
            txtout += "%s not found. " % field

    response = scraper.post(url, data=data)
    m = re.search(r'var\s+([a-z]+)\s*=\s*([0-9]+)\s*;.*?linkfile.*="([^"]+)".*linkfile,\s*\1', response.content, re.S)
    if m:
        n = int(m.group(2))
        linkfile = m.group(3)
        
        link = linkfile[0:n] + linkfile[n + 10:]
        return True, base64.b64decode(link)
    else:
        return False, "linkfile not found (%s)." % txtout
    
if __name__ == '__main__':
    import sys

    try:
        url = sys.argv[1]
    except:
        print "Please pass url in command line."
        sys.exit()
        
    print get_video_url(url, 1)
