# Author: Caleb Grode
# Purpose: take in list of AWS resources and calculate the price per month for these resources
# Inputs: list of dicts containing details about ec2 instances, list of dicts containing details about storage resources
# Output: the input dicts with the price per month added into the cost and the total cost per month of all instances

import json
import boto3


def get_ec2_cost(reg, ec2, os, pc, hours):
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
        
        

        return hours * float(price_per_hour_usd)
    except:
        return 'request failed'



def lambda_handler(event, context):

    ec2 = event['ec2'] # dicts of {'name': name, 'region':region, 'os':os, 'quantity': quantity}
    storage = event['storage'] # dicts of {'name': name, 'quantity': quantity}
    total_cost_per_month = 0
    pricing_client = boto3.client('pricing', region_name='us-east-1')

    # get cost info for all ec2 instances
    for e in ec2:
        # update individual spot
        e['price per month'] = get_ec2_cost(e['region'], e['name'], e['os'], pricing_client, 730)
        # update the total cost
        total_cost_per_month += e['price per month USD']
  
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'compute costs' : ec2,
            'storage costs' : storage,
            'total cost per month USD' : total_cost_per_month

        })
    }

