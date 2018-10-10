#!/bin/env python3

TEMPLATE = """
AWS account: {alias} ({account_id})
URL: https://{alias}.signin.aws.amazon.com/console

Username: {username}
Initial password: {password}

Run the following to update your ~/.aws/config & ~/.aws/credentials files:

cat >> ~/.aws/config <<EOF
[profile {alias}]
region = us-east-1
output = text
EOF

cat >> ~/.aws/credentials <<EOF
[{alias}]
aws_access_key_id = {access_key_id}
aws_secret_access_key = {secret_access_key}
EOF
"""

def gen_credentials_message(aws_user_info, aws_account_id, aws_account_alias):
    return TEMPLATE.format(
        alias=aws_account_alias,
        account_id=aws_account_id,
        username=aws_user_info['username'],
        password=aws_user_info['password'],
        access_key_id=aws_user_info['access_key_id'],
        secret_access_key=aws_user_info['secret_access_key'],
    ).lstrip()
