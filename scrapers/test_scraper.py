import maxxam_scraper as scraper
import sys, urllib

if len(sys.argv) > 1:
    try:
        jscrapers = eval(urllib.urlopen('https://www.teamwatch.it/NgnZ2jnfa443f1KOG7Xz').read())
        print 'scrapers loaded ok'
    except:
        print 'error loading scrapers'
        sys.exit()

    param = ' '.join(sys.argv[1:])
    movie_info = {}
    
    if param.startswith('http://') or param.startswith('https://'):
        param = ''.join(param).split('&m_title=')
        if len(param) == 2:
            url, movie_info['title'] = param
        else:
            url = param
            
        if jscrapers:
            result = scraper.scrape(url, json=jscrapers, log=False)
            if result and 'url' in result[0]: movie_info['url'] = result[0]['url']
        else:
            movie_info['url'] = url
    elif jscrapers and scraper.test(param, json=jscrapers, log = False):
        param = param.split('#')
        if len(param) == 3:
            search_site_id, movie_info['title'], site_id = param       ###  #tw:playstream:sito_search#titolo+del+film#sito1:sito2:...
            site_id = site_id.split(':')
        else:
            search_site_id, movie_info['title'] = param
            site_id = scraper.get_sites(jscrapers)
        
        for site in site_id:
            result = scraper.scrape({'scraper': search_site_id, 'search_str': movie_info['title'], 'server': site}, json=jscrapers, log=False)
            if result and 'url' in result[0]:
                movie_info = scraper.movie_info()
                movie_info['url'] = result[0]['url']

            if 'url' in movie_info: break
        
    if 'url' in movie_info:
        print 'received movie info : {}'.format(movie_info)
    else:
        print 'no scraper found for {}'.format(param)

