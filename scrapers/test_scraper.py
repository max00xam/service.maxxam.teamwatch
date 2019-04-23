import maxxam_scraper as scraper
import sys, urllib

"""
soup.select('div')
All elements named <div>

soup.select('#author')
The element with an id attribute of author

soup.select('.notice')
All elements that use a CSS class attribute named notice

soup.select('div span')
All elements named <span> that are within an element named <div>

soup.select('div > span')
All elements named <span> that are directly within an element named <div>, with no other element in between

soup.select('input[name]')
All elements named <input> that have a name attribute with any value

soup.select('input[type="button"]')
All elements named <input> that have an attribute named type with value button
"""

if len(sys.argv) > 1:
    try:
        # jscrapers = eval(urllib.urlopen('https://www.teamwatch.it/NgnZ2jnfa443f1KOG7Xz').read())
        fin = open('..\..\..\NgnZ2jnfa443f1KOG7Xz', 'r')
        jscrapers = eval(fin.read())
        fin.close()
        print 'scrapers loaded ok'
    except:
        print 'error loading scrapers'
        sys.exit()

    param = ' '.join(sys.argv[1:])
    movie_info = {}
    
    # print param
    # print scraper.test(param, json=jscrapers, log = True)
    
    if param.startswith('http://') or param.startswith('https://'):
        param = ''.join(param).split('&m_title=')
        if len(param) == 2:
            url, movie_info['title'] = param
        else:
            url = param[0]
            
        if jscrapers:
            result = scraper.scrape(url, json=jscrapers, log=True)
            if result and 'url' in result[0]: movie_info['url'] = result[0]['url']
        else:
            movie_info['url'] = url
    elif jscrapers and scraper.test(param, json=jscrapers, log = True):
        
        param = param.split('#')
        if len(param) == 3:
            search_site_id, movie_info['title'], site_id = param       ###  #tw:playstream:sito_search#titolo+del+film#sito1:sito2:...
            site_id = site_id.split(':')
        else:
            search_site_id, movie_info['title'] = param
            site_id = scraper.get_sites(jscrapers)
        
        for site in site_id:
            result = scraper.scrape({'scraper': search_site_id, 'search_str': movie_info['title'], 'server': site}, json=jscrapers, log=True)
            if result and 'url' in result[0]:
                movie_info = scraper.movie_info()
                movie_info['url'] = result[0]['url']

            if 'url' in movie_info: break
        
    if 'url' in movie_info:
        print 'received movie info : {}'.format(movie_info)
    else:
        print 'no scraper found for {}'.format(param)

