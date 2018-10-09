#!/bin/env python3

from .CellRange import CellRange
import logging
logger = logging.getLogger(__name__)
from pprint import pprint

class CellRangeData(object):
    """
    Object that contains a block of data returned by read_cells
    """
    # The result structure is a sparse matrix for network efficiency reasons, so (say) a
    # row in the requested range has some values but not all the way to the end of the row,
    # then the API result will not contain those cells. This can make it unwieldy to work
    # directly with the API's result structure because it's necessary to check whether a
    # cell in the result exists before you query its contents.
    # So to make this easier, we copy the result into a Matrix where every cell will be
    # guaranteed to be defined (and populated with None if it's empty).
    def __init__(self, cell_range : CellRange, cells : list):
        if cell_range.height() != len(cells):
            raise Exception("Error: Number of rows expected {}, but got {}".format(cell_range.height(), len(cells)))
        expected_width = cell_range.width()
        for row in cells:
            if expected_width != len(row):
                raise Exception("Error: At least 1 row had an unexpected width. Expected {}, but got {}".format(expected_width, len(row)))

        self.cell_range = cell_range
        self.cells = cells

    @staticmethod
    def from_read_result(cell_range : CellRange, result_rows : list):
        width = cell_range.width()
        # Note: "[ [None] * width] * height" does not work because all the 'rows' refer to the same list instance.
        cells = []
        for _ in range(0, cell_range.height()):
            cells.append([None] * width)
        
        row_idx = 0
        for row in result_rows:
            row_len = len(row)
            if len(row) > width:
                raise Exception("Error parsing read result: A row has more values in it ({}) than expected ({})".format(len(row), range_width))
            col_idx = 0
            for val in row:
                cells[row_idx][col_idx] = val
                col_idx += 1
            row_idx += 1
        return CellRangeData(cell_range=cell_range, cells=cells)

    def width(self):
        return self.cell_range.width()

    def height(self):
        return self.cell_range.height()

    def get_relative_cell(self, row_idx : int, col_idx : int) -> CellRange:
        return self.cell_range.get_relative_cell(row_idx=row_idx, col_idx=col_idx)

    def get_cell(self, row_idx : int, col_idx : int):
        return self.cells[row_idx][col_idx]
