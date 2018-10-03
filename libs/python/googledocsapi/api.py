#!/bin/env python3

import google.oauth2.service_account
import apiclient.discovery

SHEETS_SCOPES_READ_ONLY = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEETS_SCOPES_READ_WRITE = ['https://www.googleapis.com/auth/spreadsheets']

def getSheetsService(service_account_file, read_only=False):
    scopes = SHEETS_SCOPES_READ_ONLY if read_only else SHEETS_SCOPES_READ_WRITE
    credentials = google.oauth2.service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=scopes,
    )
    service = apiclient.discovery.build('sheets', 'v4', credentials=credentials)
    return service


class SheetWriteBuffer(object):
    def __init__(self):
        self.cells = {}

    def set(self, sheet_name, cell : str, value):
        """
        @param sheet_name - string (e.g. 'Sheet 1') | None for the first visible sheet.
        @param cell - string - cell reference to set, e.g. 'C2'
        @param value - mixed - value to place into the cell
        """
        sheet = '{0}!'.format(sheet_name) if sheet_name else ''
        ref = '{0}{1}'.format(sheet, cell)
        self.cells[ref] = value

    def getCells(self):
        return self.cells


def newSheetService(service_account_file, spreadsheet_id):
    service = getSheetsService(
        service_account_file=service_account_file,
        read_only=False,
    )
    return SheetService(service=service, spreadsheet_id=spreadsheet_id)


class SheetService(object):
    def __init__(self, service, spreadsheet_id):
        self.service = service
        self.spreadsheet_id = spreadsheet_id

    def readCells(self, cell_range : str) -> list:
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=cell_range,
        ).execute()
        return result.get('values', [])

    def writeBuffer(self, buf : SheetWriteBuffer) -> None:
        data = [
            {
                'range': cell_ref,
                'values': [[str(value)]]
            }
            for cell_ref, value in buf.getCells().items()
        ]
        if len(data) == 0:
            # Nothing to do
            return

        body = {
            'valueInputOption': 'RAW',
            'data': data,
        }

        result = self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=body,
        ).execute()
