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

from nti.contentlibrary_rendering.docutils import translator

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator

@interface.implementer(IRSTToPlastexNodeTranslator)
class DefaultRSTToPlastexNodeTranslator(object):

    def translate(self, rst_node, tex_doc):
        result = tex_doc.createElement(rst_node.tagname)
        return result

@interface.implementer(IRSTToPlastexNodeTranslator)
class TextRSTToPlastexNodeTranslator(object):

    def translate(self, rst_node, tex_doc):
        result = tex_doc.createTextNode(rst_node.astext())
        return result

@interface.implementer(IRSTToPlastexNodeTranslator)
class TitleRSTToPlastexNodeTranslator(object):

    def translate(self, rst_node, tex_doc):
        result = tex_doc.createElement(rst_node.tagname)
        title_text = tex_doc.createTextNode(rst_node.astext())
        result.append( title_text )
        return result

class _NoopRSTToPlastexNodeTranslator(object):
    """
    A translator that excludes this node from translation.
    """

    def translate(self, rst_node, tex_doc):
        pass

@interface.implementer(IRSTToPlastexNodeTranslator)
class ImageRSTToPlastexNodeTranslator(_NoopRSTToPlastexNodeTranslator):
    pass

@interface.implementer(IRSTToPlastexNodeTranslator)
class MathRSTToPlastexNodeTranslator(_NoopRSTToPlastexNodeTranslator):
    pass

@interface.implementer(IRSTToPlastexNodeTranslator)
class SectionRSTToPlastexNodeTranslator(_NoopRSTToPlastexNodeTranslator):
    # XXX: if we include sections, we'll need title attributes.
    pass

@interface.implementer(IRSTToPlastexNodeTranslator)
class ParagraphRSTToPlastexNodeTranslator(object):

    def translate(self, unused_rst_node, tex_doc):
        result = tex_doc.createElement('par')
        return result

@interface.implementer(IRSTToPlastexNodeTranslator)
class SubtitleRSTToPlastexNodeTranslator(object):

    def translate(self, rst_node, tex_doc):
        # XXX: Do we want a new section here?
        result = tex_doc.createElement('section')
        names = rst_node.attributes.get( 'names' )
        if names:
            title = names[0]
        else:
            title = rst_node.astext()
        title = tex_doc.createTextNode(title)
        result.setAttribute('title', title)
        return result

@interface.implementer(IRSTToPlastexNodeTranslator)
class DocumentRSTToPlastexNodeTranslator(object):

    def translate(self, rst_node, tex_doc):
        result = tex_doc.createElement(rst_node.tagname)
        # This should always have a title right...?
        title = tex_doc.createTextNode(rst_node.attributes['title'])
        # The document root (and sections?) will need a title element.
        result.setAttribute('title', title)
        return result

@interface.implementer(IPlastexDocumentGenerator)
class RSTToPlastexDocumentGenerator(object):
    """
    Transforms an RST document into a plasTeX document.
    """

    def _get_node_translator(self, node_name):
        return translator(node_name)

    def _handle_node(self, rst_node, tex_parent, tex_doc):
        node_translator = self._get_node_translator( rst_node.tagname )
        tex_node = node_translator.translate(rst_node, tex_doc)
        if tex_node is not None:
            tex_parent.append(tex_node)
        # If no-op, keep parsing but do so for our tex_parent.
        # XXX: Is this what we want?
        if tex_node is None:
            tex_node = tex_parent
        return tex_node

    def build_nodes(self, rst_parent, tex_parent, tex_doc):
        tex_node = self._handle_node(rst_parent, tex_parent, tex_doc)
        for rst_child in rst_parent.children or ():
            self.build_nodes(rst_child, tex_node, tex_doc)

    def generate(self, rst_document, tex_doc=None):
        # XXX: By default, we skip any preamble and start directly in the
        # body. docutils stores the title info in the preamble.
        document = TeXDocument() if tex_doc is None else tex_doc
        self.build_nodes(rst_document, document, document)
        return document
