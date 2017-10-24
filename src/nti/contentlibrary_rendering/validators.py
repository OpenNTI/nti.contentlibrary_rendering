#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.contentlibrary.interfaces import IContentValidator

from nti.contentlibrary.validators import EmptyContentError

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IContentValidator)
class TextValidator(object):

    def _do_validate(self, content):
        if not content:
            raise EmptyContentError()

    def validate(self, content=b'', unused_context=None):
        self._do_validate(content)
