#!/usr/bin/python3
import logging
logger = logging.getLogger(__name__)

import base64
import functools
import mimetypes
import copy
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
    Used in place of EmailSender, this class can be used to redirect emails to other locations.
    It's used for debugging and dry-runs.
    The "redirect_to_email" feature can also be enabled to safely exercise the Gmail send() API without
    risking sending the real email to
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._do_send_to_self = False           # Should send() redirect the email to the Gmail API authenticated user?
        self._do_output_body = False            # Should the logging message also output the body?


    def send(self, mime_message):
        logger.debug('FakeEmailSender pretended to send an email from {sender} to {to}, subject: "{subject}"'.format(
            sender=mime_message['from'],
            to=mime_message['to'],
            subject=mime_message['subject'],
        ))
        if self._do_output_body:
            logger.debug(mime_message.as_string())

        if self._do_send_to_self:
            tmp_msg = copy.copy(mime_message)
            old_to_emails = tmp_msg['to'].split(',')
            intercepted_email = old_to_emails[0].strip()
            if len(old_to_emails) > 1:
                intercepted_email += ' and {} more'.format(len(old_to_emails) - 1)

            new_subject = "[Intercepted from {}] {}".format(intercepted_email, tmp_msg['subject'])

            # Note: we del before replacing the to & subject headers, because tmp_msg['some_header']
            # will actually add a header if it exists, not replace it. del removes all existing headers
            # of that name.
            del tmp_msg['to']
            del tmp_msg['cc']
            del tmp_msg['bcc']
            del tmp_msg['subject']
            tmp_msg['to'] = self._get_self_email()
            tmp_msg['subject'] = new_subject
            super().send(mime_message=tmp_msg)


    def send_to_self(self, enabled : bool):
        """
        @param email:       An email address to redirect all emails to, or None to disable (default)
        """
        self._do_send_to_self = enabled


    def output_body(self, enabled : bool):
        """
        @param enabled:     Enable/disable logging the mail body to the debug log (default: disabled)
        """
        self._do_output_body = enabled


    @functools.lru_cache()
    def _get_self_email(self):
        """
        @return - the email address of the Gmail API user
        """
        response = self.service.users().getProfile(userId='me').execute()
        return response['emailAddress']
