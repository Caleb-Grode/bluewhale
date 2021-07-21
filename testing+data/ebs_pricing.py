import boto3
import json

# code modified from: https://medium.com/@stefanroman/calculate-price-of-ebs-volumes-with-python-76687bb24530
aws_region_map = {
    'ca-central-1': 'Canada (Central)',
    'ap-northeast-3': 'Asia Pacific (Osaka-Local)',
    'us-east-1': 'US East (N. Virginia)',
    'ap-northeast-2': 'Asia Pacific (Seoul)',
    'us-gov-west-1': 'AWS GovCloud (US)',
    'us-east-2': 'US East (Ohio)',
    'ap-northeast-1': 'Asia Pacific (Tokyo)',
    'ap-south-1': 'Asia Pacific (Mumbai)',
    'ap-southeast-2': 'Asia Pacific (Sydney)',
    'ap-southeast-1': 'Asia Pacific (Singapore)',
    'sa-east-1': 'South America (Sao Paulo)',
    'us-west-2': 'US West (Oregon)',
    'eu-west-1': 'EU (Ireland)',
    'eu-west-3': 'EU (Paris)',
    'eu-west-2': 'EU (London)',
    'us-west-1': 'US West (N. California)',
    'eu-central-1': 'EU (Frankfurt)'
    }
ebs_name_map = {
    'standard': 'Magnetic',
    'gp2': 'General Purpose',
    'io1': 'Provisioned IOPS',
    'st1': 'Throughput Optimized HDD',
    'sc1': 'Cold HDD'
}
region = 'EU (Paris)'

pricing_auth = boto3.client('pricing', region_name="us-east-1")

for ebs_code in ebs_name_map:
    response = pricing_auth.get_products(ServiceCode='AmazonEC2', Filters=[
        {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': ebs_name_map[ebs_code]}, 
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region}])
    for result in response['PriceList']:
        json_result = json.loads(result)
        for json_result_level_1 in json_result['terms']['OnDemand'].values():
            for json_result_level_2 in json_result_level_1['priceDimensions'].values():
                for price_value in json_result_level_2['pricePerUnit'].values():
                    continue
    ebs_name_map[ebs_code] = float(price_value)
    print(ebs_name_map)