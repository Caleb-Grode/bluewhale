import json
import boto3
from boto3.dynamodb.conditions import Attr

def lambda_handler(event, context):
    # parameters
    provider = event['queryStringParameters']['provider']
    dynamodb = boto3.resource('dynamodb', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('bluewhale_resources')
    
    print("Getting data...")
    # get azure and gcp vm data
    disks = table.scan(
        FilterExpression=  Attr('resource type').eq('virtual disk') 
                           & Attr('provider').eq(provider)
    )

    return {
        'statusCode': 200,
        'body': json.dumps(disks)
    }