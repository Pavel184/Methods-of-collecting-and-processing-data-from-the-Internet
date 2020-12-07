import bs4
import requests
from urllib.parse import urljoin
from database import DataBase


class GbBlogParse:

    def __init__(self, start_url: str, db: DataBase):
        self.start_url = start_url
        self.page_done = set()
        self.db = db

    def __get(self, url) -> bs4.BeautifulSoup:
        response = requests.get(url)
        self.page_done.add(url)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def run(self, url=None):
        if not url:
            url = self.start_url

        if url not in self.page_done:
            soup = self.__get(url)
            posts, pagination = self.parse(soup)

            for post_url in posts:
                page_data = self.page_parse(self.__get(post_url), post_url)
                self.save(page_data)
            for p_url in pagination:
                self.run(p_url)

    def parse(self, soup):
        ul_pag = soup.find('ul', attrs={'class': 'gb__pagination'})
        paginations = set(
            urljoin(self.start_url, url.get('href')) for url in ul_pag.find_all('a') if url.attrs.get('href'))
        posts = set(
            urljoin(self.start_url, url.get('href')) for url in soup.find_all('a', attrs={'class': 'post-item__title'}))
        return posts, paginations

    def page_parse(self, soup, url) -> dict:
        # контент есть тут
        tmp = soup.find('script', attrs={'type': 'application/ld+json'}).string

        id = soup.find('div', attrs={'class': 'm-t-xl'}).find('comments').get('commentable-id') #post id
        url_com = 'https://geekbrains.ru/api/v2/comments?commentable_type=Post&commentable_id=' + id #url for comment request
        comment_resp = requests.get(url_com) #comment request
        data_com: dict = comment_resp.json() #comment json

        data = {
            'post_data': {
                'url': url,
                'title': soup.find('h1').text,
                'image': soup.find('div', attrs={'class': 'blogpost-content'}).find('img').get('src') if soup.find(
                    'div', attrs={'class': 'blogpost-content'}).find('img') else None,
                'date': soup.find('div', attrs={'class': 'blogpost-date-views'}).find('time').get('datetime'),
            },
            'writer': {'name': soup.find('div', attrs={'itemprop': 'author'}).text,
                       'url': urljoin(self.start_url,
                                      soup.find('div', attrs={'itemprop': 'author'}).parent.get('href'))},

            'tags': [],

            'comments': [],

        }
        for tag in soup.find_all('a', attrs={'class': "small"}):
            tag_data = {
                'url': urljoin(self.start_url, tag.get('href')),
                'name': tag.text
            }
            data['tags'].append(tag_data)

        for i in data_com: # parent
            comment_data = {
                'author_name': i.get('comment').get('user').get('full_name'),
                'comment': i.get('comment').get('body')
            }
            data['comments'].append(comment_data)
            for u in i.get('comment').get('children'): #child
                comment_data = {
                    'author_name': u.get('comment').get('user').get('full_name'),
                    'comment': u.get('comment').get('body')
                }
                data['comments'].append(comment_data)
                for x in u.get('comment').get('children'):  # grandchild
                    comment_data = {
                        'author_name': x.get('comment').get('user').get('full_name'),
                        'comment': x.get('comment').get('body')
                    }
                    data['comments'].append(comment_data)
        return data

    def get_comments(self, comments_soup):
        if comments_soup:
            print(1)

    def save(self, page_data: dict):
        self.db.create_post(page_data)


if __name__ == '__main__':
    db = DataBase('sqlite:///gb_blog.db')
    parser = GbBlogParse('https://geekbrains.ru/posts', db)

    parser.run()