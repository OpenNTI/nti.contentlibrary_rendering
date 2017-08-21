#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary_rendering.docutils import get_rst_dom

from nti.contentlibrary_rendering.interfaces import IContentTransformer

from nti.contentlibrary_rendering.transformers import TransformerMixin


@interface.implementer(IContentTransformer)
class RSTTransformer(TransformerMixin):
    """
    Transforms an RST textual source into an RST DOM.
    """

    def transform(self, content, unused_context):
        rst_dom = get_rst_dom(source=content)
        return rst_dom
