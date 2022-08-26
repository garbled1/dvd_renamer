"""
dvd_rewind lookup movie on http://dvdcompare.net

Contains:
    - Lookup_movie
"""
import os
import re
import requests
from bs4 import BeautifulSoup


class Lookup_Movie:
    """Documentation of Lookup_Movie."""
    title = None
    year = None
    base_url = 'http://dvdcompare.net/comparisons'
    sr_url = base_url + '/adv_search_results.php'
    movie_list = []
    soup_movie = None

    def __init__(self, title, year):
        """Initiatlizes class."""
        self.year = str(year)
        self.title = title
        return

    def search_for_movie(self):
        """ Search for a movie."""
        search = {'title_search':self.title,
                  'director_search':'',
                  'year_search':self.year if self.year is not None else '',
                  'country_search':'',
                  'company_search':'',
                  'edition_search':'',
                  'and_or':'and' }
        x = requests.post(self.sr_url, data = search)

        movie_result = BeautifulSoup(x.text, 'html.parser')
        ml = movie_result.find_all(href=re.compile("film.php"))
        for m in ml:
            data = dict()
            # print(m)
            soup = BeautifulSoup(str(m), 'html.parser')
            data['name'] = soup.a.string.replace('\t', '')
            data['url'] = soup.a['href']
            # print("String: ", data['name'])
            # print("URL: ", data['url'])
            self.movie_list.append(data)

        if len(self.movie_list) > 0:
            return True
        return False

    def get_movie_list(self):
        return self.movie_list

    def get_url_for_movie(self, movie):
        for mov in self.movie_list:
            if mov['name'] == movie:
                return self.base_url + '/' + mov['url']
        return None

    def process_movie(self, url):
        x = requests.get(url)
        raw_text = re.sub(re.compile('<i>'), '', x.text)
        raw_text = re.sub(re.compile('</i>'), '', raw_text)
        self.soup_movie = BeautifulSoup(raw_text, 'html.parser')

    def find_time_in_movie(self, time_str):
        res = self.soup_movie.find_all(string=re.compile(time_str))
        # print(res)
        results = []
        for i in res:
            x = i.split('\r')
            for item in x:
                if item != '':
                    item = item.replace('\t', '')
                    # print("ORIG: ", item)
                    item = re.sub(re.compile('\(.*\)'), '', item)
                    # print("FIRST: ", item)
                    item = re.sub(re.compile('^-* '), '', item)
                    # print("SECOND: ", item)
                    if '"' in item:
                        l = item.split('"')[1::2]
                        # print("THIRD: ", item)
                        # print("l: ", l)
                        results.append(l[0].strip())
                    results.append(item.strip())
        fixed_results = list(dict.fromkeys(results))
        return fixed_results

    def find_fuzzy_time_in_movie(self, time_str):
        """ Strip the last second off and guess it."""
        return self.find_time_in_movie(time_str[:-2])
