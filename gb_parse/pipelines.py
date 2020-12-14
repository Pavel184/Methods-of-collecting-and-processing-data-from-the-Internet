# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
import pymongo as pm
import os
import dotenv

dotenv.load_dotenv('.env')

class GbParsePipeline:
    def __init__(self):
        mongo_client = pm.MongoClient(os.getenv('DATA_BASE'))
        self.db = mongo_client['hhru_1']
        #self.db = MongoClient()['parse_gb_11_2']

    def process_item(self, item, spider):
        #if spider.db_type == 'MONGO':
        collection = self.db[spider.name]
        collection.insert_one(item)
            ##collection = self.db[spider.name]
            #collection.insert_one(item)
        return item