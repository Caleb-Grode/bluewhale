# Author: Caleb Grode
# Purpose: take in list of AWS resources and calculate the price per month for these resources
# Inputs: list of dicts containing details about ec2 instances, list of dicts containing details about EBS resources
# Output: the input dicts with the price per month added into the cost and the total cost per month of all instances

import json
import boto3


def get_ec2_cost(reg, ec2, os, quantity, pc, hours):
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
        
        

        return hours * float(price_per_hour_usd) * int(quantity)
    except:
        return 0

def get_ebs_cost(region, ebs_type, ebs_name, quantity, size_GB, pc):

    response = pc.get_products(ServiceCode='AmazonEC2', Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': ebs_type}, 
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region}])
    
    products = []
    for priceItem in response["PriceList"]:
        priceItemJson = json.loads(priceItem)
        products.append(priceItemJson)
        print(priceItemJson)
        
    # parse out the data we want
    price_per_hour_usd = 0 # to prevent return 'None'
    for ebs in products: # this goes through the ebs volumes of type 'ebs_type' and selects the price
        sku = ebs['product']['sku']
        on_demand_code = sku + '.' + 'JRTCKXETXF'
        price_per_hr_code = '6YS6EN2CT7'
        if ebs_name == ebs['product']["attributes"]['volumeApiName']:
            price_per_hour_usd = ebs['terms']['OnDemand'][on_demand_code]['priceDimensions'][on_demand_code+'.'+price_per_hr_code]['pricePerUnit']['USD']
            
    
    
    return float(price_per_hour_usd) * int(quantity) * int(size_GB)


def lambda_handler(event, context):
    json_data = json.loads(event['body'])
    #json_data = event

    ec2 = json_data['ec2'] # dicts of {'name': name, 'region':region, 'os':os, 'quantity': quantity}
    ebs = json_data['ebs'] # dicts of {'name': name, 'region': region}
    total_cost_per_month = 0
    total_cost_per_month_EC2 = 0
    total_cost_per_month_EBS = 0
    pricing_client = boto3.client('pricing', region_name='us-east-1')

    # get cost info for all ec2 instances
    for e in ec2:
        # update individual price
        e['price per month USD'] = get_ec2_cost(e['region'], e['name'], e['os'], e['quantity'], pricing_client, 730)
        # update the total cost
        total_cost_per_month_EC2 += e['price per month USD']
    # get cost info for all ebs volumes
    for x in ebs:
        # update individual price
        x['price per month USD'] = get_ebs_cost(x['region'], x['type'], x['name'], x['quantity'], x['GB'], pricing_client)
        # update the total cost
        total_cost_per_month_EBS += x['price per month USD']    
    
    total_cost_per_month = total_cost_per_month_EBS + total_cost_per_month_EC2
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'compute costs' : ec2,
            'storage costs' : ebs,
            'total EC2 cost per month USD' : total_cost_per_month_EC2,
            'total EBS cost per month USD' : total_cost_per_month_EBS,
            'total cost per month USD' : total_cost_per_month

        })
    }

