#!/usr/bin/env python
"""
WorkQueue SplitPolicyInterface

"""
__all__ = []

import types

from WMCore.WorkQueue.Policy.PolicyInterface import PolicyInterface
from WMCore.WorkQueue.DataStructs.WorkQueueElement import WorkQueueElement
#from WMCore.WorkQueue.DataStructs.CouchWorkQueueElement import CouchWorkQueueElement as WorkQueueElement
from WMCore.WMException import WMException
from WMCore.WorkQueue.WorkQueueExceptions import WorkQueueWMSpecError, WorkQueueNoWorkError
from DBSAPI.dbsApiException import DbsConfigurationError
from WMCore.Services.DBS.DBSErrors import DBSReaderError
from WMCore import Lexicon

class StartPolicyInterface(PolicyInterface):
    """Interface for start policies"""
    def __init__(self, **args):
        PolicyInterface.__init__(self, **args)
        self.workQueueElements = []
        self.wmspec = None
        self.team = None
        self.initialTask = None
        self.splitParams = None
        self.dbs_pool = {}
        self.data = {}
        self.lumi = None
        self.couchdb = None

    def split(self):
        """Apply policy to spec"""
        raise NotImplementedError

    def validate(self):
        """Check params and spec are appropriate for the policy"""
        raise NotImplementedError

    def validateCommon(self):
        """Common validation stuff"""
        try:
            Lexicon.requestName(self.wmspec.name())
        except Exception, ex: # can throw many errors e.g. AttributeError, AssertionError etc.
            error = WorkQueueWMSpecError(self.wmspec, "Workflow name validation error: %s" % str(ex))
            raise error

        if self.initialTask.siteWhitelist():
            if type(self.initialTask.siteWhitelist()) in types.StringTypes:
                error = WorkQueueWMSpecError(self.wmspec, 'Invalid site whitelist: Must be tuple/list but is %s' % type(self.initialTask.siteWhitelist()))
                raise error
            try:
                [Lexicon.cmsname(site) for site in self.initialTask.siteWhitelist()]
            except Exception, ex: # can throw many errors e.g. AttributeError, AssertionError etc.
                error = WorkQueueWMSpecError(self.wmspec, "Site whitelist validation error: %s" % str(ex))
                raise error

        if self.initialTask.siteBlacklist():
            if type(self.initialTask.siteBlacklist()) in types.StringTypes:
                error = WorkQueueWMSpecError(self.wmspec, 'Invalid site blacklist: Must be tuple/list but is %s' % type(self.initialTask.siteBlacklist()))
                raise error
            try:
                [Lexicon.cmsname(site) for site in self.initialTask.siteBlacklist()]
            except Exception, ex: # can throw many errors e.g. AttributeError, AssertionError etc.
                error = WorkQueueWMSpecError(self.wmspec, "Site blacklist validation error: %s" % str(ex))
                raise error

        # check input dataset is valid
        try:
            if self.initialTask.getInputDatasetPath():
                Lexicon.dataset(self.initialTask.getInputDatasetPath())
        except Exception, ex: # can throw many errors e.g. AttributeError, AssertionError etc.
            error = WorkQueueWMSpecError(self.wmspec, "Dataset validation error: %s" % str(ex))
            raise error

    def newQueueElement(self, **args):
        args.setdefault('Status', 'Available')
        args.setdefault('WMSpec', self.wmspec)
        args.setdefault('Task', self.initialTask)
        args.setdefault('RequestName', self.wmspec.name())
        args.setdefault('TaskName', self.initialTask.name())
        args.setdefault('Dbs', self.initialTask.dbsUrl())
        args.setdefault('SiteWhitelist', self.initialTask.siteWhitelist())
        args.setdefault('SiteBlacklist', self.initialTask.siteBlacklist())
        args.setdefault('EndPolicy', self.wmspec.endPolicyParameters())
        args.setdefault('Priority', self.wmspec.priority())
        if not args['Priority']:
            args['Priority'] = 0
        ele = WorkQueueElement(**args)
        if not ele['Jobs']:
            raise WorkQueueWMSpecError(self.wmspec, 'No work in element: "%s"' % ele)
        for data, sites in ele['Inputs'].items():
            if not sites:
                raise WorkQueueWMSpecError(self.wmspec, 'Input data has no locations "%s"' % data)
        self.workQueueElements.append(ele)

    def __call__(self, wmspec, task, data = None, mask = None, team = None):
        self.wmspec = wmspec
        self.splitParams = self.wmspec.data.policies.start
        self.initialTask = task
        if data:
            self.data = data
        self.mask = mask
        self.validate()
        try:
            self.split()
        # For known exceptions raise custom error that will fail the workflow.
        except DbsConfigurationError, ex:
            # A dbs configuration error implies the spec is invalid
            error = WorkQueueWMSpecError(self.wmspec, "DBS config error: %s" % str(ex))
            raise error
        except AssertionError, ex:
            # Assertion generally means validation of an input field failed
            error = WorkQueueWMSpecError(self.wmspec, "Assertion error: %s" % str(ex))
            raise error
        except DBSReaderError, ex:
            # Hacky way of identifying non-existant data, DbsBadRequest chomped by DBSReader
            # DbsConnectionError: Database exception,Invalid parameters thrown by Summary api
            if 'DbsBadRequest' in str(ex) or 'Invalid parameters' in str(ex):
                data = task.data.input.pythonise_() if task.data.input else 'None'
                msg = """data: %s: mask %s. %s""" % (str(data), str(mask), str(ex))
                error = WorkQueueNoWorkError(self.wmspec, msg)
                raise error
            raise # propagate other dbs errors

        # if we have no elements then there was no work in the spec, fail it
        if not self.workQueueElements:
            data = task.data.input.pythonise_() if task.data.input else 'None'
            msg = """data: %s, mask: %s.""" % (str(data), str(mask))
            error = WorkQueueNoWorkError(self.wmspec, msg)
            raise error
        return self.workQueueElements

    def dbs(self):
        """Get DBSReader"""
        from WMCore.WorkQueue.WorkQueueUtils import get_dbs
        dbs_url = self.initialTask.dbsUrl()
        return get_dbs(dbs_url)
