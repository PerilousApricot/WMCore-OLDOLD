#!/usr/bin/env python
"""
_FileAndEventBased_

Event based splitting algorithm that will chop a fileset into
a set of jobs based on event counts.  Each jobgroup returned will only
contain jobs for a single file.
"""

__revision__ = "$Id: FileAndEventBased.py,v 1.9 2009/07/22 16:24:54 sfoulkes Exp $"
__version__  = "$Revision: 1.9 $"

from sets import Set

from WMCore.JobSplitting.JobFactory import JobFactory
from WMCore.Services.UUID import makeUUID

class FileAndEventBased(JobFactory):
    """
    Split jobs by number of events
    """
    def algorithm(self, groupInstance = None, jobInstance = None, *args,
                  **kwargs):
        """
        _algorithm_

        An event base splitting algorithm.  All available files are split into a
        set number of events per job.  
        """
        jobGroups = []
        fileset = self.subscription.availableFiles()

        #  //
        # // get the event total
        #//
        eventsPerJob = kwargs.get("events_per_job", 5000)
        try:
            selectionAlgorithm = kwargs['selection_algorithm']
        except KeyError, e:
            selectionAlgorithm = None
        carryOver = 0

        for f in fileset:
            if selectionAlgorithm:
                if not selectionAlgorithm( f ):
                    self.subscription.completeFiles( [ f ] )
                    continue
            jobGroup = groupInstance(subscription = self.subscription)
            jobGroups.append(jobGroup)
            eventsInFile = int(f["events"])

            if eventsInFile == 0:
                currentJob = jobInstance(name = makeUUID())
                self.subscription.acquireFiles(f)
                currentJob.addFile(f)
                currentJob["mask"].setMaxAndSkipEvents(eventsPerJob, 0)                
                jobGroup.add(currentJob)
                jobGroup.commit()
                continue

            currentEvent = 0
            while currentEvent < eventsInFile:
                currentJob = jobInstance(name = makeUUID())
                currentJob.addFile(f)
                currentJob["mask"].setMaxAndSkipEvents(eventsPerJob, currentEvent)
                jobGroup.add(currentJob)
                currentEvent += eventsPerJob
                
            self.subscriptions.acquireFiles(f)
            jobGroup.commit()

        return jobGroups
