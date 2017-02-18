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

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.schema.field import Bool
from nti.schema.field import Text
from nti.schema.field import Object
from nti.schema.field import Choice
from nti.schema.field import IndexedIterable
from nti.schema.field import TextLine as ValidTextLine

SUCCESS = 'Success'
PENDING = 'Pending'
FAILED = 'Failed'
RENDER_STATES = (SUCCESS, PENDING, FAILED)
RENDER_STATE_VOCABULARY = SimpleVocabulary(
    [SimpleTerm(_x) for _x in RENDER_STATES])


class IContentPackageRenderJob(ILastModified, ICreated, IZContained):
    """
    Contains status on a specific rendering of a :class:`IContentPackage`.
    """
    PackageNTIID = ValidTextLine(title="The package ntiid.")

    JobId = ValidTextLine(title="The unique job identifier.")

    Provider = ValidTextLine(title="Render provider",
                             required=True,
                             default='NTI')

    State = Choice(vocabulary=RENDER_STATE_VOCABULARY,
                   title='The state for this render job',
                   required=False,
                   default=PENDING)

    MarkRendered = Bool(title="Mark package as rendered.",
                        required=False,
                        default=True)

    Error = Text(title="Rendering error.",
                 required=False)

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

    def createJob(package, creator, provider=None, mark_rendered=True):
        """
        Creates and returns a `IContentPackageRenderJob`.
        """
    create_job = createJob

    def mostRecentRenderJob():
        """
        Returns the most recent render `IContentPackageRenderJob` or None.
        """
    most_recent_render_job = mostRecentRenderJob


class IContentQueueFactory(interface.Interface):
    """
    A factory for content rendering queues.
    """


class IContentTransformer(interface.Interface):
    """
    A utility to transform a piece of content
    """

    def transform(content, context=None, out_dir=None):
        """
        Transform the specified content to a latex file for rendering

        :param content String or buffer with the content to transform
        :param context Transformer context (e.g. :class:`IContentPackage`)
        :param out_dir Output directory
        :return a latex file
        """


class IPlastexDocumentGenerator(interface.Interface):
    """
    A utility that generates a plasTeX document from a given source
    document.
    """

    def generate(source_doc, tex_doc=None):
        """
        Translate the specified source document into a plasTeX document.

        :param source_doc The source document
        :param tex_doc If provided, the plasTeX document to build.
        :return a plasTeX document
        """


class IRenderedContentLocator(interface.Interface):
    """
    Utility to manipulate the files associated with a rendered content
    """

    def locate(path, context):
        """
        [re]locate the rendered content

        :param path Location of the rendered content
        :param context Locator context (e.g. :class:`IContentPackage`)
        :return :class:`IDelimitedHierarchyItem' with new location
        """

    def remove(context):
        """
        [re]remove the rendered content
        """
