#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPlastexDocumentGenerator)
class _IdDocumentGenerator(object):

    def generate(self, document, unused_tex_doc=None, unused_context=None):
        return document
