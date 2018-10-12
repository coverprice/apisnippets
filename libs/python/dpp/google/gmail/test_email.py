#!/usr/bin/python3

"""
Tests sending an email to yourself.
"""

import sys
import csv
from pprint import pprint
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import dpp.google
import dpp.mail

CLIENT_SECRET_FILE = os.path.expanduser('~/.secrets/gcp_service_accounts/client_secret_969537810335-lk3q1l1c4ftpp8d03a98lstmfrvbnd1h.apps.googleusercontent.com.json')
REFRESH_TOKEN_FILE = os.path.expanduser('~/.secrets/gcp_service_accounts/refresh_token.txt')
TARGET_EMAIL = 'jrussell@redhat.com'

gmail_service = dpp.google.get_gmail_service(
    client_secret_file=CLIENT_SECRET_FILE,
    refresh_token_file=REFRESH_TOKEN_FILE,
)
email_sender = dpp.google.EmailSender(service=gmail_service)
builder = dpp.mail.EmailBuilder(
    to=TARGET_EMAIL,
    subject="Test message",
)
builder.add_html_message(body="""
    <h1>Good news everyone!</h1>
    <p>Here is an HTML mail, with a <a href="https://redhat.com/">link and everything</a>.
    </p>
    """
)
email_sender.send(builder.get_mime_message())
