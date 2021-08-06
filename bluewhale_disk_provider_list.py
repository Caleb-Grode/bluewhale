# Author: Caleb Grode
# Purpose: Lists the disk options given a provider

import json
import boto3
from boto3.dynamodb.conditions import Attr

def lambda_handler(event, context):
    # parameters
    provider = event['queryStringParameters']['provider']
    dynamodb = boto3.resource('dynamodb', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('bluewhale_resources')
    
    print("Getting data...")
    # get disk data
    disks = table.scan(
        FilterExpression=   Attr('resource type').eq('virtual disk') 
                            & Attr('provider').eq(provider)
    )

    return {
        'statusCode': 200,
        'headers' : {
                'Access-Control-Allow-Origin': '*',
            },
        'body': json.dumps(disks)
    }