# Author: Caleb Grode
# Purpose: Returns region NAMES not CODES. We need these for pricing API call.
#          A region name: 'US East (Ohio)'. A region code: 'us-east-2'

from inspect import Parameter
import json
import boto3

def lambda_handler(event, context):

    # List all regions codes
    data = boto3.client('ec2').describe_regions(AllRegions=True)
    region_codes = []
    for r in data['Regions']:
        region_codes.append(r['RegionName'])
    while "NextToken" in data:
        data = boto3.client('ec2').describe_regions()
        for r in data['Regions']:
            region_codes.append(r['RegionName'])
 
    
    # Get all region names using the region codes
    client = boto3.client('ssm')
    region_names = []
    for region in region_codes:
        response = client.get_parameter(
            Name='/aws/service/global-infrastructure/regions/' + region + '/longName'
        )
        region_names.append(response['Parameter']['Value'])   
    print(region_names)
    return {
        'statusCode': 200,
        'body': json.dumps(region_names)
    }
