#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import shutil
import tempfile

from zope.component.hooks import setHooks

from zope import component

import zope.testing.cleanup

from nti.contentlibrary.interfaces import IContentUnitAnnotationUtility

from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin


def setChameleonCache(cls):
    cls.old_cache_dir = os.getenv('CHAMELEON_CACHE')
    cls.new_cache_dir = tempfile.mkdtemp(prefix="cham_")
    os.environ['CHAMELEON_CACHE'] = cls.new_cache_dir


def restoreChameleonCache(cls):
    shutil.rmtree(cls.new_cache_dir, True)
    os.environ['CHAMELEON_CACHE'] = cls.old_cache_dir


class ContentlibraryRenderingTestLayer(ZopeComponentLayer,
                                       ConfiguringLayerMixin):

    set_up_packages = ('nti.containers',
                       'nti.contentlibrary',
                       'nti.externalization',
                       'nti.contentlibrary_rendering',
                       'nti.contenttypes.presentation')

    @classmethod
    def setUp(cls):
        setChameleonCache(cls)
        setHooks()  # in case something already tore this down
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, test=None):
        # If we installed any annotations, clear them, since
        # they are tracked by NTIID and would otherwise persist
        annotations = component.getUtility(IContentUnitAnnotationUtility)
        annotations.annotations.clear()

    @classmethod
    def testTearDown(cls):
        restoreChameleonCache(cls)

import unittest

from nti.testing.base import AbstractTestBase


class ContentlibraryRenderingLayerTest(unittest.TestCase):

    layer = ContentlibraryRenderingTestLayer

    get_configuration_package = AbstractTestBase.get_configuration_package.__func__
