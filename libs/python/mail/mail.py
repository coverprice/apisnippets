#!/usr/bin/python3
import os
import pprint

import base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes

from apiclient import errors
from googleapiclient.errors import HttpError


def send_message(service, user_id, message_json):
    """
    Send an email message

    Args:
      service:      Authorized Gmail API service instance.
      user_id:      Target's email address. The special value "me" can be used to indicate
                    the authenticated user.
      message_json: Message to be sent. A dict generated from create_message or create_message_with_attachment

    Returns:
      dict with info about the sent message.
    """
    try:
        response = service.users().messages().send(userId=user_id, body=message).execute()
        # The response is a dict of info about the message
        # print('Message Id: {}'.format(message['id']))
        return message
    except errors.HttpError:
        raise


def create_message(sender, to, subject, message_text):
    """
    Create a message for an email, suitable to be sent with send_message() above.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


def create_message_with_attachment(
        sender,
        to,
        subject,
        message_text,
        file_dir,
        filename,
    ):
    """
    Create a message for an email, suitable to be sent with send_message() above.
  
    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.
      file_dir: The directory containing the file to be attached.
      filename: The name of the file to be attached.
  
    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
  
    msg = MIMEText(message_text)
    message.attach(msg)
  
    path = os.path.join(file_dir, filename)
    content_type, encoding = mimetypes.guess_type(path)
  
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    with open(path, 'rb') as fp:
        if main_type == 'text':
            msg = MIMEText(fp.read(), _subtype=sub_type)
        elif main_type == 'image':
            msg = MIMEImage(fp.read(), _subtype=sub_type)
        elif main_type == 'audio':
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
        else:
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
  
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)
  
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}
