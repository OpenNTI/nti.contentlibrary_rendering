#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from functools import total_ordering

from zope import interface

from zope.container.contained import Contained

from nti.base._compat import to_unicode

from nti.contentlibrary_rendering.interfaces import FAILED
from nti.contentlibrary_rendering.interfaces import PENDING
from nti.contentlibrary_rendering.interfaces import SUCCESS

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderJob

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.property.property import alias


@EqHash('JobId')
@total_ordering
@interface.implementer(IContentPackageRenderJob)
class ContentPackageRenderJob(SchemaConfigured,
                              PersistentCreatedModDateTrackingObject,
                              Contained):
    createDirectFieldProperties(IContentPackageRenderJob)

    __external_class_name__ = u"ContentPackageRenderJob"
    mime_type = mimeType = u'application/vnd.nextthought.content.packagerenderjob'

    creator = SYSTEM_USER_ID

    state = alias('State')
    jobId = job_id = alias('JobId')
    ntiid = package = alias('PackageNTIID')

    def __init__(self, *args, **kwargs):
        SchemaConfigured.__init__(self, *args, **kwargs)
        PersistentCreatedModDateTrackingObject.__init__(self, *args, **kwargs)

    def __str__(self, *args, **kwargs):
        return '%s (%s)' % (self.JobId, self.State)
    __repr__ = __str__

    def __lt__(self, other):
        try:
            return self.lastModified < other.lastModified
        except AttributeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.lastModified > other.lastModified
        except AttributeError:
            return NotImplemented

    def is_finished(self):
        """
        Returns whether the job is finished or has failed.
        """
        return self.State in (SUCCESS, FAILED)

    def is_pending(self):
        """
        Returns whether the job has not yet been run.
        """
        return self.State == PENDING

    def is_success(self):
        """
        Returns whether the job has succeeded.
        """
        return self.State == SUCCESS

    def update_to_failed_state(self, reason=None):
        """
        Mark this job as failing.
        """
        self.updateLastMod()
        self.State = FAILED
        self.Error = to_unicode(reason)

    def update_to_success_state(self):
        """
        Mark this job as successful.
        """
        self.updateLastMod()
        self.State = SUCCESS
