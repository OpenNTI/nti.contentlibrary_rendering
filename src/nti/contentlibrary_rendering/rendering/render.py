#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: render.py 109016 2017-03-16 20:29:46Z carlos.sanchez $
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os

import transaction

from plasTeX import Base
from plasTeX import TeXDocument

from zope import component

from zope.intid.interfaces import IIntIds

from zope.security.interfaces import IPrincipal

from zope.security.management import endInteraction
from zope.security.management import newInteraction
from zope.security.management import restoreInteraction

from nti.async.threadlocal import get_current_job

from nti.contentlibrary.utils import get_published_contents
from nti.contentlibrary.utils import get_published_snapshot

from nti.contentlibrary_rendering import RST_MIMETYPE

from nti.contentlibrary_rendering.common import mkdtemp

from nti.contentlibrary_rendering.interfaces import IContentTransformer
from nti.contentlibrary_rendering.interfaces import IPlastexDocumentGenerator

from nti.contentlibrary_rendering.processing import add_to_queue

from nti.contentlibrary_rendering.rendering import get_package
from nti.contentlibrary_rendering.rendering import Participation

from nti.contentlibrary_rendering.rendering.locator import locate_package_job

from nti.contentrendering import nti_render

from nti.contentrendering.render_document import load_packages
from nti.contentrendering.render_document import setup_environ
from nti.contentrendering.render_document import prepare_document_settings


def apply_config_overrides(tex_dom):
    # We want a single file, 'index.html'
    tex_dom.config['files']['split-level'] = 0


def prepare_tex_document(package=None, provider='NTI', jobname=None,
                         context=None, tex_dom=None, outfile_dir=None):
    """
    Build and prepare context for our plasTeX document, returning
    the new plasTeX document and the jobname.nose2
    """
    # XXX: Do we need to read in render_conf? How about cross-document refs?
    tex_dom = TeXDocument() if tex_dom is None else tex_dom
    Base.document.filenameoverride = property(lambda unused: 'index')
    # Generate a jobname, this is used in the eventual NTIID.
    specific_ntiid = None
    if not jobname:
        if package is not None:
            intids = component.getUtility(IIntIds)
            specific_ntiid = jobname = intids.getId(package)
            tex_dom.userdata['document_ntiid'] = package.ntiid
        else:
            specific_ntiid = jobname = id(tex_dom)
    jobname = str(jobname)
    specific_ntiid = str(specific_ntiid or jobname)
    tex_dom.userdata['jobname'] = jobname
    # Prep our doc
    prepare_document_settings(tex_dom,
                              provider=provider,
                              working_dir=outfile_dir,
                              specific_ntiid=specific_ntiid)
    # Pull in all necessary plugins/configs/templates.
    unused_ctx, packages_path = load_packages(context=context,
                                              load_configs=False)
    setup_environ(tex_dom, jobname, packages_path)
    return tex_dom, jobname


def render_document(source_doc, package=None, outfile_dir=None,
                    provider='NTI', jobname=None, content_type=RST_MIMETYPE):
    """
    Render the given source document.
    """
    current_dir = os.getcwd()
    outfile_dir = outfile_dir or mkdtemp()
    try:
        os.chdir(outfile_dir)
        # Get a suitable tex dom
        tex_dom, jobname = prepare_tex_document(package,
                                                provider,
                                                jobname=jobname,
                                                outfile_dir=outfile_dir)
        apply_config_overrides(tex_dom)
        # Generate our plasTeX DOM and render.
        generate_document(source_doc, tex_dom, content_type)
        return nti_render.process_document(tex_dom, jobname)
    finally:
        os.chdir(current_dir)


def get_contents_to_render(package):
    """
    Get the latest published contents for our package, otherwise fall
    back to the current contents on the package.
    """
    contents = get_published_contents(package)
    if contents is None:
        logger.warn('No published contents; falling back to current contents (%s)',
                    package.ntiid)
        contents = package.contents
    return contents


def transform_content(context, contentType, contents=None):
    if contents is None:
        contents = get_contents_to_render(context)
    transformer = component.getUtility(IContentTransformer,
                                       name=str(contentType))
    return transformer.transform(contents, context=context)


def generate_document(source_doc, tex_dom, content_type=RST_MIMETYPE):
    generator = component.getUtility(IPlastexDocumentGenerator,
                                     name=str(content_type))
    generator.generate(source_doc, tex_dom)
    return tex_dom


def place_next_job(render_job, outfile_dir):
    add_to_queue("locator_queue",
                 locate_package_job,
                 render_job,
                 outfile_dir=outfile_dir)


def process_render_job(render_job):
    provider = render_job.Provider
    package = get_package(render_job)
    contentType = package.contentType or RST_MIMETYPE

    current_dir = os.getcwd()
    outfile_dir = mkdtemp()
    try:
        os.chdir(outfile_dir)

        # 1. Transform content into dom
        snapshot = get_published_snapshot(package)
        version = snapshot.version if snapshot else None
        contents = snapshot.contents if snapshot else None
        source_doc = transform_content(package, contentType, contents)

        # save version
        render_job.Version = version

        # 2. Render
        tex_dom = render_document(source_doc,
                                  provider=provider,
                                  package=package,
                                  content_type=contentType,
                                  outfile_dir=outfile_dir)
        return tex_dom
    finally:
        os.chdir(current_dir)
    return outfile_dir


def render_package_job(render_job):
    logger.info('Rendering content (%s) (%s)',
                render_job.PackageNTIID,
                render_job.job_id)
    job_id = render_job.job_id
    creator = render_job.creator
    endInteraction()
    async_job = get_current_job()
    try:
        # set async to be side effect free
        if async_job is not None:
            async_job.is_side_effect_free = True
        # process
        newInteraction(Participation(IPrincipal(creator)))
        outfile_dir = process_render_job(render_job)
        place_next_job(render_job, outfile_dir)
    except Exception as e:
        # XXX: Do we want to fail all applicable jobs?
        logger.exception('Render job %s failed', job_id)
        render_job.update_to_failed_state(str(e))
    else:
        if async_job is not None:
            transaction.abort()
    finally:
        restoreInteraction()
