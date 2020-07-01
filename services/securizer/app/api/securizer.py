import boto3
import json
# import settings
import dateutil.parser
import time
# from backup import store,store_mongo
from dictdiffer import diff
import datetime

from fastapi import APIRouter, HTTPException
from typing import List


session = boto3.Session()
securizer = APIRouter()

@securizer.get('/')
async def test():
    return {"Securizer": "working"}

@securizer.post('/secure_and_tag_sg/',status_code=201)
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
    print("New access rules for security groups applied")