#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.contentlibrary.zodb import RenderableContentPackage

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestAdapter(ContentlibraryRenderingLayerTest):

    def test_adapter(self):
        pkg = RenderableContentPackage()
        pkg.ntiid = u'tag:nextthought.com,2011-10:USSC-HTML-Cohen.cohen_v._california.'
        meta = IContentPackageRenderMetadata(pkg, None)
        assert_that(meta, is_not(none()))
        assert_that(meta, validly_provides(IContentPackageRenderMetadata))
        assert_that(meta, verifiably_provides(IContentPackageRenderMetadata))