#! /usr/bin/env python

"""
_MiscAlgos_

Useful little tools that can be handy anywhere.
"""
import logging

def sortListByKey(input, key):
    """
    Return list of dictionaries as a
    dictionary of lists of dictionaries
    keyed by one original key

    """
    final = {}

    for entry in input:
        value = entry.get(key, None)
        if value == None:
            # Empty dict value?
            # This is an error, but we can't handle it here
            logging.error("Found entry with no key in sortListByKey: %s" % entry)
            logging.error("Skipping")
            continue
        if type(value) == set:
            try:
                v     = value
                value = v.pop()
                v.add(value)
            except KeyError:
                # Set was empty?
                # This is peculiar, we can't handle this.
                logging.error("Found list entry with empty key set in sortListByKey: %s" % entry)
                logging.error("Skipping")
                continue
        if not value in final.keys():
            final[value] = []
        final[value].append(entry)

    return final



## {{{ http://code.activestate.com/recipes/576644/ (r1)
def dict_diff(first, second):
    """ Return a dict of keys that differ with another config object.  If a value is
        not found in one fo the configs, it will be represented by KEYNOTFOUND.
        @param first:   Fist dictionary to diff.
        @param second:  Second dicationary to diff.
        @return diff:   Dict of Key => (first.val, second.val)
    """
    KEYNOTFOUND = '<KEYNOTFOUND>'
    diff = {}
    # Check all keys in first dict
    for key in first.keys():
        if (not second.has_key(key)):
            diff[key] = (first[key], KEYNOTFOUND)
        elif (first[key] != second[key]):
            diff[key] = (first[key], second[key])
    # Check all keys in second dict to find missing
    for key in second.keys():
        if (not first.has_key(key)):
            diff[key] = (KEYNOTFOUND, second[key])
    return diff
## end of http://code.activestate.com/recipes/576644/ }}}
