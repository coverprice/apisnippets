#!/bin/env python3

from .CellRange import CellRange

class SheetWriteBuffer(object):
    """
    This is a buffer used to store multiple writes to a spreadsheet. To use it, instantiate it
    and start making calls to set() to set the value of individual cells (see below). Then when
    you're ready to actually update the spreadsheet, pass this object to SheetService.writeBuffer.
    """
    def __init__(self):
        self.cells = {}

    def set(self, cell : CellRange, value):
        """
        @param cell -  cell reference, must refer to a single cell.
        @param value - mixed - value to place into the cell
        """
        if cell.width() != 1 or cell.height() != 1:
            raise Exception("Invalid cell range. Width must be 1x1, but this cell range is {} wide and {} high.".format(cell_range.width(), cell_range.height()))
        self.cells[str(cell)] = value

    def num_pending_writes(self):
        return len(self.cells)
