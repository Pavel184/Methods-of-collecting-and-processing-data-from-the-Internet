import json
import scrapy
import datetime as dt
from ..items import InstaTag, InstaPost

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']

    query_hash = {
        'tag_paginate': '9b498c08113f1e09617a1703c22b2f32'
    }
    {"tag_name": "python",
     "first": 2,
     "after": "QVFEeGhna1dpcnZuQUFfbDQ2eGV1SzZUVWtVMDBuTGc1UnZJVkw4WW1EakpvTF8xVXlJQWRYWXhWVHdBX0hqYWkzLXE3b3BDNVRnbTVpWEVnN0QzSDEtUA=="}
    api_url = '/graphql/query/'
    query_hash = {
        'tag_posts': "9b498c08113f1e09617a1703c22b2f32",
    }

    def __init__(self, login, password, tag_list, *args, **kwargs):
        self.login = login
        self.password = password
        self.tag_list = tag_list
        super(InstagramSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password,
                },
                headers={'X-CSRFToken': js_data['config']['csrf_token']}
            )
        except AttributeError:
            if response.json().get('authenticated'):
                for tag in self.tag_list:
                    yield response.follow(f'/explore/tags/{tag}', callback=self.tag_parse)


    def tag_parse(self, response):
        tag_data = self.js_data_extract(response)['entry_data']['TagPage'][0]['graphql']['hashtag']

        yield InstaTag(
            date_parse=dt.datetime.utcnow(),
            type='Tag',
            data={
                'id': tag_data['id'],
                'name': tag_data['name'],
                'profile_pic_url': tag_data['profile_pic_url'],
            },
            images=[tag_data['profile_pic_url']]
        )

        yield from self.get_posts_data(tag_data, response)

    def get_posts_data(self, tag_data, response):
        if tag_data['edge_hashtag_to_media']['page_info']['has_next_page']:
            variables = {
                'tag_name': tag_data['name'],
                'first': 100,
                'after': tag_data['edge_hashtag_to_media']['page_info']['end_cursor'],
            }
            url = f'{self.api_url}?query_hash={self.query_hash["tag_posts"]}&variables={json.dumps(variables)}'
            yield response.follow(url, callback=self.tag_api_parse,)
        yield from self.get_post_item(tag_data['edge_hashtag_to_media']['edges'])

    def tag_api_parse(self, response):
        yield from self.get_posts_data(response.json()['data']['hashtag'], response)

    @staticmethod
    def get_post_item(edges):
        for node in edges:
            yield InstaPost(
                type='Post',
                date_parse=dt.datetime.utcnow(),
                data=node['node'],
                images=[x['src'] for x in node['node']['thumbnail_resources']]
            )


    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace("window._sharedData = ", '')[:-1])