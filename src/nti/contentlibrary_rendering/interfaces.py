#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.container.interfaces import IContainer

from zope.location.interfaces import IContained as IZContained

from zope.schema import vocabulary

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.schema.field import Object
from nti.schema.field import Choice
from nti.schema.field import ValidTextLine
from nti.schema.field import IndexedIterable

SUCCESS = 'Success'
PENDING = 'Pending'
FAILED = 'Failed'
RENDER_STATES = (SUCCESS, PENDING, FAILED)
RENDER_STATE_VOCABULARY = \
    vocabulary.SimpleVocabulary([vocabulary.SimpleTerm(_x) for _x in RENDER_STATES])

class IContentPackageRenderJob(ILastModified, ICreated, IZContained):
    """
    Contains status on a specific rendering of a :class:`IContentPackage`.
    """
    PackageNTIID = ValidTextLine(title="The package ntiid.")

    JobId = ValidTextLine(title="The unique job identifier.")

    State = Choice(vocabulary=RENDER_STATE_VOCABULARY,
                   title='The state for this render job',
                   required=False,
                   default=PENDING)

    def is_finished():
        """
        Returns whether the job is finished or has failed.
        """

    def is_pending():
        """
        Returns whether the job has not yet been run.
        """

    def is_success():
        """
        Returns whether the job has succeeded.
        """

    def update_to_failed_state(reason=None):
        """
        Mark this job as failing.
        """

    def update_to_success_state():
        """
        Mark this job as successful.
        """

class IContentPackageRenderMetadata(IContainer):
    """
    Contains information on :class:`IContentPackage` rendering,
    if available.
    """

    render_jobs = IndexedIterable(title="An iterable of render jobs",
                                  value_type=Object(IContentPackageRenderJob),
                                  unique=True,
                                  default=(),
                                  required=False)

    def createJob(self):
        """
        Creates and returns a `IContentPackageRenderJob`.
        """

    def mostRecentRenderJob(self):
        """
        Returns the most recent render `IContentPackageRenderJob` or None.
        """

class IContentQueueFactory(interface.Interface):
    """
    A factory for content rendering queues.
    """
