#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import re
import six
import sys

try:
    from urllib import url2pathname
except ImportError: # pragma: no cover
    from urllib.request import url2pathname

from docutils import nodes

from docutils.writers.html4css1 import HTMLTranslator as BaseHTMLTranslator

import PIL

logger = __import__('logging').getLogger(__name__)


class HTMLTranslator(BaseHTMLTranslator):

    def encode(self, text):
        """
        Encode special characters in `text` & return.
        """
        # Use only named entities known in both XML and HTML
        # other characters are automatically encoded "by number" if required.
        # @@@ A codec to do these and all other HTML entities would be nice.
        text = six.text_type(text)
        return text.translate(self.special_characters)

    def starttag(self, node, tagname, suffix='\n', empty=False, **attributes):
        """
        Construct and return a start tag given a node (id & class attributes
        are extracted), tag name, and optional attributes.
        """
        tagname = tagname.lower()
        prefix = []
        atts = {}
        ids = []
        for (name, value) in attributes.items():
            atts[name.lower()] = value
        classes = []
        languages = []
        # unify class arguments and move language specification
        for cls in node.get('classes', []) + atts.pop('class', '').split():
            if cls.startswith('language-'):
                languages.append(cls[9:])
            elif cls.strip() and cls not in classes:
                classes.append(cls)
        if languages:
            # attribute name is 'lang' in XHTML 1.0 but 'xml:lang' in 1.1
            atts[self.lang_attribute] = languages[0]
        if classes:
            atts['class'] = ' '.join(classes)
        assert 'id' not in atts
        ids.extend(node.get('ids', []))
        if 'ids' in atts:
            ids.extend(atts['ids'])
            del atts['ids']
        if ids:
            atts['id'] = ids[0]
            for id_ in ids[1:]:
                # Add empty "span" elements for additional IDs.  Note
                # that we cannot use empty "a" elements because there
                # may be targets inside of references, but nested "a"
                # elements aren't allowed in XHTML (even if they do
                # not all have a "href" attribute).
                if empty \
                   or isinstance(node,
                                 (nodes.bullet_list, nodes.docinfo,
                                  nodes.definition_list, nodes.enumerated_list,
                                  nodes.field_list, nodes.option_list,
                                  nodes.table)):
                    # Insert target right in front of element.
                    prefix.append('<span id="%s"></span>' % id_)
                else:
                    # Non-empty tag.  Place the auxiliary <span> tag
                    # *inside* the element, as the first child.
                    suffix += '<span id="%s"></span>' % id_
        attlist = atts.items()
        attlist.sort()
        parts = [tagname]
        for name, value in attlist:
            # value=None was used for boolean attributes without
            # value, but this isn't supported by XHTML.
            assert value is not None
            if isinstance(value, list):
                values = [six.text_type(v) for v in value]
                parts.append('%s="%s"' % (name.lower(),
                                          self.attval(' '.join(values))))
            else:
                parts.append('%s="%s"' % (name.lower(),
                                          self.attval(six.text_type(value))))
        if empty:
            infix = ' /'
        else:
            infix = ''
        return ''.join(prefix) + '<%s%s>' % (' '.join(parts), infix) + suffix

    def visit_image(self, node):
        atts = {}
        uri = node['uri']
        ext = os.path.splitext(uri)[1].lower()
        if ext in self.object_image_types:
            atts['data'] = uri
            atts['type'] = self.object_image_types[ext]
        else:
            atts['src'] = uri
            atts['alt'] = node.get('alt', uri)
        # image size
        if 'width' in node:
            atts['width'] = node['width']
        if 'height' in node:
            atts['height'] = node['height']
        if 'scale' in node:
            if (    not ('width' in node and 'height' in node)
                and self.settings.file_insertion_enabled):
                imagepath = url2pathname(uri)
                try:
                    source = imagepath.encode(sys.getfilesystemencoding())
                    img = PIL.Image.open(source)
                except (IOError, UnicodeEncodeError) as e:
                    logger.warn("Error while opening image. %s", e)
                else:
                    self.settings.record_dependencies.add(imagepath.replace('\\', '/'))
                    if 'width' not in atts:
                        atts['width'] = '%dpx' % img.size[0]
                    if 'height' not in atts:
                        atts['height'] = '%dpx' % img.size[1]
                    del img
            for att_name in 'width', 'height':
                if att_name in atts:
                    match = re.match(r'([0-9.]+)(\S*)$', atts[att_name])
                    assert match
                    atts[att_name] = '%s%s' % (
                        float(match.group(1)) * (float(node['scale']) / 100),
                        match.group(2)
                    )
        style = []
        for att_name in 'width', 'height':
            if att_name in atts:
                if re.match(r'^[0-9.]+$', atts[att_name]):
                    # Interpret unitless values as pixels.
                    atts[att_name] += 'px'
                style.append('%s: %s;' % (att_name, atts[att_name]))
                del atts[att_name]
        if style:
            atts['style'] = ' '.join(style)
        if (    isinstance(node.parent, nodes.TextElement)
            or (    isinstance(node.parent, nodes.reference)
                and not isinstance(node.parent.parent, nodes.TextElement))):
            # Inline context or surrounded by <a>...</a>.
            suffix = ''
        else:
            suffix = '\n'
        if 'align' in node:
            atts['class'] = 'align-%s' % node['align']
        if ext in self.object_image_types:
            # do NOT use an empty tag: incorrect rendering in browsers
            self.body.append(self.starttag(node, 'object', suffix, **atts) +
                             node.get('alt', uri) + '</object>' + suffix)
        else:
            self.body.append(self.emptytag(node, 'img', suffix, **atts))
