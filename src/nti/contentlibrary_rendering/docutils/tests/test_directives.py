#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904


from hamcrest import assert_that

from nti.testing.matchers import validly_provides

from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestDirectives(ContentlibraryRenderingLayerTest):

    def test_directives(self):
        from nti.contentlibrary_rendering.docutils import directives
        assert_that(directives, validly_provides(IDirectivesModule))
