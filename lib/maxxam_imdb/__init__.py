# coding: utf-8

import re
import urllib2
import urllib
import HTMLParser

def _request(url):
    headers = {'User-Agent': "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3"}
    headers = {'User-Agent': "Mozilla/4.0 (compatible;MSIE 6.0;Windows NT 5.1;SV1;.NET CLR 1.1.4322;.NET CLR 2.0.50727;.NET CLR 3.0.04506.30)"}

    req = urllib2.Request(url)
    req.add_header('User-Agent', headers['User-Agent'])
    response = urllib2.urlopen(req)
    html = response.read()
    response.close()

    return html


def unescape(text):
    if (sys.version_info[0] < 3):
        parser = HTMLParser.HTMLParser()
    else:
        parser = html.parser.HTMLParser()
    return (parser.unescape(text))

def _translate(r_text, to_language="it", from_language="en"):
    text = urllib.quote_plus(r_text)
    link = "http://translate.google.com/m?hl={}&sl={}&q={}".format(to_language, from_language, text)

    try:
        html = _request(link).decode("utf-8")
    except:
        return text

    res = re.findall(r'class="t0">(.*?)<', html)
    if len(res):
        return HTMLParser.HTMLParser().unescape(res[0])
    else:
        return r_text

def _kodiJson(movie):
    movie_json = {'Title': movie['title'].replace(' - IMDb','')}

    if 'genres' in movie: movie_json['Genre'] = movie['genres']
    if 'description' in movie:
        movie_json['Plot'] = movie['storyline']  # summary_text
        movie_json['PlotOutline'] = movie['description']
    if 'cast' in movie: movie_json['Cast'] = movie['cast']

    return movie_json

def search(title, translate='it'):
    imdb = 'https://www.imdb.com/find?q={}&s=all'.format('+'.join(title.split()))

    try:
        html = _request(imdb)
    except:
        return {'error': 'error opening imdb find title url.', 'imdb': imdb}

    regex = r"result_text.*?(?P<imdb_id>tt[0-9]+)[^>]+>(?P<title>[^<]+)<\/a>\s+(?P<year>\([0-9]+\))"
    search = re.findall(regex, html, re.MULTILINE | re.DOTALL)

    if len(search):
        return get(search[0][0], translate)
    else:
        return {'error': 'movie title not found.', 'imdb': imdb}

def get(imdb_id, translate='it'):
    imdb = 'https://www.imdb.com/title/{}/'.format(imdb_id)

    try:
        html = _request(imdb)
    except:
        return {'error': 'error opening imdb title url.', 'imdb': imdb}

    result = {}
    search = re.search('og:title[\'"].*?[\'"](.*?)[\'"]', html, re.MULTILINE | re.DOTALL)
    if search: result['title'] = search.group(1).strip()

    search = re.search('og:description[\'"].*?[\'"](.*?)[\'"]', html, re.MULTILINE | re.DOTALL)
    if search: result['description'] = search.group(1).strip()

    search = re.search("summary_text\">([^<]+?)<", html, re.MULTILINE | re.DOTALL)
    if search: result['summary_text'] = search.group(1).strip()

    search = re.search("Storyline.*?<span>(.*?)<\/span", html, re.MULTILINE | re.DOTALL)
    if search: result['storyline'] = search.group(1).strip()

    search = re.search("Stars.*?fullcredits", html, re.MULTILINE | re.DOTALL)
    if search:
        matches = re.finditer("<a.*?>([^<]+)<\/a>", search.group(), re.MULTILINE | re.DOTALL)
        result['cast'] = [m.group(1) for m in matches]

    search = re.search('[\'"]genre[\'"]:\s+\[([^\]]+)\]', html, re.MULTILINE | re.DOTALL)
    if search:
        genres = search.group(1).strip()
        result['genres'] = [x.strip() for x in genres.replace('\n','').replace('\r','').replace('"','').split(',')]

    search = re.search('[\'"]image[\'"]:\s+[\'"](.*?)[\'"]', html, re.MULTILINE | re.DOTALL)
    if search: result['image_url'] = search.group(1).strip()

    if translate:
        if 'description' in result.keys():
            result['description'] = _translate(result['description'], translate)

        if 'summary_text' in result.keys():
            result['summary_text'] = _translate(result['summary_text'], translate)

        if 'storyline' in result.keys():
            result['storyline'] = _translate(result['storyline'], translate)

        if 'genres' in result.keys():
            result['genres'] = [_translate(x, translate) for x in result['genres']]

    return result

if __name__ == '__main__':
    print search('the bourne identity')
