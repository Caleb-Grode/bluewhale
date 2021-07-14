import boto3

# get ec2 instance information
data = boto3.client('ec2').describe_instance_types()

# associates name with compute category
vm_types = {
    'm':'general purpose', 't':'general purpose', 'a':'general purpose', 
    'c':'compute optimized',
    'r':'memory optimized', 'u':'memory optimized', 'x':'memory optimized', 'z':'memory optimized',
    'i':'storage optimized', 'd':'storage optimized','h':'storage optimized',
    'p':'accelerated computing', 'inf':'accelerated computing', 'g':'accelerated computing', 'f':'accelerated computing'       
}


ec2_specs = []
for instance in data['InstanceTypes']:
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
            'vCPUs': instance['VCpuInfo']['DefaultVCpus'],
            'MemoryGB': str(round(int(instance['MemoryInfo']['SizeInMiB']/1000))), # convert from MiB to GB and round to nearest whole number
            'NetworkInfo': instance['NetworkInfo'],
            'provider': 'AWS'

        }
    )

# put data in DB
table = boto3.resource('dynamodb').Table('bluewhale_resources')
for item in ec2_specs:
    table.put_item(Item=item)

