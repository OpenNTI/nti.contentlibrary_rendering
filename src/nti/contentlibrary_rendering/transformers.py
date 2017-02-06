#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import tempfile

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIds

from nti.contentlibrary_rendering.interfaces import IContentTransformer

from nti.property.property import Lazy


class TransformerMixin(object):

    @Lazy
    def _intids(self):
        return component.getUtility(IIntIds)

    def _get_id(self, context):
        return str(self._intids.getId(context))

    def _out_file(self, context):
        return self._get_id(context) + ".tex"


@interface.implementer(IContentTransformer)
class TextTransformer(TransformerMixin):

    def transform(self, content, context, out_dir=None):
        out_dir = out_dir or tempfile.mkdtemp()
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        latex_file = os.path.join(out_dir, self._out_file(context))
        with open(latex_file, "wb") as fp:
            fp.write("\\documentclass{book}\n")
            fp.write("%%% Body\n")
            fp.write("\\begin{document}\n")
            fp.write(content)
            fp.write("\n\\end{document}\n")
        return latex_file
