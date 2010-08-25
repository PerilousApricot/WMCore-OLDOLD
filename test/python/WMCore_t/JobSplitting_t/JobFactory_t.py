#!/usr/bin/env python
"""
_JobFactory_t_

Test the job splitting Job Factory
"""

__revision__ = "$Id: JobFactory_t.py,v 1.1 2010/06/23 18:29:40 sfoulkes Exp $"
__version__ = "$Revision: 1.1 $"

import unittest

from WMCore.DataStructs.File import File
from WMCore.DataStructs.Fileset import Fileset
from WMCore.DataStructs.Subscription import Subscription
from WMCore.DataStructs.Workflow import Workflow

from WMCore.JobSplitting.JobFactory import JobFactory

class JobFactoryTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def testMetaData(self):
        """
        _testMetaData_

        Make sure that the workflow name, task, owner and white and black lists
        make it into each job object.
        """
        testWorkflow = Workflow(spec = "spec.pkl", owner = "Steve",
                                name = "TestWorkflow", task = "TestTask")

        testFileset = Fileset(name = "TestFileset")
        testFile = File(lfn = "someLFN")
        testFileset.addFile(testFile)
        testFileset.commit()

        testSubscription = Subscription(fileset = testFileset,
                                        workflow = testWorkflow,
                                        split_algo = "FileBased")

        myJobFactory = JobFactory(subscription = testSubscription)
        testJobGroups =  myJobFactory(siteWhiteList = ["site1"], siteBlackList = ["site2"])

        for testJobGroup in testJobGroups:
            for job in testJobGroup.jobs:
                assert job["task"] == "TestTask", \
                       "Error: Task is wrong."
                assert job["workflow"] == "TestWorkflow", \
                       "Error: Workflow is wrong."
                assert job["owner"] == "Steve", \
                       "Error: Owner is wrong."
                assert job["siteWhiteList"] == ["site1"], \
                       "Error: Site white list is wrong."
                assert job["siteBlackList"] == ["site2"], \
                       "Error: Site black list is wrong."
        return
  
if __name__ == '__main__':
    unittest.main()