#!/usr/bin/env python
"""
_ListOpen_

MySQL implementation of Fileset.ListOpen
"""

__all__ = []



from WMCore.Database.DBFormatter import DBFormatter

class ListOpen(DBFormatter):
    sql = "SELECT name FROM wmbs_fileset WHERE open = 1"
    
    def format(self, results):
        """
        _format_

        Take the array of rows that were returned by the query and format that
        into a single list of open fileset names.
        """
        results = DBFormatter.format(self, results)
        openFilesetNames = []

        for result in results:
            openFilesetNames.append(str(result[0]))

        return openFilesetNames
        
    def execute(self, conn = None, transaction = False):
        result = self.dbi.processData(self.sql, conn = conn,
                                      transaction = transaction)
        return self.format(result)
