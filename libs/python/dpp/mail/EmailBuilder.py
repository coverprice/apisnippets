#!/usr/bin/python3
import os

from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes


class EmailBuilder(object):
    """
    Assists creating a MIMEMultipart message. Example

        builder = EmailBuilder(sender="ajones@example.com", to="recipient@example.com", subject="Some topic")
        builder.add_html_message('<h1>Great news!</h1>')
        builder.add_attachment_from_file('/path/to/dir', 'thing.jpg')
        send_message(builder.get_mime())
    """
    def __init__(self,
            to : str,
            subject : str,
            sender : str = 'me',
        ):
        """
        @param to:          Email address of the receiver.
        @param subject:     The subject of the email message.
        @param sender:      Email address of the sender. When using the GMail API, 'me' is
                            a special value that means the current authenticated user, *but*
                            the recipient will only see the email address,
                            e.g. 'youremail@domain.com'. If you want to include your full name,
                            specify it like so: "Your Full Name <youremail@domain.com>"

        """
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        self.message = message

    def get_mime_message(self):
        """
        @return MIMEMultipart message created so far
        """
        return self.message

    def add_message(self, body : str, subtype='text'):
        msg = MIMEText(body, _subtype=subtype)
        self.message.attach(msg)

    def add_html_message(self, body : str):
        self.add_message(body=body, subtype='html')

    def add_attachment_from_var(self,
            contents,
            filename : str,
            content_type='application/octet-stream',
        ):
        self.message.attach(
            _encapsulate_contents(contents=contents, content_type=content_type, filename=filename)
        )

    def add_attachment_from_file(self, file_dir : str, filename : str):
        path = os.path.join(file_dir, filename)
        content_type, encoding = mimetypes.guess_type(path)
      
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'

        self.message.attach(
            _encapsulate_contents(contents=fp.read(), content_type=content_type, filename=filename)
        )


def _encapsulate_contents(contents, content_type, filename):
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        msg = MIMEText(contents, _subtype=sub_type)
    elif main_type == 'image':
        msg = MIMEImage(contents, _subtype=sub_type)
    elif main_type == 'audio':
        msg = MIMEAudio(contents, _subtype=sub_type)
    else:
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(contents)

    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    return msg
