#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.intid.interfaces import IIntIdRemovedEvent

from zc.intid.interfaces import IAfterIdAddedEvent

from nti.contentlibrary.interfaces import IRenderableContentPackage
from nti.contentlibrary.interfaces import IContentPackageRemovedEvent

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.recorder.interfaces import ITransactionRecordHistory

logger = __import__('logging').getLogger(__name__)


@component.adapter(IRenderableContentPackage, IIntIdRemovedEvent)
def _content_removed(package, unused_event=None):
    meta = IContentPackageRenderMetadata(package, None)
    if meta is not None:
        # pylint: disable=too-many-function-args
        meta.clear()


@component.adapter(IRenderableContentPackage, IContentPackageRemovedEvent)
def _content_package_removed(package, unused_event=None):
    _content_removed(package)


@component.adapter(IRenderableContentPackage, IAfterIdAddedEvent)
def _after_id_added_event(package, unused_event):
    # init record history
    ITransactionRecordHistory(package)
