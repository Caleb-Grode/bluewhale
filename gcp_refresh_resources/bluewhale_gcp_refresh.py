import json
import boto3
import os
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/Users/grode/Documents/Bluewhale/code/bluewhale/gcp_refresh_resources/cred.json'


def lambda_handler():
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
                    'MemoryMB' : machine_type['memoryMb']
                }
            request = service.machineTypes().list_next(previous_request=request, previous_response=response)
    for k in machines.keys():
        print(machines[k])

lambda_handler()