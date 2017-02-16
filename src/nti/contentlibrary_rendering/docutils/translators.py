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

from nti.contentlibrary_rendering.docutils import get_translator

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

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

    def translate(self, rst_node, tex_doc, tex_parent=None):
        pass


class NoOpPlastexNodeTranslator(TranslatorMixin):
    """
    A translator that excludes this node from translation.
    """


class DefaultNodeToPlastexNodeTranslator(TranslatorMixin):

    __name__ = u''

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createElement(rst_node.tagname)
        return result


class TextToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "#text"

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createTextNode(rst_node.astext())
        return result


class TitleToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "title"

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createElement(rst_node.tagname)
        title_text = tex_doc.createTextNode(rst_node.astext())
        result.append(title_text)
        return result


class ImageToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = "image"


class MathToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = "math"


class SectionToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = 'section'


class SubtitleToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'subtitle'
     
    def translate(self, rst_node, tex_doc, tex_parent=None):
        # XXX: Do we want a new section here?
        result = tex_doc.createElement('section')
        names = rst_node.attributes.get('names')
        if names:
            title = names[0]
        else:
            title = rst_node.astext()
        title = tex_doc.createTextNode(title)
        result.setAttribute('title', title)
        return result


class DocumentToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'document'

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createElement(rst_node.tagname)
        title = rst_node.attributes.get('title')
        if title:
            title = tex_doc.createTextNode(title)
            result.setAttribute('title', title)
        return result


class BlockQuoteToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = 'block_quote'


class StrongToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'strong'

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createElement("textbf")
        return result


class ParagraphToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'paragraph'

    def translate(self, rst_node, tex_doc, tex_parent=None):
        tex_node = tex_doc.createElement('par')
        return tex_node


class ListItemToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'list_item'

    def translate(self, rst_node, tex_doc, tex_parent=None):
        tex_node = tex_doc.createElement('list_item')
        return tex_node


class EnumeratedListToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'enumerated_list'

    def translate(self, rst_node, tex_doc, tex_parent=None):
        tex_node = tex_doc.createElement('enumerate')
        return tex_node


class BulletListToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'bullet_list'

    def translate(self, rst_node, tex_doc, tex_parent=None):
        tex_node = tex_doc.createElement('itemize')
        return tex_node


class BuilderMixin(object):

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


@interface.implementer(IPlastexDocumentGenerator)
class PlastexDocumentGenerator(BuilderMixin):
    """
    Transforms an RST document into a plasTeX document.
    """

    @classmethod
    def create_document(cls):
        document = TeXDocument()
        document.userdata['idgen'] = IdGen()
        return document

    def generate(self, rst_document=None, tex_doc=None):
        # XXX: By default, we skip any preamble and start directly in the
        # body. docutils stores the title info in the preamble.
        if tex_doc is None:
            tex_doc = self.create_document()
        self.build_nodes(rst_document, tex_doc, tex_doc)
        return tex_doc
