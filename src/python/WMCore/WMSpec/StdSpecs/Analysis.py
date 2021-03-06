#!/usr/bin/env python
# encoding: utf-8
# pylint: disable-msg=C0301,W0142

import logging
import time

from WMCore.WMSpec.StdSpecs.StdBase import StdBase


def getTestArguments():
    """generate some test data"""
    args = {}
    args['Requestor'] = "mmascher"
    args['Username'] = "mmascher"
    args['ProcessingVersion'] = ""
    args['RequestorDN'] = "/DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=mmascher/CN=720897/CN=Marco Mascheroni"
    args['InputDataset'] = "/RelValProdTTbar/JobRobot-MC_3XY_V24_JobRobot-v1/GEN-SIM-DIGI-RECO"
    args["ScramArch"] =  "slc5_ia32_gcc434"
    args['CMSSWVersion'] = "CMSSW_4_2_0"
    args["userSandbox"] = 'http://home.fnal.gov/~ewv/agent.tgz'

    return args

def remoteLFNPrefix(site, lfn=''):
    """
    Convert a site name to the relevant remote LFN prefix
    """
    from WMCore.Services.PhEDEx.PhEDEx import PhEDEx
    phedexJSON = PhEDEx(responseType='json')

    seName = phedexJSON.getNodeSE(site)
    uri = phedexJSON.getPFN(nodes=[site], lfns=[lfn])[(site,lfn)]

    return uri.replace(lfn, ''), seName # Don't want the actual LFN, just prefix

