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

    def __next__(self):
        self.counter += 1
        return self.counter


@interface.implementer(IRSTToPlastexNodeTranslator)
class TranslatorMixin(object):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        pass


class NoOpPlastexNodeTranslator(TranslatorMixin):
    """
    A translator that excludes this node from translation.
    """


class DefaultNodeToPlastexNodeTranslator(TranslatorMixin):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createElement(rst_node.tagname)
        return result


class TextToPlastexNodeTranslator(TranslatorMixin):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createTextNode(rst_node.astext())
        return result


class TitleToPlastexNodeTranslator(TranslatorMixin):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createElement(rst_node.tagname)
        title_text = tex_doc.createTextNode(rst_node.astext())
        result.append(title_text)
        return result


class ImageToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    pass


class MathToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    pass


class SectionToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    # XXX: if we include sections, we'll need title attributes.
    pass


class DocumentToPlastexNodeTranslator(TranslatorMixin):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        result = tex_doc.createElement(rst_node.tagname)
        # This should always have a title right...?
        title = tex_doc.createTextNode(rst_node.attributes['title'])
        # The document root (and sections?) will need a title element.
        result.setAttribute('title', title)
        return result


class SubtitleToPlastexNodeTranslator(TranslatorMixin):

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


class BuilderMixin(object):

    def translator(self, node_name):
        return get_translator(node_name)

    def handle_node(self, rst_node, tex_parent, tex_doc):
        node_translator = self.translator(rst_node.tagname)
        result = node_translator.translate(rst_node, tex_doc, tex_parent)
        if result is not None:
            tex_parent.append(result)
        # If no-op, keep parsing but do so for our tex_parent.
        # XXX: Is this what we want?
        if result is None:
            result = tex_parent
        return result

    def process_children(self, rst_node, tex_node, text_doc):
        for rst_child in rst_node.children or ():
            self.build_nodes(rst_child, tex_node, text_doc)

    def build_nodes(self, rst_node, tex_parent, tex_doc):
        tex_node = self.handle_node(rst_node, tex_parent, tex_doc)
        return tex_node


class ParagraphToPlastexNodeTranslator(TranslatorMixin,
                                       BuilderMixin):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        tex_node = tex_doc.createElement('par')
        self.process_children(rst_node, tex_node, tex_doc)
        return tex_node


class BlockTypeToPlastexNodeTranslator(TranslatorMixin,
                                       BuilderMixin):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        tex_node = tex_doc.createElement('par')
        self.process_children(rst_node, tex_node, tex_doc)
        return tex_node


class ListItemToPlastexNodeTranslator(BuilderMixin,
                                      TranslatorMixin):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        tex_node = tex_doc.createElement('list_item')
        self.process_children(rst_node, tex_node, tex_doc)
        return tex_node


class BulletListToPlastexNodeTranslator(BuilderMixin,
                                        TranslatorMixin):

    def translate(self, rst_node, tex_doc, tex_parent=None):
        tex_node = tex_doc.createElement('itemize')
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
