# Author: Caleb Grode
# Purpose: list all 3rd party virtual machines for the front end to display

import json
import boto3
from boto3.dynamodb.conditions import Attr

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('bluewhale_resources')
    
    print("Getting data...")
    # get azure and gcp vm data
    third_party_vm = table.scan(
        FilterExpression= Attr('resource type').eq('virtual machine') & (Attr('provider').eq('Azure') or Attr('provider').eq('GCP'))
    )
    
    # json does not support the decimal type that DynamoDB stores our numbers as so we need to re-cast the data types
    for item in third_party_vm['Items']:
        print(item)
        if 'MemoryMB' in item:
            item['MemoryMB'] = int(item['MemoryMB'])
        if 'vCPUs' in item:
            item['vCPUs'] = int(item['vCPUs'])
        if 'vCPUsPerCore' in item:
            item['vCPUsPerCore'] = int(item['vCPUsPerCore'])
        
    return {
        'statusCode': 200,
        'headers' : {
                'Access-Control-Allow-Origin': '*',
            },
        'body': json.dumps(third_party_vm)
    }
