#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import not_none
from hamcrest import assert_that

from nti.testing.matchers import validly_provides

from docutils.parsers.rst.directives import directive as docutils_directive

from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestDirectives(ContentlibraryRenderingLayerTest):

    def test_uid_directive(self):
        from nti.contentlibrary_rendering.docutils.directives import uid
        assert_that(uid, validly_provides(IDirectivesModule))
        assert_that(docutils_directive('uid', None, None), is_(not_none()))

    def test_pseudo_types_directives(self):
        from nti.contentlibrary_rendering.docutils.directives import sectioning
        assert_that(sectioning, validly_provides(IDirectivesModule))
        assert_that(docutils_directive('fakesection', None, None), 
                    is_(not_none()))
        assert_that(docutils_directive('fakeparagraph', None, None), 
                    is_(not_none()))
        assert_that(docutils_directive('fakesubsection', None, None), 
                    is_(not_none()))
        assert_that(docutils_directive('fakesubsubsection', None, None), 
                    is_(not_none()))

    def test_label_directive(self):
        from nti.contentlibrary_rendering.docutils.directives import label
        assert_that(label, validly_provides(IDirectivesModule))
        assert_that(docutils_directive('label', None, None), is_(not_none()))
        
    def test_meta_directive(self):
        from nti.contentlibrary_rendering.docutils.directives import meta
        assert_that(meta, validly_provides(IDirectivesModule))
        assert_that(docutils_directive('meta', None, None), is_(not_none()))

    def test_embedwidget_directive(self):
        from nti.contentlibrary_rendering.docutils.directives import embedwidget
        assert_that(embedwidget, validly_provides(IDirectivesModule))
        assert_that(docutils_directive('embedwidget', None, None), is_(not_none()))
