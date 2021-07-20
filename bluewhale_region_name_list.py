# Author: Caleb Grode
# Purpose: Returns region NAMES not CODES. We need these for an API call.
#          A region name: 'US East (Ohio)'. A region code: 'us-east-2'

import json
import boto3

def lambda_handler(event, context):
    # List all regions codes
    client = boto3.client('ec2')
    region_codes = [region['RegionName'] for region in client.describe_regions()['Regions']]
    
    # Get all region names using the region codes
    client = boto3.client('ssm')
    region_names = []
    for region in region_codes:
        response = client.get_parameter(
            Name='/aws/service/global-infrastructure/regions/' + region + '/longName'
        )
        region_names.append(response['Parameter']['Value'])   
    
    return {
        'statusCode': 200,
        'body': json.dumps(region_names)
    }
