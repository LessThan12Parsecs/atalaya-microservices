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

# EC2, Security Groups and VPCs

@explorer.get('/ec2_instaces/',status_code=201)
async def ec2_list_instances():
    """Listing EC2 Intances and storing them on a Mongo Collection"""
    ec2 = session.client('ec2')
    response = ec2.describe_instances()
    # store_mongo(response,'EC2_INSTANCES')
    print(json.dumps(response['Reservations'][0], indent=1, default=str))


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

async def list_vpcs():
    """ List VCPs """
    ec2 = session.client('ec2')
    response = ec2.describe_vpcs()
    # store_mongo(response, 'VPCS')
    print(json.dumps(response, indent=1, default=str))

async def list_security_groups():
    """List Security Groups"""
    ec2 = session.client('ec2')
    response = ec2.describe_security_groups()
    # store(response,'SECURITY_GROUPS')
    # store_mongo(response, 'SECURITY_GROUPS')
    print(json.dumps(response, indent=1, default=str))

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
    store(insecureGroups, 'SECURITY_GROUPS')
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