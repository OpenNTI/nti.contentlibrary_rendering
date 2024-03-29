#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class

from zope import interface

from zope.container.interfaces import IContainer

from zope.location.interfaces import IContained as IZContained

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from nti.base.interfaces import ICreated
from nti.base.interfaces import INamedFile
from nti.base.interfaces import ILastModified

from nti.schema.field import Bool
from nti.schema.field import Text
from nti.schema.field import Object
from nti.schema.field import Choice
from nti.schema.field import IndexedIterable
from nti.schema.field import DecodingValidTextLine
from nti.schema.field import TextLine as ValidTextLine

FAILED = u'Failed'
PENDING = u'Pending'
RUNNING = u'Running'
SUCCESS = u'Success'
RENDER_STATES = (SUCCESS, PENDING, FAILED, RUNNING)
RENDER_STATE_VOCABULARY = SimpleVocabulary(
    [SimpleTerm(x) for x in RENDER_STATES]
)


class IRenderJob(ILastModified, ICreated, IZContained):
    """
    Contains status on a specific rendering job
    """

    JobId = ValidTextLine(title=u"The unique job identifier.")

    Provider = ValidTextLine(title=u"Render provider",
                             required=True,
                             default=u'NTI')

    State = Choice(vocabulary=RENDER_STATE_VOCABULARY,
                   title=u"The state for this render job",
                   required=False,
                   default=PENDING)

    Error = Text(title=u"Rendering error.",
                 required=False)

    OutputRoot = interface.Attribute(u"Render output location")
    OutputRoot.setTaggedValue('_ext_excluded_out', True)

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

    def is_failed():
        """
        Returns whether the job has failed.
        """
    has_failed = is_failed

    def update_to_failed_state(reason=None):
        """
        Mark this job as failing.
        """

    def update_to_success_state():
        """
        Mark this job as successful.
        """


class IContentPackageRenderJob(IRenderJob):
    """
    Contains status on a specific rendering of a :class:`IContentPackage`.
    """
    PackageNTIID = ValidTextLine(title=u"The package ntiid.")

    Version = ValidTextLine(title=u"Rendered contents version",
                            required=False)
    Version.setTaggedValue('_ext_excluded_out', True)

    MarkRendered = Bool(title=u"Mark package as rendered.",
                        required=False,
                        default=True)
    MarkRendered.setTaggedValue('_ext_excluded_out', True)


class ILibraryRenderJob(IRenderJob):
    """
    Contains status on a specific rendering of a source
    """
    Source = Object(INamedFile, title=u"The source.")
    Source.setTaggedValue('_ext_excluded_out', True)
    
    PackageNTIID = DecodingValidTextLine(title=u"The package ntiid.",
                                         required=False)


class IContentPackageRenderMetadata(IContainer):
    """
    Contains information on :class:`IContentPackage` rendering,
    if available.
    """

    render_jobs = IndexedIterable(title=u"An iterable of render jobs",
                                  value_type=Object(IContentPackageRenderJob),
                                  unique=True,
                                  default=(),
                                  required=False)

    def createJob(package, creator, provider=None, mark_rendered=True):
        """
        Creates and returns a `IContentPackageRenderJob`.
        """
    create_job = createJob

    def removeJob(job):
        """
        Remove the specified job
        """
    remove_job = removeJob

    def mostRecentRenderJob():
        """
        Returns the most recent render `IContentPackageRenderJob` or None.
        """
    most_recent_render_job = mostRecentRenderJob

    def clear():
        """
        remove all jobs
        """


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

    def generate(source_doc, tex_doc=None, context=None):
        """
        Translate the specified source document into a plasTeX document.

        :param source_doc The source document
        :param tex_doc If provided, the plasTeX document to build.
        :param context Source context object
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

    def remove(bucket):
        """
        remove the rendered content specified but the bucket

        :param bucket the :class:`IEnumerableDelimitedHierarchyBucket` bucket
        """

    def move(source, root):
        """
        move the specified source files to the root destination

        :param source Location of the rendered content
        :param root the library root
        """
