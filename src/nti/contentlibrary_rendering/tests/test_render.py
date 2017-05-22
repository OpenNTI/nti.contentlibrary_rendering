#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import os
import shutil
import tempfile

from nti.contentlibrary.filesystem import FilesystemBucket

from nti.contentlibrary.zodb import RenderableContentPackage

from nti.contentlibrary_rendering._render import copy_package_data

from nti.contentrendering.nti_render import process_document

from nti.contentrendering.render_document import parse_tex


from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestRender(ContentlibraryRenderingLayerTest):

    def _parse_sample(self, tmp_dir):
        source = os.path.join(os.path.dirname(__file__), 'sample.tex')
        document, _, jobname, _ = parse_tex(source,
                                            provider=u'NTI',
                                            outdir=tmp_dir,
                                            load_configs=False)
        return process_document(document, jobname=jobname)

    def test_render_copy(self):
        cwd = os.getcwd()
        tmp_dir = tempfile.mkdtemp()
        try:
            # render
            os.chdir(tmp_dir)
            document = self._parse_sample(tmp_dir)
            assert_that(document, is_not(none()))
            # copy to target data
            bucket = FilesystemBucket(name="sample")
            bucket.absolute_path = tmp_dir
            target = RenderableContentPackage()
            target.ntiid = u'tag:nextthought.com,2011-10:NTI-HTML-sample.0'
            copy_package_data(bucket, target)
            # check
            assert_that(target,
                        has_property('ntiid', 'tag:nextthought.com,2011-10:NTI-HTML-sample.0'))
            assert_that(target,
                        has_property('children', has_length(1)))
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp_dir, True)
