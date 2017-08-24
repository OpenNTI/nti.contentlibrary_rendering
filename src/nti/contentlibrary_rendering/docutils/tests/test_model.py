#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904


from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries

import os

from nti.contentlibrary.zodb import RenderableContentPackage

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest

from nti.externalization.externalization import to_external_object


class TestModel(ContentlibraryRenderingLayerTest):

    def _get_data(self, source):
        name = os.path.join(os.path.dirname(__file__), 'data/%s' % source)
        with open(name, "rb") as fp:
            return fp.read()

    def test_renderable_io(self):
        package = RenderableContentPackage()
        package.ntiid = u'tag:nextthought.com,2011-10:NTI-HTML-human_physiology'
        package.title = u'Human Physiology'
        package.description = u'Human Physiology'
        package.contentType = b'text/x-rst'
        package.contents = self._get_data("label.rst")
        ext_obj = to_external_object(package, name='exporter')
        assert_that(ext_obj,
                    has_entries('isPublished', is_(False),
                                'MimeType', 'application/vnd.nextthought.renderablecontentpackage',
                                'NTIID', 'tag:nextthought.com,2011-10:NTI-HTML-human_physiology',
                                'title', is_('Human Physiology'),
                                'contents', has_length(200)))
