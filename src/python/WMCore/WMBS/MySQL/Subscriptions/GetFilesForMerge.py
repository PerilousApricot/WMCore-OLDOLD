#!/usr/bin/env python
"""
_GetFilesForMerge_

MySQL implementation of Subscription.GetFilesForMerge
"""

from WMCore.Database.DBFormatter import DBFormatter

class GetFilesForMerge(DBFormatter):
    """
    This query needs to return the following for any files that is deemed
    mergeable:
      WMBS ID (file_id)
      Events (file_events)
      Size (file_size)
      LFN (file_lfn)
      First event in file (file_first_event)
      Runs in file (file_run)
      Lumi sections in file (file_lumi)
      MIN(ID) of the file's parent (file_parent)
      Location

    A file is deemed mergeable if:
      - The file is in the input fileset for the merging subscription
      - It has not been acquired/completed/failed by it's subscription
      - All jobs that processed the parent succeeded
    """
    sql = """SELECT merge_files.fileid AS file_id,
                    merge_files.parent AS file_parent,
                    wmbs_file_details.events AS file_events,
                    wmbs_file_details.filesize AS file_size,
                    wmbs_file_details.lfn AS file_lfn,
                    wmbs_file_details.first_event AS file_first_event,
                    MIN(wmbs_file_runlumi_map.run) AS file_run,
                    MIN(wmbs_file_runlumi_map.lumi) AS file_lumi,
                    wmbs_location.se_name AS se_name
             FROM (
               SELECT wmbs_sub_files_available.fileid AS fileid,
                      MIN(wmbs_file_parent.parent) AS parent,
                      COUNT(wmbs_sub_files_available.fileid),
                      COUNT(b.id)
               FROM wmbs_sub_files_available
               INNER JOIN wmbs_subscription ON
                 wmbs_sub_files_available.subscription = wmbs_subscription.id
               INNER JOIN wmbs_file_parent ON
                 wmbs_file_parent.child = wmbs_sub_files_available.fileid
               INNER JOIN wmbs_job_assoc ON
                 wmbs_file_parent.parent = wmbs_job_assoc.fileid
               INNER JOIN wmbs_workflow_output ON
                 wmbs_subscription.fileset = wmbs_workflow_output.output_fileset
               INNER JOIN wmbs_subscription c ON
                 wmbs_workflow_output.workflow_id = c.workflow
               INNER JOIN wmbs_jobgroup ON
                 c.id = wmbs_jobgroup.subscription
               INNER JOIN wmbs_job a ON
                 a.id = wmbs_job_assoc.job AND
                 a.jobgroup = wmbs_jobgroup.id
               LEFT OUTER JOIN wmbs_job b ON
                 b.id = wmbs_job_assoc.job AND
                 b.outcome = 1
               WHERE wmbs_sub_files_available.subscription = :p_1
               GROUP BY wmbs_sub_files_available.fileid, a.jobgroup
               HAVING COUNT(wmbs_sub_files_available.fileid) = COUNT(b.id)) merge_files
             INNER JOIN wmbs_file_details ON
               wmbs_file_details.id = merge_files.fileid
             INNER JOIN wmbs_file_runlumi_map ON
               wmbs_file_runlumi_map.fileid = merge_files.fileid
             INNER JOIN wmbs_file_location ON
               wmbs_file_details.id = wmbs_file_location.fileid
             INNER JOIN wmbs_location ON
               wmbs_file_location.location = wmbs_location.id
             GROUP BY merge_files.fileid, merge_files.parent,
                      wmbs_file_details.events, wmbs_file_details.filesize,
                      wmbs_file_details.lfn, wmbs_file_details.first_event,
                      wmbs_location.se_name"""

    def execute(self, subscription = None, conn = None, transaction = False):
        results = self.dbi.processData(self.sql, {"p_1": subscription}, conn = conn,
                                      transaction = transaction)
        return self.formatDict(results)
