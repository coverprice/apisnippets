#!/bin/env python3

from pprint import pprint
import tempfile
import subprocess
import logging
logger = logging.getLogger(__name__)
import googledocsapi

from .UserToCreate import (
    UserToCreate,
    UserCreateStatus,
)

SHEET_NAME = 'Form Responses 1'
MIN_ROW = 2
MAX_ROW = 100       # The largest row # to process
STATUS_COLUMN = 'I'
ERROR_NOTES_COLUMN = 'J'

def get_cell_range(left_col, right_col):
   return '{sheet_name}!{left_col}{min_row}:{right_col}{max_row}'.format(
        sheet_name=SHEET_NAME,
        left_col=left_col,
        min_row=MIN_ROW,
        right_col=right_col,
        max_row=MAX_ROW,
    )

class GoogleSheetsDataBridge(object):
    def __init__(self,
            spreadsheet_id : str,
            service_account_file : str,
        ):
        self.spreadsheet_id = spreadsheet_id
        logger.debug('Connecting to Google Sheets API')
        self.service = googledocsapi.SheetService.new_instance(
            spreadsheet_id=spreadsheet_id,
            service_account_file=service_account_file,
        )


    def fix_up_user_status(self) -> None:
        """
        When a user is added to the row by the Google Form, the Status column is blank (because that's not part of the form).
        This method reads in the Status column and populates any missing ones.
        """
        logger.debug('Fixing up the status values , id: {}'.format(self.service.spreadsheet_id))
        cells = self.service.read_cells(cell_range=get_cell_range(STATUS_COLUMN, STATUS_COLUMN))

        write_buffer = googledocsapi.SheetWriteBuffer()
        for row_idx in range(0, cells.height()):
            status = cells.get_cell(row_idx, 0)
            if status is None or status == '':
                write_buffer.set(
                    cell=cells.get_relative_cell(row_idx=row_idx,  col_idx=0),
                    value='In Review',
                )
        if write_buffer.num_pending_writes():
            logger.debug('Updating {} user status cells.'.format(write_buffer.num_pending_writes()))
            self.service.update_cells(write_buffer)


    def get_users_to_create(self) -> list:
        logger.debug('Retrieving values from Google spreadsheet, id: {}'.format(self.service.spreadsheet_id))
        cells = self.service.read_cells(cell_range=get_cell_range('B', STATUS_COLUMN))

        users_to_create = []
        for row_idx in range(0, cells.height()):
            email = cells.get_cell(row_idx, 0)
            if email is None or email == '':
                # No email address, so ignore this row.
                continue
            email = email.lower().strip()

            status = cells.get_cell(row_idx, 7)
            if status != 'Approved-but-not-created':
                continue

            gpg_key = cells.get_cell(row_idx, 6)
            if "-----BEGIN PGP PUBLIC KEY BLOCK-----" not in gpg_key:
                gpg_key = None

            # TODO - if we want to update the user status, we'll have to add the sheet row # into the object.
            users_to_create.append(UserToCreate(
                user_id=email,
                gpg_key=gpg_key,
                spreadsheet_row=row_idx + 2,
            ))
        return users_to_create


    def update_user_status(self, users : list) -> None:
        """
        After an account is successfully created, update the 'Status' column in the spreadsheet.
        """

        def update_status(user, new_value):
            write_buffer.set(
                cell=googledocsapi.CellRange(sheet=SHEET_NAME, top_left_col=STATUS, top_left_row=user.spreadsheet_row),
                value=new_value,
            )

        def update_error_notes(user, new_value):
            write_buffer.set(
                cell=googledocsapi.CellRange(sheet=SHEET_NAME, top_left_col=ERROR_NOTES_COLUMN, top_left_row=user.spreadsheet_row),
                value=new_value,
            )

        logger.debug('Updating the spreadsheet to reflect the new User status.')
        write_buffer = googledocsapi.SheetWriteBuffer()
        for user in users:
            assert(user.spreadsheet_row is not None)
            if user.status == UserCreateStatus.ACCOUNT_CREATED:
                update_status('Account created')
                update_error_notes(user, None)
            elif user.status == UserCreateStatus.FAILED_PREFLIGHT_CHECK:
                update_error_notes(user, ', '.join(user.errors))

        if write_buffer.num_pending_writes():
            logger.debug('Updating {} user status cells.'.format(write_buffer.num_pending_writes()))
            self.service.update_cells(write_buffer)
