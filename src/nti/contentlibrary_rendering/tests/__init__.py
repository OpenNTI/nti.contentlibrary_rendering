#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from zope.component.hooks import setHooks

from zope import component

import zope.testing.cleanup

from nti.contentlibrary.interfaces import IContentUnitAnnotationUtility

from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin


class ContentlibraryRenderingTestLayer(ZopeComponentLayer,
                                       ConfiguringLayerMixin):

    set_up_packages = ('nti.containers',
                       'nti.contentlibrary',
                       'nti.externalization',
                       'nti.contentlibrary_rendering',
                       'nti.contenttypes.presentation')

    @classmethod
    def setUp(cls):
        setHooks()  # in case something already tore this down
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, unused_test=None):
        # If we installed any annotations, clear them, since
        # they are tracked by NTIID and would otherwise persist
        annotations = component.getUtility(IContentUnitAnnotationUtility)
        annotations.annotations.clear()

    @classmethod
    def testTearDown(cls):
        pass

import unittest

from nti.testing.base import AbstractTestBase


class ContentlibraryRenderingLayerTest(unittest.TestCase):

    layer = ContentlibraryRenderingTestLayer

    get_configuration_package = AbstractTestBase.get_configuration_package.__func__
