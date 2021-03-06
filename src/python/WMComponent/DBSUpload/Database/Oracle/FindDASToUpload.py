#!/usr/bin/env python

"""
This code should load the necessary information regarding
dataset-algo combinations from the DBSBuffer.

Oracle version

"""




from WMComponent.DBSUpload.Database.MySQL.FindDASToUpload import FindDASToUpload as MySQLFindDASToUpload


class FindDASToUpload(MySQLFindDASToUpload):
    """
    Find Uploadable DAS

    """


    sql = """SELECT das1.dataset_id AS dataset, ds1.Path as Path, das1.algo_id as Algo, das1.in_dbs as in_dbs,
               das1.id AS das_id,
               da1.app_name AS ApplicationName, 
               da1.app_ver AS ApplicationVersion, 
               da1.app_fam AS ApplicationFamily, 
               da1.PSet_Hash as PSetHash,
               da1.Config_Content as PSetContent,
               da1.in_dbs AS algo_in_dbs,
               ds1.valid_status AS valid_status
             FROM dbsbuffer_algo_dataset_assoc das1
             INNER JOIN dbsbuffer_algo da1 ON da1.id = das1.algo_id
             INNER JOIN dbsbuffer_dataset ds1 ON ds1.id = das1.dataset_id
             WHERE das1.id IN
             (SELECT DISTINCT das.id
             FROM dbsbuffer_algo_dataset_assoc das
             INNER JOIN dbsbuffer_dataset ds2 ON ds2.id = das.dataset_id
             WHERE EXISTS (SELECT id FROM dbsbuffer_file dbsfile
                            WHERE dbsfile.dataset_algo = das.id
                            AND dbsfile.status = 'NOTUPLOADED')
             AND UPPER(ds2.Path) NOT LIKE 'BOGUS')
             """
