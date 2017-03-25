#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import bz2
import sys
import gzip
import time
import shutil
import zipfile
import tarfile
import tempfile
import traceback
import simplejson

from zope import lifecycleevent

from zope.security.interfaces import IPrincipal

from zope.security.management import endInteraction
from zope.security.management import newInteraction
from zope.security.management import restoreInteraction

from nti.contentrendering.nti_render import render

from nti.contentlibrary_rendering import LIBRARY_RENDER_JOB

from nti.contentlibrary_rendering.common import redis_client
from nti.contentlibrary_rendering.common import Participation

from nti.contentlibrary_rendering.interfaces import FAILED
from nti.contentlibrary_rendering.interfaces import RUNNING
from nti.contentlibrary_rendering.interfaces import SUCCESS

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.zodb.containers import time_to_64bit_int

from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import make_specific_safe


EXPIRY_TIME = 86400  # 24hrs

# common


def format_exception(e):
    result = []
    exc_type, exc_value, exc_traceback = sys.exc_info()
    result['message'] = str(e)
    result['code'] = e.__class__.__name__
    result['traceback'] = repr(traceback.format_exception(exc_type,
                                                          exc_value,
                                                          exc_traceback))
    return simplejson.dumps(result, indent='\t')


# jobs


def generate_job_id(source, creator=None):
    creator = creator or SYSTEM_USER_ID
    current_time = time_to_64bit_int(time.time())
    specific = "%s_%s_%s" % (creator, source.filename, current_time)
    specific = make_specific_safe(specific)
    return make_ntiid(nttype=LIBRARY_RENDER_JOB, specific=specific)


def job_id_status(jobId):
    return "%s=status" % jobId


def job_id_error(jobId):
    return "%s=error" % jobId


def update_job_status(jobId, status, expiry=EXPIRY_TIME):
    redis = redis_client()
    if redis is not None:
        key = job_id_status(jobId)
        redis.setex(key, value=status, time=expiry)
        return key


def update_job_error(jobId, error, expiry=EXPIRY_TIME):
    redis = redis_client()
    if redis is not None:
        key = job_id_error(jobId)
        redis.setex(key, value=error, time=expiry)
        return key

# source


def is_archive(source, magic):
    if hasattr(source, "read"):
        source.seek(0)
        file_start = source.read(len(magic))
    else:
        with open(source, "rb") as fp:
            file_start = fp.read(len(magic))
    return file_start.startswith(magic)


def is_gzip(source):
    return is_archive(source, b"\x1f\x8b\x08")


def is_bz2(source):
    return is_archive(source, b"\x42\x5a\x68")


def process_source(source):
    if not os.path.isfile(source):
        return source
    if is_gzip(source):
        target, _ = os.path.splitext(source)
        with gzip.open(source, "rb") as f_in, open(target, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return process_source(target)
    elif is_bz2(source):
        target, _ = os.path.splitext(source)
        with bz2.BZ2File(source) as f_in, open(target, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return process_source(target)
    elif tarfile.is_tarfile(source):
        target = tempfile.mkdtemp()
        tar = tarfile.TarFile(source)
        tar.extractall(target)
        files = os.listdir(target)
        if files and len(files) == 1 and os.path.isdir(files[0]):
            target = os.path.join(target, files[0])
        return process_source(target)
    elif zipfile.is_zipfile(source):
        target = tempfile.mkdtemp()
        zf = zipfile.ZipFile(source)
        zf.extractall(target)
        files = os.listdir(target)
        if files and len(files) == 1 and os.path.isdir(files[0]):
            target = os.path.join(target, files[0])
        return process_source(target)
    else:
        raise ValueError("Unsupported format")


def save_source(source, path=None):
    path = path or tempfile.mkdtemp()
    name = os.path.split(source.filename)[1]
    name = os.path.join(path, name)
    with open(name, "wb") as fp:
        fp.write(source.data)
    return name


# rendering


def find_renderable(archive):
    if os.path.isfile(archive):
        return archive  # assume renderable
    tex = os.path.basename(archive) + '.tex'
    if os.path.exists(os.path.join(archive, tex)):
        return os.path.join(archive, tex)
    for name in os.listdir(archive):
        lname = name.lower()
        if lname.endswith('.tex'):
            return os.path.join(archive, name)
    raise ValueError("Cannot find renderable LaTeX file")


def render_archive(source, provider='NTI', docachefile=False):
    source = os.path.abspath(source)
    archive = process_source(source)
    tex_file = find_renderable(archive)
    path, _ = os.path.split(tex_file)
    current_dir = os.getcwd()
    try:
        os.chdir(path)
        render(tex_file, provider, docachefile=docachefile)
    finally:
        os.chdir(current_dir)
    return archive


def render_library_job(render_job):
    logger.info('Rendering content (%s)', render_job.job_id)
    job_id = render_job.job_id
    creator = render_job.creator
    tmp_dir = tempfile.mkdtemp()
    endInteraction()
    try:
        update_job_status(job_id, RUNNING)
        newInteraction(Participation(IPrincipal(creator)))
        source = save_source(render_job.Source, tmp_dir)
        render_archive(source, render_job.Provider)
    except Exception as e:
        logger.exception('Render job %s failed', job_id)
        traceback_msg = format_exception(e)
        render_job.update_to_failed_state(traceback_msg)
        update_job_status(job_id, FAILED)
        update_job_error(job_id, traceback_msg)
    else:
        update_job_status(job_id, SUCCESS)
        render_job.update_to_success_state()
        lifecycleevent.modified(render_job)
    finally:
        restoreInteraction()
        lifecycleevent.modified(render_job)
        shutil.rmtree(tmp_dir, ignore_errors=True)
    return render_job
