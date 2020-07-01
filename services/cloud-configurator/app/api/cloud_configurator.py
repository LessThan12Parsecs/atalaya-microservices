import boto3
import json
# import settings
import dateutil.parser
import time
import click
# from backup import store,store_mongo
import datetime

from fastapi import APIRouter, HTTPException
from typing import List


session = boto3.Session()
cloud_configurator = APIRouter()

@cloud_configurator.get('/',status_code=201)
async def test():
    return {"cloud_configurator": "Working"}