#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import contains_string

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
        index = None
        name = os.path.join(os.path.dirname(__file__), 'data/%s' % source)
        with open(name, "rb") as fp:
            source_doc = publish_doctree(fp.read())
        tex_dir = tempfile.mkdtemp(prefix="render_")
        try:
            render_document(source_doc,
                            outfile_dir=tex_dir,
                            jobname="sample")
            index = os.path.join(tex_dir, 'index.html')
            assert_that(os.path.exists(index), is_(True))
            with open(index, "r") as fp:
                index = fp.read()
        except Exception:
            print('Exception %s, %s' % (source, tex_dir))
            raise
        else:
            shutil.rmtree(tex_dir)
        return index

    def test_bullet_list(self):
        index = self._generate_from_file('bullet_list.rst')
        assert_that(index, 
                    contains_string('Bullet List Item 1</p> <ul class="itemize">'))
        assert_that(index, 
                    contains_string('Nested Bullet List Item 1-1</p> </li>'))
        assert_that(index, 
                    contains_string('Double Nested Bullet List Item 1-2-1</p> </li>'))
        assert_that(index, 
                    contains_string('Double Nested Bullet List Item 1-2-2</p> </li>'))
        assert_that(index,
                    contains_string('Nested Bullet List Item 1-3</p> </li> <li>'))
        assert_that(index, 
                    contains_string('Nested Bullet List Item 1-4</p> </li> </ul>'))
        assert_that(index, 
                    contains_string('Bullet List Item 2</p> <ul class="itemize">'))
        assert_that(index, 
                    contains_string('Nested Bullet List Item 2-1</p> </li>'))
        assert_that(index, 
                    contains_string('Nested Bullet List Item 2-2</p> </li>'))
        assert_that(index, 
                    contains_string('Nested Bullet List Item 2-3</p> </li>'))
        assert_that(index, 
                    contains_string('Bullet List Item 3</p> </li>'))
        assert_that(index, 
                    contains_string('Bullet List Item 4</p> </li>'))

    def test_ordered_list(self):
        index = self._generate_from_file('ordered_list.rst')
        assert_that(index, 
                    contains_string('Ordered List Item 1</p> <ol class="enumerate" start="1">'))
        assert_that(index,
                    contains_string('Nested Ordered List Item 1-1</p> </li>'))
        assert_that(index, 
                    contains_string('Nested Ordered List Item 1-2</p> <ol class="enumerate"'))
        assert_that(index, 
                    contains_string('Double Nested Ordered List Item 1-2-1</p> </li>'))
        assert_that(index, 
                    contains_string('Double Nested Ordered List Item 1-2-2</p> </li>'))
        assert_that(index, 
                    contains_string('Nested Ordered List Item 1-3</p> </li>'))
        assert_that(index, 
                    contains_string('Nested Ordered List Item 1-4</p> </li>'))

    def test_roles(self):
        index = self._generate_from_file('roles.rst')
        assert_that(index,
                    contains_string('<b class="bfseries"><em>ichigo</em></b> kurosaki</p>'))
        assert_that(index, 
                    contains_string('<span class="underline">aizen</span> sosuke</p>'))
        assert_that(index, 
                    contains_string('<b class="bfseries"><span class="underline">rukia</span></b> kuchiki</p>'))
        assert_that(index, 
                    contains_string('<em><span class="underline">Byakuya</span></em> kuchiki</p>'))
        assert_that(index, 
                    contains_string('<b class="bfseries"><em><span class="underline">Genryusai</span></em></b> Yamamoto</p>'))

    def test_uid(self):
        index = self._generate_from_file('uid.rst')
        assert_that(index, 
                    contains_string('id="exceptional" ntiid="t'))
        assert_that(index, 
                    contains_string('<p class="par" id="ichigo">Ichigo has been'))

    def test_fakesections(self):
        index = self._generate_from_file('fakesections.rst')
        assert_that(index, 
                    contains_string('<div class="subsection title" id="2">this is a fake subsection</div>'))
        assert_that(index, 
                    contains_string('<div class="chapter title">this is a fake section</div>'))
        assert_that(index, 
                    contains_string('<div class="chapter title">Another title</div>'))

    def test_label(self):
        index = self._generate_from_file('label.rst')
        assert_that(index, 
                    contains_string('id="material" ntiid="tag:nextthought.com,2011-10:NTI-HTML-sample.material">'))

    def test_links(self):
        index = self._generate_from_file('links.rst')
        assert_that(index, 
                    contains_string('like <a href="http://www.python.org/">Python</a>'))
        assert_that(index, 
                    contains_string('Click <a href="http://www.google.com">here</a></p>'))
        
    def test_meta(self):
        index = self._generate_from_file('meta.rst')
        assert_that(index, 
                    contains_string('<title>Bankai Ichigo</title>'))
        assert_that(index, 
                    contains_string('<div class="title">Bankai Ichigo</div>'))
        
    def test_formats(self):
        index = self._generate_from_file('formats.rst')
        assert_that(index, 
                    contains_string('<em><span class="underline">Examine the differences between the Democratic and Republican Parties</span></em><span class="underline">, the social impact of terrorist organizations, the growing suspicions over the reach of the federal government,</span> <b class="bfseries">and the subsequent end of Reconstruction.</b>'))
