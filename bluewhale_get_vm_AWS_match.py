# Author: Caleb Grode
# Input: Third party vm name, AWS region name, operating system
# Output: AWS EC2 match(s) with price in desired region
# Purpose: On the front end the customer will select a vm from gcp or azure and the backend will need to 
#          return the available EC2 matches as well as their price in the desired region
# This code was heavily inspired by this blog: https://www.sentiatechblog.com/using-the-ec2-price-list-api
import json
import boto3
from boto3.dynamodb.conditions import Key

def get_price_info(reg, ec2, os, pc):
    # if this region, ec2 and os combo is not available this code might fail
    # so we will try + catch and return None if there is an issue
    try:
        paginator = pc.get_paginator('get_products')

        response_iterator = paginator.paginate(
            ServiceCode="AmazonEC2",
            Filters=[
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'location',
                    'Value': reg
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'instanceType',
                    'Value': ec2
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'capacitystatus',
                    'Value': 'Used'
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'tenancy',
                    'Value': 'Shared'
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'preInstalledSw',
                    'Value': 'NA'
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'operatingSystem',
                    'Value': os
                }
            ],
            PaginationConfig={
                'PageSize': 100
            }
        )

        products = []
        for response in response_iterator:
            for priceItem in response["PriceList"]:
                priceItemJson = json.loads(priceItem)
                products.append(priceItemJson)
        
        # parse out the data we want
        sku = products[0]['product']['sku']
        on_demand_code = sku + '.' + 'JRTCKXETXF'
        price_per_hr_code = '6YS6EN2CT7'
        price_per_hour_usd = products[0]['terms']['OnDemand'][on_demand_code]['priceDimensions'][on_demand_code+'.'+price_per_hr_code]['pricePerUnit']['USD']
        instance_meta_data = products[0]['product']['attributes']
        
        # build a dict of the data we want
        data = {
            'name' : ec2,
            'price per hour USD' : price_per_hour_usd,
            'instance meta data' : instance_meta_data
        }

        return data
    except:
        return None



def lambda_handler(event, context):
    print(event)
    # parameters
    vm_name = event['vm']
    region = event['region']
    operating_system = event['os']
    matches = []
    match_data = []

    dynamodb = boto3.resource('dynamodb', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('bluewhale_resources')

    # query for potential matches
    data = table.query(
        # virtual machine from AWS which has the same type and more or equal vCPUs and similar ram capacity
        KeyConditionExpression= Key('name').eq(vm_name)
    )

    matches = data['Items'][0]['AWS_matches']

    pricing_client = boto3.client('pricing', region_name='us-east-1')       

    for ec2 in matches:
        price_info = get_price_info(region, ec2, operating_system, pricing_client)
        if price_info != None:
            match_data.append(price_info)

    if not match_data:
        print("Region or OS not availiable for current selection")
        return {
            'statusCode': 200,
            'body': json.dumps("Invalid region + os selection")
        }
    else:
        print(match_data)
        return {
            'statusCode': 500,
            'body': json.dumps(match_data)
        }







