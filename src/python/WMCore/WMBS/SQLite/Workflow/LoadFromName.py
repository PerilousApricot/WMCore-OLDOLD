#!/usr/bin/env python
"""
_LoadFromName_

SQLite implementation of Workflow.LoadFromName

"""
__all__ = []



from WMCore.WMBS.MySQL.Workflow.LoadFromName import LoadFromName as LoadWorkflowMySQL

class LoadFromName(LoadWorkflowMySQL):
    sql = LoadWorkflowMySQL.sql
    