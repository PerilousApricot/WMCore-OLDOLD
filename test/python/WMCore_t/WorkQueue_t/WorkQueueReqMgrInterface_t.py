#!/usr/bin/env python

"""
WorkQueueRegMgrInterface test
"""

import os
import logging
import threading
import unittest
import time
import shutil
import WMCore.WMInit
from subprocess import Popen, PIPE
import types

from WMCore.Agent.Configuration import loadConfigurationFile

from WMCore.WorkQueue.WorkQueue import WorkQueue, globalQueue, localQueue

from WMQuality.Emulators.RequestManagerClient.RequestManager \
    import RequestManager as fakeReqMgr

from WMCore_t.WorkQueue_t.WorkQueueTestCase import WorkQueueTestCase
from WMCore.Services.EmulatorSwitch import EmulatorHelper
from WMCore.WorkQueue.WorkQueueReqMgrInterface import WorkQueueReqMgrInterface

def getFirstTask(wmspec):
    """Return the 1st top level task"""
    # http://www.logilab.org/ticket/8774
    # pylint: disable-msg=E1101,E1103
    return wmspec.taskIterator().next()

class WorkQueueReqMgrInterfaceTest(WorkQueueTestCase):
    """
    TestCase for WorkQueueReqMgrInterface module
    """
    def setSchema(self):
        self.schema = []
        self.couchApps = ["WorkQueue"]

    def setUp(self):
        WorkQueueTestCase.setUp(self)
        EmulatorHelper.setEmulators(phedex = True, dbs = True,
                                    siteDB = True, requestMgr = False)
        self.globalQCouchUrl = "%s/%s" % (self.testInit.couchUrl, self.globalQDB)
        self.localQCouchUrl =  "%s/%s" % (self.testInit.couchUrl,
                                          self.localQInboxDB)

    def tearDown(self):
        WorkQueueTestCase.tearDown(self)
        EmulatorHelper.resetEmulators()

    def getConfig(self):
        """
        _createConfig_

        General config file
        """
        #configPath=os.path.join(WMCore.WMInit.getWMBASE(), \
        #                        'src/python/WMComponent/WorkQueueManager/DefaultConfig.py')):


        config = self.testInit.getConfiguration()
        # http://www.logilab.org/ticket/8961
        # pylint: disable-msg=E1101, E1103
        config.component_("WorkQueueManager")
        config.section_("General")
        config.General.workDir = "."
        config.WorkQueueManager.team = 'team_usa'
        config.WorkQueueManager.requestMgrHost = 'cmssrv49.fnal.gov:8585'
        config.WorkQueueManager.serviceUrl = "http://cmssrv18.fnal.gov:6660"

        config.WorkQueueManager.logLevel = 'INFO'
        config.WorkQueueManager.pollInterval = 10
        config.WorkQueueManager.level = "GlobalQueue"
        return config


    def setupGlobalWorkqueue(self, **kwargs):
        """Return a workqueue instance"""
        globalQ = globalQueue(DbName = self.globalQDB,
                              InboxDbName = self.globalQInboxDB,
                              QueueURL = self.globalQCouchUrl,
                              Teams = ["The A-Team", "some other bloke"],
                              **kwargs)
        return globalQ

    def setupLocalQueue(self):
        """Create a local queue"""
        localQ = localQueue(DbName = self.localQDB,
                            InboxDbName = self.localQInboxDB,
                            QueueURL = self.localQCouchUrl,
                            Teams = ["The A-Team", "some other bloke"],
                            ParentQueueCouchUrl = self.globalQCouchUrl,
                            CacheDir = self.testInit.testDir)
        return localQ

    def testReqMgrPollerAlgorithm(self):
        """ReqMgr reporting"""
        # don't actually talk to ReqMgr - mock it.
        globalQ = self.setupGlobalWorkqueue()
        localQ = self.setupLocalQueue()
        reqMgr = fakeReqMgr(splitter = 'Block')
        reqMgrInt = WorkQueueReqMgrInterface()
        reqMgrInt.reqMgr = reqMgr

        # 1st run should pull a request
        self.assertEqual(len(globalQ), 0)
        reqMgrInt(globalQ)
        self.assertEqual(len(globalQ), 2)
        self.assertEqual(reqMgr.status[reqMgr.names[0]], 'acquired')

        # local queue acquires and runs
        globalQ.updateLocationInfo()
        work = localQ.pullWork({'T2_XX_SiteA' : 10000, 'T2_XX_SiteB' : 10000})
        self.assertEqual(len(globalQ), 0)
        reqMgrInt(globalQ)
        self.assertEqual(reqMgr.status[reqMgr.names[0]], 'acquired')

        # start running work
        globalQ.setStatus('Running', WorkflowName = reqMgr.names[0])
        globalQ.performQueueCleanupActions()
        reqMgrInt(globalQ) # report back to ReqMgr
        self.assertEqual(reqMgr.status[reqMgr.names[0]], 'running')

        # finish work
        work = globalQ.status()
        globalQ.setStatus('Done', elementIDs = [x.id for x in work])
        reqMgrInt(globalQ)
        globalQ.performQueueCleanupActions()
        reqMgrInt(globalQ)
        self.assertEqual(reqMgr.status[reqMgr.names[0]], 'completed')
        # and removed from WorkQueue
        self.assertEqual(len(globalQ.status()), 0)

        # reqMgr problems should not crash client
        reqMgrInt.reqMgr = None
        reqMgrInt(globalQ)
        reqMgr._removeSpecs()


    def testReqMgrProgress(self):
        """ReqMgr interaction with block level splitting"""
        globalQ = self.setupGlobalWorkqueue()
        reqMgr = fakeReqMgr(splitter = 'Block')
        reqMgrInt = WorkQueueReqMgrInterface()
        reqMgrInt.reqMgr = reqMgr

        self.assertEqual(len(globalQ), 0)
        reqMgrInt(globalQ)
        self.assertEqual(len(globalQ), 2)
        globalQ.setStatus('Acquired', WorkflowName = reqMgr.names[0])
        reqMgrInt(globalQ) # report back to ReqMgr
        self.assertEqual(reqMgr.status[reqMgr.names[0]], 'acquired')
        globalQ.setStatus('Running', WorkflowName = reqMgr.names[0])
        elements = globalQ.status()
        self.assertEqual(len(elements), 2)
        [globalQ.backend.updateElements(x.id, PercentComplete = 75, PercentSuccess = 25) for x in elements]
        elements = globalQ.status()
        globalQ.performQueueCleanupActions()
        reqMgrInt(globalQ) # report back to ReqMgr
        self.assertEqual(reqMgr.status[reqMgr.names[0]], 'running')
        globalQ.performQueueCleanupActions()
        reqMgrInt(globalQ)
        self.assertEqual(reqMgr.progress[reqMgr.names[0]]['percent_complete'],
                         75)
        self.assertEqual(reqMgr.progress[reqMgr.names[0]]['percent_success'],
                         25)
        self.assertEqual(reqMgr.status[reqMgr.names[0]], 'running')
        globalQ.setStatus('Done', WorkflowName = reqMgr.names[0])
        reqMgrInt(globalQ) # report back to ReqMgr
        globalQ.performQueueCleanupActions()
        reqMgrInt(globalQ)
        self.assertEqual(reqMgr.progress[reqMgr.names[0]]['percent_complete'],
                         75)
        self.assertEqual(reqMgr.status[reqMgr.names[0]], 'completed')
        reqMgr._removeSpecs()


    def testInvalidSpec(self):
        """Report invalid spec back to ReqMgr"""
        globalQ = self.setupGlobalWorkqueue()
        reqMgr = fakeReqMgr(inputDataset = 'thisdoesntexist')
        reqMgrInt = WorkQueueReqMgrInterface()
        reqMgrInt.reqMgr = reqMgr
        reqMgrInt(globalQ)
        self.assertEqual('failed', reqMgr.status[reqMgr.names[0]])
        self.assertTrue('No work in spec:' in reqMgr.msg[reqMgr.names[0]])
        reqMgr._removeSpecs()

        globalQ = self.setupGlobalWorkqueue()
        reqMgr = fakeReqMgr(dbsUrl = 'wrongprot://dbs.example.com')
        reqMgrInt = WorkQueueReqMgrInterface()
        reqMgrInt.reqMgr = reqMgr
        reqMgrInt(globalQ)
        self.assertEqual('failed', reqMgr.status[reqMgr.names[0]])
        self.assertTrue('DBS config error' in reqMgr.msg[reqMgr.names[0]])
        reqMgr._removeSpecs()

    def testDrainMode(self):
        """Stop acquiring work when DrainMode set"""
        globalQ = self.setupGlobalWorkqueue(DrainMode = True)
        reqMgr = fakeReqMgr()
        reqMgrInt = WorkQueueReqMgrInterface()
        reqMgrInt.reqMgr = reqMgr
        self.assertEqual(len(globalQ), 0)
        reqMgrInt(globalQ)
        self.assertEqual(len(globalQ), 0)

    def testCancelPickedUp(self):
        """WorkQueue cancels if canceled in ReqMgr"""
        globalQ = self.setupGlobalWorkqueue()
        reqMgr = fakeReqMgr()
        reqMgrInt = WorkQueueReqMgrInterface()
        reqMgrInt.reqMgr = reqMgr
        reqMgrInt(globalQ)
        # abort in reqmgr
        reqMgr.status[reqMgr.names[0]] = 'aborted'
        # workqueue will detect abort and cancel workflow
        reqMgrInt(globalQ)
        self.assertEqual(globalQ.status(WorkflowName=reqMgr.names[0])[0]['Status'], 'Canceled')
        # check stays canceled
        reqMgrInt(globalQ)
        self.assertEqual(globalQ.status(WorkflowName=reqMgr.names[0])[0]['Status'], 'Canceled')

if __name__ == '__main__':
    unittest.main()
