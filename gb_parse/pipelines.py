# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
import pymongo as pm
import os
import dotenv

dotenv.load_dotenv('.env')


class GbParsePipeline:
    def __init__(self):
        mongo_client = pm.MongoClient(os.getenv('DATA_BASE'))
        self.db = mongo_client['instgrm_1']

    def process_item(self, item, spider):
        #if spider.db_type == 'MONGO':
        collection = self.db[spider.name]
        collection.insert_one(item)
        return item


class GbImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for img_url in item['images']:
            yield Request(img_url)

    def item_completed(self, results, item, info):
        item['images'] = [itm[1] for itm in results]
        return item