# Author: Caleb Grode
# Purpose: Refresh the databse with GCP vm & Disk offerings

import json
import boto3
import os
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import base64
from botocore.exceptions import ClientError


def get_secret():
    secret_name = "bluewhale_gcp_app_creds"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret

print(get_secret())
secret = json.loads(get_secret())

with open('/tmp/cred.json', 'w') as json_file:
  json.dump(secret, json_file)

os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/tmp/cred.json'

def lambda_handler(event, context):
    # we want the information about the virtual machines that GCP offers
    # their API gives us info by GCP zone
    # to get all vm info we thus need to look through all zones
    zones = []
    credentials = GoogleCredentials.get_application_default()

    service = discovery.build('compute', 'v1', credentials=credentials)
    # Project ID for this request.
    project = 'learned-iris-320618'
    request = service.zones().list(project=project)
    while request is not None:
        response = request.execute()

        for zone in response['items']:
            # TODO: Change code below to process each `zone` resource:
            zones.append(zone['name'])

        request = service.zones().list_next(previous_request=request, previous_response=response)
    machines = {}

        # associates the first letter of a machine with its (AWS equivalent) compute category
    vm_types = {
        'e':'general purpose', 'n':'general purpose', 'f':'general purpose', 'g':'general purpose',
        'c':'compute optimized',
        'm':'memory optimized',
        'a':'accelerated computing'       
    }


    # get machine for each zones
    for zone in zones:
        request = service.machineTypes().list(project=project, zone=zone)
        while request is not None:
            response = request.execute()
            # get each machines details
            for machine_type in response['items']:
                machines[machine_type['name']] = {
                    'name' : machine_type['name'],
                    'vCPUs' : machine_type['guestCpus'],
                    'MemoryMB' : machine_type['memoryMb'],
                    'virtual machine type' : vm_types[machine_type['name'][0]],
                    'provider': 'GCP',
                    'resource type': 'virtual machine'
                }
            request = service.machineTypes().list_next(previous_request=request, previous_response=response)
    # now we have a list of all the machines!
    resource_table =  boto3.resource('dynamodb').Table('bluewhale_resources')
    # put machines into the DB
    for k in machines.keys():
        resource_table.put_item(Item=machines[k])
    return {
        'statusCode': 200,
        'body': json.dumps('Refresh complete!')
    }
