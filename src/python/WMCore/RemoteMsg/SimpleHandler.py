#!/usr/bin/env python

"""
_SimpleHandler_

This module contains a class that is an example of handler for incoming
remote messages. It could be mapped to a msgType using the
'RemoteMsg.setHandler' method.
"""





import time

class SimpleHandler(object):
    """ 
    _SimpleHandler_
    """
    def __init__(self, params = None):
        pass

     # this we overload from the base handler
    def __call__(self, msgType, payload):
        """
        Handles the msg with payload
        """
        print "\nSimpleHandler acting on message: %s" % (time.ctime())
        # Simulate that it takes some time...
        time.sleep(2)
        print "\nSimpleHandler received: msgType: %s" % (msgType)
        print "                payload: "+payload
        print "Ended: SimpleHandler at %s" % (time.ctime())
 
        result = ['This is an example of what can be returned', \
                   0, {'dict': 'also'}]
        return result
