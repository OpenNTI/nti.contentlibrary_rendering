#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904


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

    def test_sectioning_directive(self):
        from nti.contentlibrary_rendering.docutils.directives import pseudo_types
        assert_that(pseudo_types, validly_provides(IDirectivesModule))
        assert_that(docutils_directive('fakesection', None, None), is_(not_none()))
        assert_that(docutils_directive('fakeparagraph', None, None), is_(not_none()))
        assert_that(docutils_directive('fakesubsection', None, None), is_(not_none()))
        assert_that(docutils_directive('fakesubsubsection', None, None), is_(not_none()))
