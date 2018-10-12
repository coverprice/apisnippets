#!/bin/env python3

import boto3
import botocore
import functools
from pprint import pprint
import sys
from ..AwsSession import AwsSession
from ..Operations import Operations


class Ec2Operations(Operations):
    @classmethod
    def get_service_client_name(cls):
        return 'ec2'

    def list_regions(self):
        """
        @return [str] - list of regions that the current account has access to, e.g. 'us-west-1', 'us-east-2', ...
        """
        response = self.aws_client.describe_regions()
        return [region['RegionName'] for region in response['Regions']]

    def list_instances(self):

        paginator = self.aws_client.get_paginator('describe_instances')
        ret = []
        try:
            for response in paginator.paginate():
                ret += response['Reservations']
        except botocore.exceptions.ClientError:
            return []

        # ret = sorted(ret, key=lambda rec:str.lower(rec['UserName']))
        return ret
