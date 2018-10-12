import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

from .Ec2Operations import (
    Ec2Operations,
)
__all__ = [
    'Ec2Operations',
]
