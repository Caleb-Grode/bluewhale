# Author: Caleb Grode
# Purpose: This function calls an EC2 API to retrieve specs about the different AWS EC2 offerings. 
#          It categorizes and selects the desired specs for every returned instance and puts them into the DynamoDB
#          Table 'bluewhale_resources'


import boto3
import json

def ebs_refresh():
    # this is one of the few hard coded values, if a new category is updated, this will need to change
    ebs_categories = ['Magnetic', 'General Purpose', 'Provisioned IOPS', 'Throughput Optimized HDD', 'Cold HDD']

    pricing_client = boto3.client('pricing', region_name='us-east-1')

    # get all ebs products
    # this block is an API call that parses the json data
    ebs_details = []
    ebs_names = []
    for ebs_type in ebs_categories:
        response = ["NextToken"]
        while "NextToken" in response:
            response = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': ebs_type}])

            for priceItem in response["PriceList"]:
                priceItemJson = json.loads(priceItem)
                name = priceItemJson['product']["attributes"]['volumeApiName']
                if name not in ebs_names:
                    ebs_names.append(name)
                    ebs_details.append(priceItemJson)
    
    # we now have data about the volumes but need to parse out and only grab that data we want for the DB
    refresh_data = []
    # get the name and attributes for each!
    for details in ebs_details:
        attrs = details['product']['attributes']
        ebs_data = {}
        ebs_data['name'] = attrs['volumeApiName']
        ebs_data['provider'] = 'AWS'
        ebs_data['resource type'] = 'virtual disk'
        ebs_data['maxIopsvolume'] = attrs['maxIopsvolume']
        ebs_data['maxThroughputvolume'] = attrs['maxThroughputvolume']
        ebs_data['maxVolumeSize'] = attrs['maxVolumeSize']
        ebs_data['storageMedia'] = attrs['storageMedia']
        ebs_data['volumeType'] = attrs['volumeType']
        ebs_data['MaxSizeGiB'] = int(attrs['maxVolumeSize'].split(' ')[0]) * 1024
        refresh_data.append(ebs_data)
    
    return refresh_data

def lambda_handler(event, context):
    # get ec2 instance information
    data = boto3.client('ec2').describe_instance_types()
    
    instances = data['InstanceTypes']
    
    while "NextToken" in data:
        data = boto3.client('ec2').describe_instance_types(NextToken=data["NextToken"])
        instances.extend(data['InstanceTypes'])
    
    # associates name with compute category
    vm_types = {
        'm':'general purpose', 't':'general purpose', 'a':'general purpose', 
        'c':'compute optimized',
        'r':'memory optimized', 'u':'memory optimized', 'x':'memory optimized', 'z':'memory optimized',
        'i':'storage optimized', 'd':'storage optimized','h':'storage optimized',
        'p':'accelerated computing', 'inf':'accelerated computing', 'g':'accelerated computing', 'f':'accelerated computing'       
    }
    
    print(len(instances))
    ec2_specs = []
    for instance in instances:
        # categorize instance
        if instance['InstanceType'][0] == 'i': # this block catches edge case where two different categories of instances start with 'i'
            if instance['InstanceType'][1] == '3':
                type = 'storage optimized'
            else:
                type = 'accelerated computing'
        else:
            type = vm_types[instance['InstanceType'][0]]
    
        # get data ready to be put in DB
        ec2_specs.append(
            {
                'name': instance['InstanceType'],
                'resource type' : 'virtual machine',
                'virtual machine type' : type,
                'vCPUs': int(instance['VCpuInfo']['DefaultVCpus']),
                'MemoryMB': int(int(instance['MemoryInfo']['SizeInMiB']) * 1.049), # conver from Mib to 
                'NetworkInfo': instance['NetworkInfo'],
                'provider': 'AWS'
    
            }
        )
    
    # put data in DB
    table = boto3.resource('dynamodb').Table('bluewhale_resources')
    for item in ec2_specs:
        table.put_item(Item=item)
    for item in ebs_refresh():
        table.put_item(Item=item)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Refresh complete!')
    }
