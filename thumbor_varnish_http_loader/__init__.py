#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2014 voxmedia.com

import re
from urlparse import urlparse
from functools import partial

import tornado.httpclient

from thumbor.loaders LoaderResult
from thumbor.utils import logger
from thumbor.loaders import http_loader
from tornado.concurrent import return_future


def _normalize_url(url):
    if not url.startswith('http'):
        url = 'http://%s' % url

    if not context.config.VARNISH_SOURCES_TO_PROXY:
        return url

    parsed_url = urlparse(url)
    for pattern in context.config.VARNISH_SOURCES_TO_PROXY:
        if re.match('^%s$' % pattern, parsed_url.hostname):
            return re.sub(pattern, context.config.VARNISH_HOST, url, 1)

    return url if url.startswith('http') else 'http://%s' % url


def validate(context, url, normalize_url_func=_normalize_url):
    return http_loader.validate(context, url, normalize_url_func=_normalize_url)


def return_contents(response, url, callback, context):
    result = LoaderResult()

    context.metrics.incr('original_image.status.' + str(response.code))
    if response.error:
        result.successful = False
        if response.code == 599:
            raise tornado.web.HTTPError(503)
            result.error = LoaderResult.ERROR_TIMEOUT
        else:
            result.error = LoaderResult.ERROR_NOT_FOUND
            callback(None)

        logger.warn("ERROR retrieving image {0}: {1}".format(url, str(response.error)))

    elif response.body is None or len(response.body) == 0:
        result.successful = False
        result.error = LoaderResult.ERROR_UPSTREAM
        logger.warn("ERROR retrieving image {0}: Empty response.".format(url))
        callback(None)

    else:
        if response.time_info:
            for x in response.time_info:
                context.metrics.timing('original_image.time_info.' + x, response.time_info[x] * 1000)
            context.metrics.timing('original_image.time_info.bytes_per_second', len(response.body) / response.time_info['total'])
        result.buffer = response.body

    callback(result)

@return_future
def load(context, url, callback, normalize_url_func=_normalize_url):
    return http_loader.load_sync(context, url, callback, normalize_url_func=_normalize_url)

def encode(string):
    return http_loader.encode(string)
