#!/usr/bin/env python
"""
_WMWorkload_t_

Unittest for WMWorkload class
"""

import os
import unittest

from WMCore.WMSpec.WMWorkload import WMWorkload, WMWorkloadHelper, WMWorkloadException
from WMCore.WMSpec.WMTask import WMTask, WMTaskHelper

class WMWorkloadTest(unittest.TestCase):
    def setUp(self):
        """
        _setUp_

        """
        self.persistFile = "%s/WMWorkloadPersistencyTest.pkl" % os.getcwd()
        return

    def tearDown(self):
        """
        _tearDown_

        """
        if os.path.exists(self.persistFile):
            os.remove(self.persistFile)
        return

    def testInstantiation(self):
        """
        _testInstantiation_

        Verify that the WMWorkload class and the WMWorkloadHelper class can
        be instantiated.
        """
        workload = WMWorkload("workload1")
        helper = WMWorkloadHelper(WMWorkload("workload2"))
        return

    def testB(self):
        """adding Tasks"""

        workload = WMWorkloadHelper(WMWorkload("workload1"))

        task1 = WMTask("task1")
        task2 = WMTaskHelper(WMTask("task2"))

        # direct addition of task
        workload.addTask(task1)
        workload.addTask(task2)

        self.assertEqual(workload.listAllTaskNodes(), ["task1", "task2"])

        # using factory method to create new task when added
        task3 = workload.newTask("task3")

        task4 = workload.newTask("task4")

        workload.newTask("task5")
        workload.removeTask("task5")

        self.assertEqual(workload.listAllTaskNodes(),
                         ["task1", "task2", "task3", "task4"])

        # prevent adding duplicate tasks
        self.assertRaises(RuntimeError, workload.addTask, task1)
        self.assertRaises(RuntimeError, workload.newTask, "task4")

        self.assertEqual(workload.listAllTaskNodes(),
                         ["task1", "task2", "task3", "task4"])


        self.assertEqual(workload.getTask("task1").name(), "task1")
        self.assertEqual(workload.getTask("task2").name(), "task2")
        self.assertEqual(workload.getTask("task3").name(), "task3")
        self.assertEqual(workload.getTask("task4").name(), "task4")


    def testC(self):
        """test persistency"""

        workload = WMWorkloadHelper(WMWorkload("workload1"))
        workload.newTask("task1")
        workload.newTask("task2")
        workload.newTask("task3")
        workload.newTask("task4")

        workload.save(self.persistFile)

        workload2 = WMWorkloadHelper(WMWorkload("workload2"))
        workload2.load(self.persistFile)

        self.assertEqual(
            workload.listAllTaskNames(),
            workload2.listAllTaskNames()
            )
        # probably need to flesh this out a bit more

    def testD_Owner(self):
        """Test setOwner/getOwner function. """

        workload = WMWorkloadHelper(WMWorkload("workload1"))

        workload.setOwnerDetails(name = "Lumumba", group = "Hoodoo")
        self.assertEqual(workload.data.owner.name, "Lumumba")
        self.assertEqual(workload.data.owner.group, "Hoodoo")
        self.assertEqual(workload.data.owner.dn, 'DEFAULT')

        result = workload.getOwner()

        ownerProps = {'capital': 'Kinshasa',
                      'adversary': 'Katanga',
                      'removedby': 'Kabila'}

        workload.setOwnerDetails(name = "Mobutu", group = "DMWM", ownerProperties = ownerProps)
        result = workload.getOwner()

        for key in ownerProps.keys():
            self.assertEqual(result[key], ownerProps[key])


    def testE_Properties(self):
        """
        _Properties_

        Check the values attached to the workloads general properties
        """
        name = "ThisIsASillyString"

        workload = WMWorkloadHelper(WMWorkload("workload1"))
        workload.setValidStatus(validStatus = name)
        workload.setProcessingVersion(processingVersion = name)
        workload.setAcquisitionEra(acquisitionEra = name)
        workload.setCustodialSite(siteName = name)

        self.assertEqual(workload.getValidStatus(), name)
        self.assertEqual(workload.getProcessingVersion(), name)
        self.assertEqual(workload.getAcquisitionEra(), name)
        self.assertEqual(workload.getCustodialSite(), name)

        return

        

    def testWhiteBlacklists(self):
        """
        _testWhiteBlacklists_

        Verify that setting site/block/run black and white lists through the
        workload helper class works as expected.  For site black and white lists
        the workload helper class should update the lists for all tasks.  For
        run and block lists only tasks that have input datasets defined should
        be updated.
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))

        procTestTask = testWorkload.newTask("ProcessingTask")
        procTestTaskCMSSW = procTestTask.makeStep("cmsRun1")
        procTestTaskCMSSW.setStepType("CMSSW")

        procTestTask.addInputDataset(primary = "PrimaryDataset",
                                     processed = "ProcessedDataset",
                                     tier = "DATATIER",
                                     block_whitelist = ["Block1", "Block2"],
                                     black_blacklist = ["Block3"],
                                     run_whitelist = [1, 2],
                                     run_blacklist = [3])

        mergeTestTask = procTestTask.addTask("MergeTask")
        mergeTestTask.setInputReference(procTestTaskCMSSW, outputModule = "output")

        weirdTestTask = mergeTestTask.addTask("WeirdTask")
        weirdTestTask.addInputDataset(primary = "PrimaryDatasetB",
                                      processed = "ProcessedDatasetB",
                                      tier = "DATATIERB",
                                      block_whitelist = ["BlockA", "BlockB"],
                                      black_blacklist = ["BlockC"],
                                      run_whitelist = [11, 12],
                                      run_blacklist = [13])

        testWorkload.setSiteWhitelist(["T1_US_FNAL", "T0_CH_CERN"])
        testWorkload.setSiteBlacklist(["T1_DE_KIT"])
        testWorkload.setBlockWhitelist(["Block4"])
        testWorkload.setBlockBlacklist(["Block5", "Block6"])
        testWorkload.setRunWhitelist([4])
        testWorkload.setRunBlacklist([5, 6])

        for task in [procTestTask, mergeTestTask, weirdTestTask]:
            self.assertEqual(len(task.siteWhitelist()), 2,
                             "Error: Wrong number of sites in white list.")
            self.assertEqual(len(task.siteBlacklist()), 1,
                             "Error: Wrong number of sites in black list.")

            self.assertTrue("T1_US_FNAL" in task.siteWhitelist(),
                            "Error: Site missing from white list.")
            self.assertTrue("T0_CH_CERN" in task.siteWhitelist(),
                            "Error: Site missing from white list.")
            self.assertTrue("T1_DE_KIT" in task.siteBlacklist(),
                            "Error: Site missing from black list.")

        for task in [procTestTask, weirdTestTask]:
            self.assertEqual(len(task.inputBlockWhitelist()), 1,
                             "Error: Wrong number of blocks in white list.")
            self.assertEqual(len(task.inputBlockBlacklist()), 2,
                             "Error: Wrong number of blocks in black list.")
            self.assertEqual(len(task.inputRunWhitelist()), 1,
                             "Error: Wrong number of runs in white list.")
            self.assertEqual(len(task.inputRunBlacklist()), 2,
                             "Error: Wrong number of runs in black list.")

            self.assertTrue("Block4" in task.inputBlockWhitelist(),
                            "Error: Block missing from white list.")
            self.assertTrue("Block5" in task.inputBlockBlacklist(),
                            "Error: Block missing from black list.")
            self.assertTrue("Block6" in task.inputBlockBlacklist(),
                            "Error: Block missing from black list.")

            self.assertTrue(4 in task.inputRunWhitelist(),
                            "Error: Run missing from white list.")
            self.assertTrue(5 in task.inputRunBlacklist(),
                            "Error: Run missing from black list.")
            self.assertTrue(6 in task.inputRunBlacklist(),
                            "Error: Run missing from black list.")

        self.assertEqual(mergeTestTask.inputBlockWhitelist(), None,
                         "Error: Block white list should be empty.")
        self.assertEqual(mergeTestTask.inputBlockBlacklist(), None,
                         "Error: Block black list should be empty.")
        self.assertEqual(mergeTestTask.inputRunWhitelist(), None,
                         "Error: Run white list should be empty.")
        self.assertEqual(mergeTestTask.inputRunBlacklist(), None,
                         "Error: Run black list should be empty.")

        return

    def testUpdatingMergeParameters(self):
        """
        _testUpdatingMergeParameters_

        Verify that the setMergeParameters() method updates all of the merge
        tasks in the workflow as well as the minimum merge size for processing
        tasks.
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))

        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setSplittingAlgorithm("FileBased", files_per_job = 1)
        procTask.setTaskType("Processing")
        procTaskCMSSW = procTask.makeStep("cmsRun1")
        procTaskCMSSW.setStepType("CMSSW")
        procTaskStageOut = procTaskCMSSW.addStep("StageOut1")
        procTaskStageOut.setStepType("StageOut")
        procTask.applyTemplates()
        procTaskStageOutHelper = procTaskStageOut.getTypeHelper()
        procTaskStageOutHelper.setMinMergeSize(1, 1)
        procTaskCMSSWHelper = procTaskCMSSW.getTypeHelper()
        procTaskCMSSWHelper.addOutputModule("output", dataTier = "RECO")
        procTaskCMSSWHelper.addOutputModule("outputDQM", dataTier = "DQM")        

        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setInputReference(procTaskCMSSW, outputModule = "output")
        mergeTask.setTaskType("Merge")
        mergeTask.setSplittingAlgorithm("WMBSMergeBySize", max_merge_size = 2,
                                        max_merge_events = 2, min_merge_size = 2)
        mergeTaskStageOut = mergeTask.makeStep("StageOut1")
        mergeTaskStageOut.setStepType("StageOut")
        mergeTaskCMSSW = mergeTask.makeStep("cmsRun1")
        mergeTaskCMSSW.setStepType("CMSSW")

        mergeDQMTask = procTask.addTask("MergeDQMTask")
        mergeDQMTask.setInputReference(procTaskCMSSW, outputModule = "outputDQM")
        mergeDQMTask.setTaskType("Merge")
        mergeDQMTask.setSplittingAlgorithm("WMBSMergeBySize", max_merge_size = 4,
                                           max_merge_events = 4, min_merge_size = 4,
                                           merge_across_runs = False)
        mergeDQMTaskCMSSW = mergeDQMTask.makeStep("cmsRun1")
        mergeDQMTaskCMSSW.setStepType("CMSSW")
        mergeDQMTaskStageOut = mergeDQMTaskCMSSW.addStep("StageOut1")
        mergeDQMTaskStageOut.setStepType("StageOut")
        mergeDQMTask.applyTemplates()
        mergeDQMTaskCMSSWHelper = mergeDQMTaskCMSSW.getTypeHelper()
        mergeDQMTaskCMSSWHelper.addOutputModule("Merged", dataTier = "DQM")

        skimTask = mergeTask.addTask("SkimTask")
        skimTask.setTaskType("Skim")
        skimTask.setInputReference(mergeTaskCMSSW, outputModule = "merged")
        skimTask.setSplittingAlgorithm("FileBased", files_per_job = 1, include_parents = True)
        skimTaskStageOut = skimTask.makeStep("StageOut1")
        skimTaskStageOut.setStepType("StageOut")
        skimTaskStageOutHelper = skimTaskStageOut.getTypeHelper()
        skimTaskStageOutHelper.setMinMergeSize(3, 3)
        testWorkload.setMergeParameters(minSize = 10, maxSize = 100, maxEvents = 1000)

        procSplitParams = procTask.jobSplittingParameters()
        self.assertEqual(len(procSplitParams.keys()), 4,
                         "Error: Wrong number of params for proc task.")
        self.assertEqual(procSplitParams["algorithm"], "FileBased",
                         "Error: Wrong job splitting algo for proc task.")
        self.assertEqual(procSplitParams["files_per_job"], 1,
                         "Error: Wrong number of files per job.")
        self.assertEqual(procSplitParams["siteWhitelist"], [],
                         "Error: Site white list was updated.")
        self.assertEqual(procSplitParams["siteBlacklist"], [],
                         "Error: Site black list was updated.")

        skimSplitParams = skimTask.jobSplittingParameters()
        self.assertEqual(len(skimSplitParams.keys()), 5,
                         "Error: Wrong number of params for skim task.")
        self.assertEqual(skimSplitParams["algorithm"], "FileBased",
                         "Error: Wrong job splitting algo for skim task.")
        self.assertEqual(skimSplitParams["files_per_job"], 1,
                         "Error: Wrong number of files per job.")
        self.assertEqual(skimSplitParams["include_parents"], True,
                         "Error: Include parents is wrong.")        
        self.assertEqual(skimSplitParams["siteWhitelist"], [],
                         "Error: Site white list was updated.")
        self.assertEqual(skimSplitParams["siteBlacklist"], [],
                         "Error: Site black list was updated.")

        mergeSplitParams = mergeTask.jobSplittingParameters()
        self.assertEqual(len(mergeSplitParams.keys()), 6,
                         "Error: Wrong number of params for merge task.")
        self.assertEqual(mergeSplitParams["algorithm"], "WMBSMergeBySize",
                         "Error: Wrong job splitting algo for merge task.")
        self.assertEqual(mergeSplitParams["min_merge_size"], 10,
                         "Error: Wrong min merge size.")
        self.assertEqual(mergeSplitParams["max_merge_size"], 100,
                         "Error: Wrong max merge size.")
        self.assertEqual(mergeSplitParams["max_merge_events"], 1000,
                         "Error: Wrong max merge events.")
        self.assertEqual(mergeSplitParams["siteWhitelist"], [],
                         "Error: Site white list was updated.")
        self.assertEqual(mergeSplitParams["siteBlacklist"], [],
                         "Error: Site black list was updated.")

        mergeDQMSplitParams = mergeDQMTask.jobSplittingParameters()
        self.assertEqual(len(mergeDQMSplitParams.keys()), 7,
                         "Error: Wrong number of params for merge task.")
        self.assertEqual(mergeDQMSplitParams["algorithm"], "WMBSMergeBySize",
                         "Error: Wrong job splitting algo for merge task.")
        self.assertEqual(mergeDQMSplitParams["min_merge_size"], 4,
                         "Error: Wrong min merge size: %s" % mergeDQMSplitParams)
        self.assertEqual(mergeDQMSplitParams["max_merge_size"], 4,
                         "Error: Wrong max merge size.")
        self.assertEqual(mergeDQMSplitParams["max_merge_events"], 4,
                         "Error: Wrong max merge events.")
        self.assertEqual(mergeDQMSplitParams["siteWhitelist"], [],
                         "Error: Site white list was updated.")
        self.assertEqual(mergeDQMSplitParams["siteBlacklist"], [],
                         "Error: Site black list was updated.")        

        self.assertEqual(procTaskStageOutHelper.minMergeSize(), 10,
                         "Error: Min merge size for proc task is wrong.")
        self.assertEqual(skimTaskStageOutHelper.minMergeSize(), 10,
                         "Error: Min merge size for skim task is wrong.")

        testWorkload.setJobSplittingParameters("/TestWorkload/ProcessingTask", "EventBased",
                                               {"events_per_job": 2})
        testWorkload.setMergeParameters(minSize = 20, maxSize = 100, maxEvents = 1000)

        self.assertEqual(procTaskStageOutHelper.minMergeSize(), -1,
                         "Error: Min merge size for proc task is wrong.")
        self.assertEqual(skimTaskStageOutHelper.minMergeSize(), 20,
                         "Error: Min merge size for skim task is wrong.")
        return

    def testUpdatingLFNAndDataset(self):
        """
        _testUpdatingLFNAndDataset_

        Verify that after chaning the acquisition era, processing version and
        merge/unmerged LFN bases that all the output datasets are named
        correctly and that the metadata contained in each output module is
        correct.  Also verify that the listOutputDatasets() method works
        correctly.
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))

        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setTaskType("Processing")
        procTaskCMSSW = procTask.makeStep("cmsRun1")
        procTaskCMSSW.setStepType("CMSSW")
        procTaskCMSSWHelper = procTaskCMSSW.getTypeHelper()
        procTaskCMSSW2 = procTaskCMSSW.addStep("cmsRun2")
        procTaskCMSSW2.setStepType("CMSSW")
        procTaskCMSSW2Helper = procTaskCMSSW2.getTypeHelper()
        procTask.applyTemplates()
        procTaskCMSSW2Helper.keepOutput(False)

        acquisitionEra = "TestAcqEra"
        primaryDataset = "bogusPrimary"
        procEra        = "vTest"

        procTaskCMSSWHelper.addOutputModule("OutputA",
                                            primaryDataset = primaryDataset,
                                            processedDataset = "bogusProcessed",
                                            dataTier = "DATATIERA",
                                            lfnBase = "bogusUnmerged",
                                            mergedLFNBase = "bogusMerged",
                                            filterName = None)
        procTaskCMSSW2Helper.addOutputModule("OutputC",
                                            primaryDataset = primaryDataset,
                                            processedDataset = "bogusProcessed",
                                            dataTier = "DATATIERC",
                                            lfnBase = "bogusUnmerged",
                                            mergedLFNBase = "bogusMerged",
                                            filterName = None)        
        procTaskCMSSWHelper.addOutputModule("OutputB",
                                            primaryDataset = primaryDataset,
                                            processedDataset = "bogusProcessed",
                                            dataTier = "DATATIERB",
                                            lfnBase = "bogusUnmerged",
                                            mergedLFNBase = "bogusMerged",
                                            filterName = None)

        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setTaskType("Merge")
        mergeTaskCMSSW = mergeTask.makeStep("cmsRun1")
        mergeTaskCMSSW.setStepType("CMSSW")
        mergeTaskCMSSWHelper = mergeTaskCMSSW.getTypeHelper()
        mergeTask.applyTemplates()

        mergeTaskCMSSWHelper.addOutputModule("Merged",
                                             primaryDataset = "bogusPrimary",
                                             processedDataset = "bogusProcessed",
                                             dataTier = "DATATIERA",
                                             lfnBase = "bogusMerged",
                                             mergedLFNBase = "bogusMerged",
                                             filterName = None)

        skimTask = mergeTask.addTask("SkimTask")
        skimTask.setTaskType("Skim")
        skimTaskCMSSW = skimTask.makeStep("cmsRun1")
        skimTaskCMSSW.setStepType("CMSSW")
        skimTaskCMSSWHelper = skimTaskCMSSW.getTypeHelper()
        skimTask.applyTemplates()



        skimTaskCMSSWHelper.addOutputModule("SkimA",
                                            primaryDataset = primaryDataset,
                                            processedDataset = "bogusProcessed",
                                            dataTier = "DATATIERA",
                                            lfnBase = "bogusUnmerged",
                                            mergedLFNBase = "bogusMerged",
                                            filterName = "bogusFilter")

        testWorkload.setAcquisitionEra(acquisitionEra)

        outputModules = [procTaskCMSSWHelper.getOutputModule("OutputA"),
                         procTaskCMSSWHelper.getOutputModule("OutputB"),
                         mergeTaskCMSSWHelper.getOutputModule("Merged"),
                         skimTaskCMSSWHelper.getOutputModule("SkimA")]

        for outputModule in outputModules:
            self.assertEqual(outputModule.primaryDataset, "bogusPrimary",
                             "Error: Primary dataset was modified.")
            dataTier = outputModule.dataTier
            filterName = outputModule.filterName

            if filterName == None:
                procDataset = "%s-None" % (acquisitionEra)
                self.assertEqual(outputModule.processedDataset, procDataset,
                                 "Error: Processed dataset is incorrect.")
            else:
                procDataset = "%s-%s-None" % (acquisitionEra, filterName)
                self.assertEqual(outputModule.processedDataset, procDataset,
                                 "Error: Processed dataset is incorrect.")

            if filterName != None:
                mergedLFN = "/store/data/%s/%s/%s/%s-%s" % (acquisitionEra, primaryDataset, dataTier, filterName, 'None')
                unmergedLFN = "/store/unmerged/%s/%s/%s/%s-%s" % (acquisitionEra, primaryDataset, dataTier, filterName, 'None')
            else:
                mergedLFN = "/store/data/%s/%s/%s/%s" % (acquisitionEra, primaryDataset, dataTier, 'None')
                unmergedLFN = "/store/unmerged/%s/%s/%s/%s" % (acquisitionEra, primaryDataset, dataTier, 'None')                

            if outputModule._internal_name == "Merged":
                self.assertEqual(outputModule.lfnBase, mergedLFN,
                                 "Error: Incorrect unmerged LFN %s." % outputModule.lfnBase)
                self.assertEqual(outputModule.mergedLFNBase, mergedLFN,
                                 "Error: Incorrect merged LFN %s." % outputModule.mergedLFNBase)
            else:
                self.assertEqual(outputModule.lfnBase, unmergedLFN,
                                 "Error: Incorrect unmerged LFN %s." % outputModule.lfnBase)
                self.assertEqual(outputModule.mergedLFNBase, mergedLFN,
                                 "Error: Incorrect merged LFN %s." % outputModule.mergedLFNBase)

        testWorkload.setProcessingVersion(procEra)

        for outputModule in outputModules:
            self.assertEqual(outputModule.primaryDataset, "bogusPrimary",
                             "Error: Primary dataset was modified.")

            dataTier = outputModule.dataTier
            filterName = outputModule.filterName

            if filterName == None:
                procDataset = "TestAcqEra-vTest"
                self.assertEqual(outputModule.processedDataset, procDataset,
                                 "Error: Processed dataset is incorrect.")
            else:
                procDataset = "TestAcqEra-%s-vTest" % filterName
                self.assertEqual(outputModule.processedDataset, procDataset,
                                 "Error: Processed dataset is incorrect.")

            if filterName != None:
                mergedLFN = "/store/data/%s/%s/%s/%s-%s" % (acquisitionEra, primaryDataset, dataTier, filterName, "vTest")
                unmergedLFN = "/store/unmerged/%s/%s/%s/%s-%s" % (acquisitionEra, primaryDataset, dataTier, filterName, "vTest")
            else:
                mergedLFN = "/store/data/%s/%s/%s/%s" % (acquisitionEra, primaryDataset, dataTier, "vTest")
                unmergedLFN = "/store/unmerged/%s/%s/%s/%s" % (acquisitionEra, primaryDataset, dataTier, "vTest")

            if outputModule._internal_name == "Merged":
                self.assertEqual(outputModule.lfnBase, mergedLFN,
                                 "Error: Incorrect unmerged LFN.")
                self.assertEqual(outputModule.mergedLFNBase, mergedLFN,
                                 "Error: Incorrect merged LFN.")
            else:
                self.assertEqual(outputModule.lfnBase, unmergedLFN,
                                 "Error: Incorrect unmerged LFN %s" % outputModule.lfnBase)
                self.assertEqual(outputModule.mergedLFNBase, mergedLFN,
                                 "Error: Incorrect merged LFN %s." % outputModule.mergedLFNBase)

        mergedLFNBase   = "/store/temp/merged"
        unmergedLFNBase = "/store/temp/unmerged"
        testWorkload.setLFNBase(mergedLFNBase, unmergedLFNBase)

        self.assertEqual(testWorkload.getLFNBases(), (mergedLFNBase,
                                                      unmergedLFNBase),
                         "Error: Wrong LFN bases.")

        for outputModule in outputModules:
            self.assertEqual(outputModule.primaryDataset, "bogusPrimary",
                             "Error: Primary dataset was modified.")

            dataTier = outputModule.dataTier
            filterName = outputModule.filterName

            if filterName == None:
                procDataset = "TestAcqEra-vTest"
                self.assertEqual(outputModule.processedDataset, procDataset,
                                 "Error: Processed dataset is incorrect.")
            else:
                procDataset = "TestAcqEra-%s-vTest" % filterName
                self.assertEqual(outputModule.processedDataset, procDataset,
                                 "Error: Processed dataset is incorrect.")

            if filterName != None:
                mergedLFN = "/store/temp/merged/%s/%s/%s/%s-%s" % (acquisitionEra, primaryDataset, dataTier, filterName, 'vTest')
                unmergedLFN = "/store/temp/unmerged/%s/%s/%s/%s-%s" % (acquisitionEra, primaryDataset, dataTier, filterName, 'vTest')
            else:
                mergedLFN = "/store/temp/merged/%s/%s/%s/%s" % (acquisitionEra, primaryDataset, dataTier, 'vTest')
                unmergedLFN = "/store/temp/unmerged/%s/%s/%s/%s" % (acquisitionEra, primaryDataset, dataTier, 'vTest')

            if outputModule._internal_name == "Merged":
                self.assertEqual(outputModule.lfnBase, mergedLFN,
                                 "Error: Incorrect unmerged LFN.")
                self.assertEqual(outputModule.mergedLFNBase, mergedLFN,
                                 "Error: Incorrect merged LFN.")
            else:
                self.assertEqual(outputModule.lfnBase, unmergedLFN,
                                 "Error: Incorrect unmerged LFN %s" % outputModule.lfnBase)
                self.assertEqual(outputModule.mergedLFNBase, mergedLFN,
                                 "Error: Incorrect merged LFN %s" % outputModule.mergedLFNBase)

        outputDatasets = testWorkload.listOutputDatasets()
        self.assertEqual(len(outputDatasets), 3,
                         "Error: Wrong number of output datasets: %s" % testWorkload.listOutputDatasets())
        self.assertTrue("/bogusPrimary/TestAcqEra-vTest/DATATIERA" in outputDatasets,
                        "Error: A dataset is missing")
        self.assertTrue("/bogusPrimary/TestAcqEra-vTest/DATATIERB" in outputDatasets,
                        "Error: A dataset is missing")
        self.assertTrue("/bogusPrimary/TestAcqEra-bogusFilter-vTest/DATATIERA" in outputDatasets,
                        "Error: A dataset is missing")
        return

    def testUpdatingSplitParameters(self):
        """
        _testUpdatingSplitParameters_

        Verify that the method to update all the splitting algorithms for a
        given type of task works correctly.
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))
        testWorkload.setWorkQueueSplitPolicy("Block", "FileBased", {"files_per_job": 1})
        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setSplittingAlgorithm("FileBased", files_per_job = 1)
        procTask.setTaskType("Processing")
        procTaskCmssw = procTask.makeStep("cmsRun1")
        procTaskCmssw.setStepType("CMSSW")
        procTaskStageOut = procTask.makeStep("StageOut1")
        procTaskStageOut.setStepType("StageOut")
        procTaskStageOut.getTypeHelper().setMinMergeSize(2, 2)
        procTask.applyTemplates()

        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setTaskType("Merge")
        mergeTask.setSplittingAlgorithm("WMBSMergeBySize", max_merge_size = 2,
                                        max_merge_events = 2, min_merge_size = 2)

        skimTask = mergeTask.addTask("SkimTask")
        skimTask.setTaskType("Skim")
        skimTaskCmssw = skimTask.makeStep("cmsRun1")
        skimTaskCmssw.setStepType("CMSSW")
        skimTask.setSplittingAlgorithm("FileBased", files_per_job = 1, include_parents = True)
        skimTask.applyTemplates()

        testWorkload.setJobSplittingParameters("/TestWorkload/ProcessingTask", "FileBased",
                                               {"files_per_job": 2, "include_parents": True})
        testWorkload.setJobSplittingParameters("/TestWorkload/ProcessingTask/MergeTask/SkimTask", "RunBased",
                                               {"max_files": 21,
                                                "some_other_param": "value"})

        self.assertEqual(testWorkload.startPolicy(), "Block",
                         "Error: Wrong start policy: %s" % testWorkload.startPolicy())
        self.assertEqual(testWorkload.startPolicyParameters()["SliceType"], "NumberOfFiles",
                         "Errror: Wrong slice type.")
        self.assertEqual(testWorkload.startPolicyParameters()["SliceSize"], 2,
                         "Errror: Wrong slice size.")

        procSplitParams = procTask.jobSplittingParameters()
        self.assertEqual(len(procSplitParams.keys()), 5,
                         "Error: Wrong number of params for proc task.")
        self.assertEqual(procSplitParams["algorithm"], "FileBased",
                         "Error: Wrong job splitting algo for proc task.")
        self.assertEqual(procSplitParams["files_per_job"], 2,
                         "Error: Wrong number of files per job.")
        self.assertEqual(procSplitParams["include_parents"], True,
                         "Error: Include parents is wrong.")        
        self.assertEqual(procSplitParams["siteWhitelist"], [],
                         "Error: Site white list was updated.")
        self.assertEqual(procSplitParams["siteBlacklist"], [],
                         "Error: Site black list was updated.")

        stepHelper = procTask.getStepHelper("StageOut1")
        self.assertEqual(stepHelper.minMergeSize(), 2,
                         "Error: Wrong min merge size: %s" % stepHelper.minMergeSize())

        skimSplitParams = skimTask.jobSplittingParameters()
        self.assertEqual(len(skimSplitParams.keys()), 5,
                         "Error: Wrong number of params for skim task.")
        self.assertEqual(skimSplitParams["algorithm"], "RunBased",
                         "Error: Wrong job splitting algo for skim task.")
        self.assertEqual(skimSplitParams["max_files"], 21,
                         "Error: Wrong number of files per job.")
        self.assertEqual(skimSplitParams["some_other_param"], "value",
                         "Error: Wrong other param.")
        self.assertEqual(skimSplitParams["siteWhitelist"], [],
                         "Error: Site white list was updated.")
        self.assertEqual(skimSplitParams["siteBlacklist"], [],
                         "Error: Site black list was updated.")

        mergeSplitParams = mergeTask.jobSplittingParameters()
        self.assertEqual(len(mergeSplitParams.keys()), 6,
                         "Error: Wrong number of params for merge task.")
        self.assertEqual(mergeSplitParams["algorithm"], "ParentlessMergeBySize",
                         "Error: Wrong job splitting algo for merge task.")
        self.assertEqual(mergeSplitParams["min_merge_size"], 2,
                         "Error: Wrong min merge size.")
        self.assertEqual(mergeSplitParams["max_merge_size"], 2,
                         "Error: Wrong max merge size.")
        self.assertEqual(mergeSplitParams["max_merge_events"], 2,
                         "Error: Wrong max merge events.")
        self.assertEqual(mergeSplitParams["siteWhitelist"], [],
                         "Error: Site white list was updated.")
        self.assertEqual(mergeSplitParams["siteBlacklist"], [],
                         "Error: Site black list was updated.")

        testWorkload.setJobSplittingParameters("/TestWorkload/ProcessingTask", "EventBased",
                                               {"events_per_job": 4})

        self.assertEqual(testWorkload.startPolicy(), "Block",
                         "Error: Wrong start policy.")
        self.assertEqual(testWorkload.startPolicyParameters()["SliceType"], "NumberOfEvents",
                         "Errror: Wrong slice type.")
        self.assertEqual(testWorkload.startPolicyParameters()["SliceSize"], 4,
                         "Errror: Wrong slice size.")

        stepHelper = procTask.getStepHelper("StageOut1")
        self.assertEqual(stepHelper.minMergeSize(), -1,
                         "Error: Wrong min merge size.")

        mergeSplitParams = mergeTask.jobSplittingParameters()
        self.assertEqual(len(mergeSplitParams.keys()), 6,
                         "Error: Wrong number of params for merge task.")
        self.assertEqual(mergeSplitParams["algorithm"], "WMBSMergeBySize",
                         "Error: Wrong job splitting algo for merge task.")
        self.assertEqual(mergeSplitParams["min_merge_size"], 2,
                         "Error: Wrong min merge size.")
        self.assertEqual(mergeSplitParams["max_merge_size"], 2,
                         "Error: Wrong max merge size.")
        self.assertEqual(mergeSplitParams["max_merge_events"], 2,
                         "Error: Wrong max merge events.")
        self.assertEqual(mergeSplitParams["siteWhitelist"], [],
                         "Error: Site white list was updated.")
        self.assertEqual(mergeSplitParams["siteBlacklist"], [],
                         "Error: Site black list was updated.")

        testWorkload.setJobSplittingParameters("/TestWorkload/ProcessingTask", "FileBased",
                                               {"files_per_job": 4})

        stepHelper = procTask.getStepHelper("StageOut1")
        self.assertEqual(stepHelper.minMergeSize(), 2,
                         "Error: Wrong min merge size.")
        return

    def testListJobSplittingParametersByTask(self):
        """
        _testListJobSplittingParametersByTask_

        Verify that the listJobSplittingParametersByTask() method works
        correctly.
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))

        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setSplittingAlgorithm("FileBased", files_per_job = 1)
        procTask.setTaskType("Processing")

        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setTaskType("Merge")
        mergeTask.setSplittingAlgorithm("WMBSMergeBySize", max_merge_size = 2,
                                        max_merge_events = 2, min_merge_size = 2)

        skimTask = mergeTask.addTask("SkimTask")
        skimTask.setTaskType("Skim")
        skimTask.setSplittingAlgorithm("FileBased", files_per_job = 1)

        testWorkload.setJobSplittingParameters("/TestWorkload/ProcessingTask", "FileBased",
                                               {"files_per_job": 2})
        testWorkload.setJobSplittingParameters("/TestWorkload/ProcessingTask/MergeTask/SkimTask", "RunBased",
                                               {"max_files": 21,
                                                "some_other_param": "value"})

        results = testWorkload.listJobSplittingParametersByTask()

        self.assertEqual(len(results.keys()), 3, \
               "Error: Wrong number of tasks.")
        self.assertTrue("/TestWorkload/ProcessingTask" in results.keys(),
                        "Error: Task is missing.")
        self.assertTrue("/TestWorkload/ProcessingTask/MergeTask" in results.keys(),
                        "Error: Task is missing.")
        self.assertTrue("/TestWorkload/ProcessingTask/MergeTask/SkimTask" in results.keys(),
                        "Error: Task is missing.")

        self.assertEqual(results["/TestWorkload/ProcessingTask"], {"files_per_job": 2,
                                                                   "algorithm": "FileBased",
                                                                   "type": "Processing"},
                         "Error: Wrong splitting parameters: %s")
        self.assertEqual(results["/TestWorkload/ProcessingTask/MergeTask/SkimTask"],
                         {"max_files": 21, "algorithm": "RunBased", "some_other_param": "value", "type": "Skim"},
                         "Error: Wrong splitting parameters.")
        self.assertEqual(results["/TestWorkload/ProcessingTask/MergeTask"],
                         {"algorithm": "ParentlessMergeBySize", "max_merge_size": 2,
                          "max_merge_events": 2, "min_merge_size": 2, "type": "Merge"},
                         "Error: Wrong splitting parameters.")

        return

    def testUpdatingTimeouts(self):
        """
        _testUpdatingTimeouts_

        Verify that task timeouts are set correctly.
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))

        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setTaskType("Processing")
        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setTaskType("Merge")

        testWorkload.setTaskTimeOut("/TestWorkload/ProcessingTask", 60)
        testWorkload.setTaskTimeOut("/TestWorkload/ProcessingTask/MergeTask", 30)

        self.assertEqual(testWorkload.listTimeOutsByTask(),
                         {"/TestWorkload/ProcessingTask": 60,
                          "/TestWorkload/ProcessingTask/MergeTask": 30},
                         "Error: Timeouts not set correctly.")
        return

    def testDashboardActivity(self):
        """
        _testDashboardActivity_

        Verify that the dashboard activity can be read and set.
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))
        testWorkload.setDashboardActivity("Activity!")
        self.assertEqual(testWorkload.getDashboardActivity(), "Activity!",
                         "Error: Wrong dashboard activity.")
        return
        

    def testTruncate(self):
        """
        _testTruncate_

        Verify that the truncate method works correctly.
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))
        testWorkload.setOwnerDetails("sfoulkes", "DMWM")
        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setSplittingAlgorithm("FileBased", files_per_job = 1)
        procTask.setTaskType("Processing")
        procTaskCmssw = procTask.makeStep("cmsRun1")
        procTaskCmssw.setStepType("CMSSW")
        procTask.applyTemplates()
        procTaskCmsswHelper = procTaskCmssw.getTypeHelper()
        procTaskCmsswHelper.addOutputModule("output",
                                            primaryDataset = "primary",
                                            processedDataset = "processed",
                                            dataTier = "tier",
                                            filterName = "filter",
                                            lfnBase = "/store/data",
                                            mergedLFNBase = "/store/unmerged")

        procTaskStageOut = procTask.makeStep("StageOut1")
        procTaskStageOut.setStepType("StageOut")
        procTaskStageOut.getTypeHelper().setMinMergeSize(2, 2)
        procTask.applyTemplates()

        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setTaskType("Merge")
        mergeTask.setSplittingAlgorithm("WMBSMergeBySize", max_merge_size = 2,
                                        max_merge_events = 2, min_merge_size = 2)
        mergeTaskCmssw = mergeTask.makeStep("cmsRun1")
        mergeTaskCmssw.setStepType("CMSSW")
        mergeTask.applyTemplates()
        mergeTask.setInputReference(procTask, outputModule = "output")

        cleanupTask = procTask.addTask("CleanupTask")
        cleanupTask.setTaskType("Cleanup")
        cleanupTask.setSplittingAlgorithm("SiblingProcessingBased", files_per_job = 50)
        cleanupTaskCmssw = cleanupTask.makeStep("cmsRun1")
        cleanupTaskCmssw.setStepType("CMSSW")
        cleanupTask.applyTemplates()
        cleanupTask.setInputReference(procTask, outputModule = "output")

        skimTask = mergeTask.addTask("SkimTask")
        skimTask.setTaskType("Skim")
        skimTaskCmssw = skimTask.makeStep("cmsRun1")
        skimTaskCmssw.setStepType("CMSSW")
        skimTask.setSplittingAlgorithm("FileBased", files_per_job = 1)
        skimTask.applyTemplates()

        testWorkload.truncate("TestWorkload", "/TestWorkload/ProcessingTask",
                              "somecouchurl", "somedatabase")
        testWorkload.truncate("TestWorkloadResubmit", "/TestWorkload/ProcessingTask/MergeTask",
                              "somecouchurl", "somedatabase")

        self.assertEqual(testWorkload.getInitialJobCount(), 20000000,
                         "Error: Initial job count is wrong.")

        mergeTask = testWorkload.getTaskByPath("/TestWorkloadResubmit/MergeTask")
        self.assertEqual(mergeTask.jobSplittingParameters()["initial_lfn_counter"],
                         20000000, "Error: Initial LFN counter is incorrect.")

        self.assertEqual(len(testWorkload.getTopLevelTask()), 2,
                         "Error: There should be two top level tasks.")
        goldenTasks = [mergeTask.getPathName(), cleanupTask.getPathName()]
        for topLevelTask in testWorkload.getTopLevelTask():
            self.assertTrue(topLevelTask.getPathName() in goldenTasks,
                            "Error: Extra top level task.")
            goldenTasks.remove(topLevelTask.getPathName())

        self.assertEqual(testWorkload.name(), "TestWorkloadResubmit",
                         "Error: The workload name is wrong.")

        self.assertEqual(len(testWorkload.listAllTaskPathNames()), 3,
                         "Error: There should only be three tasks")
        self.assertEqual(len(testWorkload.listAllTaskNames()), 3,
                         "Error: There should only be three tasks")
        self.assertTrue("/TestWorkloadResubmit/MergeTask" in testWorkload.listAllTaskPathNames(),
                        "Error: Merge task is missing.")
        self.assertTrue("/TestWorkloadResubmit/CleanupTask" in testWorkload.listAllTaskPathNames(),
                        "Error: Cleanup task is missing.")
        self.assertTrue("/TestWorkloadResubmit/MergeTask/SkimTask" in testWorkload.listAllTaskPathNames(),
                        "Error: Skim task is missing.")
        self.assertTrue("MergeTask" in testWorkload.listAllTaskNames(),
                        "Error: Merge task is missing.")
        self.assertTrue("CleanupTask" in testWorkload.listAllTaskNames(),
                        "Error: Cleanup task is missing.")
        self.assertTrue("SkimTask" in testWorkload.listAllTaskNames(),
                        "Error: Skim task is missing.")
        self.assertEqual("ResubmitBlock", testWorkload.startPolicy(),
                         "Error: Start policy is wrong.")
        self.assertEqual(mergeTask.getInputACDC(),
                         {"database": "somedatabase", "fileset": "/TestWorkload/ProcessingTask/MergeTask",
                          "collection": "TestWorkload", "server": "somecouchurl"})

        return

    def testSetCMSSWParams(self):
        """
        _testSetCMSSWParams_

        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))
        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setSplittingAlgorithm("FileBased", files_per_job = 1)
        procTask.setTaskType("Processing")
        procTaskCmssw = procTask.makeStep("cmsRun1")
        procTaskCmssw.setStepType("CMSSW")
        procTask.applyTemplates()
        procTaskCmsswHelper = procTaskCmssw.getTypeHelper()
        procTaskCmsswHelper.addOutputModule("output",
                                            primaryDataset = "primary",
                                            processedDataset = "processed",
                                            dataTier = "tier",
                                            filterName = "filter",
                                            lfnBase = "/store/data",
                                            mergedLFNBase = "/store/unmerged")

        procTaskStageOut = procTask.makeStep("StageOut1")
        procTaskStageOut.setStepType("StageOut")
        procTaskStageOut.getTypeHelper().setMinMergeSize(2, 2)
        procTask.applyTemplates()

        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setTaskType("Merge")
        mergeTask.setSplittingAlgorithm("WMBSMergeBySize", max_merge_size = 2,
                                        max_merge_events = 2, min_merge_size = 2)
        mergeTaskCmssw = mergeTask.makeStep("cmsRun1")
        mergeTaskCmssw.setStepType("CMSSW")
        mergeTask.applyTemplates()
        mergeTask.setInputReference(procTask, outputModule = "output")

        cleanupTask = procTask.addTask("CleanupTask")
        cleanupTask.setTaskType("Cleanup")
        cleanupTask.setSplittingAlgorithm("SiblingProcessingBased", files_per_job = 50)
        cleanupTaskCmssw = cleanupTask.makeStep("cmsRun1")
        cleanupTaskCmssw.setStepType("CMSSW")
        cleanupTask.applyTemplates()
        cleanupTask.setInputReference(procTask, outputModule = "output")

        skimTask = mergeTask.addTask("SkimTask")
        skimTask.setTaskType("Skim")
        skimTaskCmssw = skimTask.makeStep("cmsRun1")
        skimTaskCmssw.setStepType("CMSSW")
        skimTask.setSplittingAlgorithm("FileBased", files_per_job = 1)
        skimTask.applyTemplates()

        testWorkload.setCMSSWParams(cmsswVersion = "CMSSW_1_1_1", globalTag =
                                    "GLOBALTAG", scramArch = "SomeSCRAMArch")

        def verifyParams(initialTask = None):
            """
            _verifyParams_

            Verify that the cmssw version and global tag parameters are
            correct.
            """
            taskIterator = initialTask.childTaskIterator()

            for task in taskIterator:
                for stepName in task.listAllStepNames():
                    stepHelper = task.getStepHelper(stepName)
                    if stepHelper.stepType() == "CMSSW":
                        self.assertEqual(stepHelper.getCMSSWVersion(),
                                         "CMSSW_1_1_1",
                                         "Error: CMSSW Version should match.")
                        self.assertEqual(stepHelper.getGlobalTag(),
                                         "GLOBALTAG",
                                         "Error: Global tag should match.")
                        self.assertEqual(stepHelper.getScramArch(), "SomeSCRAMArch",
                                         "Error: Scram arch should match.")

        for task in testWorkload.taskIterator():
            verifyParams(task)
        return

    def testGenerateSummaryInfo(self):
        """
        _testGenerateSummaryInfo_
        
        Test that we can generate the summary info for a workload
        
        Checks listInputDatasets by proxy
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))
    
        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setTaskType("Processing")
        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setTaskType("Merge")
    
        procTaskCMSSW = procTask.makeStep("cmsRun1")
        procTaskCMSSW.setStepType("CMSSW")
        procTaskCMSSWHelper = procTaskCMSSW.getTypeHelper()
        procTask.applyTemplates()
        
        summary = testWorkload.generateWorkloadSummary()

        # All that should be in here should be tasks.
        self.assertEqual(summary, {'input': [], 'ACDC': {'filesets': {}, 'collection': None},
                                   'tasks': ['/TestWorkload/ProcessingTask',
                                             '/TestWorkload/ProcessingTask/MergeTask'],
                                   'output': [],
                                   'performance': {'/TestWorkload/ProcessingTask': {},
                                                   '/TestWorkload/ProcessingTask/MergeTask': {}},
                                   'owner': {}})

        procTask.addInputDataset(primary = "PrimaryDatasetB",
                                 processed = "ProcessedDatasetB",
                                 tier = "DataTierB",
                                 block_whitelist = ["BlockA", "BlockB"],
                                 black_blacklist = ["BlockC"],
                                 run_whitelist = [11, 12],
                                 run_blacklist = [13])
        
        procTaskCMSSWHelper.addOutputModule("OutputA",
                                            primaryDataset = "bogusPrimary",
                                            processedDataset = "bogusProcessed",
                                            dataTier = "DataTierA",
                                            lfnBase = "bogusUnmerged",
                                            mergedLFNBase = "bogusMerged",
                                            filterName = None)

        summary = testWorkload.generateWorkloadSummary()

        # Now see if we have the input and output dataset
        self.assertEqual(summary.get('input', None),
                         ['/PrimaryDatasetB/ProcessedDatasetB/DataTierB'])
        self.assertEqual(summary.get('output', None),
                         ['/bogusPrimary/bogusProcessed/DataTierA'])

        return


    def test_addPerformanceMonitor(self):
        """
        _addPerformanceMonitor_

        Don't use this, and don't play around with it.
        """

        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))
    
        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setTaskType("Processing")
        mergeTask = procTask.addTask("MergeTask")
        mergeTask.setTaskType("Merge")
    
        
        testWorkload.setupPerformanceMonitoring(maxRSS = 101, maxVSize = 102)
        self.assertEqual(testWorkload.data.tasks.ProcessingTask.watchdog.PerformanceMonitor.maxRSS, 101)
        self.assertEqual(testWorkload.data.tasks.ProcessingTask.watchdog.PerformanceMonitor.maxVSize, 102)
        self.assertFalse(hasattr(testWorkload.data.tasks.ProcessingTask.tree.children.MergeTask, 'watchdog'))
        return

    def test_parseSiteWildcards(self):
        """
        _parseSiteWildcards_

        Parse the methods by which we add wildcards to the site
        whitelist/blacklist
        """

        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))
        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setTaskType("Processing")

        wildcardKeys = {'T1*': 'T1_*', 'T2*': 'T2_*',
                        'T3*': 'T3_*', 'US*': '_US_'}
        siteList = ['T1_US_FNAL', 'T1_CH_CERN', 'T1_UK_RAL',
                    'T2_US_UCSD', 'T2_US_UNL', 'T2_US_CIT']
        wildcardSites = {'T2*': ['T2_US_UCSD', 'T2_US_UNL', 'T2_US_CIT'],
                         'US*': ['T1_US_FNAL', 'T2_US_UCSD', 'T2_US_UNL', 'T2_US_CIT'],
                         'T1*': ['T1_US_FNAL', 'T1_CH_CERN', 'T1_UK_RAL']}

        # Test full set
        testWorkload.setSiteWildcardsLists(siteWhitelist = ['US*', 'T1*'],
                                           siteBlacklist = [],
                                           wildcardDict = wildcardSites)
        self.assertEqual(testWorkload.data.tasks.ProcessingTask.constraints.sites.whitelist.sort(),
                         siteList.sort())

        # Test one subset
        testWorkload.setSiteWildcardsLists(siteWhitelist = ['US*'],
                                           siteBlacklist = [],
                                           wildcardDict = wildcardSites)
        self.assertEqual(testWorkload.data.tasks.ProcessingTask.constraints.sites.whitelist.sort(),
                         ['T1_US_FNAL', 'T2_US_UCSD', 'T2_US_UNL', 'T2_US_CIT'].sort())

        # Test one subset plus one site
        testWorkload.setSiteWildcardsLists(siteWhitelist = ['US*', 'T1_UK_RAL'],
                                           siteBlacklist = [],
                                           wildcardDict = wildcardSites)
        self.assertEqual(testWorkload.data.tasks.ProcessingTask.constraints.sites.whitelist.sort(),
                         ['T1_US_FNAL', 'T2_US_UCSD', 'T2_US_UNL', 'T2_US_CIT', 'T1_UK_RAL'].sort())

        # Repeat above with blacklist
        # Test full set
        testWorkload.setSiteWildcardsLists(siteBlacklist = ['US*', 'T1*'],
                                           siteWhitelist = [],
                                           wildcardDict = wildcardSites)
        self.assertEqual(testWorkload.data.tasks.ProcessingTask.constraints.sites.blacklist.sort(),
                         siteList.sort())

        # Test one subset
        testWorkload.setSiteWildcardsLists(siteBlacklist = ['US*'],
                                           siteWhitelist = [],
                                           wildcardDict = wildcardSites)
        self.assertEqual(testWorkload.data.tasks.ProcessingTask.constraints.sites.blacklist.sort(),
                         ['T1_US_FNAL', 'T2_US_UCSD', 'T2_US_UNL', 'T2_US_CIT'].sort())

        # Test one subset plus one site
        testWorkload.setSiteWildcardsLists(siteBlacklist = ['US*', 'T1_UK_RAL'],
                                           siteWhitelist = [],
                                           wildcardDict = wildcardSites)
        self.assertEqual(testWorkload.data.tasks.ProcessingTask.constraints.sites.blacklist.sort(),
                         ['T1_US_FNAL', 'T2_US_UCSD', 'T2_US_UNL', 'T2_US_CIT', 'T1_UK_RAL'].sort())


        # Test an invalid
        raises = False
        try:
            testWorkload.setSiteWildcardsLists(siteBlacklist = ['T3*'],
                                               siteWhitelist = [],
                                               wildcardDict = wildcardSites)
        except WMWorkloadException, ex:
            raises = True
            self.assertTrue("Invalid wildcard site T3* in site blacklist!" in str(ex))
            pass
        self.assertTrue(raises)
        return

    def test_getCMSSWVersion(self):
        """
        _getCMSSWVersion_

        Test our ability to pull out the CMSSW Version from a workload
        """
        testWorkload = WMWorkloadHelper(WMWorkload("TestWorkload"))
        procTask = testWorkload.newTask("ProcessingTask")
        procTask.setSplittingAlgorithm("FileBased", files_per_job = 1)
        procTask.setTaskType("Processing")
        procTaskCmssw = procTask.makeStep("cmsRun1")
        procTaskCmssw.setStepType("CMSSW")
        procTask.applyTemplates()

        testWorkload.setCMSSWParams(cmsswVersion = "CMSSW_1_1_1", globalTag =
                                    "GLOBALTAG", scramArch = "SomeSCRAMArch")

        self.assertEqual(testWorkload.getCMSSWVersions(), ["CMSSW_1_1_1"])
        return
                         

if __name__ == '__main__':
    unittest.main()
