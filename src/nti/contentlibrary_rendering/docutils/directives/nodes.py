#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from docutils.nodes import Element
from docutils.nodes import General

logger = __import__('logging').getLogger(__name__)


class meta(General, Element):
    pass


class label(General, Element):
    pass


class fakesection(General, Element):
    pass


class fakeparagraph(General, Element):
    pass


class fakesubsection(General, Element):
    pass


class fakesubsubsection(General, Element):
    pass


class embedwidget(General, Element):
    pass
