import boto3
import json
# import settings
import dateutil.parser
import time
# from backup import store,store_mongo
import datetime

from fastapi import APIRouter, HTTPException
from typing import List


session = boto3.Session(region_name="eu-west-2")
explorer = APIRouter()

# EC2, Security Groups and VPCs

@explorer.get('/', status_code=201)
async def index():
    return {"Explorer": "Working"}

@explorer.get('/ec2_instances/',status_code=201)
async def ec2_list_instances():
    """Listing EC2 Intances and storing them on a Mongo Collection"""
    ec2 = session.client('ec2')
    response = ec2.describe_instances()
    # store_mongo(response,'EC2_INSTANCES')
    return json.dumps(response['Reservations'][0], indent=1, default=str)

@explorer.get('/insecure_groups',status_code=201)
async def list_insecure_groups():
    """List groups with ports open to all ip adresses"""
    ec2 = session.client('ec2')
    response = ec2.describe_security_groups()
    insecureGroups = [{}]
    for sg in response['SecurityGroups']:
        for ipPerm in sg['IpPermissions']:
            for ipRange in ipPerm['IpRanges']: #TODO Change this triple loop
                if ipRange['CidrIp'] == '0.0.0.0/0' and ipPerm['IpProtocol'] != '-1':
                    insecureGroups.append(
                        {'Security Group': sg['GroupName'],
                            'Port': ipPerm['FromPort']})
    # store_mongo(response, 'INSECURE_GROUPS')
    print(json.dumps(insecureGroups, indent=1, default=str))

@explorer.get('/vpcs',status_code=201)
async def list_vpcs():
    """ List VCPs """
    ec2 = session.client('ec2')
    response = ec2.describe_vpcs()
    # store_mongo(response, 'VPCS')
    print(json.dumps(response, indent=1, default=str))

@explorer.get('/security_groups',status_code=201)
async def list_security_groups():
    """List Security Groups"""
    ec2 = session.client('ec2')
    response = ec2.describe_security_groups()
    # store(response,'SECURITY_GROUPS')
    # store_mongo(response, 'SECURITY_GROUPS')
    print(json.dumps(response, indent=1, default=str))

@explorer.get('/iam_users',status_code=201)
async def iam_list_users():
    """ List IAM users in account """
    iam = session.client('iam')
    response = iam.list_users()
    for iamuser in response['Users']:
        policies = iam.list_attached_user_policies(UserName=iamuser['UserName'])
        iamuser['Policies'] = policies
        groups = iam.list_groups_for_user(UserName=iamuser['UserName'])
        iamuser['Groups'] = groups
    print(json.dumps(response, indent=1, default=str))


@explorer.get('/iam_groups',status_code=201)
async def iam_list_groups():
    """ List IAM groups in account """
    iam = session.client('iam')
    response = iam.list_groups()
    print(json.dumps(response, indent=1, default=str))

@explorer.get('/iam_roles',status_code=201)
async def iam_list_roles():
    """ List IAM roles in account """
    iam = session.client('iam')
    response = iam.list_roles()
    print(json.dumps(response, indent=1, default=str))

@explorer.get('/iam_policies',status_code=201)
async def iam_list_policies():
    """ List IAM policies in account """
    iam = session.client('iam')
    response = iam.list_policies()
    print(json.dumps(response, indent=1, default=str))

############# LAMBDAS #############

@explorer.get('/lambdas',status_code=201)
async def lambdas_list():
    """ List Lambdas in account """
    lmda = session.client('lambda')
    response = lmda.list_functions()
  
    print(json.dumps(response, indent=1, default=str))

############# ORGANIZATIONS #############

@explorer.get('/accounts',status_code=201)
async def org_list_accounts():
    """ List accounts in organization """
    org = session.client('organizations')
    response = org.list_accounts()
  
    print(json.dumps(response, indent=1, default=str))

@explorer.get('/org_units',status_code=201)
async def org_organization_units():
    """ List Organizational Units in organization """
    org = session.client('organizations')
    response = org.list_accounts()
   
    print(json.dumps(response, indent=1, default=str))


############# RDS #############

@explorer.get('/rds_databases',status_code=201)
async def rds_list_databases():
    """ List RDS """
    rds = session.client('rds')
    response = rds.describe_db_instances()
    
    print(json.dumps(response, indent=1, default=str))

############# S3  #############

@explorer.get('/s3_buckets',status_code=201)
async def s3_list_buckets():
    """ List All S3 buckets """
    s3 = session.client('s3')
    response = s3.list_buckets()
    for bucket in response['Buckets']: # YOU CAN GET A LOT OF THINGS FROM BUCKETS
        bucketRegion = s3.get_bucket_location(
            Bucket=bucket['Name']
        )
        bucket['Region'] = bucketRegion
        # bucketPolicy = s3.get_bucket_policy(
        #     Bucket=bucket['Name']
        # )
        # bucket['Policy'] = bucketPolicy
        try:
            bucketEncryption = s3.get_bucket_encryption(
                Bucket=bucket['Name']
            )
            bucket['Encryption'] = bucketEncryption

        except: #TODO: not really, could be other exceptions
            bucket['Encryption'] = 'NONE'
    print(json.dumps(response, indent=1, default=str))

@explorer.get('/s3_uncrypted_buckets',status_code=201)
async def s3_list_unencrypted_buckets():
    """ List All unencrypted S3 buckets """
    s3 = session.client('s3')
    response = s3.list_buckets()
    unencryptedBuckets = [{}]
    for bucket in response['Buckets']:
        try:
            bucketEncryption = s3.get_bucket_encryption(
                Bucket=bucket['Name']
            )
            bucket['Encryption'] = bucketEncryption
        except: #TODO: not really, could be other exceptions
            bucket['Encryption'] = 'NONE'
            unencryptedBuckets.append(bucket)
    print(json.dumps(unencryptedBuckets, indent=1, default=str))

@explorer.get('/s3_policies',status_code=201)
async def s3_get_bucket_policy(bucketName):
    """ Get Bucket Policy by bucketName """
    s3 = session.client('s3')
    result = s3.get_bucket_policy(Bucket='bucketName')
    print(json.dumps(result, indent=1, default=str))


############# CLOUDWATCH #############
@explorer.get('/cloudwatch_alarms',status_code=201)
async def get_cloudwatch_alarms():
    """ List cloudwatch Alarms """
    cloudwatch = session.client('cloudwatch')
    response = cloudwatch.describe_alarms()
    print(json.dumps(response, indent=1, default=str))