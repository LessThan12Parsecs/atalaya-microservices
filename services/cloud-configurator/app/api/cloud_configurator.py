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


#TODO: Move this to models.aws
from pydantic import BaseModel 
class Account(BaseModel):
    name: str
    email: str
class S3Bucket(BaseModel):
    name: str
class User(BaseModel):
    username: str

class CloudTrail(BaseModel):
    bucketName: str
    trailName: str

session = boto3.Session()
cloud_configurator = APIRouter()



@cloud_configurator.get('/',status_code=201)
async def test():
    return {"cloud_configurator": "Working"}

    
@cloud_configurator.post('/create_account')
async def create_account(account: Account):
    """ Create account NAME with EMAIL in organization """
    orgs = session.client('organizations')
    orgs.create_account(
        Email=account.email,
        AccountName=account.name,
        IamUserAccessToBilling='DENY'
    )
    print("Account " + account.name + " created")



@cloud_configurator.post('/create_s3_bucket')
async def s3_create_bucket(bucket: S3Bucket): #
    """ Create new encrypted bucket with name BucketName """
    s3 = session.client('s3')
    response = s3.create_bucket(
        ACL='private',
        Bucket=bucket.name,
        CreateBucketConfiguration={
            'LocationConstraint': 'us-east-2' # TODO Check region constraints
        },
    )
    s3.put_public_access_block(
        Bucket=bucket.name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': False,
            'IgnorePublicAcls': False,
            'BlockPublicPolicy': False,
            'RestrictPublicBuckets': False
        }
    )
    s3.put_bucket_encryption(
        Bucket=bucket.name,
        ServerSideEncryptionConfiguration={
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256',
                    }
                },
            ]
        }
    )
    print(bucket.name + " Created")


#FIXME: 
@cloud_configurator.post('/create_log_user',status_code=201)
async def create_and_assing_log_user(user:User):
    """ Creates and assing log user to access S3 Bucket """
    s3 = session.client('s3')
    iam = session.client('iam')
    date = datetime.datetime.now().strftime("%Y%m%d%H%M")
    bucketName = 'Logs-' + date
    response = s3.create_bucket(
        ACL='private',
        Bucket=bucketName,
        CreateBucketConfiguration={
            'LocationConstraint': 'us-east-2' # TODO Check region constraints
        },
    )
    s3.put_public_access_block(
        Bucket=bucketName,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )
    s3.put_bucket_encryption(
        Bucket=bucketName,
        ServerSideEncryptionConfiguration={
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256',
                    }
                },
            ]
        }
    )
    try:
        iam.create_group(GroupName='ReadOnlyS3')
        pass #TODO: Handle Error
    except:
        pass
    policyString = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::" + bucketName
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                ],
                "Resource": "arn:aws:s3:::" + bucketName
            }
        ]
    })
    iam.put_group_policy(GroupName='ReadOnlyS3', PolicyName='ReadOnlyS3', PolicyDocument=policyString)
    iam.create_user(UserName='TestLogRead')
    iam.add_user_to_group(UserName='TestLogRead', GroupName='ReadOnlyS3') #TODO: TEST THIS
    print("Log user " + userName + "Created")



@cloud_configurator.post('/create_cloud_trail',status_code=201)
async def cloud_trail(cloudtrail: CloudTrail): #TODO: this is just an example policy
    """ Creates a cloudtrail trail with trailName and saving to bucketName"""
    cloudTrail = session.client('cloudtrail')
    policyString = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AWSCloudTrailAclCheck20150319",
                "Effect": "Allow",
                "Principal": {"Service": "cloudtrail.amazonaws.com"},
                "Action": "s3:GetBucketAcl",
                "Resource": "arn:aws:s3:::"+cloudtrail.bucketName,
            },
            {
                "Sid": "AWSCloudTrailWrite20150319",
                "Effect": "Allow",
                "Principal": {"Service": "cloudtrail.amazonaws.com"},
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::"+ cloudtrail.bucketName + "/*",
                "Condition": {"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}}
            }
        ]
    })
    s3 = session.client('s3')
    s3.put_bucket_policy(Bucket=cloudtrail.bucketName, Policy=policyString)
    response = cloudTrail.create_trail(
        Name=cloudtrail.trailName,
        S3BucketName=cloudtrail.bucketName,
        # S3KeyPrefix='string',
        # SnsTopicName='string',
        IncludeGlobalServiceEvents=True,
        IsMultiRegionTrail=True,
        EnableLogFileValidation=True,
        # CloudWatchLogsLogGroupArn='string',
        # CloudWatchLogsRoleArn='string',
        # KmsKeyId='string',
        IsOrganizationTrail=False,
        TagsList=[
            {
                'Key': 'Type',
                'Value': 'LOGTEST'
            },
        ]
    )
    # arn:aws:cloudtrail:eu-west-1:142790238724:trail/trialTest
    print(json.dumps(response, indent=1, default=str))

# @cloud_configurator.get('/cf_create_stack_set',status_code=201)
#async def cf_create_stack_set():
#     """ Create AtalayaFormationTemplate stackset on cloudformation """
#     cloudform = session.client('cloudformation')
#     stack = open('stacks/AtalayaFormationTemplate.yaml').read()
#     response = cloudform.create_stack_set(
#       StackSetName="StackSetTest", TemplateBody=stack, Capabilities=['CAPABILITY_NAMED_IAM'] #TODO: Handle if already exists
#     )
#     print(response)
# @cloud_configurator.get('/stackset_to_account',status_code=201)
#async def set_stackset_to_accounts():
#     """ Set stackset instances to children accounts """
#     cloudform = session.client('cloudformation')
#     org = session.client('organizations')
#     accounts = org.list_accounts()
#     response = cloudform.create_stack_instances(
#         StackSetName='StackSetTest', #TODO: add real name 
#         Accounts = [
#            '049447156073'
#         ],
#         Regions = ['eu-west-1']
#     )
#     print(response)
