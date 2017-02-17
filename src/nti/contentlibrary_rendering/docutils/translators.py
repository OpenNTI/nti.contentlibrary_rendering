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

from nti.base._compat import to_unicode

from nti.contentlibrary_rendering.docutils import get_translator

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentlibrary_rendering.docutils.utils import DocumentProxy
from nti.contentlibrary_rendering.docutils.utils import rst_traversal_count

from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator


class IdGen(object):

    __slots__ = ('counter',)

    def __init__(self):
        self.counter = 0

    def __iter__(self):
        return self

    def next(self):
        self.counter += 1
        return self.counter


@interface.implementer(IRSTToPlastexNodeTranslator)
class TranslatorMixin(object):

    __name__ = None

    def translator(self, node_name):
        return get_translator(node_name)

    def translate(self, rst_node, tex_doc, tex_parent):
        pass


class NoOpPlastexNodeTranslator(TranslatorMixin):
    """
    A translator that excludes this node from translation.
    """


class DefaultNodeToPlastexNodeTranslator(TranslatorMixin):

    __name__ = u''

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement(rst_node.tagname)
        return result


class ImageToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = "image"


class MathToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = "math"


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

    def translate(self, rst_node, tex_doc, tex_parent):
        section_tag = self._get_section_tag(rst_node)
        result = tex_doc.createElement(section_tag)
        self._set_title(rst_node, tex_doc, result)
        return result


# Titles


class TitleToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "title"

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement(rst_node.tagname)
        title_text = tex_doc.createTextNode(rst_node.astext())
        result.append(title_text)
        return result


class SubtitleToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'subtitle'

    def translate(self, rst_node, tex_doc, tex_parent):
        # TODO: Do we want a new section here?
        result = tex_doc.createElement('section')
        names = rst_node.attributes.get('names')
        if names:
            title = names[0]
        else:
            title = rst_node.astext()
        title = tex_doc.createTextNode(title)
        result.setAttribute('title', title)
        return result


# Text


class TextToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "#text"

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createTextNode(rst_node.astext())
        return result


class StrongToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'strong'

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("textbf")
        return result


class EmphasisToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'emphasis'

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("emph")
        return result


class UnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "underlined"

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("uline")
        return result


class BoldItalicToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "bolditalic"

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("bolditalic")
        return result


class BoldUnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "boldunderlined"

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("boldunderlined")
        return result


class BoldItalicUnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "bolditalicunderlined"

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement("bolditalicunderlined")
        return result


# Paragraph


class BlockQuoteToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = 'block_quote'


class ParagraphToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'paragraph'

    def _get_title(self, rst_node, tex_doc):
        title = rst_node.attributes.get('title')
        title = title or rst_node.attributes.get('id')
        return title or 'par_%s' % tex_doc._inc_paragraph_counter()

    def translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('par')
        # XXX: We need a title for a paragraph b/c the renderer uses it
        # to generate and ntiid for it
        tex_node.title = to_unicode(self._get_title(rst_node, tex_doc))
        return tex_node


# Lists


class ListItemToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'list_item'

    def translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('list_item')
        return tex_node


class EnumeratedListToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'enumerated_list'

    def translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('enumerate')
        return tex_node


class BulletListToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'bullet_list'

    def translate(self, rst_node, tex_doc, tex_parent):
        tex_node = tex_doc.createElement('itemize')
        return tex_node


# Document


class DocumentToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'document'

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement(rst_node.tagname)
        title = rst_node.attributes.get('title')
        if title:
            title = tex_doc.createTextNode(title)
            result.setAttribute('title', title)
        return result


@interface.implementer(IPlastexDocumentGenerator)
class PlastexDocumentGenerator(object):
    """
    Transforms an RST document into a plasTeX document.
    """

    def translator(self, node_name):
        return get_translator(node_name)

    def handle_node(self, rst_node, tex_parent, tex_doc):
        """
        Handle our node by translating it and adding it to the doc.
        """
        node_translator = self.translator(rst_node.tagname)
        result = node_translator.translate(rst_node, tex_doc, tex_parent)
        if result is not None:
            tex_parent.append(result)
        # If no-op, keep parsing but do so for our tex_parent.
        # XXX: Is this what we want?
        if result is None:
            result = tex_parent
        return result

    def process_children(self, rst_node, tex_node, tex_doc):
        for rst_child in rst_node.children or ():
            self.build_nodes(rst_child, tex_node, tex_doc)

    def build_nodes(self, rst_node, tex_parent, tex_doc):
        """
        Handle our node by translating it and adding it to the doc
        and then processing the children.
        """
        tex_node = self.handle_node(rst_node, tex_parent, tex_doc)
        self.process_children(rst_node, tex_node, tex_doc)
        return tex_node

    def generate(self, rst_document=None, tex_doc=None):
        # XXX: By default, we skip any preamble and start directly in the
        # body. docutils stores the title info in the preamble.
        if tex_doc is None:
            tex_doc = TeXDocument()
        if 'idgen' not in tex_doc.userdata:
            tex_doc.userdata['idgen'] = IdGen()
        self.build_nodes(rst_document, tex_doc, DocumentProxy(tex_doc))
        return tex_doc
