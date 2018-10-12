#!/usr/bin/python3
import logging
logger = logging.getLogger(__name__)

import base64
import mimetypes
import pprint
from apiclient import errors
from googleapiclient.errors import HttpError


class EmailSender(object):
    def __init__(self, service):
        """
        @param service:         Authorized Gmail API service instance.
        """
        self.service = service

    def send(self, mime_message):
        """
        Send an email message using the Gmail API

        @param mime_message:    email.mime.MIMEText or email.mime.MIMEMultipart
                                message to be sent.
        @return dict with info about the sent message.
        """
        message = {
            'raw': base64.urlsafe_b64encode(mime_message.as_string().encode()).decode()
        }
        # TechDebt - Gmail has a separate (but more complex) API for sending S/MIME messages that
        # is more appropriate for sending encrypted contents.
        try:
            # userId indicates who to send the mail as.
            # userId='me' is a special value that indicates the authenticated user.
            response = self.service.users().messages().send(userId='me', body=message).execute()
            # The response is a dict of info about the message
            # print('Message Id: {}'.format(message['id']))
            return response
        except errors.HttpError:
            raise


class FakeEmailSender(EmailSender):
    """
    Used for debugging and dry-runs.
    """
    def send(self, mime_message):
        logger.debug('Pretended to send a message from "{}", to "{}"'.format(mime_message['from'], mime_message['to']))
