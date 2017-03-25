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
from hamcrest import starts_with

import os
import bz2
import gzip
import shutil
import tarfile
import tempfile
from io import BytesIO

import fudge
import fakeredis

from nti.contentlibrary_rendering.archive import is_bz2
from nti.contentlibrary_rendering.archive import is_gzip
from nti.contentlibrary_rendering.archive import process_source
from nti.contentlibrary_rendering.archive import find_renderable
from nti.contentlibrary_rendering.archive import generate_job_id
from nti.contentlibrary_rendering.archive import update_job_status

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestArchive(ContentlibraryRenderingLayerTest):

    data = b'ichigo and aizen'

    @fudge.patch('nti.contentlibrary_rendering.archive.redis_client')
    def test_job_id(self, mock_rc):
        mock_rc.is_callable().with_args().returns(fakeredis.FakeStrictRedis())
        source = fudge.Fake()
        source.filename = "bleach.zip"
        jid = generate_job_id(source, "tite kubo")
        assert_that(jid, 
                    starts_with('tag:nextthought.com,2011-10:LibraryRenderJob-tite_kubo_bleach_zip_'))
        key = update_job_status(jid, "SUCCESS")
        assert_that(key, starts_with(jid))
        assert_that(key, ends_with("=status"))

    def test_is_gzip(self):
        bio = BytesIO()
        with gzip.GzipFile(fileobj=bio, mode="wb") as fp:
            fp.write(self.data)
        assert_that(is_gzip(bio), is_(True))

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
