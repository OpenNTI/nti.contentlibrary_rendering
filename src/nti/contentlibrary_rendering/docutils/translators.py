#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from plasTeX import TeXDocument

from zope import interface

from nti.base._compat import text_

from nti.contentlibrary_rendering.docutils import get_translator

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentlibrary_rendering.docutils.utils import DocumentProxy
from nti.contentlibrary_rendering.docutils.utils import rst_traversal_count

from nti.contentlibrary_rendering.docutils.writers import HTMLTranslator

from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator

from nti.contentrendering.plastexpackages.ntihtml import ntirawhtml

from nti.contentrendering.plastexpackages.ntilatexmacros import ntiembedwidget

from nti.contentrendering.plastexpackages.ntisidebar import sidebar

from nti.contentrendering.plastexpackages.ulem import uline

logger = __import__('logging').getLogger(__name__)


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

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement(rst_node.tagname)
        return result


class MathToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = "math"


# Titles


class LabelToPlastexNodeTranslator(NoOpPlastexNodeTranslator):
    __name__ = "label"


class TitleToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "title"

    def _process_document_title(self, rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement('maketitle')
        tex_doc.userdata['title'] = rst_node.astext()
        for name in  ('author', 'date', 'thanks', 'description'):
            tex_doc.userdata[name] = ''
        # Make sure we remove child node
        rst_node.children = rst_node.children[1:]
        return result

    def _process_title(self, rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement(rst_node.tagname)
        assert rst_node.children
        # We actually get the text from the child node
        title_text = tex_doc.createTextNode(rst_node.astext())
        result.append(title_text)
        # Make sure we remove child node
        rst_node.children = rst_node.children[1:]
        return result

    def do_translate(self, rst_node, tex_doc, tex_parent):
        if tex_doc.userdata.get('title') is None:
            return self._process_document_title(rst_node, tex_doc, tex_parent)
        else:
            return self._process_title(rst_node, tex_doc, tex_parent)


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

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement('section')
        self._set_title(rst_node, tex_doc, result)
        # This title gets rendered, so we need to make sure
        # the child title is not also rendered.
        rst_node.children = rst_node.children[1:]
        return result


# Text


class TextToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "#text"

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createTextNode(rst_node.astext())
        return result


class StrongToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'strong'

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement("textbf")
        return result


class EmphasisToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'emphasis'

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement("emph")
        return result


class UnderlineToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "underline"

    def do_translate(self, unused_rst_node, unused_tex_doc, unused_tex_parent):
        result = uline()
        return result


class UnderlinedToPlastexNodeTranslator(UnderlineToPlastexNodeTranslator):
    __name__ = "underlined"


class BoldItalicToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "bolditalic"

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement("bolditalic")
        return result


class BoldUnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "boldunderlined"

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement("boldunderlined")
        return result


class ItalicUnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "italicunderlined"

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement("italicunderlined")
        return result


class BoldItalicUnderlinedToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "bolditalicunderlined"

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        result = tex_doc.createElement("bolditalicunderlined")
        return result


# Lists


class ListItemToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'list_item'

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('list_item')
        return tex_node


class EnumeratedListToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'enumerated_list'

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('enumerate')
        return tex_node


class BulletListToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'bullet_list'

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('itemize')
        return tex_node


# reference


class TargetToPlastexNodeTranslator(NoOpPlastexNodeTranslator):

    __name__ = 'target'


class ReferenceToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'reference'

    special_chars = {
        ord('#'): ur'\#',
        ord('%'): ur'\%',
        ord('\\'): ur'\\',
    }

    def has_unbalanced_braces(self, s):
        """
        Test whether there are unmatched '{' or '}' characters.
        """
        level = 0
        for ch in s:
            if ch == '{':
                level += 1
            if ch == '}':
                level -= 1
            if level < 0:
                return True
        return level != 0

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        # external reference (URL)
        if 'refuri' in rst_node:
            href = text_(rst_node['refuri']).translate(self.special_chars)
            # problematic chars double caret and unbalanced braces:
            if href.find('^^') != -1 or self.has_unbalanced_braces(href):
                raise ValueError(
                    'External link "%s" not supported by LaTeX.\n'
                    ' (Must not contain "^^" or unbalanced braces.)' % href)

            tex_node = tex_doc.createElement('href')
            tex_node.setAttribute('url', rst_node['refuri'])
            return tex_node
        elif 'refid' in rst_node:
            tex_node = tex_doc.createElement('simpleref')
            tex_node.setAttribute('url', rst_node['refid'])
        else:
            raise ValueError('Unsupported reference')


# Sectioning


class LabelMixin(TranslatorMixin):

    def _handle_label(self, rst_node, unused_tex_doc, tex_node):
        children = rst_node.children
        nid = rst_node.attributes.get('id')
        if not nid and children and children[0].tagname == 'label':
            tex_node.id = children[0]['id'].encode("latin-1", 'replace')
            tex_node.id = text_(tex_node.id)
            tex_node.setAttribute('id', tex_node.id)
            rst_node.children = children[1:]


# Paragraph


class BlockQuoteToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'block_quote'

    def do_translate(self, unused_rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('ntiblockquote')
        return tex_node


class ParagraphToPlastexNodeTranslator(LabelMixin):

    __name__ = 'paragraph'

    def _handle_title(self, rst_node, tex_node, tex_doc):
        # We need a title for a paragraph b/c the renderer uses it
        # to generate and ntiid for it
        title = rst_node.attributes.get('title') \
            or  rst_node.attributes.get('id') \
            or 'par_%s' % tex_doc.px_inc_paragraph_counter()
        tex_node.title = text_(title)

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('par')
        self._handle_title(rst_node, tex_node, tex_doc)
        self._handle_label(rst_node, tex_node, tex_doc)
        return tex_node


# Chapter


class ChapterToPlastexNodeTranslator(LabelMixin):

    __name__ = 'chapter'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('chapter')
        self._handle_label(rst_node, tex_node, tex_doc)
        return tex_node


# Sections


class SectionToPlastexNodeTranslator(LabelMixin):

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

    def _handle_title(self, rst_node, tex_doc, tex_node):
        # Titles are required by sections.
        assert  rst_node.children
        title_child = rst_node.children[0]
        assert title_child.tagname == 'title'
        translator = self.translator('title')
        title_node = translator.translate(title_child, tex_doc, tex_node)
        tex_node.setAttribute('title', title_node)
        # Make sure we remove the node
        rst_node.children = rst_node.children[1:]

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        section_tag = self._get_section_tag(rst_node)
        result = tex_doc.createElement(section_tag)
        self._handle_title(rst_node, tex_doc, result)
        self._handle_label(rst_node, tex_doc, result)
        return result


class FakesectionToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'fakesection'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('fakesection')
        tex_node.setAttribute('title', rst_node['title'])
        return tex_node


class FakesubsectionToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'fakesubsection'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('fakesubsection')
        tex_node.setAttribute('title', rst_node['title'])
        return tex_node


class FakeparagraphToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'fakeparagraph'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        tex_node = tex_doc.createElement('fakeparagraph')
        tex_node.setAttribute('title', rst_node['title'])
        return tex_node


# Codeblocks


class LiteralBlockToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'literal_block'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        tex_doc.px_toggle_skip()
        rst_document = tex_doc.px_rst_document()
        translator = HTMLTranslator(rst_document)
        rst_node.walkabout(translator)
        result = ntirawhtml()
        result.set_html(''.join(translator.body))
        return result

    def do_depart(self, unused_rst_node, unused_tex_node, tex_doc):
        tex_doc.px_toggle_skip()


# sidebars


class SidebarToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'sidebar'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        result = sidebar()
        result.ownerDocument = tex_doc
        if rst_node.children and rst_node.children[0].tagname == 'title':
            result.title = rst_node.children[0].astext()
            rst_node.children = rst_node.children[1:]
        return result


# embedwidgets


class EmbedWidgetToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'embedwidget'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        result = ntiembedwidget()
        result.ownerDocument = tex_doc
        result.setAttribute('url', rst_node.attributes['source'])
        for key, val in rst_node.attributes.items():
            if key.lower() in ('src', 'source', 'url'):
                # For src, it must be the same value as the source, otherwise it would cause rendering error in UI.
                # Don't set it for now.
                continue
            if val:
                result.setAttribute(key, val)
        return result


# Document


class MetaToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'meta'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
        title = rst_node.attributes.get('title', None)
        if title:
            elements = tex_doc.getElementsByTagName('document')
            doc_element = elements[0] if elements else None
            if doc_element is not None:
                tex_doc.userdata['title'] = title
                title = tex_doc.createTextNode(title)
                doc_element.setAttribute('title', title)
        for name in ('icon', 'description'):
            value = rst_node.attributes.get(name, None)
            if value:
                tex_doc.userdata[name] = value
        return None


class DocumentToPlastexNodeTranslator(TranslatorMixin):

    __name__ = 'document'

    def do_translate(self, rst_node, tex_doc, unused_tex_parent):
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
            tex_node.id = text_(uid)
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
    # Is this what we want?
    if result is None:
        result = tex_parent
    return result


def process_children(rst_node, tex_node, tex_doc):
    for rst_child in rst_node.children or ():
        build_nodes(rst_child, tex_node, tex_doc)


def skip_node(node):
    # should we not just default to including node?
    return node.tagname in ('system_message', 'comment')


def build_nodes(rst_node, tex_parent, tex_doc):
    """
    Handle our node by translating it and adding it to the doc
    and then processing the children.
    """
    if skip_node(rst_node):
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

    def __init__(self, context=None):
        self.context = context

    def build_nodes(self, rst_node, tex_parent, tex_doc):
        build_nodes(rst_node, tex_parent, tex_doc)

    def generate(self, rst_document=None, tex_doc=None, context=None):
        context = self.context if context is None else context
        # By default, we skip any preamble and start directly in the
        # body. docutils stores the title info in the preamble.
        if tex_doc is None:
            tex_doc = TeXDocument()
        if 'idgen' not in tex_doc.userdata:
            tex_doc.userdata['idgen'] = IdGen()
        # Proxy allows us to set useful state fields without modified original
        # context object is available in node translators
        doc_proxy = DocumentProxy(tex_doc, context=context,
                                  rst_document=rst_document)
        self.build_nodes(rst_document, tex_doc, doc_proxy)
        return tex_doc
