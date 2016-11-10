import re
import cfscrape

def get_video_url(url, DEBUG=0):
    scraper = cfscrape.create_scraper()
    response = scraper.get(url)

    if response.ok:
        html = response.content

        data = {}
        m = re.search('<input type="hidden" name="streamLink" value="([^"]+)">', html)
        if m: 
            data['streamLink'] = m.group(1)
        else:
            if DEBUG: 
                print "streamLink not found."
                if DEBUG > 1: print html
            
        m = re.search('<input type="hidden" name="templink" value="([^"]+)">', html)
        if m: 
            data['templink'] = m.group(1)
        else:
            if DEBUG: 
                print "templink not found."
                if DEBUG > 1: print html

        if data:
            domain = re.search(r'http://([^/]+)/', url)
            
            scraper.headers['Referer'] = url
            response = scraper.post('http://%s/viewvideo.php' % domain.group(1), data = data)
        else:
            return False, "No streamLink and no templink found."
            
        html = response.content
        m = re.search('<source src="([^"]+)" type="video/[^"]+"', html)
        if m:
            return True, m.group(1)
        else:
            if DEBUG: print html
            return False, "Video not found."
            
if __name__ == '__main__':
    import sys

    try:
        url = sys.argv[1]
    except:
        url = 'http://abysstream.com/video/bvawcff4nckk'
        
    print get_video_url(url, 1)