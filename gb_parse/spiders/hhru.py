import scrapy
from ..loaders import HHVacancyLoader, HHCompanyLoader


class HhruSpider(scrapy.Spider):
    name = 'hhru'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']
    _xpath = {
        'pagination': '//div[@data-qa="pager-block"]//a[@data-qa="pager-page"]/@href',
        'vacancy_urls': '//a[@data-qa="vacancy-serp__vacancy-title"]/@href',
    }
    vacancy_xpath = {
        "title": '//h1[@data-qa="vacancy-title"]/text()',
        "salary": '//p[@class="vacancy-salary"]//text()',
        "description": '//div[@data-qa="vacancy-description"]//text()',
        "skills": '//div[@class="bloko-tag-list"]//span[@data-qa="bloko-tag__text"]/text()',
        "company_url": '//a[@data-qa="vacancy-company-name"]/@href',
    }

    company_xpath = {
        'name': '//h1/span[contains(@class, "company-header-title-name")]/text()',
        'company_url': '//a[contains(@data-qa, "company-site")]/@href',
        'profile': '//div[@class="employer-sidebar-block"][3]//p//text()',
        'description': '//div[contains(@data-qa, "company-description")]//text()',

    }

    def parse(self, response, **kwargs):
        for pag_page in response.xpath(self._xpath['pagination']):
            yield response.follow(pag_page, callback=self.parse)

        for vacancy_page in response.xpath(self._xpath['vacancy_urls']):
            yield response.follow(vacancy_page, callback=self.vacancy_parse)

    def vacancy_parse(self, response, **kwargs):
        loader = HHVacancyLoader(response=response)
        loader.add_value('url', response.url)
        for key, value in self.vacancy_xpath.items():
            loader.add_xpath(key, value)

        yield loader.load_item()
        yield response.follow(response.xpath(self.vacancy_xpath['company_url']).get(), callback=self.company_parse)

    def company_parse(self, response, **kwargs):
        loader = HHCompanyLoader(response=response)
        loader.add_value('url', response.url)
        for key, value in self.company_xpath.items():
            loader.add_xpath(key, value)

        yield loader.load_item()
        yield response.follow(response.xpath('//a[contains(@data-qa, "employer-page__employer-vacancies-link")]/@href').get(), callback=self.parse)