class AnalysisWorkloadFactory(StdBase):
    """
    Analysis workload.
    """

    def __init__(self):
        StdBase.__init__(self)


    def buildWorkload(self):
        """
        _buildWorkload_

        Build a workflow for Analysis  requests.
        """

        workload = self.createWorkload()
        workload.setDashboardActivity("analysis")
        analysisTask = workload.newTask("Analysis")

        (self.inputPrimaryDataset, self.inputProcessedDataset, self.inputDataTier) = self.inputDataset[1:].split("/")

        lfnBase = '/store/temp/user/%s' % self.userName
        self.unmergedLFNBase = lfnBase
        userOutBase = '%s/CRAB-Out' % lfnBase
        logBase = '/store/temp/user/%s/logs/' % self.userName
        logCollBase = '/store/user/%s/CRAB-Out' % self.userName
        lcPrefix, seName = remoteLFNPrefix(site=self.asyncDest, lfn=logCollBase)

        # Force ACDC input if present
        self.inputStep = None
        if self.ACDCID:
            analysisTask.addInputACDC(self.ACDCURL, self.ACDCDBName, self.origRequest, self.ACDCID)
            self.inputDataset = None

        outputMods = self.setupProcessingTask(analysisTask, "Analysis", inputDataset=self.inputDataset,
                                              inputStep=self.inputStep,
                                              couchURL = self.couchURL, couchDBName = self.couchDBName,
                                              configDoc = self.analysisConfigCacheID, splitAlgo = self.analysisJobSplitAlgo,
                                              splitArgs = self.analysisJobSplitArgs, \
                                              userDN = self.owner_dn, asyncDest = self.asyncDest,
                                              owner_vogroup = self.owner_vogroup, owner_vorole = self.owner_vorole,
                                              userSandbox = self.userSandbox, userFiles = self.userFiles)

        # Put temporary log files in /store/temp/user/USERNAME/
        logArchiveStep = analysisTask.getStep('logArch1')
        logArchiveStep.addOverride('altLFN',  logBase)

        # Change handling and stageout location of final logfiles
        logCollectTask = self.addLogCollectTask(analysisTask)
        logCollectStep = logCollectTask.getStep('logCollect1')

        stageOut = analysisTask.getStep('stageOut1')
        stageOutHelper = stageOut.getTypeHelper()
        stageOutHelper.setMinMergeSize(1, 1)

        if not self.saveLogs:
            logCollectStep.addOverride('dontStage', True)
        else:
            logCollectStep.addOverride('dontStage', False)

        logCollectStep.addOverride('userLogs',  True)
        logCollectStep.addOverride('seName',    seName)
        logCollectStep.addOverride('lfnBase',   logCollBase)
        logCollectStep.addOverride('lfnPrefix', lcPrefix)
        if self.ACDCID:
            workload.setWorkQueueSplitPolicy("ResubmitBlock", self.analysisJobSplitAlgo, self.analysisJobSplitArgs)
        else:
            workload.setWorkQueueSplitPolicy("Block", self.analysisJobSplitAlgo, self.analysisJobSplitArgs)

        cmsswStep = analysisTask.getStep('cmsRun1')
        cmsswHelper = cmsswStep.getTypeHelper()
        cmsswHelper.setUserLFNBase(userOutBase)

        for outputFile in self.outputFiles:
            cmsswHelper.addAnalysisFile(outputFile, fileName = outputFile, lfnBase = userOutBase)

        return workload



    def __call__(self, workloadName, arguments):
        """
        Create a workload instance for an Analysis request
        """

        StdBase.__call__(self, workloadName, arguments)

        self.globalTag = arguments.get("GlobalTag", None)

        # Required parameters.
        self.frameworkVersion = arguments["CMSSWVersion"]
        self.inputDataset = arguments['InputDataset']
        self.processingVersion = arguments.get('ProcessingVersion', 'v1')
        self.origRequest = arguments.get('OriginalRequestName', '')
        self.emulation = arguments.get("Emulation", False)

        self.blockBlacklist = arguments.get("BlockBlacklist", [])
        self.blockWhitelist = arguments.get("BlockWhitelist", [])
        self.runWhitelist = arguments.get("RunWhitelist", [])
        self.runBlacklist = arguments.get("RunBlacklist", [])

        self.couchURL = arguments.get("CouchUrl")
        self.couchDBName = arguments.get("CouchDBName", "wmagent_configcache")
        self.analysisConfigCacheID = arguments.get("AnalysisConfigCacheDoc", None)
        self.ACDCURL = arguments.get("ACDCUrl", "")
        self.ACDCDBName = arguments.get("ACDCDBName", "wmagent_acdc")
        self.ACDCID = arguments.get("ACDCDoc", None)

        # These are mostly place holders because the job splitting algo and
        # parameters will be updated after the workflow has been created.
        self.analysisJobSplitAlgo  = arguments.get("JobSplitAlgo", "EventBased")

        if self.ACDCID and self.analysisJobSplitAlgo not in ['LumiBased']:
            raise RuntimeError('Running on selected lumis only supported in split mode(s) %s' %
                               'LumiBased')

        if self.analysisJobSplitAlgo == 'EventBased':
            self.analysisJobSplitArgs  = arguments.get('JobSplitArgs', {'events_per_job' : 1000})
        elif self.analysisJobSplitAlgo == 'LumiBased':
            self.analysisJobSplitArgs  = arguments.get('JobSplitArgs', {'lumis_per_job' : 15})
            if self.ACDCID:
                self.analysisJobSplitArgs.update(
                            {'filesetName' : self.ACDCID,
                             'collectionName' : self.origRequest,
                             'couchURL' : self.ACDCURL,
                             'couchDB' : self.ACDCDBName,
                             'owner' : self.owner,
                             'group' : self.group,
                            })
            self.analysisJobSplitArgs.update(
                           {'halt_job_on_file_boundaries' : False,
                            'splitOnRun' : False,
                           })
        else:
            self.analysisJobSplitArgs  = arguments.get('JobSplitArgs', {})

        self.asyncDest = arguments.get("asyncDest", "T1_US_FNAL_Buffer")
        self.minMergeSize = 1 # arguments.get("MinMergeSize", 1)
        self.acquisitionEra = arguments.get("PublishDataName", str(int(time.time())))
        self.owner_vogroup = arguments.get("VoGroup", '')
        self.owner_vorole = arguments.get("VoRole", '')
        self.userSandbox = arguments.get("userSandbox", None)
        self.userFiles   = arguments.get("userFiles", [])
        self.userName    = arguments.get("Username",'jblow')
        self.saveLogs    = arguments.get("SaveLogs", True)
        self.outputFiles = arguments.get("OutputFiles", [])

        return self.buildWorkload()

    def validateSchema(self, schema):
        """
        _validateSchema_

        Check for required fields, and some skim facts
        """
        def _checkSiteList(list):
            if self.has_key(list) and hasattr(self,'allCMSNames'):
                for site in self[list]:
                    if not site in self.allCMSNames: #self.allCMSNames needs to be initialized to allow sitelisk check
                        raise RuntimeError("The site " + site + " provided in the " + list + " param has not been found. Check https://cmsweb.cern.ch/sitedb/json/index/SEtoCMSName?name= for a list of known sites")

        requiredFields = ["CMSSWVersion", "ScramArch",
                          "InputDataset", "Requestor",
                          "RequestorDN" , "RequestName"]
        self.requireValidateFields(fields = requiredFields, schema = schema,
                                   validate = False)

        _checkSiteList("SiteWhitelist")
        _checkSiteList("SiteBlacklist")

        #Control if the request name contain spaces
        if schema.get("RequestName").count(' ') > 0:
            msg = "RequestName cannot contain spaces"
            self.raiseValidationException(msg = msg)



        return
