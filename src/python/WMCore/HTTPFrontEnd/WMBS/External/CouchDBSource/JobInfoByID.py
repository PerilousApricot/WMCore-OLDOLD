"""
JobInfoByID

Retrieve information about a job from couch and format it nicely.
"""

import sys
import datetime
import os

from WMCore.HTTPFrontEnd.WMBS.External.CouchDBSource.CouchDBConnectionBase \
    import CouchDBConnectionBase

def getJobInfo(jobID):
    """
    _getJobInfo_

    Retrieve all the job metadata out of couch.
    """
    jobID = int(jobID)
    changeStateDB = CouchDBConnectionBase.getCouchDB()

    jobDoc = {}
    fwjrDocs = {}
    transitionDocs = {}
    options = {"startkey": jobID, "endkey": jobID}
    result = changeStateDB.loadView("JobDump",
                                    "stateTransitionsByJobID",
                                    options)

    for row in result["rows"]:
        if not transitionDocs.has_key(row["value"]["timestamp"]):
            transitionDocs[row["value"]["timestamp"]] = []

        transitionDocs[row["value"]["timestamp"]].append(row["value"])

    options = {"startkey": jobID, "endkey": jobID, "include_docs": True}
    fwjrDocsResult = changeStateDB.loadView("JobDump", "fwjrsByJobID", options)
    jobDocResult = changeStateDB.loadView("JobDump", "jobsByJobID", options)

    if len(jobDocResult["rows"]) == 0:
        print "Unknown job: %s" % jobID
        sys.exit(1)
    elif len(jobDocResult["rows"]) > 1:
        print "Multiple entries for this job: %s" % jobID
        sys.exit(1)

    jobDoc = jobDocResult["rows"][0]["doc"]

    for row in fwjrDocsResult["rows"]:
        fwjrDocs[row["doc"]["retrycount"]] = row["doc"]["fwjr"]

    return {'jobDoc' : jobDoc}

#def printJobInfo():
#    """
#    _printJobInfo_
#
#    Print the job name, mask and primary/secondary input files.
#    """
#    print "\nName: %s" % jobDoc["name"]
#    print "Owner: %s" % jobDoc["owner"]
#    print "Workflow: %s" % jobDoc["workflow"]
#    print "Task: %s" % jobDoc["task"]
#
#    print "\nMask:"
#    print "  First Event: %s" % jobDoc["mask"]["firstevent"]
#    print "  Last Event: %s" % jobDoc["mask"]["lastevent"]
#    print "  First Lumi: %s" % jobDoc["mask"]["firstlumi"]
#    print "  Last Lumi: %s" % jobDoc["mask"]["lastlumi"]
#    print "  First Run: %s" % jobDoc["mask"]["firstrun"]
#    print "  Last Run: %s" % jobDoc["mask"]["lastrun"]
#
#    print "\nInput Files"
#    for inputFile in jobDoc["inputfiles"]:
#        print "  %s" % inputFile["lfn"]
#
#        for inputFileParent in inputFile["parents"]:
#            print "    %s" % inputFileParent["lfn"]
#
#def printTransitionInfo():
#    """
#    _printTransitionInfo_
#
#    Print the state transition information and use it to determine how many
#    times the job was retried and it's outcome.
#    """
#    timestamps = transitionDocs.keys()
#    timestamps.sort()
#
#    print "\nState transitions:"
#
#    retryCount = 0
#    successSeen = False
#    exhaustedSeen = False
#    for timestamp in timestamps:
#        timestampDate = datetime.datetime.fromtimestamp(timestamp)
#        for transition in transitionDocs[timestamp]:
#            if transition["newstate"] == "executing":
#                retryCount += 1
#            elif transition["newstate"] == "success":
#                successSeen = True
#            elif transition["newstate"] == "exhausted":
#                exhaustedSeen = True
#
#            if transition["location"] == "Agent":
#                print "  %s %s -> %s" % (timestampDate.isoformat(" "),
#                                         transition["oldstate"],
#                                         transition["newstate"])
#            else:
#                print "  %s %s -> %s (%s)" % (timestampDate.isoformat(" "),
#                                              transition["oldstate"],
#                                              transition["newstate"],
#                                              transition["location"])
#
#    print "\nRetries: %s" % (retryCount - 1)
#
#    if successSeen:
#        print "\nOutcome: Success"
#    elif exhaustedSeen:
#        print "\nOutcome: Failure"
#    else:
#        print "\nOutcome: Unknown, still running."
#
#    return
#
#def printFWJRInfo():
#    """
#    _printFWJRInfo_
#
#    Search the FWJRs for error and logarchive information, print anything that
#    is found.
#    """
#    logArchiveLFNs = {}
#
#    for retryNumber in fwjrDocs.keys():
#        for stepName in fwjrDocs[retryNumber]["steps"].keys():
#            if fwjrDocs[retryNumber]["steps"][stepName]["status"] != 0:
#                print ""
#                print "Rerty %s, step %s failed:" % (retryNumber, stepName)
#
#                for error in fwjrDocs[retryNumber]["steps"][stepName]["errors"]:
#                    print "  Type: %s" % error["type"]
#                    print "  Details: %s" % error["details"]
#                    print "  Exit Code: %s" % error["exitCode"]
#            if stepName == "logArch1":
#                logArchStep = fwjrDocs[retryNumber]["steps"][stepName]
#                if logArchStep["output"].has_key("logArchive"):
#                    if len(logArchStep["output"]["logArchive"]) > 0:
#                        logArchiveLFNs[retryNumber] = logArchStep["output"]["logArchive"][0]["lfn"]
#
#    logArchiveRetries = logArchiveLFNs.keys()
#    logArchiveRetries.sort()
#
#    if len(logArchiveRetries) > 0:
#        print "\nLog Archive LFNs:"
#
#        for logArchiveRetry in logArchiveRetries:
#            print "  %s -> %s" % (logArchiveRetry, logArchiveLFNs[logArchiveRetry])
#
#    return
#
#getJobInfo()
#
#printJobInfo()
#printTransitionInfo()
#printFWJRInfo()