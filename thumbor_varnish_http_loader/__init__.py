#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2014 voxmedia.com

import re
from urlparse import urlparse
from functools import partial

import tornado.httpclient

from thumbor.utils import logger


def _normalize_url(context, url):
    if not url.startswith('http'):
      url = 'http://%s' % url

    if not context.config.VARNISH_SOURCES_TO_PROXY:
        return url

    parsed_url = urlparse(url)
    for pattern in context.config.VARNISH_SOURCES_TO_PROXY:
      regex = '^%s$' % pattern
      if re.match(regex, parsed_url.hostname):
        return re.sub(regex, context.config.VARNISH_HOST, url)

    return url

def validate(context, url):
    url = _normalize_url(context, url)
    res = urlparse(url)

    if not res.hostname:
        return False

    if not context.config.ALLOWED_SOURCES:
        return True

    for pattern in context.config.ALLOWED_SOURCES:
        if re.match('^%s$' % pattern, res.hostname):
            return True

    return False


def return_contents(response, url, callback, context):
    context.statsd_client.incr('original_image.status.' + str(response.code))
    if response.error:
        logger.warn("ERROR retrieving image {0}: {1}".format(url, str(response.error)))
        if response.code == 599:
          raise tornado.web.HTTPError(503)
        else:
          callback(None)
    elif response.body is None or len(response.body) == 0:
        logger.warn("ERROR retrieving image {0}: Empty response.".format(url))
        callback(None)
    else:
        for x in response.time_info:
            context.statsd_client.timing('original_image.time_info.' + x, response.time_info[x] * 1000)
        context.statsd_client.timing('original_image.time_info.bytes_per_second', len(response.body) / response.time_info['total'])
        callback(response.body)


def load(context, url, callback):
    tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    client = tornado.httpclient.AsyncHTTPClient()

    user_agent = None
    if context.config.HTTP_LOADER_FORWARD_USER_AGENT:
        if 'User-Agent' in context.request_handler.request.headers:
            user_agent = context.request_handler.request.headers['User-Agent']
    if user_agent is None:
        user_agent = context.config.HTTP_LOADER_DEFAULT_USER_AGENT

    url = _normalize_url(url)
    req = tornado.httpclient.HTTPRequest(
        url=encode(url),
        connect_timeout=context.config.HTTP_LOADER_CONNECT_TIMEOUT,
        request_timeout=context.config.HTTP_LOADER_REQUEST_TIMEOUT,
        follow_redirects=context.config.HTTP_LOADER_FOLLOW_REDIRECTS,
        max_redirects=context.config.HTTP_LOADER_MAX_REDIRECTS,
        user_agent=user_agent,
        proxy_host=encode(context.config.HTTP_LOADER_PROXY_HOST),
        proxy_port=context.config.HTTP_LOADER_PROXY_PORT,
        proxy_username=encode(context.config.HTTP_LOADER_PROXY_USERNAME),
        proxy_password=encode(context.config.HTTP_LOADER_PROXY_PASSWORD),
        ca_certs=encode(context.config.HTTP_LOADER_CA_CERTS),
        client_key=encode(context.config.HTTP_LOADER_CLIENT_KEY),
        client_cert=encode(context.config.HTTP_LOADER_CLIENT_CERT)
    )

    client.fetch(req, callback=partial(return_contents, url=url, callback=callback, context=context))

def encode(string):
    return None if string is None else string.encode('ascii')
