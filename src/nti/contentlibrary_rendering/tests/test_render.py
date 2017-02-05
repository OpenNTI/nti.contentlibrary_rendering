#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import shutil
import tempfile

from nti.contentlibrary_rendering._render import render_latex

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestRender(ContentlibraryRenderingLayerTest):

    def _render_sample(self, tmp_dir):
        source = os.path.join(os.path.dirname(__file__), 'sample.tex')
        sample_tex = os.path.join(tmp_dir, "sample.tex")
        shutil.copy(source, sample_tex)
        return render_latex(sample_tex)

    def test_render(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            self._render_sample(tmp_dir)
        finally:
            shutil.rmtree(tmp_dir, True)
