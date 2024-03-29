#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.intid.interfaces import IIntIds

from nti.contentlibrary.utils import NTI

from nti.contentlibrary_rendering.common import mkdtemp

from nti.contentlibrary_rendering.interfaces import IContentTransformer

from nti.contentrendering.nti_render import process_document

from nti.contentrendering.render_document import parse_tex

logger = __import__('logging').getLogger(__name__)


class TransformerMixin(object):

    @Lazy
    def _intids(self):
        return component.getUtility(IIntIds)

    def _get_id(self, context):
        # pylint: disable=no-member
        return str(self._intids.getId(context))

    def _out_file(self, context):
        return self._get_id(context) + ".tex"


@interface.implementer(IContentTransformer)
class LaTeXTransformer(TransformerMixin):

    @classmethod
    def render_latex(cls, source, out_dir):
        document, _, jobname, _ = parse_tex(source,
                                            outdir=out_dir,
                                            provider=NTI)
        return process_document(document, jobname=jobname)

    def write_out(self, content, latex_file):
        with open(latex_file, "wb") as fp:
            fp.write(content)

    def transform(self, content, context):
        out_dir = mkdtemp()
        latex_file = os.path.join(out_dir, self._out_file(context))
        try:
            self.write_out(content, latex_file)
            return self.render_latex(latex_file, out_dir)
        finally:
            os.remove(latex_file)


@interface.implementer(IContentTransformer)
class TextTransformer(LaTeXTransformer):

    def write_out(self, content, latex_file):
        with open(latex_file, "w") as fp:
            fp.write("\\documentclass{book}\n")
            fp.write("%%% Body\n")
            fp.write("\\begin{document}\n")
            fp.write(content)
            fp.write("\n\\end{document}\n")
