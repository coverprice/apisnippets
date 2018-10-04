#!/bin/env python3

from pprint import pprint
import sys
import os.path
import tempfile
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs', 'python'))
import googledocsapi.api

SPREADSHEET_ID = '1TxlsWyV970ct9EYaPrnSU5Ag7eTKw3Yfi2zfLsfqgxM'
SERVICE_ACCOUNT_FILE = os.path.expanduser('~/.secrets/gcp_service_accounts/openshift-devproducti-3fd6f7ce7d12.json')

service = googledocsapi.api.getSheetsService(
    service_account_file=SERVICE_ACCOUNT_FILE,
    read_only=True,
)

# Call the Sheets API
result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Form Responses 1!B2:I8',
    ).execute()
values = result.get('values', [])
if not values:
    print('No data found.')
    sys.exit(1)

records = []
for row in values:
    if len(row) < 8:
        continue
    status = row[7] if len(row) >= 8 else 'In Review'
    if status not in ['In Review', 'Approved-but-not-created']:
        continue
    records.append({
        'email': row[0],
        'name': row[4],
        'gpg_key': row[6],
        'status': status,
    })

with tempfile.TemporaryDirectory() as temp_dir:
    keyfile = os.path.join(temp_dir, 'keyfile')
    for record in records:
        print("{name}\t\t{email}".format(name=record['name'], email=record['email']))

        with open(keyfile, 'w') as kf:
            kf.write(record['gpg_key'])

        subprocess.check_output([
            './aws/create_openshift_dev_user.py',
            '--keyfile', keyfile,
            '--outfile', './{}.gpg'.format(record['email']),
            '--skip-account-create',
            record['email']
        ])
