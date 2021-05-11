#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.component.zcml import utility

from nti.asynchronous import get_job_queue as async_queue

from nti.asynchronous.interfaces import IRedisQueue

from nti.asynchronous.redis_queue import PriorityQueue as RedisQueue

from nti.asynchronous.scheduled import ImmediateQueueRunner
from nti.asynchronous.scheduled import NonRaisingImmediateQueueRunner

from nti.contentlibrary_rendering import QUEUE_NAMES

from nti.contentlibrary_rendering.interfaces import IContentQueueFactory

from nti.coremetadata.interfaces import IRedisClient

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IContentQueueFactory)
class _ImmediateQueueFactory(object):

    def get_queue(self, unused_name):
        return ImmediateQueueRunner()


@interface.implementer(IContentQueueFactory)
class _TestImmediateQueueFactory(object):

    def get_queue(self, unused_name):
        return NonRaisingImmediateQueueRunner()


@interface.implementer(IContentQueueFactory)
class _AbstractProcessingQueueFactory(object):

    queue_interface = None

    def get_queue(self, name):
        queue = async_queue(name, self.queue_interface)
        if queue is None:
            msg = "No queue exists for content rendering queue (%s)." % name
            raise ValueError(msg)
        return queue


class _ContentRenderingQueueFactory(_AbstractProcessingQueueFactory):

    queue_interface = IRedisQueue

    def __init__(self, _context):
        for name in QUEUE_NAMES:
            queue = RedisQueue(self._redis, name)
            utility(_context, provides=IRedisQueue, component=queue, name=name)

    def _redis(self):
        return component.getUtility(IRedisClient)


def registerImmediateProcessingQueue(_context):
    logger.info("Registering immediate content rendering queue")
    factory = _ImmediateQueueFactory()
    utility(_context, provides=IContentQueueFactory, component=factory)


def registerTestImmediateProcessingQueue(_context):
    logger.info("Registering immediate content rendering queue")
    factory = _TestImmediateQueueFactory()
    utility(_context, provides=IContentQueueFactory, component=factory)


def registerProcessingQueue(_context):
    logger.info("Registering content rendering redis queue")
    factory = _ContentRenderingQueueFactory(_context)
    utility(_context, provides=IContentQueueFactory, component=factory)
