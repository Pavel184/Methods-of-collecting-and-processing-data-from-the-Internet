import json
import scrapy
import datetime as dt
from ..items import InstaFollows, InstaFollowers

global nodes_follow
global nodes_followers
nodes_follow = []
nodes_followers = []
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
        'posts': '56a7068fea504063273cc2120ffd54f3',
        'follow': 'd04b0a864b4b54837c0d870b0e77e076',
        'followers': 'c76146de99bb02f6415203be841dd25a'
    }

    def __init__(self, login, users, password, tag_list, *args, **kwargs):
        self.login = login
        self.users = users
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
                for user in self.users:
                    yield response.follow(f'/{user}/', callback=self.user_page_parse)

    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace("window._sharedData = ", '')[:-1])


    def user_page_parse(self, response):
        user_data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']


        yield from self.get_api_follow_request(response, user_data)
        yield from self.get_api_followed_request(response, user_data)



    def get_api_follow_request(self, response, user_data, variables=None):
        if not variables:
            variables = {
                'id': user_data['id'],
                'first': 100,
            }
        url = f'{self.api_url}?query_hash={self.query_hash["follow"]}&variables={json.dumps(variables)}'
        yield response.follow(url, callback=self.get_api_follow, cb_kwargs={'user_data': user_data})



    def get_api_follow(self, response, user_data):
        if b'application/json' in response.headers['Content-Type']:
            data = response.json()
            user_follows = data['data']['user']['edge_follow']['edges']

            for node in user_follows:
                nodes_follow.append(node['node'])


            if response.json()['data']['user']['edge_follow']['page_info']['has_next_page']:
                variables = {
                    'id': user_data['id'],
                    'first': 100,
                    'after': data['data']['user']['edge_follow']['page_info']['end_cursor'],
                }
                yield from self.get_api_follow_request(response, user_data, variables)

            if not response.json()['data']['user']['edge_follow']['page_info']['has_next_page']:
                temp_1 = nodes_follow.copy()
                nodes_follow.clear()
                yield InstaFollows(
                    date_parse=dt.datetime.utcnow(),
                    user_data=user_data,
                    follows=temp_1,
                )


    def get_api_followed_request(self, response, user_data, variables=None):
        if not variables:
            variables = {
                'id': user_data['id'],
                'first': 100,
            }
        url = f'{self.api_url}?query_hash={self.query_hash["followers"]}&variables={json.dumps(variables)}'
        yield response.follow(url, callback=self.get_api_followed, cb_kwargs={'user_data': user_data})


    def get_api_followed(self, response, user_data):
        if b'application/json' in response.headers['Content-Type']:
            data = response.json()
            user_followers = data['data']['user']['edge_followed_by']['edges']

            for node in user_followers:
                nodes_followers.append(node['node'])


            if response.json()['data']['user']['edge_followed_by']['page_info']['has_next_page']:
                variables = {
                    'id': user_data['id'],
                    'first': 100,
                    'after': data['data']['user']['edge_followed_by']['page_info']['end_cursor'],
                }
                yield from self.get_api_followed_request(response, user_data, variables)

            if not response.json()['data']['user']['edge_followed_by']['page_info']['has_next_page']:
                temp_2 = nodes_followers.copy()
                nodes_followers.clear()
                yield InstaFollowers(
                    date_parse=dt.datetime.utcnow(),
                    user_data=user_data,
                    followers=temp_2
                )