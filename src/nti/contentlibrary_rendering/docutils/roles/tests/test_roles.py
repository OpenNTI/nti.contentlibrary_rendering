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

from docutils.parsers.rst import languages

from nti.contentlibrary_rendering.docutils.interfaces import IRolesModule

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestRoles(ContentlibraryRenderingLayerTest):

    def test_formatting_roles(self):
        from nti.contentlibrary_rendering.docutils.roles import formatting
        assert_that(formatting, validly_provides(IRolesModule)) 
        assert_that(languages.en.roles['underlined'], is_not(none()))
        assert_that(languages.en.roles['bolditalic'], is_not(none()))
        assert_that(languages.en.roles['boldunderlined'], is_not(none()))
        assert_that(languages.en.roles['italicunderlined'], is_not(none()))
        assert_that(languages.en.roles['bolditalicunderlined'], is_not(none()))
