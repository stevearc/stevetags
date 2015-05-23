""" WSGI middleware for adding modern security headers to HTTP responses. """
import re
from fnmatch import fnmatch


class SecurityHeaders(object):

    def __init__(self, app, config=None, frame_options=None,
                 xss_protection=None, content_type_options=None,
                 content_security_policy=None, strict_transport_security=None,
                 **kwargs):
        self.app = app
        self.frame_options = frame_options
        self.xss_protection = xss_protection
        self.content_type_options = content_type_options
        self.content_security_policy = content_security_policy
        self.strict_transport_security = strict_transport_security
        self.glob_csp = {}
        for key, value in kwargs.iteritems():
            if key.startswith('csp.'):
                name = key[4:]
                self.glob_csp[kwargs['csp_path.' + name]] = value

    def _merge_csp(self, csp, nonce):
        if nonce is None:
            return csp
        return re.sub(
            r'script-src ([^;]+)',
            r"script-src \1 nonce-%s" %
            nonce,
            csp)

    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            csp_nonce = None
            path = environ['PATH_INFO']
            webpage = False
            i = 0
            while i < len(headers):
                header = headers[i]
                if header[0] == 'Content-Type':
                    webpage = header[1].split(';')[0].strip() == 'text/html'
                elif header[0] == 'X-CSP-Nonce':
                    csp_nonce = header[1]
                    del headers[i]
                    continue
                i += 1
            if webpage:
                if self.frame_options is not None:
                    headers.append(('X-Frame-Options', self.frame_options))
                if self.xss_protection is not None:
                    headers.append(('X-XSS-Protection', self.xss_protection))
                if self.content_type_options is not None:
                    headers.append(
                        ('X-Content-Type-Options', self.content_type_options))
                has_csp = False
                for pattern, csp in self.glob_csp.iteritems():
                    if fnmatch(path, pattern):
                        headers.append(('Content-Security-Policy',
                                        self._merge_csp(csp, csp_nonce)))
                        has_csp = True
                        break
                if self.content_security_policy is not None and not has_csp:
                    headers.append(
                        ('Content-Security-Policy',
                         self._merge_csp(
                             self.content_security_policy,
                             csp_nonce)))
                if self.strict_transport_security is not None:
                    headers.append(
                        ('Strict-Transport-Security',
                         self.strict_transport_security))

            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)
