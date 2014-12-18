# Thumbor Varnish HTTP Loader

This Thumbor HTTP loader plugin is designed to rewrite incoming urls to instead make requests to
an appropriately configured Varnish server. The purpose of this is to defer the responsibility
of caching unprocessed images to a different software and server.

In short, this plugin acts just like the default Thumbor HTTP loader except on source
urls that match `VARNISH_SOURCES_TO_PROXY`, it will replace the host with `VARNISH_HOST`

Additional Thumbor configuration values used:

- `VARNISH_HOST` The host of the varnish server.  
- `VARNISH_SOURCES_TO_PROXY` Expects an array of regexes, just like `ALLOWED_SOURCES`
