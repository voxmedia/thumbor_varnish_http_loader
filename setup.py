# coding: utf-8

from setuptools import setup, find_packages

setup(
	name = 'thumbor_varnish_http_loader',
	version = "1",
	description = 'Thumbor HTTP Loader, using Varnish as a cache',
	author = 'Clif Reeder',
	author_email = 'clif@voxmedia.com',
	zip_safe = False,
	include_package_data = True,
	packages=find_packages(),
	requires=['thumbor']
)
