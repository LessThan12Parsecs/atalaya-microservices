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
listener = APIRouter()

@listener.get('/')
async def test():
    return {"Listener": "working"}