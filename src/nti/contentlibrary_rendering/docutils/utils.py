#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.proxy import ProxyBase


class DocumentProxy(ProxyBase):

    def __new__(cls, *args, **kwds):
        return super(DocumentProxy, cls).__new__(cls, *args, **kwds)

    def __init__(self, *args, **kwds):
        super(DocumentProxy, self).__init__(*args, **kwds)
        self._v_paragraph_counter = 0
            
    def __getattr__(self, name):
        if name.startswith('_v'):
            return self.__dict__[name]
        return ProxyBase.__getattr__(self, name)

    def __setattr__(self, name, value):
        if name.startswith('_v'):
            self.__dict__[name] = value
        else:
            return ProxyBase.__setattr__(self, name, value)

    def _inc_paragraph_counter(self):
        self._v_paragraph_counter += 1
        return self._v_paragraph_counter


def rst_traversal_count(rst_node, tagname):
    """
    Traverse the RST tree, returning a count of how many elements
    are found for tagname.
    """
    count = 0
    parent = rst_node.parent
    while parent is not None:
        if parent.tagname == tagname:
            count += 1
        parent = parent.parent
    return count


def rst_lineage(resource):
    while resource is not None:
        yield resource
        try:
            resource = resource.parent
        except AttributeError:
            resource = None


def rst_find_interface(resource, clazz):
    test = lambda arg: isinstance(arg, clazz)
    for location in rst_lineage(resource):
        if test(location):
            return location


def rst_find_all_interface(resource, clazz):
    test = lambda arg: isinstance(arg, clazz)
    for location in rst_lineage(resource):
        if test(location):
            yield location
