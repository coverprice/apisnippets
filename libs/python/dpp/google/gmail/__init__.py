import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

from .send import (
    EmailSender,
    FakeEmailSender,
)
__all__ = [
    'EmailSender',
    'FakeEmailSender',
]
