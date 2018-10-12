#!/bin/env python3

"""
boto3 & botocore are the AWS python API libraries. They can be installed with:

$ sudo dnf install python3-boto3 python3-botocore
"""

import boto3
import botocore
import functools
from pprint import pprint
from .AwsSession import AwsSession
from .Operations import Operations


class Route53Operations(Operations):
    @classmethod
    def get_service_client_name(cls):
        return 'route53'

    def get_hosted_zones(self):
        """
        @return a list of zones, with each zone looking like:
            {
                'Id': 'string',
                'Name': 'string',
                'CallerReference': 'string',
                'Config': {
                    'Comment': 'string',
                    'PrivateZone': True|False
                },
                'ResourceRecordSetCount': 123,
                'LinkedService': {
                    'ServicePrincipal': 'string',
                    'Description': 'string'
                }
            }
        """
        paginator = self.aws_client.get_paginator('list_hosted_zones')
        ret = []
        try:
            for response in paginator.paginate():
                ret += response['HostedZones']
        except botocore.exceptions.ClientError:
            print("Permission denied")
            return []

        ret = sorted(ret, key=lambda rec:str.lower(rec['Name']))
        return ret
