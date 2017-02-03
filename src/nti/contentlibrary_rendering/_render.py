#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary_rendering import RST_MIMETYPE

from nti.contentlibrary_rendering.interfaces import IContentTransformer

from nti.contentrendering import nti_render
 
from nti.ntiids.ntiids import find_object_with_ntiid


def render_latex(tex_source, unit=None):
    return nti_render.render(tex_source)


def transform_content(unit):
    contentType = unit.contentType or RST_MIMETYPE
    transformer = component.getUtility(IContentTransformer, 
                                       name=str(contentType))
    latex_file = transformer.transform(unit.contents, 
                                       context=unit)
    return render_latex(latex_file, unit)


def _do_render_package(render_job):
    ntiid = render_job.PackageNTIID
    package = find_object_with_ntiid(ntiid)
    if package is None:
        raise ValueError("Package not found", ntiid)
    elif not IRenderableContentPackage.providedBy(package):
        raise TypeError("Invalid content package", ntiid)
    transform_content(package)


def render_package_job(render_job):
    logger.info( 'Rendering content (%s) (%s)',
                 render_job.PackageNTIID,
                 render_job.job_id)
    job_id = render_job.job_id
    try:
        _do_render_package(render_job)
    except Exception as e:
        logger.exception('Render job %s failed', job_id)
        render_job.update_to_failed_state(str(e))
    else:
        logger.info( 'Finished rendering content (%s) (%s)',
                     render_job.PackageNTIID,
                     render_job.job_id)
        render_job.update_to_success_state()
