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


class Operations(object):
    """
    Abstract class for making various AWS operations easier
    """
    def __init__(self, session, aws_client):
        self.session = session
        self.aws_client = aws_client


    @classmethod
    def get_service_client_name(cls):
        raise NotImplemented()

    @classmethod
    def for_session(cls, aws_session : AwsSession):
        """
        Use this factory method when you have a session that's already tied to the account you want the API client for
        """
        return cls(
            session=aws_session.session,
            aws_client=aws_session.get_client(service_name=cls.get_service_client_name()),
        )

    @classmethod
    def for_account(cls, aws_session : AwsSession, credentials : dict):
        """
        Use this factory method when you have a session tied to an AWS account, but you want an API client for a different account.

        Given the ephemeral credentials (which also imply a specific sub-account),
        and return a Route53 client for that sub-account with those credentials.
        """
        return cls(
            session=aws_session.session,
            aws_client=aws_session.get_client_for_account(
                service_name=cls.get_service_client_name(),
                credentials=credentials,
            ),
        )
