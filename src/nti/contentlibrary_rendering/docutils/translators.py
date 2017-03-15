#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX import TeXDocument

from plasTeX.Logging import getLogger
logger = getLogger(__name__)

from zope import interface

from nti.base._compat import unicode_

from nti.contentlibrary_rendering.docutils import get_translator

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentlibrary_rendering.docutils.utils import DocumentProxy
from nti.contentlibrary_rendering.docutils.utils import rst_traversal_count

from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator

from nti.contentrendering.plastexpackages.ulem import uline


class IdGen(object):

    __slots__ = ('counter',)

    def __init__(self):
        self.counter = 0

    def __iter__(self):
        return self

    def next(self):
        self.counter += 1
        return str(self.counter)


@interface.implementer(IRSTToPlastexNodeTranslator)
class TranslatorMixin(object):

    __name__ = None

    def translator(self, node_name):
        return get_translator(node_name)

    def do_translate(self, rst_node, tex_doc, tex_parent):
        pass

    def translate(self, rst_node, tex_doc, tex_parent):
        if tex_doc.px_skipping():
            tex_doc.px_push(rst_node)
        else:
            return self.do_translate(rst_node, tex_doc, tex_parent)

    def do_depart(self, rst_node, tex_node, tex_doc):
        pass

    def depart(self, rst_node, tex_node, tex_doc):
        return self.do_depart(rst_node, tex_node, tex_doc)


class NoOpPlastexNodeTranslator(TranslatorMixin):
    """
    A translator that excludes this node from translation.
    """


class DefaultNodeToPlastexNodeTranslator(TranslatorMixin):

    __name__ = u''

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement(rst_node.tagname)
        return result


class ImageToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = "image"


class MathToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = "math"


# Titles


class TitleToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "title"

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement(rst_node.tagname)
        assert rst_node.children
        # We actually get the text from the child node
        title_text = tex_doc.createTextNode(rst_node.astext())
        result.append(title_text)
        # Make sure we remove child node
        rst_node.children = rst_node.children[1:]
        return result


class SubtitleToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'subtitle'

    def _set_title(self, rst_node, tex_doc, tex_node):
        """
        Titles are required by sections.
        """
        assert rst_node.children
        title_child = rst_node.children[0]
        assert title_child.tagname == '#text'
        node_translator = get_translator(title_child.tagname)
        title_node = node_translator.translate(title_child, tex_doc, tex_node)
        tex_node.setAttribute('title', title_node)

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement('section')
        self._set_title(rst_node, tex_doc, result)
        # This title gets rendered, so we need to make sure
        # the child title is not also rendered.
        rst_node.children = rst_node.children[1:]
        return result


# Text


class TextToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "#text"

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createTextNode(rst_node.astext())
        return result


class StrongToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'strong'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("textbf")
        return result


class EmphasisToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'emphasis'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("emph")
        return result


class UnderlineToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "underline"

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = uline()
        return result


class UnderlinedToPlastexNodeTranslator(UnderlineToPlastexNodeTranslator):
    __name__ = "underlined"


class BoldItalicToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "bolditalic"

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("bolditalic")
        return result


class BoldUnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "boldunderlined"

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("boldunderlined")
        return result


class ItalicUnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "italicunderlined"

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("italicunderlined")
        return result


class BoldItalicUnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "bolditalicunderlined"

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("bolditalicunderlined")
        return result


# Paragraph


class BlockQuoteToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = 'block_quote'


class ParagraphToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'paragraph'

    def _get_title(self, rst_node, tex_doc):
        result = rst_node.attributes.get('title') \
             or  rst_node.attributes.get('id') \
             or 'par_%s' % tex_doc.px_inc_paragraph_counter()
        return result

    def do_translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('par')
        # XXX: We need a title for a paragraph b/c the renderer uses it
        # to generate and ntiid for it
        tex_node.title = unicode_(self._get_title(rst_node, tex_doc))
        return tex_node


# Lists


class ListItemToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'list_item'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('list_item')
        return tex_node


class EnumeratedListToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'enumerated_list'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('enumerate')
        return tex_node


class BulletListToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'bullet_list'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('itemize')
        return tex_node


# Sections


class SectionToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'section'

    SECTION_DEPTH_MAX = 3
    SECTION_MAP = {1: 'section',
                   2: 'subsection',
                   3: 'subsubsection'}

    def _get_section_tag(self, rst_node):
        parent_section_count = rst_traversal_count(rst_node, 'section')
        if parent_section_count >= self.SECTION_DEPTH_MAX:
            raise ValueError('Only three levels of sections are allowed.')
        section_level = parent_section_count + 1
        section_val = self.SECTION_MAP[section_level]
        return section_val

    def _set_title(self, rst_node, tex_doc, tex_node):
        """
        Titles are required by sections.
        """
        assert rst_node.children
        title_child = rst_node.children[0]
        assert title_child.tagname == 'title'
        translator = self.translator('title')
        title_node = translator.translate(title_child, tex_doc, tex_node)
        tex_node.setAttribute('title', title_node)

    def do_translate(self, rst_node, tex_doc, tex_parent):
        section_tag = self._get_section_tag(rst_node)
        result = tex_doc.createElement(section_tag)
        self._set_title(rst_node, tex_doc, result)
        rst_node.children = rst_node.children[1:]
        return result


class FakesectionToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'fakesection'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('fakesection')
        tex_node.setAttribute('title', rst_node['title'])
        return tex_node


class FakesubsectionToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'fakesubsection'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('fakesubsection')
        tex_node.setAttribute('title', rst_node['title'])
        return tex_node


class FakeparagraphToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'fakeparagraph'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('fakeparagraph')
        tex_node.setAttribute('title', rst_node['title'])
        return tex_node


# Document


class DocumentToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'document'

    def do_translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement(rst_node.tagname)
        title = rst_node.attributes.get('title')
        if title:
            title = tex_doc.createTextNode(title)
            result.setAttribute('title', title)
        return result


# Transformer

def handle_uid(rst_node, tex_node):
    if hasattr(rst_node, 'attributes'):  # check for docid
        uid = rst_node.attributes.get('uid')
        if uid and not tex_node.getAttribute('id'):
            tex_node.id = unicode_(uid)
            tex_node.setAttribute('id', tex_node.id)
            return tex_node.id
    return None


def depart_node(rst_node, tex_node, tex_doc):
    node_translator = get_translator(rst_node.tagname)
    result = node_translator.depart(rst_node, tex_node, tex_doc)
    handle_uid(rst_node, tex_node)
    return result


def handle_node(rst_node, tex_parent, tex_doc):
    """
    Handle our node by translating it and adding it to the doc.
    """
    node_translator = get_translator(rst_node.tagname)
    result = node_translator.translate(rst_node, tex_doc, tex_parent)
    if result is not None and tex_parent is not None:
        tex_parent.append(result)
    # If no-op, keep parsing but do so for our tex_parent.
    # XXX: Is this what we want?
    if result is None:
        result = tex_parent
    return result


def process_children(rst_node, tex_node, tex_doc):
    for rst_child in rst_node.children or ():
        build_nodes(rst_child, tex_node, tex_doc)


def build_nodes(rst_node, tex_parent, tex_doc):
    """
    Handle our node by translating it and adding it to the doc
    and then processing the children.
    """
    # Bypass all system messages
    if rst_node.tagname == 'system_message':
        return
    tex_node = handle_node(rst_node, tex_parent, tex_doc)
    process_children(rst_node, tex_node, tex_doc)
    depart_node(rst_node, tex_node, tex_doc)
    return tex_node


@interface.implementer(IPlastexDocumentGenerator)
class PlastexDocumentGenerator(object):
    """
    Transforms an RST document into a plasTeX document.
    """

    def build_nodes(self, rst_node, tex_parent, tex_doc):
        build_nodes(rst_node, tex_parent, tex_doc)

    def generate(self, rst_document=None, tex_doc=None):
        # XXX: By default, we skip any preamble and start directly in the
        # body. docutils stores the title info in the preamble.
        if tex_doc is None:
            tex_doc = TeXDocument()
        if 'idgen' not in tex_doc.userdata:
            tex_doc.userdata['idgen'] = IdGen()
        # Proxy allows us to set useful state fields without modified original
        doc_proxy = DocumentProxy(tex_doc)
        self.build_nodes(rst_document, tex_doc, doc_proxy)
        return tex_doc
