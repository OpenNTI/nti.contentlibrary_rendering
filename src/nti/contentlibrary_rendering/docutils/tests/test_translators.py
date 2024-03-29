#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import is_not
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

from nti.contentlibrary_rendering.docutils import get_rst_dom

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
            source_doc = get_rst_dom(fp.read())
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
                    contains_string('<ul class="itemize">'))
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
                    contains_string('Bullet List Item 2</p> <blockquote class="ntiblockquote"><ul class="itemize">'))
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
                    contains_string('Ordered List Item 1</p> <blockquote class="ntiblockquote"><ol class="enumerate" start="1">'))
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
                    contains_string('<span class="underline">Examine the differences between the Democratic and Republican Parties</span><em><span class="underline">, the social impact of terrorist organizations, the growing suspicions over the reach of the federal government,</span></em> <b class="bfseries"><span class="underline">and the subsequent end of Reconstruction.</span></b>'))

    def test_literal_block(self):
        index = self._generate_from_file('literal_block.rst')
        assert_that(index,
                    contains_string('<pre class="code python literal-block"><span class="keyword">def</span>'))
        assert_that(index,
                    contains_string('<span class="name function">my_function</span><span class="punctuation">():</span>'))
        assert_that(index,
                    contains_string('<span class="comment single"># and now for something completely different</span>'))

    def test_sidebar(self):
        index = self._generate_from_file('sidebar.rst')
        assert_that(index,
                    contains_string('<div class="sidebar-title">Genesis</div>'))
        assert_that(index,
                    contains_string('<div class="sidebar" data-ntiid="tag:nextthought.com,2011-10:NTI-HTML:NTISidebar-sample.sidebar.genesis'))
        assert_that(index,
                    contains_string('In the beginning God created'))

    def test_embed_widget(self):
        index = self._generate_from_file('embedwidget.rst')
        assert_that(index,
                    contains_string('<div class="title">EmbedWidget Test</div>'))
        assert_that(index,
                    contains_string('<param name="source" value="https://cdnapisec.kaltura.com/p/2401761/sp/240176100/embedIframeJs/uiconf_id/42593641/partner_id/2401761?iframeembed=true&amp;playerId=kaltura_player&amp;entry_id=0_4vwjecdg&amp;flashvars[streamerType]=auto&amp;flashvars[localizationCode]=en&amp;flashvars[leadWithHTML5]=true&amp;flashvars[sideBarContainer.plugin]=true&amp;flashvars[sideBarContainer.position]=left&amp;flashvars[sideBarContainer.clickToClose]=true&amp;flashvars[chapters.plugin]=true&amp;flashvars[chapters.layout]=vertical&amp;flashvars[chapters.thumbnailRotator]=false&amp;flashvars[streamSelector.plugin]=true&amp;flashvars[EmbedPlayer.SpinnerTarget]=videoHolder&amp;flashvars[dualScreen.plugin]=true&amp;flashvars[raptMedia.plugin]=true&amp;flashvars[raptMedia.parent]=videoHolder&amp;flashvars[raptMedia.behaviorOnEnd]=pause&amp;flashvars[scrubber.plugin]=false&amp;flashvars[durationLabel.plugin]=false&amp;flashvars[playPauseBtn.plugin]=false&amp;flashvars[raptMediaScrubber.plugin]=true&amp;flashvars[raptMediaDurationLabel.plugin]=true&amp;flashvars[raptMediaPlayPauseBtn.plugin]=true&amp;flashvars[EmbedPlayer.WebKitPlaysInline]=true&amp;flashvars[forceMobileHTML5]=true&amp;&amp;wid=0_21lfx0zk" />'))
        assert_that(index,
                    contains_string('<param name="no-sandboxing" value="true" />'))
        assert_that(index,
                    contains_string('<param name="height" value="285px" />'))
        assert_that(index,
                    contains_string('<param name="width" value="400px" />'))
        assert_that(index,
                    contains_string('<param name="title" value="embed title" />'))
        assert_that(index,
                    contains_string('<param name="arbitrary_1" value="arbitrary val1" />'))

        assert_that(index,
                    is_not(contains_string('<param name="src"')))
        assert_that(index,
                    is_not(contains_string('<param name="source" value="abc" />')))
        assert_that(index,
                    is_not(contains_string('<param name="url"')))
