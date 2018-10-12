#!/bin/env python3

"""
This file contains a higher-level API for reading/writing Google Sheets.
"""

from ..apiutils import get_sheets_service
from .CellRange import CellRange
from .CellRangeData import CellRangeData
from .SheetWriteBuffer import SheetWriteBuffer

class SheetService(object):
    """
    This class offers a friendly interface to the Google Sheets API. It supports easy read/write of blocks of data.
    """
    def __init__(self, service, spreadsheet_id):
        """
        It's recommended to use the static new_instance() method below to instantiate this class.
        """
        self.service = service
        self.spreadsheet_id = spreadsheet_id


    @staticmethod
    def new_instance(spreadsheet_id : str, service_account_file : str):
        """
        @param service_account_file - path to the service account credentials file for accessing this spreadsheet
        @param spreadsheet_id - the ID of the spreadsheet (the long hexdigits in the spreadsheet's URL)
        """
        service = get_sheets_service(
            service_account_file=service_account_file,
            read_only=False,
        )
        return SheetService(service=service, spreadsheet_id=spreadsheet_id)


    def read_cells(self, cell_range : str) -> CellRangeData:
        """
        @param cell_range - a string describing the block of cells to read, e.g. "Sheet 1!B2:C4"
        """
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=cell_range,
        ).execute()

        return CellRangeData.from_read_result(
            cell_range=CellRange.from_string(cell_range),
            result_rows=result.get('values', []),
        )


    def update_cells(self, buf : SheetWriteBuffer) -> None:
        data = [
            {
                'range': cell_ref,
                'values': [[str(value)]]
            }
            for cell_ref, value in buf.cells.items()
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

        # TODO - deal with result
