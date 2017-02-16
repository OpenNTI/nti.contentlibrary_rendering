#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import os

from zope import component

from nti.contentlibrary_rendering.docutils import get_translator

from nti.contentlibrary_rendering.docutils import publish_doctree

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentlibrary_rendering.docutils.translators import PlastexDocumentGenerator

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestTranslators(ContentlibraryRenderingLayerTest):

    def test_registered(self):
        translators = list(component.getUtilitiesFor(IRSTToPlastexNodeTranslator))
        assert_that(translators, has_length(11))

    def test_bullet_list(self):
        name = os.path.join(os.path.dirname(__file__), 
                            'data/bullet_list.rst')
        with open(name, "rb") as fp:
            source = fp.read()
        tree = publish_doctree(source)
        assert_that(tree, has_property('children', has_length(1)))
        translator = get_translator("bullet_list")
        translator.translate(tree[0], 
                             PlastexDocumentGenerator.create_document())
