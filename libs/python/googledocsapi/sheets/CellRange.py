#!/bin/env python3

import re
import copy


def colname_to_idx(col : str) -> int:
    """
    Converts a column name like "A" or "AA" into an index number, offset 0. A => 0, B => 1, ... AA => 26, AB => 27
    """
    if not re.search('^[A-Z]{1,2}$', col, re.IGNORECASE):
        raise Exception("Cannot parse column name: '{}'".format(col))

    col = col.upper()
    if len(col) == 1:
        return ord(col) - ord('A')

    return (ord(col[0]) - ord('A') + 1) * 26 + ord(col[1]) - ord('A')


def colidx_to_colname(idx : int) -> str:
    """
    Converts a column index # into a Google Sheets column name, i.e. 0 => 'A', 1 => 'B', 26 => 'AA', 27 => 'AB'
    """
    ret = ''
    high = idx // 26
    if high > 0:
        ret += chr(ord('A') + (high - 1))
    low = idx % 26
    ret += chr(ord('A') + low)
    return ret


class CellRange(object):
    """
    Data object describing the bounds of a block of data within a sheet.
    Typically created using the from_string() static method.

    Makes it easy to access info about the block including:
        - Sheet name
        - top left column/row (and numerical index of the column)
        - bottom right column/row (and numerical index of the row)
    """
    def __init__(self,
            sheet : str,
            top_left_col : str,
            top_left_row : int,
            bottom_right_col : str = None,
            bottom_right_row : int = None,
        ):

        self.sheet = sheet
        self.top_left_col = top_left_col
        self.top_left_row = top_left_row

        if (bottom_right_col is None) != (bottom_right_row is None):
            raise Exception("Bottom_right_{col,idx} must be either both None, or both specified.")

        if bottom_right_col is None:
            self.bottom_right_col = top_left_col
            self.bottom_right_row = top_left_row
        else:
            self.bottom_right_col = bottom_right_col
            self.bottom_right_row = bottom_right_row

        if self.bottom_right_col < self.top_left_col or self.bottom_right_row < self.top_left_row:
            raise Exception("Error parsing cell reference; top left cell must be <= bottom right cell. '{}'".format(str(self)))

    def width(self):
        return self.bottom_right_col_idx() - self.top_left_col_idx() + 1

    def height(self):
        return self.bottom_right_row - self.top_left_row + 1

    def top_left_col_idx(self):
        return colname_to_idx(self.top_left_col)

    def bottom_right_col_idx(self):
        return colname_to_idx(self.bottom_right_col)

    def __str__(self):
        """ Format is "[<Sheet name>!]<Top left cell>[:<bottom right cell>] """
        ret = ''
        if self.sheet:
            ret += self.sheet + '!'
        ret += "{}{}".format(self.top_left_col, self.top_left_row)
        if not (self.top_left_col == self.bottom_right_col and self.top_left_row == self.bottom_right_row):
            ret += ":{}{}".format(self.bottom_right_col, self.bottom_right_row)
        return ret

    def clone(self):
        return copy.copy(self)

    @staticmethod
    def from_string(cell_range):
        """
        Parses a Sheets cell range (Canonically "<Sheet name>!<Top left cell>[:bottom right cell]") and returns
        an object describing the cell.

        @return dict
            'sheet': str | None - sheet name
            'top_left_col': str - col name (e.g. 'A', 'B', 'C')
            'top_left_row': int - row number (e.g. 1, 2, 3)
            'bottom_right_col': str | None - col name (as above) - only present if it was specified in the range.
            'bottom_right_row': int | None- row number (as above)
        }
        """
        matches = re.search("""
            ^
            (?: ([^!]+)!)?                  # Optional sheet name
            (?: ([A-Z]+)([0-9]+))           # Top left cell ref 'AB34'
            (?: : (?: ([A-Z]+)([0-9]+)))?   # Optional bottom right cell ref
            $
            """,
            cell_range,
            re.VERBOSE | re.IGNORECASE
        )
        if matches is None:
            raise Exception("Could not parse cell range string: '{}'".format(cell_range))

        top_left_col = matches.group(2).upper()
        top_left_row = int(matches.group(3))
        bottom_right_col = matches.group(4)
        bottom_right_row = None

        if bottom_right_col is None:
            # Means there was just 1 cell, so bottom right == top left
            bottom_right_col = top_left_col
            bottom_right_row = top_left_row
        else:
            bottom_right_col = bottom_right_col.upper()
            bottom_right_row = int(matches.group(5))

        return CellRange(
            sheet=matches.group(1),
            top_left_col=top_left_col,
            top_left_row=top_left_row,
            bottom_right_col=bottom_right_col,
            bottom_right_row=bottom_right_row,
        )

    def get_relative_cell(self, row_idx : int, col_idx : str) -> str:
        """
        @param row_idx - integer offset into this cell range (not the row number in the sheet)
        @param col_idx - int offset into this cell range (not the column name in the sheet)
        @return CellRange - a new CellRange describing just this cell
        """

        col_name = colidx_to_colname(self.top_left_col_idx() + col_idx)
        row = self.top_left_row + row_idx
        return CellRange(
            sheet=self.sheet,
            top_left_col=col_name,
            top_left_row=row,
        )
