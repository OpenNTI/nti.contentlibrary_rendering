#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.proxy import ProxyBase

logger = __import__('logging').getLogger(__name__)


class DocumentProxy(ProxyBase):

    def __new__(cls, *args, **unused_kwds):
        return super(DocumentProxy, cls).__new__(cls, *args)

    def __init__(self, *args, **kwds):
        context = kwds.pop('context', None)
        super(DocumentProxy, self).__init__(*args, **kwds)
        self._v_skip = False
        self._v_store = list()
        self._v_context = context
        self._v_media_counter = 0
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

    # context

    def px_context(self):
        return self._v_context

    # store

    def px_store(self):
        return self._v_store

    def px_push(self, data):
        self._v_store.append(data)

    def px_clear(self):
        self._v_store = list()

    # skip

    def px_skipping(self):
        return self._v_skip

    def px_toggle_skip(self):
        self._v_skip = not self._v_skip

    # par

    def px_inc_paragraph_counter(self):
        self._v_paragraph_counter += 1
        return self._v_paragraph_counter

    # media

    def px_inc_media_counter(self):
        self._v_media_counter += 1
        return self._v_media_counter


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
    def test(arg): return isinstance(arg, clazz)
    for location in rst_lineage(resource):
        if test(location):
            return location


def rst_find_all_interface(resource, clazz):
    def test(arg): return isinstance(arg, clazz)
    for location in rst_lineage(resource):
        if test(location):
            yield location
