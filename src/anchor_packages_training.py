import json
from urllib.request import urlopen
from urllib.error import HTTPError

import boto3
import botocore
import config
from bs4 import BeautifulSoup
from collections import defaultdict


def train_anchor_packages():
    # set up client for s3 operations.
    client = boto3.client(
        's3',
        aws_access_key_id=config.AWS_S3_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_S3_SECRET_ACCESS_KEY,
        config=botocore.client.Config(signature_version='s3v4')
    )

    session = boto3.session.Session(aws_access_key_id=config.AWS_S3_ACCESS_KEY_ID,
                                    aws_secret_access_key=config.AWS_S3_SECRET_ACCESS_KEY)

    s3_resource = session.resource('s3', config=botocore.client.Config(
        signature_version='s3v4'))

    bucket = s3_resource.Bucket(config.AWS_BUCKET_NAME)

    # get a paginator to list all objects from bucket.
    paginator = client.get_paginator('list_objects')
    # denotes the sub-folder name from which to collect data : <bucket_name>/<prefix>
    folder_prefix = 'maven/'
    maven_package_list = []
    # collect all the prefixes (i.e package name) for folders in a paginated way.
    for result in paginator.paginate(Bucket='prod-bayesian-core-data', Prefix=folder_prefix, Delimiter='/'):
        for o in result.get('CommonPrefixes'):
            print(o.get('Prefix'))
            maven_package_list.append(o.get('Prefix').split("maven", 1)[1].rstrip('/').lstrip('/'))

    set_of_group_id = set()
    org_id_to_package_mapping = defaultdict(list)
    org_id_to_anchor_packages = defaultdict(list)

    # identify unique group ids from the package list.
    for package in maven_package_list:
        set_of_group_id.add(package.split(':')[0])

    # map packages to their respective group ids.
    for package in maven_package_list:
        key = package.split(':')[0]
        org_id_to_package_mapping[key].append(package)

    # this is the base url for scraping the data.
    base_url = "http://www.mvnrepository.com/artifact"

    # this threshold defines the number of packages that should be present at minimum in order for a group id to become a sub-ecosystem.
    sub_ecosystem_threshold = 200

    for group_id in set_of_group_id:
        if len(org_id_to_package_mapping[group_id]) >= sub_ecosystem_threshold:
            try:
                # this points to the group id page on mvnrepsoitory.
                # example url would look like: http://www.mvnrepository.com/artifact/<group_id>
                page_url = base_url + "/" + group_id
                print(page_url)
                page = urlopen(page_url)
                soup = BeautifulSoup(page, 'html.parser')
                anchor_package_threshold = -1
                list_subtitle = soup.find_all('div', attrs={'class': 'im'})
                for subtitle in list_subtitle:
                    package_usages_anchor = subtitle.find('a', attrs={'class': 'im-usage'})
                    if package_usages_anchor is not None:
                        package_usages = int(package_usages_anchor.find('b').string.replace(',', ''))
                        # collecting top 30% packages and marking them as anchor for the sub-ecosystem.
                        anchor_package_threshold = package_usages * 0.3 \
                            if anchor_package_threshold == -1 \
                            else anchor_package_threshold
                        if package_usages >= anchor_package_threshold:
                            package_name = subtitle.find('p', attrs={'class': 'im-subtitle'}).find('a').string
                            print(package_name, anchor_package_threshold, package_usages)
                            org_id_to_anchor_packages[group_id].append(package_name)
                            # print(type(soup.find_all('p', attrs={'class': 'im-subtitle'})))

            except HTTPError as http_error:
                print(http_error.msg, http_error.code)

    with open('anchor-packages.json', 'w') as anchor_package_file:
        json.dump(org_id_to_anchor_packages, anchor_package_file)

    bucket.upload_file('anchor-packages.json', 'anchor-packages.json')

    # s3_resource.Object(config.AWS_BUCKET_NAME, "anchor-packages.json").put(Body=json.dumps(org_id_to_anchor_packages))
    return json.dumps(org_id_to_anchor_packages)
