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

from nti.contentrendering.nti_render import process_document

from nti.contentrendering.render_document import parse_tex

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
class LaTeXTransformer(TransformerMixin):

    @classmethod
    def render_latex(cls, source, out_dir):
        document, _, jobname, _ = parse_tex(source,
                                            outdir=out_dir,
                                            provider='NTI')
        return process_document(document, jobname=jobname)

    def write_out(self, content, latex_file):
        with open(latex_file, "wb") as fp:
            fp.write(content)

    def transform(self, content, context):
        out_dir = tempfile.mkdtemp()
        latex_file = os.path.join(out_dir, self._out_file(context))
        try:
            self.write_out(content, latex_file)
            return self.render_latex(latex_file, out_dir)
        finally:
            os.remove(latex_file)


@interface.implementer(IContentTransformer)
class TextTransformer(LaTeXTransformer):

    def write_out(self, content, latex_file):
        with open(latex_file, "wb") as fp:
            fp.write(b"\\documentclass{book}\n")
            fp.write(b"%%% Body\n")
            fp.write(b"\\begin{document}\n")
            fp.write(content)
            fp.write(b"\n\\end{document}\n")
