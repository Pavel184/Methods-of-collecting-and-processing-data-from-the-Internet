import scrapy
import pymongo as pm
import os
import dotenv
import re
import base64

dotenv.load_dotenv('.env')



class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']

    ccs_query = {
        'brands': 'div.ColumnItemList_container__5gTrc div.ColumnItemList_column__5gjdt a.blackLink',
        'pagination': '.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'ads': 'article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mongo_client = pm.MongoClient(os.getenv('DATA_BASE'))
        self.db = mongo_client['parse_11']

    def parse(self, response):
        for brand in response.css(self.ccs_query['brands']):
            yield response.follow(brand.attrib.get('href'), callback=self.brand_page_parse)

    def brand_page_parse(self, response):
        for pag_page in response.css(self.ccs_query['pagination']):
            yield response.follow(pag_page.attrib.get('href'), callback=self.brand_page_parse)

        for ads_page in response.css(self.ccs_query['ads']):
            yield response.follow(ads_page.attrib.get('href'), callback=self.ads_parse)

    def ads_parse(self, response):
        data = {
            'title': response.css('.AdvertCard_advertTitle__1S1Ak::text').get(),
            'images': [img.attrib.get('src') for img in response.css('figure.PhotoGallery_photo__36e_r img')],
            'description': response.css('div.AdvertCard_descriptionInner__KnuRi::text').get(),
            'url': response.url,
            'autor': self.js_decoder_autor(response),
            'phone': self.phone(response),
            'specification': self.get_specifications(response),
        }

        collection = self.db['youla']
        collection.insert_one(data)

    def get_specifications(self, response):
        return {itm.css('.AdvertSpecs_label__2JHnS::text').get(): itm.css(
            '.AdvertSpecs_data__xK2Qx::text').get() or itm.css('a::text').get() for itm in
                response.css('.AdvertSpecs_row__ljPcX')}

    def js_decoder_autor(self, response):
        # script = response.xpath('//script[contains(text(), "window.transitState =")]/text()').get()
        script = response.css('script:contains("window.transitState = decodeURIComponent")::text').get()
        script_salon = response.css('script:contains("am.ru")::text').get()
        re_str = re.compile(r"youlaId%22%2C%22([0-9|a-zA-Z]+)%22%2C%22avatar")
        re_salon = re.compile(r"sellerLink%22%2C%22%2F([0-9|a-zA-Z]+)%2F([0-9|a-zA-Z]+.([0-9|a-zA-Z]+).([0-9|a-zA-Z]+).([0-9|a-zA-Z]+).([0-9|a-zA-Z]+).([0-9|a-zA-Z]+).([0-9|a-zA-Z]+))%2F%22%2C%22type")
        result = re.findall(re_str, script)
        return f'https://youla.ru/user/{result[0]}' if result else f'https://auto.youla.ru/cardealers/{(re.findall(re_salon, script_salon))[0][1]}'

    def phone(self, response):
        script = response.css('script:contains("window.transitState = decodeURIComponent")::text').get()
        re_phone = re.compile(r'phone%22%2C%22(.{32})Xw%3D%3D%22%2C%22tim')
        result_phone = re.findall(re_phone, script)
        return base64.b64decode(base64.b64decode(result_phone[0].encode())).decode()