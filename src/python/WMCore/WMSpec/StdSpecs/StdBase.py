#!/usr/bin/env python
"""
_StdBase_

Base class with helper functions for standard WMSpec files.
"""
import logging

from WMCore.WMSpec.WMWorkload import newWorkload
from WMCore.WMSpec.WMStep import makeWMStep
from WMCore.WMSpec.Steps.StepFactory import getStepTypeHelper

from WMCore.Cache.WMConfigCache import ConfigCache, ConfigCacheException
from WMCore.Lexicon import lfnBase, identifier
from WMCore.WMException import WMException
from WMCore.Database.CMSCouch import CouchNotFoundError

class WMSpecFactoryException(WMException):
    """
    _WMSpecFactoryException_

    This exception will be raised by validation functions if
    the code fails validation.  It will then be changed into
    a proper HTTPError in the ReqMgr, with the message you enter
    used as the message for farther up the line.
    """
    pass

class StdBase(object):
    """
    _StdBase_

    Base class with helper functions for standard WMSpec file.
    """
    def __init__(self):
        """
        __init__

        Setup parameters that will be used by all workflows.  These parameters
        are not required to be set when the workflow is first created but will
        need to be set before the sandbox is created and jobs are made.

        These parameters can be changed after the workflow has been created by
        the methods in the WMWorkloadHelper class.
        """
        self.workloadName = None
        self.priority = 0
        self.owner = "unknown"
        self.owner_dn = "unknown"
        self.group = "unknown"
        self.owner_vogroup = "DEFAULT"
        self.owner_vorole = "DEFAULT"
        self.acquisitionEra = None
        self.scramArch = None
        self.inputPrimaryDataset = None
        self.inputProcessedDataset = None
        self.inputDataTier = None
        self.processingVersion = None
        self.siteBlacklist = []
        self.siteWhitelist = []
        self.unmergedLFNBase = None
        self.mergedLFNBase = None
        self.minMergeSize = 2147483648
        self.maxMergeSize = 4294967296
        self.maxWaitTime = 24 * 3600
        self.maxMergeEvents = 100000
        self.validStatus = None
        self.includeParents = False
        self.dbsUrl = None
        self.multicore = False
        self.multicoreNCores = 1
        return

    def __call__(self, workloadName, arguments):
        """
        __call__

        Look through the arguments that were passed into the workload's call
        method and pull out any that are setup by this base class.
        """
        self.workloadName = workloadName
        self.priority = arguments.get("Priority", 0)
        self.owner = arguments.get("Requestor", "unknown")
        self.owner_dn = arguments.get("RequestorDN", "unknown")
        self.group = arguments.get("Group", "unknown")
        if arguments.has_key('VoGroup'):
            self.owner_vogroup = arguments['VoGroup']
        if arguments.has_key('VoRole'):
            self.owner_vorole = arguments['VoRole']
        self.acquisitionEra = arguments.get("AcquisitionEra", None)
        self.scramArch = arguments.get("ScramArch", None)
        self.processingVersion = arguments.get("ProcessingVersion", None)
        self.siteBlacklist = arguments.get("SiteBlacklist", [])
        self.siteWhitelist = arguments.get("SiteWhitelist", [])
        self.unmergedLFNBase = arguments.get("UnmergedLFNBase", "/store/unmerged")
        self.mergedLFNBase = arguments.get("MergedLFNBase", "/store/data")
        self.minMergeSize = arguments.get("MinMergeSize", 2147483648)
        self.maxMergeSize = arguments.get("MaxMergeSize", 4294967296)
        self.maxWaitTime = arguments.get("MaxWaitTime", 24 * 3600)
        self.maxMergeEvents = arguments.get("MaxMergeEvents", 100000)
        self.validStatus = arguments.get("ValidStatus", "PRODUCTION")
        self.dbsUrl = arguments.get("DbsUrl", "http://cmsdbsprod.cern.ch/cms_dbs_prod_global/servlet/DBSServlet")

        if arguments.get("IncludeParents", False) == "True":
            self.includeParents = True
        else:
            self.includeParents = False

        if arguments.has_key("Multicore"):
            numCores = arguments.get("Multicore")
            if numCores == None or numCores == "":
                self.multicore = False
            elif numCores == "auto":
                self.multicore = True
                self.multicoreNCores = "auto"
            else:
                self.multicore = True
                self.multicoreNCores = numCores

        return

    def determineOutputModules(self, scenarioFunc = None, scenarioArgs = None,
                               configDoc = None, couchURL = None,
                               couchDBName = None):
        """
        _determineOutputModules_

        Determine the output module names and associated metadata for the
        given config.
        """
        outputModules = {}
        if configDoc != None and configDoc != "":
            configCache = ConfigCache(couchURL, couchDBName)
            configCache.loadByID(configDoc)
            outputModules = configCache.getOutputModuleInfo()
        else:
            if scenarioFunc in [ "promptReco", "expressProcessing" ]:
                for output in scenarioArgs.get('outputs',[]):
                    dataTier = output['dataTier']
                    moduleLabel = output['moduleLabel']
                    filterName = output.get('filterName', None)
                    outputModules[moduleLabel] = {'dataTier' : dataTier,
                                                  'filterName' : filterName}
            elif scenarioFunc == "alcaSkim":
                for alcaSkim in scenarioArgs.get('skims',[]):
                    dataTier = "ALCARECO"
                    moduleLabel = "ALCARECOStream%s" % alcaSkim
                    filterName = alcaSkim
                    outputModules[moduleLabel] = {'dataTier' : dataTier,
                                                  'filterName' : filterName}

        return outputModules

    def addDashboardMonitoring(self, task):
        """
        _addDashboardMonitoring_

        Add dashboard monitoring for the given task.
        """
        gb = 1024.0 * 1024.0 * 1024.0

        monitoring = task.data.section_("watchdog")
        monitoring.interval = 600
        monitoring.monitors = ["DashboardMonitor", "PerformanceMonitor"]
        monitoring.section_("DashboardMonitor")
        monitoring.DashboardMonitor.softTimeOut = 300000
        monitoring.DashboardMonitor.hardTimeOut = 600000
        monitoring.DashboardMonitor.destinationHost = "cms-wmagent-job.cern.ch"
        monitoring.DashboardMonitor.destinationPort = 8884
        monitoring.section_("PerformanceMonitor")
        monitoring.PerformanceMonitor.maxRSS = 4 * gb
        monitoring.PerformanceMonitor.maxVSize = 4 * gb
        return task

    def createWorkload(self):
        """
        _createWorkload_

        Create a new workload.
        """
        ownerProps = {'dn': self.owner_dn, 'vogroup': self.owner_vogroup, 'vorole': self.owner_vorole}

        workload = newWorkload(self.workloadName)
        workload.setOwnerDetails(self.owner, self.group, ownerProps)
        workload.setStartPolicy("DatasetBlock", SliceType = "NumberOfFiles", SliceSize = 1)
        workload.setEndPolicy("SingleShot")
        workload.setAcquisitionEra(acquisitionEra = self.acquisitionEra)
        workload.setProcessingVersion(processingVersion = self.processingVersion)
        workload.setValidStatus(validStatus = self.validStatus)
        return workload

    def setupProcessingTask(self, procTask, taskType, inputDataset = None, inputStep = None,
                            inputModule = None, scenarioName = None,
                            scenarioFunc = None, scenarioArgs = None, couchURL = None,
                            couchDBName = None, configDoc = None, splitAlgo = "LumiBased",
                            splitArgs = {'lumis_per_job': 8}, seeding = None, totalEvents = None,
                            userDN = None, asyncDest = None, owner_vogroup = "DEFAULT",
                            owner_vorole = "DEFAULT", stepType = "CMSSW",
                            userSandbox = None, userFiles = [], primarySubType = None):

        """
        _setupProcessingTask_

        Given an empty task add cmsRun, stagOut and logArch steps.  Configure
        the input depending on the method parameters:
          inputDataset not empty: This is a top level processing task where the
            input will be fed in by DBS.  Setup the whitelists and blacklists.
          inputDataset empty: This processing task will be fed from the output
            of another task.  The inputStep and name of the output module from
            that step (inputModule) must be specified.

        Processing config will be setup as follows:
          configDoc not empty - Use a ConfigCache config, couchURL and
            couchDBName must not be empty.
          configDoc empty - Use a Configuration.DataProcessing config.  The
            scenarioName, scenarioFunc and scenarioArgs parameters must not be
            empty.

        The seeding and totalEvents parameters are only used for production jobs.
        """
        self.addDashboardMonitoring(procTask)
        procTaskCmssw = procTask.makeStep("cmsRun1")
        procTaskCmssw.setStepType(stepType)
        procTaskStageOut = procTaskCmssw.addStep("stageOut1")
        procTaskStageOut.setStepType("StageOut")
        procTaskStageOut.setUserDN(userDN)
        procTaskStageOut.setAsyncDest(asyncDest)
        procTaskStageOut.setUserRoleAndGroup(owner_vogroup, owner_vorole)
        procTaskLogArch = procTaskCmssw.addStep("logArch1")
        procTaskLogArch.setStepType("LogArchive")
        procTask.applyTemplates()
        procTask.setTaskPriority(self.priority)


        procTask.setTaskLogBaseLFN(self.unmergedLFNBase)
        procTask.setSiteWhitelist(self.siteWhitelist)
        procTask.setSiteBlacklist(self.siteBlacklist)

        newSplitArgs = {}
        for argName in splitArgs.keys():
            newSplitArgs[str(argName)] = splitArgs[argName]

        procTask.setSplittingAlgorithm(splitAlgo, **newSplitArgs)
        procTask.setTaskType(taskType)

        if taskType == "Production" and totalEvents != None:
            procTask.addGenerator(seeding)
            procTask.addProduction(totalevents = totalEvents)
        else:
            if inputDataset != None:
                (primary, processed, tier) = self.inputDataset[1:].split("/")
                procTask.addInputDataset(primary = primary, processed = processed,
                                         tier = tier, dbsurl = self.dbsUrl,
                                         block_blacklist = self.blockBlacklist,
                                         block_whitelist = self.blockWhitelist,
                                         run_blacklist = self.runBlacklist,
                                         run_whitelist = self.runWhitelist)
            elif inputStep == None:
                procTask.setInputStep(inputStep)
            else:
                procTask.setInputReference(inputStep, outputModule = inputModule)

        if primarySubType:
            procTask.setPrimarySubType(subType = primarySubType)

        procTaskCmsswHelper = procTaskCmssw.getTypeHelper()
        procTaskStageHelper = procTaskStageOut.getTypeHelper()

        if self.multicore:
            # if multicore, poke in the number of cores setting
            procTaskCmsswHelper.setMulticoreCores(self.multicoreNCores)

        procTaskCmsswHelper.setUserSandbox(userSandbox)
        procTaskCmsswHelper.setUserFiles(userFiles)
        procTaskCmsswHelper.setGlobalTag(self.globalTag)
        procTaskCmsswHelper.setErrorDestinationStep(stepName = procTaskLogArch.name())
        procTaskStageHelper.setMinMergeSize(self.minMergeSize, self.maxMergeEvents)
        procTaskCmsswHelper.cmsswSetup(self.frameworkVersion, softwareEnvironment = "",
                                       scramArch = self.scramArch)
        if configDoc != None and configDoc != "":
            procTaskCmsswHelper.setConfigCache(couchURL, configDoc, couchDBName)
        else:
            procTaskCmsswHelper.setDataProcessingConfig(scenarioName, scenarioFunc,
                                                        **scenarioArgs)

        configOutput = self.determineOutputModules(scenarioFunc, scenarioArgs,
                                                   configDoc, couchURL, couchDBName)
        outputModules = {}
        for outputModuleName in configOutput.keys():
            outputModule = self.addOutputModule(procTask,
                                                outputModuleName,
                                                self.inputPrimaryDataset,
                                                configOutput[outputModuleName]["dataTier"],
                                                configOutput[outputModuleName]["filterName"])
            outputModules[outputModuleName] = outputModule

        return outputModules

    def addOutputModule(self, parentTask, outputModuleName,
                        primaryDataset, dataTier, filterName,
                        stepName = "cmsRun1"):
        """
        _addOutputModule_

        Add an output module to the given processing task.
        """
        if parentTask.name() == 'Analysis':
            # TODO in case of user data need to implement policy to define
            #  1  processedDataset
            #  2  primaryDataset
            #  ( 3  dataTier should be always 'USER'.)
            #  4 then we'll know how to deal with Merge
            dataTier = 'USER'

        if filterName != None and filterName != "":
            processedDataset = "%s-%s-%s" % (self.acquisitionEra, filterName,
                                             self.processingVersion)
            processingString = "%s-%s" % (filterName, self.processingVersion)
        else:
            processedDataset = "%s-%s" % (self.acquisitionEra,
                                          self.processingVersion)
            processingString = "%s" % (self.processingVersion)

        if parentTask.name() == 'Analysis':
            if filterName:
                unmergedLFN = "%s/%s/%s-%s/%s" % (self.unmergedLFNBase, primaryDataset,
                                                  self.acquisitionEra, filterName,
                                                  self.processingVersion)
            else:
                unmergedLFN = "%s/%s/%s/%s" % (self.unmergedLFNBase, primaryDataset,
                                               self.acquisitionEra, self.processingVersion)
            mergedLFN = unmergedLFN
            lfnBase(unmergedLFN)
        else:
            unmergedLFN = "%s/%s/%s/%s/%s" % (self.unmergedLFNBase, self.acquisitionEra,
                                              primaryDataset, dataTier, processingString)
            mergedLFN = "%s/%s/%s/%s/%s" % (self.mergedLFNBase, self.acquisitionEra,
                                            primaryDataset, dataTier,
                                            processingString)
            lfnBase(unmergedLFN)
            lfnBase(mergedLFN)

        cmsswStep = parentTask.getStep(stepName)
        cmsswStepHelper = cmsswStep.getTypeHelper()
        cmsswStepHelper.addOutputModule(outputModuleName,
                                        primaryDataset = primaryDataset,
                                        processedDataset = processedDataset,
                                        dataTier = dataTier,
                                        filterName = filterName,
                                        lfnBase = unmergedLFN,
                                        mergedLFNBase = mergedLFN)

        return {"primaryDataset": primaryDataset,
                "dataTier": dataTier,
                "processedDataset": processedDataset,
                "filterName": filterName}

    def addLogCollectTask(self, parentTask, taskName = "LogCollect", filesPerJob = 500):
        """
        _addLogCollectTask_

        Create a LogCollect task for log archives that are produced by the
        parent task.
        """
        logCollectTask = parentTask.addTask(taskName)
        self.addDashboardMonitoring(logCollectTask)
        logCollectStep = logCollectTask.makeStep("logCollect1")
        logCollectStep.setStepType("LogCollect")
        logCollectTask.applyTemplates()
        logCollectTask.setSplittingAlgorithm("MinFileBased", files_per_job = filesPerJob)
        logCollectTask.setTaskType("LogCollect")

        parentTaskLogArch = parentTask.getStep("logArch1")
        logCollectTask.setInputReference(parentTaskLogArch, outputModule = "logArchive")
        return logCollectTask

    def addMergeTask(self, parentTask, parentTaskSplitting, parentOutputModuleName,
                     parentStepName = "cmsRun1"):
        """
        _addMergeTask_

        Create a merge task for files produced by the parent task.
        """
        mergeTask = parentTask.addTask("%sMerge%s" % (parentTask.name(), parentOutputModuleName))
        self.addDashboardMonitoring(mergeTask)
        mergeTaskCmssw = mergeTask.makeStep("cmsRun1")
        mergeTaskCmssw.setStepType("CMSSW")

        mergeTaskStageOut = mergeTaskCmssw.addStep("stageOut1")
        mergeTaskStageOut.setStepType("StageOut")
        mergeTaskLogArch = mergeTaskCmssw.addStep("logArch1")
        mergeTaskLogArch.setStepType("LogArchive")

        mergeTask.setTaskLogBaseLFN(self.unmergedLFNBase)
        self.addLogCollectTask(mergeTask, taskName = "%s%sMergeLogCollect" % (parentTask.name(), parentOutputModuleName))

        mergeTask.setTaskType("Merge")
        mergeTask.applyTemplates()
        mergeTask.setTaskPriority(self.priority + 5)

        if parentTaskSplitting == "EventBased" and parentTask.taskType() != "Production":
            splitAlgo = "WMBSMergeBySize"
        else:
            splitAlgo = "ParentlessMergeBySize"

        parentTaskCmssw = parentTask.getStep(parentStepName)
        parentOutputModule = parentTaskCmssw.getOutputModule(parentOutputModuleName)

        mergeTaskCmsswHelper = mergeTaskCmssw.getTypeHelper()
        mergeTaskCmsswHelper.cmsswSetup(self.frameworkVersion, softwareEnvironment = "",
                                        scramArch = self.scramArch)

        if getattr(parentOutputModule, "dataTier") == "DQM":
            # DQM wants everything to be a single file per run, so we'll merge
            # accordingly.  We'll set the max_wait_time to two weeks as files
            # tend to be garbage collected after that.
            mergeTask.setSplittingAlgorithm(splitAlgo,
                                            max_merge_size = 21000000000,
                                            min_merge_size = 20000000000,
                                            max_merge_events = 21000000000,
                                            max_wait_time = 14 * 24 * 3600,
                                            merge_across_runs = False,
                                            siteWhitelist = self.siteWhitelist,
                                            siteBlacklist = self.siteBlacklist)
            mergeTaskCmsswHelper.setDataProcessingConfig("cosmics", "merge", dqm_format = True)
        else:
            mergeTask.setSplittingAlgorithm(splitAlgo,
                                            max_merge_size = self.maxMergeSize,
                                            min_merge_size = self.minMergeSize,
                                            max_merge_events = self.maxMergeEvents,
                                            max_wait_time = self.maxWaitTime,
                                            siteWhitelist = self.siteWhitelist,
                                            siteBlacklist = self.siteBlacklist)
            mergeTaskCmsswHelper.setDataProcessingConfig("cosmics", "merge")

        mergeTaskCmsswHelper.setErrorDestinationStep(stepName = mergeTaskLogArch.name())
        mergeTaskCmsswHelper.setGlobalTag(self.globalTag)

        mergedLFN = "%s/%s/%s/%s/%s" % (self.mergedLFNBase, self.acquisitionEra,
                                        getattr(parentOutputModule, "primaryDataset"),
                                        getattr(parentOutputModule, "dataTier"),
                                        self.processingVersion)
        mergeTaskCmsswHelper.addOutputModule("Merged",
                                             primaryDataset = getattr(parentOutputModule, "primaryDataset"),
                                             processedDataset = getattr(parentOutputModule, "processedDataset"),
                                             dataTier = getattr(parentOutputModule, "dataTier"),
                                             filterName = getattr(parentOutputModule, "filterName"),
                                             lfnBase = mergedLFN)

        mergeTask.setInputReference(parentTaskCmssw, outputModule = parentOutputModuleName)
        self.addCleanupTask(parentTask, parentOutputModuleName)
        return mergeTask

    def addCleanupTask(self, parentTask, parentOutputModuleName):
        """
        _addCleanupTask_

        Create a cleanup task to delete files produces by the parent task.
        """
        cleanupTask = parentTask.addTask("%sCleanupUnmerged%s" % (parentTask.name(), parentOutputModuleName))
        self.addDashboardMonitoring(cleanupTask)
        cleanupTask.setTaskType("Cleanup")

        parentTaskCmssw = parentTask.getStep("cmsRun1")
        cleanupTask.setInputReference(parentTaskCmssw, outputModule = parentOutputModuleName)
        cleanupTask.setSplittingAlgorithm("SiblingProcessingBased", files_per_job = 50)

        cleanupStep = cleanupTask.makeStep("cleanupUnmerged%s" % parentOutputModuleName)
        cleanupStep.setStepType("DeleteFiles")
        cleanupTask.applyTemplates()
        cleanupTask.setTaskPriority(self.priority + 5)
        return

    def setupPileup(self, task, pileupConfig):
        """
        Support for pileup input for MonteCarlo and RelValMC workloads

        """
        # task is instance of WMTaskHelper (WMTask module)
        # retrieve task helper (cmssw step helper), top step name is cmsRun1
        stepName = task.getTopStepName()
        stepHelper = task.getStepHelper(stepName)
        stepHelper.setupPileup(pileupConfig, self.dbsUrl)
        return

    def validateSchema(self, schema):
        """
        _validateSchema_

        Validate the schema prior to building the workload
        This function should be overridden by individual specs

        If something breaks, raise a WMSpecFactoryException.  A message
        in that excpetion will be transferred to an HTTP Error later on.
        """
        return

    def validateWorkload(self, workload):
        """
        _validateWorkload_

        Just in case you have something that you want to validate
        after the workload gets created, this is where you should
        put it.

        If something breaks, raise a WMSpecFactoryException.  A message
        in that excpetion will be transferred to an HTTP Error later on.
        """
        return

    def factoryWorkloadConstruction(self, workloadName, arguments):
        """
        _factoryWorkloadConstruction_

        Master build for ReqMgr - builds the entire workload
        and also performs the proper validation.

        Named this way so that nobody else will try to use this name.
        """

        self.validateSchema(schema = arguments)
        workload = self.__call__(workloadName = workloadName, arguments = arguments)
        self.validateWorkload(workload)

        return workload

    def requireValidateFields(self, fields, schema, validate = False):
        """
        _requireValidateFields_

        Standard tool for StdBase derived classes to make sure
        that a schema has a certain set of valid fields.  Uses WMCore.Lexicon.identifier

        To be used in validateWorkload()
        """

        for field in fields:
            if not field in schema.keys():
                msg = "Missing required field %s in workload validation!" % field
                self.raiseValidationException(msg = msg)
            if schema[field] == None:
                msg = "NULL value for required field %s!" % field
                self.raiseValidationException(msg = msg)
            if validate:
                try:
                    identifier(candidate = schema[field])
                except AssertionError, ex:
                    msg = "Schema value for field %s failed Lexicon validation" % field
                    self.raiseValidationException(msg = msg)
        return

    def raiseValidationException(self, msg):
        """
        _raiseValidationException_

        Inbuilt method for raising exception so people don't have
        to import WMSpecFactoryException all over the place.
        """

        logging.error("About to raise exception %s" % msg)
        raise WMSpecFactoryException(message = msg)

    def validateConfigCacheExists(self, configID, couchURL, couchDBName,
                                  getOutputModules = False):
        """
        _validateConfigCacheExists_

        If we have a configCache, we should probably try and load it.
        """
        from WMCore.Cache.WMConfigCache import ConfigCache
        configCache = ConfigCache(dbURL = couchURL,
                                  couchDBName = couchDBName,
                                  id = configID)
        try:
            configCache.loadByID(configID = configID)
        except ConfigCacheException, ex:
            self.raiseValidationException(msg = "Failure to load ConfigCache while validating workload")

        duplicateCheck = {}
        outputModuleInfo = configCache.getOutputModuleInfo()
        for outputModule in outputModuleInfo.values():
            dataTier   = outputModule.get('dataTier', None)
            filterName = outputModule.get('filterName', None)
            if not dataTier:
                self.raiseValidationException(msg = "No DataTier in output module.")
            if not filterName:
                self.raiseValidationException(msg = "No FilterName in output module.")

            # Add dataTier to duplicate dictionary
            if not dataTier in duplicateCheck.keys():
                duplicateCheck[dataTier] = []
            if filterName in duplicateCheck[dataTier]:
                # Then we've seen this combination before
                self.raiseValidationException(msg = "Duplicate dataTier/filterName combination.")
            else:
                duplicateCheck[dataTier].append(filterName)

        if getOutputModules:
            return outputModuleInfo

        return
