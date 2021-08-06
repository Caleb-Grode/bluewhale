# Author: Caleb Grode
# Purpose: Matches the 3rd party disk offerings with AWS matches
# This code will need to be maintaned as the matches are done through a dict
# we at first wanted to match based off IOPs but the way the different providers list or calculate IOPs differs a lot
# so the disks are martched by use case

import json
import boto3
from boto3.dynamodb.conditions import Attr

def lambda_handler(event, context):
    # there are only a few general categories of block storage available so we match the instances
    # with a hard coded dict--the GCP disks calculate IOPs in a very different way than AWS or Azure
    # so I went with a hard coded solution
    # because of this, this code will need to be maintained
    match_map = {
        'pd-extreme' : ['io1', 'io2'],
        'pd-ssd' : ['gp2', 'gp3'],
        'pd-balanced' : ['gp2', 'gp3'],
        'pd-standard' : ['st1', 'sc1'],
        'Premium_LRS': ['io1', 'io2','gp2', 'gp3'],
        'Premium_ZRS': ['io1', 'io2','gp2', 'gp3'],
        'StandardSSD_LRS' : ['gp2', 'gp3'],
        'StandardSSD_ZRS' : ['gp2', 'gp3'],
        'Standard_LRS' : ['st1', 'sc1'],
        'UltraSSD_LRS' : ['io1', 'io2']
    }
    
    
    dynamodb = boto3.resource('dynamodb', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('bluewhale_resources')
    
    print("Getting data...")
    # get azure and gcp disk data
    third_party_disk = table.scan(
        FilterExpression= Attr('resource type').eq('virtual disk') & (Attr('provider').eq('Azure') or Attr('provider').eq('GCP'))
        )
    # add the matches into the DB entries!
    for disk in third_party_disk['Items']:
        table.update_item(
            Key={
                'name': disk['name']
                },
            UpdateExpression="set AWS_matches=:a",
            ExpressionAttributeValues={
                ':a': match_map[disk['name']]
            },
            ReturnValues="UPDATED_NEW"
        )
    print("done!")
    return {
        'statusCode': 200,
        'body': json.dumps('Matching complete!')
    }

