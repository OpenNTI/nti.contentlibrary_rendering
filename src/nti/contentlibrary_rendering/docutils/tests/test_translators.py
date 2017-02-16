#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import os

from zope import component

from nti.contentlibrary_rendering.docutils import publish_doctree

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentlibrary_rendering.docutils.translators import PlastexDocumentGenerator

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestTranslators(ContentlibraryRenderingLayerTest):

    def test_registered(self):
        translators = component.getUtilitiesFor(IRSTToPlastexNodeTranslator)
        translators = list(translators)
        assert_that(translators, has_length(11))
        for _, translator in translators:
            assert_that(translator,
                        validly_provides(IRSTToPlastexNodeTranslator))
            assert_that(translator,
                        verifiably_provides(IRSTToPlastexNodeTranslator))

    def test_bullet_list(self):
        name = os.path.join(os.path.dirname(__file__),
                            'data/bullet_list.rst')
        with open(name, "rb") as fp:
            source = fp.read()
        tree = publish_doctree(source)
        assert_that(tree, has_property('children', has_length(1)))
        generator = PlastexDocumentGenerator()
        from IPython.core.debugger import Tracer; Tracer()()
        generator.generate(tree)
