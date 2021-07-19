import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr
import time
start = time.time()

dynamodb = boto3.resource('dynamodb', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

table = dynamodb.Table('bluewhale_resources')

# query for AWS vm
AWS_vm= table.scan(
            # virtual machine from AWS which has the same type and more or equal vCPUs and similar ram capacity
            FilterExpression= Attr('resource type').eq('virtual machine') 
                            & Attr('provider').eq('AWS')
)

def match_vm(vm,t):
    # get vm specs
    vCPUs = vm['vCPUs']
    memory = vm['MemoryMB']
    type = vm['virtual machine type']
    potential_matches = []
    matched_instances = []

    # filter potential matches
    for vm in AWS_vm['Items']:
        if vm['virtual machine type'] == type and 'vCPUs' == vCPUs and 'MemoryMB' >= int(float(memory) - (float(memory)*0.2)):
            potential_matches.append(vm)

    # edge case where AWS does not offer large enough instance in terms of vCPUs
    if not potential_matches:
        # if this is the case, we will return the largest possible instance
        # get all of the specified type
        data = t.scan(
            FilterExpression= Attr('resource type').eq('virtual machine') 
                            & Attr('provider').eq('AWS')
                            & Attr('virtual machine type').eq(type)   
        )
        if not data['Items']:
            return []
        # find the lowest number of vCPUs for potential match
        values = [x['vCPUs'] for x in data['Items']]
        max_vCPUs = max(values)

        # add all instances of this largest size to a list
        largest_matches = []
        for instance in data['Items']:
            if instance['vCPUs'] == max_vCPUs:
                largest_matches.append(instance['name'])
        
        return largest_matches
    
    # find the lowest number of vCPUs for potential match
    
    min_vCPUs = min(potential_matches, key=lambda x:x['vCPUs'] == vm['vCPUs'])

    # we now have the instances matched by vCPUs now we need to match by memory


    # we are going to try to find the 5 closest instances in memory
    for i in range(0,5):
        # while we still have options
        if min_vCPUs:
            # find the closest instance
            closest = min(min_vCPUs, key=lambda x:abs(x['MemoryMB']-vm['MemoryMB']))
            # add the instance to our final list
            matched_instances.append(closest['name'])
            
            # remove the closest from the potential matches so we can find the next closest
            potential_matches = [i for i in potential_matches if not (i['name'] == closest['name'])]
            
            # repeat 5x

    return matched_instances

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




