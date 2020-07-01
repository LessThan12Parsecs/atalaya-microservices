import json
import datetime
from os import path, makedirs
import pymongo

def store_mongo(data,contentType):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/") #TODO: change this
    mydb = myclient["Atalaya"]
    mycol = mydb[contentType]
    x = mycol.insert_one(data)
