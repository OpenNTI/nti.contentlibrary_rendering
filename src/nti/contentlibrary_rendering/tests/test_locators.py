#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import starts_with
from hamcrest import contains_string

import fudge

import os
import socket
import shutil
import tempfile

from nti.contentlibrary import DELETED_MARKER
from nti.contentlibrary import AUTHORED_PREFIX

from nti.contentlibrary.filesystem import FilesystemBucket

from nti.contentlibrary_rendering.locators import FilesystemLocator
from nti.contentlibrary_rendering.locators import DevFilesystemLocator

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestLocator(ContentlibraryRenderingLayerTest):

    def _test_fs_locator(self, locator, callable_check):
        sample = os.path.join(os.path.dirname(__file__), 'sample.tex')
        source_dir = tempfile.mkdtemp()
        target_dir = tempfile.mkdtemp()
        try:
            shutil.copy(sample, source_dir + "/sample.tex")
            root = FilesystemBucket(name="source")
            root.absolute_path = target_dir
            bucket = locator._do_locate(source_dir, root=root, context=None)

            assert_that(bucket, is_not(none()))
            assert_that(bucket.absolute_path, contains_string(AUTHORED_PREFIX))
            assert_that(bucket.absolute_path,
                        contains_string(socket.gethostname()))
            assert_that(bucket.absolute_path, contains_string("_1000"))
            assert_that(bucket.absolute_path, starts_with(target_dir))

            assert_that(os.path.exists(bucket.absolute_path), is_(True))
            assert_that(os.path.isdir(bucket.absolute_path), is_(True))

            callable_check(bucket, source_dir)
        finally:
            shutil.rmtree(source_dir, True)
            shutil.rmtree(target_dir, True)

    @fudge.patch('nti.contentlibrary_rendering.locators.FilesystemLocator._get_id')
    def test_filelocator(self, m_gid):
        m_gid.is_callable().returns("1000")

        def _check(bucket, source_dir):
            assert_that(os.path.exists(os.path.join(source_dir, DELETED_MARKER)),
                        is_(True))
            assert_that(os.path.exists(os.path.join(bucket.absolute_path, 'sample.tex')),
                        is_(True))
        self._test_fs_locator(FilesystemLocator(), _check)

    @fudge.patch('nti.contentlibrary_rendering.locators.FilesystemLocator._get_id')
    def test_dev_filelocator(self, m_gid):
        m_gid.is_callable().returns("1000")

        def _check(unused_bucket, source_dir):
            assert_that(os.path.exists(source_dir),
                        is_(False))
        self._test_fs_locator(DevFilesystemLocator(), _check)
