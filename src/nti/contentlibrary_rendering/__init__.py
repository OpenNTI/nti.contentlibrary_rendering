#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from nti.contentlibrary import NTI

from nti.contentlibrary_rendering.interfaces import IContentQueueFactory

#: NTI provider
NTI_PROVIDER = NTI

#: text mime type
TEXT_MIMETYPE = b'text/plain'

#: latex mime type
LaTeX_MIMETYPE = b'application/x-latex'

#: Render job NTIID Type
RENDER_JOB = u'RenderJob'

#: Library ender job NTIID Type
LIBRARY_RENDER_JOB = u'LibraryRenderJob'

#: redis hset
CONTENT_UNITS_HSET = '++etc++contentlibrary++contentunits++hset'

#: redis hset
CONTENT_UNITS_HSET_EXPIRY = 7200  # 2 hr

#: Rendering redis queue name
CONTENT_UNITS_QUEUE = '++etc++contentlibrary++queue++contentunits'

QUEUE_NAMES = (CONTENT_UNITS_QUEUE,)


def get_factory():
    return component.getUtility(IContentQueueFactory)

### from gevent.event import Event; import threading; threading._Event = Event; from IPython.terminal.debugger import set_trace;set_trace()
