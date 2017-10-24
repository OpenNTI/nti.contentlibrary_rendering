#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.base.interfaces import ILastModified

from nti.contentlibrary_rendering.model import ContentPackageRenderJob

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderJob

from nti.contentlibrary_rendering.tests import ContentlibraryRenderingLayerTest


class TestModel(ContentlibraryRenderingLayerTest):

    def test_job(self):
        job = ContentPackageRenderJob()
        job.JobId = u'foo'
        job.State = u'Failed'
        job.PackageNTIID = u'tag:nextthought.com,2011-10:USSC-HTML-Cohen.cohen_v._california.'
        assert_that(job, validly_provides(ILastModified))
        assert_that(job, validly_provides(IContentPackageRenderJob))
        assert_that(job, verifiably_provides(IContentPackageRenderJob))
