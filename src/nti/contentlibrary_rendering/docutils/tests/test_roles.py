#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

from nti.testing.matchers import validly_provides

from docutils.parsers.rst import languages

from nti.contentlibrary_rendering.docutils.interfaces import IRolesModule

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestRoles(ContentlibraryRenderingLayerTest):

    def test_roles(self):
        from nti.contentlibrary_rendering.docutils import roles
        assert_that(roles, validly_provides(IRolesModule)) 
        assert_that(languages.en.roles['underlined'], is_not(none()))
        assert_that(languages.en.roles['bolditalic'], is_not(none()))
        assert_that(languages.en.roles['boldunderlined'], is_not(none()))
        assert_that(languages.en.roles['italicunderlined'], is_not(none()))
        assert_that(languages.en.roles['bolditalicunderlined'], is_not(none()))
