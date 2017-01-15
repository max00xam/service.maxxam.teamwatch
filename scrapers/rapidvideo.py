import re
import js2py
import cfscrape

def regex(regex, data, falgs=None):
    m = re.search(regex, data)
    if m:
        return m.group(1)
    else:
        return None
        
def get_video_url(url, DEBUG=0):
    url_regex = '^https{0,1}://(?:www\.){0,1}rapidvideo\.org/([^/]+).*$'
    # url_regex = '^http://(?:www\.)?rapidvideo\.org/([^/]+).*$'
    m = re.match(url_regex, url)
    if m: 
        url = 'http://www.rapidvideo.org/%s' % m.group(1)
    else:
        return False, "Invalid url: %s" % url
    
    scraper = cfscrape.create_scraper()
    response = scraper.get(url)

    if response.ok:
        html = response.content
        
        if "File Not Found" in html: return False, "File Not Found"
            
        form = ''
        for m in re.findall(r'<form.*?(http://[^\'"]+)[\'"].*?>(.*?)</form.*?>', html, re.I + re.S):
            if m[0] == url: 
                form = m[1]
                break;
        
        if not form: 
            print html
            return (False, "Form not found")
        
        out = ''
        data = {}
        for name in ['op', 'usr_login', 'id', 'fname', 'referer', 'hash', 'imhuman']:
            tmp = regex('<input.*?(?:(?:name\s*=\s*[\'"]%s[\'"].*?value\s*=\s*[\'"]([^\'"]*)[\'"])|(?:value\s*=\s*[\'"]([^\'"]*)[\'"].*?name\s*=\s*[\'"]%s[\'"])).*?>' % (name, name), form, re.I)
            if tmp == None:
                out += "input name = \"%s\" not found." % name
            else:
                data[name] = tmp
                
        scraper.headers['Referer'] = url
        response = scraper.post(url, data = data)

        if 'p,a,c,k,e,d' in response.content:
            try:
                packed = re.search(r'<script[^>]+>(eval\(function\(p,a,c,k,e,d\).*?)</script>', response.content, re.S).group(1)
            except:
                return False, "Packed regex error"
            
            try:
                jwconfig = js2py.eval_js(packed.replace('eval', 'a='))
            except:
                return False, "Error in eval_js"
            
            url = ''
            try:
                url = re.search('file:"([^"]+)"', jwconfig).group(1)
            except:
                return False, "Url not found in jwconfig."
                if DEBUG: print jwconfig
                
            return True, url
        else:
            return False, "packed not found " + out
    else:
        return False, "Error scraper.get %s" % url

if __name__ == '__main__':
    import sys

    try:
        url = sys.argv[1]
    except:
        url = 'http://www.rapidvideo.org/yy0h6cxq66l6'
        
    print get_video_url(url, 1)