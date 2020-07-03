import boto3
import json
# import settings
import dateutil.parser
import time
import click
# from backup import store,store_mongo
from dictdiffer import diff
import datetime

from fastapi import APIRouter, HTTPException
from typing import List


session = boto3.Session(profile_name='atalaya')
explorer = APIRouter()
