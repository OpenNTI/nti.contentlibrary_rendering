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
import gzip
import shutil
import zipfile
import tarfile
import tempfile

from nti.contentrendering.nti_render import render


def is_archive(source, magic):
    with open(source, "rb") as fp:
        file_start = fp.read(len(magic))
        if file_start.startswith(magic):
            return True
    return False


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
        return render(tex_file, provider, docachefile=docachefile)
    finally:
        os.chdir(current_dir)
    return archive
