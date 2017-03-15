#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.contentlibrary_rendering.interfaces import IContentQueueFactory

#: text mime type
TEXT_MIMETYPE = b'text/plain'

#: latex mime type
LaTeX_MIMETYPE = b'application/x-latex'

#: reStructuredText mime type
RST_MIMETYPE = b'text/x-rst'

#: Render job NTIID Type
RENDER_JOB = 'RenderJob'

#: redis hset
CONTENT_UNITS_HSET = '++etc++contentlibrary++contentunits++hset'

#: Rendering redis queue name
CONTENT_UNITS_QUEUE = '++etc++contentlibrary++queue++contentunits'

QUEUE_NAMES = (CONTENT_UNITS_QUEUE,)


def get_factory():
    return component.getUtility(IContentQueueFactory)

### from IPython.terminal.debugger import set_trace;set_trace()
