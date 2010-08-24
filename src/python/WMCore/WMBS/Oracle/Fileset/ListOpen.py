#!/usr/bin/env python
"""
_ListOpen_

Oracle implementation of Fileset.ListOpen
"""

__all__ = []
__revision__ = "$Id: ListOpen.py,v 1.1 2009/03/03 17:35:22 sfoulkes Exp $"
__version__ = "$Revision: 1.1 $"

from WMCore.WMBS.MySQL.Fileset.ListOpen import ListOpen as ListOpenFilesetMySQL

class ListOpen(ListOpenFilesetMySQL):
    sql = ListOpenFilesetMySQL.sql
