# Author: Caleb Grode
# Purpose: Match each GCP and Azure vm with up to 5 AWS matches. Add string set of AWS instance names to each 3rd party vm object in DynamoDB

import json
import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr

# this function can throttle DynamoDB
# with 5 RCUs it takes about 26 minutes
# with 250 RCUs it takes about 1.5 minutes

def match_vm(vm,t):
    # get vm specs
    vCPUs = vm['vCPUs']
    memory = vm['MemoryMB']
    type = vm['virtual machine type']

    # query for potential matches
    matches = t.scan(
            # virtual machine from AWS which has the same type and more or equal vCPUs and similar ram capacity
            FilterExpression= Attr('resource type').eq('virtual machine') 
                            & Attr('provider').eq('AWS')
                            & Attr('virtual machine type').eq(type)
                            & Attr('vCPUs').gte(vCPUs)
                            # memory in range inf to (-20%)
                            & Attr('MemoryMB').gte(int(float(memory) - (float(memory)*0.2)))
    )


    # edge case where AWS does not offer large enough instance in terms of vCPUs
    if not matches['Items']:
        # if this is the case, we will return the largest possible instance
        # get all of the specified type
        data = t.scan(
            FilterExpression= Attr('resource type').eq('virtual machine') 
                            & Attr('provider').eq('AWS')
                            & Attr('virtual machine type').eq(type)   
        )
        if not data['Items']:
            return []
        # find the highest number of vCPUs for potential match
        values = [x['vCPUs'] for x in data['Items']]
        max_vCPUs = max(values)

        # add all instances of this largest size to a list
        largest_matches = []
        for instance in data['Items']:
            if instance['vCPUs'] == max_vCPUs:
                largest_matches.append(instance['name'])
        
        return largest_matches
    
    # find the lowest number of vCPUs for potential match
    values = [x['vCPUs'] for x in matches['Items']]
    min_vCPUs = min(values)


    # add all instances with that many vCPUs to list
    # find the lowest amount of memory at the same time
    matched_instances = []
    potential_matches = []
    for instance in matches['Items']:
        if instance['vCPUs'] == min_vCPUs:
            potential_matches.append(instance)

    # we now have the instances matched by vCPUs now we need to match by memory

    # we are going to try to find the 5 closest instances in memory
    for i in range(0,5):
        # while we still have options
        if potential_matches:
            # find the closest instance
            closest = min(potential_matches, key=lambda x:abs(x['MemoryMB']-vm['MemoryMB']))
            # add the instance to our final list
            matched_instances.append(closest['name'])
            
            # remove the closest from the potential matches so we can find the next closest
            potential_matches = [i for i in potential_matches if not (i['name'] == closest['name'])]
            
            # repeat 5x

    return matched_instances
    
    
def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('bluewhale_resources')
    
    print("Getting data...")
    # get azure and gcp vm data
    third_party_vm = table.scan(
        FilterExpression= Attr('resource type').eq('virtual machine') & (Attr('provider').eq('Azure') or Attr('provider').eq('GCP'))
        )
    
    print("begin matching...")
    counter = 0
    # add in the AWS matches to each vm!
    for vm in third_party_vm['Items']:
        counter = counter + 1
        print(str(counter) + ' ' + vm['name'])
    
        matches = match_vm(vm,table)
        table.update_item(
            Key={
                'name': vm['name']
                },
            UpdateExpression="set AWS_matches=:a",
            ExpressionAttributeValues={
                ':a': matches
            },
            ReturnValues="UPDATED_NEW"
        )
    print("done!")
    return {
        'statusCode': 200,
        'body': json.dumps('Matching complete!')
    }
