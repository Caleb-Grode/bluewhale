# Author: Caleb Grode
# Purpose: This function calls an Azure API to retrieve specs about the different Azure VM & virtual disk offerings. 
#          It categorizes and selects the desired specs for every returned instance and puts them into the DynamoDB
#          table 'bluewhale_resources'

import json
import requests
import adal
import boto3
from decimal import Decimal
import os

# timeout: 30 seconds (takes about 15)
# memory: 512MB (uses about 251)

def lambda_handler(event, context):

    # info for azure authentification
    azure_client_id = os.environ['azure_client_id']
    azure_secret = os.environ['azure_secret']
    azure_subscription_id = os.environ['azure_subscription_id']
    azure_tenant = os.environ['azure_tenant']
    authority_url = 'https://login.microsoftonline.com/' + azure_tenant
    resource = 'https://management.azure.com/'
    
    # for API request
    context = adal.AuthenticationContext(authority_url)
    token = context.acquire_token_with_client_credentials(resource, azure_client_id, azure_secret)
    
    # API request header
    headers = {'Authorization': 'Bearer ' + token['accessToken'], 'Content-Type': 'application/json'}
    # API params and url
    params = {'api-version': '019-04-01'}
    url = 'https://management.azure.com/subscriptions/'+azure_subscription_id+'/providers/Microsoft.Compute/skus'
    
    
    print("calling API")
    azure_SKUs_JSON = requests.get(url, headers=headers, params=params)
    print("API called!")
    azure_SKUs_JSON = azure_SKUs_JSON.json()

    
    # now we have our Azure data
    # begin parsing
    
    vm = []
    disk = []
    for j in azure_SKUs_JSON['value']:
            # grab all VMs
        if j['resourceType'] == 'virtualMachines':
            vm.append(
                j
            )
        # grab all disks
        elif j['resourceType'] == 'disks':
            disk.append(
                j
            )
    
    # associates the first letter of a vm size with its (AWS equivalent) compute category
    vm_types = {
        'D':'general purpose', 'A':'general purpose', 'B':'general purpose', 
        'F':'compute optimized','H':'compute optimized',
        'E':'memory optimized', 'M':'memory optimized', 'G':'memory optimized',
        'L':'storage optimized',
        'N':'accelerated computing',
        'P':'unknown edge case'        
    }
    
    # parse out the specifications of the VMs
    all_vm_specs = []
    name_dict = {}
    for v in vm:       
        vm_specs = {}
        vm_specs['name'] = v['name']
        vm_specs['virtual machine type'] = vm_types[v['size'][0]] # categorize the vm type based off above dictionary
        for c in v['capabilities']:
            if c['name'] == 'vCPUs' or c['name'] == 'MemoryGB' or c['name'] == 'ACUs' or c['name'] == 'vCPUsPerCore' or c['name'] == 'MaxResourceVolumeMB' or c['name'] == 'GPUs':
                
                if c['name'] == 'MemoryGB':
                    vm_specs['MemoryMB'] = int(Decimal(c['value'])*1000) # convert to GB
                if c['name'] == 'vCPUs' or c['name'] == 'vCPUsPerCore':
                    vm_specs[c['name']] = int(c['value'])
                else:
                    vm_specs[c['name']] = c['value']
        name_dict[v['name']] = vm_specs

    


    # add in data columns
    for key,value in name_dict.items():   
        value['resource type'] = 'virtual machine'
        value['provider'] = 'Azure'
        all_vm_specs.append(value)
        
    
    # parse out the specifications of the disks
    name_dict.clear()
    all_disk_specs = []
    for d in disk:
        disk_specs = {}
        disk_specs['name'] = d['name']
        disk_specs['size'] = d['size']
        for c in d['capabilities']:
            disk_specs[c['name']] = c['value']
        name_dict[d['name']] = disk_specs
           
    for ky,val in name_dict.items():
        val['resource type'] = 'virtual disk'
        val['provider'] = 'Azure'
        all_disk_specs.append(val)

    # now we have the data we want!


    print('Number of VMs: ' + str(len(all_vm_specs)))
    print('Number of disks: ' + str(len(all_disk_specs)))


    print("Inputing VMs into DB...")
    # put the data into the database
    azure_vm_table = boto3.resource('dynamodb').Table('bluewhale_resources')
    for item in all_vm_specs:
        azure_vm_table.put_item(Item=item)
    print("Done!")
    
    print("Inputing disks into DB...")
    azure_disk_table = boto3.resource('dynamodb').Table('bluewhale_resources')
    for item in all_disk_specs:
        azure_disk_table.put_item(Item=item)
    print("Done!")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Refresh complete!')
    }
