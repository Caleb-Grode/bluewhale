import json
import boto3

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
        ebs_data = details['product']['attributes']
        ebs_data['name'] = details['product']['attributes']['volumeApiName']
        ebs_data['provider'] = 'AWS'
        ebs_data['resource type'] = 'virtual disk'
        refresh_data.append(ebs_data)
    



ebs_refresh()