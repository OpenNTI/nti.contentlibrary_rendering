#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import ends_with
from hamcrest import assert_that

import os
import bz2
import gzip
import shutil
import tarfile
import tempfile

from nti.contentlibrary_rendering.archive import is_bz2
from nti.contentlibrary_rendering.archive import is_gzip
from nti.contentlibrary_rendering.archive import process_source
from nti.contentlibrary_rendering.archive import find_renderable

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestArchive(ContentlibraryRenderingLayerTest):

    data = b'ichigo and aizen'

    def test_is_gzip(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            out_name = os.path.join(tmp_dir, 'data.dat')
            with gzip.GzipFile(out_name, mode="wb") as fp:
                fp.write(self.data)
            assert_that(is_gzip(out_name), is_(True))
        finally:
            shutil.rmtree(tmp_dir, True)

    def test_is_bz2(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            out_name = os.path.join(tmp_dir, 'data.dat')
            with bz2.BZ2File(out_name, mode="wb") as fp:
                fp.write(self.data)
            assert_that(is_bz2(out_name), is_(True))
        finally:
            shutil.rmtree(tmp_dir, True)

    def test_process_source_tar_gz(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            out_name = os.path.join(tmp_dir, 'data.tex')
            with open(out_name, "wb") as fp:
                fp.write(self.data)
            tar_name = os.path.join(tmp_dir, 'data.tar.gz')
            with tarfile.open(tar_name, mode="w:gz") as fp:
                fp.add(out_name, arcname='data.tex')
            source = process_source(tar_name)
            assert_that(source, is_not(none()))
            assert_that(os.path.isdir(source), is_(True))

            latex = find_renderable(source)
            assert_that(latex, is_not(none()))
            assert_that(os.path.isfile(latex), is_(True))
            assert_that(latex, ends_with('data.tex'))

            shutil.rmtree(source, True)
        finally:
            shutil.rmtree(tmp_dir, True)
