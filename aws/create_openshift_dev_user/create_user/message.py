#!/bin/env python3

MAIN_MESSAGE = """
<p>
  You have been provisioned an IAM account in the {alias} AWS account. This account is
  intended for OpenShift 4.0 development. Your encrypted credentials are attached to this
  email.
</p>

<p>
  Please read <a href="https://docs.google.com/document/d/1j7bhLXT_cIAjpMh_x2jeegtpE7495Mj5A-EcQsgZEDo/edit">these instructions</a>
  for standing up a cluster, including Route 53 specifics.
</p>

<p>
  <em>Current status:</em><br />
  <ul>
    <li>
      You have full account admin privileges. Do not abuse them! Over time we will be
      locking these down to just the essentials.
    </li>
    <li>
      <em>There is no resource pruning, and service limits are tight.</em> Clean up
      after yourself!
    </li>
  </ul>
</p>

<p>
  Any problems, please contact the DPP team:
  <ul>
    <li>in the <a href="https://coreos.slack.com/messages/CBUT43E94">#forum-dp-platform</a></li>
    <li>file a ticket at <a href="mailto:openshift-service-requests@redhat.com">openshift-service-requests@redhat.com</a></li>
  </ul>
</p>

<p>
  Others can sign up for this AWS account with <a href="https://goo.gl/forms/9zrAZ0pERWSdrLrR2">this sign-up form</a>.
</p>

<p>
  Thanks,
</p>

<p>
  The Developer Productivity Platform team
</p>
"""


CREDENTIALS_TEMPLATE = """
AWS account: {alias} ({account_id})
URL: https://{alias}.signin.aws.amazon.com/console

Username: {username}
Initial password: {password}

Run the following to update your ~/.aws/config & ~/.aws/credentials files:

cat >> ~/.aws/config <<"EOF"
[profile {alias}]
region = us-east-1
output = text
EOF

cat >> ~/.aws/credentials <<"EOF"
[{alias}]
aws_access_key_id = {access_key_id}
aws_secret_access_key = {secret_access_key}
EOF
"""

def gen_main_message(aws_account_alias):
    """
    This is the unencrypted "welcome" message.
    """
    return MAIN_MESSAGE.format(
        alias=aws_account_alias,
    ).lstrip()


def gen_credentials_message(aws_account_alias, aws_account_id, aws_user_info):
    """
    This is the message that will be encrypted.
    """
    return CREDENTIALS_TEMPLATE.format(
        alias=aws_account_alias,
        account_id=aws_account_id,
        username=aws_user_info['username'],
        password=aws_user_info['password'],
        access_key_id=aws_user_info['access_key_id'],
        secret_access_key=aws_user_info['secret_access_key'],
    ).lstrip()
