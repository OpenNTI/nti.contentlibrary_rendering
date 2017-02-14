#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from docutils.core import publish_doctree


def get_rst_dom(source):
    rst_dom = publish_doctree(source=source)
    return rst_dom
