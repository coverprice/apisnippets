#!/bin/env python3
import random
import secrets
from pprint import pprint


def generate_password(
        min_length : int,
        use_lowercase : bool,
        use_uppercase : bool,
        use_digits : bool,
        use_symbols : bool,
    ) -> str:
    """
    Generate a cryptographically-secure password, compatible with an AWS console account.
    """

    def chars_in_range(lo : str, hi : str):
        return [chr(x) for x in range(ord(lo), ord(hi)+1)]

    def add_chars(chars : list):
        choose_from_chars += chars
        # The new password must contain at least 1 character from this set, so add it here.
        new_password.append(secrets.choice(chars))
        
    new_password = []
    choose_from_chars = []
    if use_lowercase:
        add_chars(chars_in_range('a', 'z'))
    if use_uppercase:
        add_chars(chars_in_range('A', 'Z'))
    if use_digits:
        add_chars(chars_in_range('0', '9'))
    if use_symbols:
        add_chars(list(r"!@#$%^&*()_+-=[]{}|'"))     # This set of chars was copied from AWS's UI

    if len(choose_from_chars) == 0:
        raise Exception("Password policy gives us no password characters to choose from!")

    while len(new_password) < min_length:
        new_password.append(secrets.choice(choose_from_chars))   # secrets.choice is cryptographically-safe

    # The algorithm above ensures that at least 1 character is chosen from each required character
    # class (lowercase / uppercase / digits / symbols), but it means that the first 1-4 characters in new_password
    # have predicatable character classes. So we shuffle here to stymie that prediction.
    random.shuffle(new_password)
    return ''.join(new_password)
