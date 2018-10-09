#!/bin/env python3

"""
boto3 & botocore are the AWS python API libraries. They can be installed with:

$ sudo dnf install python3-boto3 python3-botocore
"""

import boto3
import botocore
import functools
from pprint import pprint


class Route53Operations(object):
    """
    Class for making various IAM operations easier
    """
    def __init__(self, session, route53_client):
        self.session = session
        self.route53_client = route53_client


    @staticmethod
    def for_session(session):
        """
        Use this factory method when you have a session that's already tied to the account you want the IAM client for
        """
        client = session.client('route53')
        return Route53Operations(session=session, route53_client=client)


    @staticmethod
    def for_account(session, credentials):
        """
        Use this factory method when you have a session tied to an AWS account, but you want an Route53 client for a different account.

        Given the ephemeral credentials (which also imply a specific sub-account),
        and return a Route53 client for that sub-account with those credentials.
        """
        client = boto3.client(
            service_name='route53',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
        )
        return Route53Operations(session=session, route53_client=client)


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
        paginator = self.route53_client.get_paginator('list_hosted_zones')
        ret = []
        try:
            for response in paginator.paginate():
                ret += response['HostedZones']
        except botocore.exceptions.ClientError:
            print("Permission denied")
            return []

        ret = sorted(ret, key=lambda rec:str.lower(rec['Name']))
        return ret
