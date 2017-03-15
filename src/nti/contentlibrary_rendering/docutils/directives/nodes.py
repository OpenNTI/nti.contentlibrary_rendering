#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from docutils.nodes import Element
from docutils.nodes import General


class fakesection(General, Element):
    pass


class fakeparagraph(General, Element):
    pass


class fakesubsection(General, Element):
    pass


class fakesubsubsection(General, Element):
    pass
