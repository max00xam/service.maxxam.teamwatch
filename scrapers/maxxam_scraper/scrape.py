from selenium import webdriver
from bs4 import BeautifulSoup as bs
import re

class scraper():
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)
        self.soup = None

    def purge(self, text):
        text = re.sub('\[[^\]]+\]', '', text)
        return re.sub('\([^\)]+\)', '', text).strip()

    def bestmatch(self, search, titles):
        slist = search.lower().replace(' ', '+').split('+')

        res = []
        for title in titles:
            tlist = title['title'].lower().replace(' ', '+').split('+')
            score = len([a for a in slist if a in tlist]) - len([a for a in tlist if a not in slist])
            res.append([score, title])

        return max(res)

    def _get(url):
        self.driver.get(url)
        self.soup = bs(self.driver.page_source, 'html.parser')

    def cb01(driver, search):        
        if ' ' in search: search = search.replace(' ', '+')

        self._get('https://cb01.pub/?s={}'.format(search))       

        res = [{'title': self.purge(a.text), 'url': a.attrs['href']} for a in self.soup.select('h3.card-title a')]
        best = self.bestmatch(search, res)

        self._get(best['url'])

        res = []
        for td in [td for td in soup.select('article table.cbtable table td') if td.text]:
            if 'download' in td.text: break
            if td.a: res.append([td.text, td.a.attrs['href']])

        return res

if __name__ == '__main__':
    scr = scraper()
    print (scr.cb01('non+sposate+le+mie+figlie'))


