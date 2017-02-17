#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import has_property

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import os
import shutil
import tempfile

from zope import component

from nti.contentlibrary_rendering._render import render_document

from nti.contentlibrary_rendering.docutils import publish_doctree

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestTranslators(ContentlibraryRenderingLayerTest):

    def test_registered(self):
        translators = component.getUtilitiesFor(IRSTToPlastexNodeTranslator)
        translators = list(translators)
        for name, translator in translators:
            assert_that(translator,
                        has_property('__name__', is_(name)))
            assert_that(translator,
                        validly_provides(IRSTToPlastexNodeTranslator))
            assert_that(translator,
                        verifiably_provides(IRSTToPlastexNodeTranslator))

    def _generate_from_file(self, source):
        name = os.path.join(os.path.dirname(__file__), 'data/%s' % source)
        with open(name, "rb") as fp:
            source_doc = publish_doctree(fp.read())
        tex_dir =  tempfile.mkdtemp(prefix="render_")
        print(tex_dir)
        try:
            document = render_document(source_doc, 
                                       outfile_dir=tex_dir, 
                                       jobname="sample")
            index = os.path.join(tex_dir, 'index.html')
            assert_that(os.path.exists(index), is_(True))
        except Exception:
            print('Exception %s, %s' % (source, tex_dir))
            raise
        else:
            shutil.rmtree(tex_dir)
        return document

    def xtest_basic(self):
        self._generate_from_file('basic.rst')
        
    def test_bullet_list(self):
        self._generate_from_file('bullet_list.rst')

    def test_ordered_list(self):
        self._generate_from_file('ordered_list.rst')

    def test_roles(self):
        self._generate_from_file('roles.rst')

