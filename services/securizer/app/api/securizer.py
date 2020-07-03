import boto3
import json
# import settings
import dateutil.parser
import time
# from backup import store,store_mongo
import datetime

#TODO: Move this to models.aws
from pydantic import BaseModel 
class Account(BaseModel):
    name: str
    email: str
    id: str

from fastapi import APIRouter, HTTPException
from typing import List


session = boto3.Session()
securizer = APIRouter()

@securizer.get('/')
async def test():
    return {"Securizer": "working"}

@securizer.get('/secure_and_tag_sg/',status_code=201)
async def secure_sg_and_tag():
    """ Limit ip addresses to insecure groups and tag resources """
    ec2 = session.client('ec2')
    response = ec2.describe_security_groups()
    insecureGroups = []
    for sg in response['SecurityGroups']:
        isGroupInsecure = False
        insecurePerms = []
        for ipPerm in sg['IpPermissions']:
            if ipPerm['IpProtocol'] == '-1':
                insecurePerms.append(ipPerm)
                isGroupInsecure = True
            elif ipPerm['IpProtocol'] == 'tcp' or ipPerm['IpProtocol'] == 'udp' or ipPerm['IpProtocol'] == 'icmp' or \
                    ipPerm['IpProtocol'] == 'tcicmpv6p':
                for ipRange in ipPerm['IpRanges']:
                    if ipRange['CidrIp'] == '0.0.0.0/0':
                        insecurePerms.append(ipPerm)
                        isGroupInsecure = True
        if isGroupInsecure:
            insecureGroups.append(
                {'GroupId': sg['GroupId'],
                 'IpPermissions': insecurePerms})
    for isg in insecureGroups:
        # ec2.revoke_security_group_ingress(
        #     GroupId = isg['GroupId'],
        #     IpPermissions = isg['IpPermissions']
        # )

        # ec2.authorize_security_group_ingress(
        #     GroupId = insecureGroups[0]['GroupId'],
        #     IpPermissions = insecureGroups[0]['IpPermissions']
        # )
        ec2.create_tags(
            DryRun=False,
            Resources=[
                isg['GroupId'],
            ],
            Tags=[
                {
                    'Key': 'vulnerability',
                    'Value': 'OPEN'
                },
            ]
        )
    return "New access rules for security groups applied"


@securizer.get('/s3_encrypt_all/',status_code=201)
async def s3_encrypt_all():
    """ Enable encryption in all buckets for new data """
    s3 = session.client('s3')
    response = s3.list_buckets()
    for bucket in response['Buckets']:
        s3.put_bucket_encryption(
            Bucket=bucket['Name'],
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
    print("All S3 Buckets encryptation activated")


@securizer.post('/s3_set_pab_account',status_code=201)
async def s3_set_pab_to_account(account:Account):
    """ Set public access block to account accountID """
    s3 = session.client('s3')
    s3.put_public_access_block(
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        },
        AccountId=account.id
    )
    print("Account id" + account.id + " Has blocked public access to new S3 Buckets")

