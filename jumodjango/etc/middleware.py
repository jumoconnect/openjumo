from cStringIO import StringIO
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.core.urlresolvers import resolve, reverse
from django.db import connections
from django.http import Http404, HttpResponseRedirect, HttpResponsePermanentRedirect, get_host
from etc import cache
from etc.constants import ACCOUNT_COOKIE_SALT, ACCOUNT_COOKIE, SOURCE_COOKIE
from etc.user import check_cookie
import logging, os, sys, tempfile
import logging.handlers
import re
from users.models import User
from urlparse import urlsplit, urlunsplit

class DetectUserMiddleware(object):
    def process_request(self, request):
        if ACCOUNT_COOKIE in request.COOKIES and ACCOUNT_COOKIE_SALT in request.COOKIES:
            if check_cookie(request.COOKIES[ACCOUNT_COOKIE], request.COOKIES[ACCOUNT_COOKIE_SALT]):
                try:
                    request.user = cache.get(User, int(request.COOKIES[ACCOUNT_COOKIE]))
                    return None
                except:
                    pass

        request.user = AnonymousUser()
        return None

class AddExceptionMessageMiddleware(object):
    def process_exception(self, request, exception):
        request.exception = exception
        return None

class ConsoleExceptionMiddleware(object):
    """from http://www.djangosnippets.org/snippets/420/"""
    def process_exception(self, request, exception):
        # only process if we are in debug mode and this isn't a vanilla 404.
        if settings.DEBUG and not isinstance(exception, Http404):
            import traceback
            import sys
            exc_info = sys.exc_info()
            print "######################## Exception #############################"
            print '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
            print "################################################################"
            if getattr(settings, 'CONSOLE_MIDDLEWARE_DEBUGGER', False):
                # stop in the debugger with an exception post-mortem
                import pdb
                pdb.post_mortem(exc_info[2])

class MultipleProxyMiddleware(object):
    FORWARDED_FOR_FIELDS = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_FORWARDED_HOST',
        'HTTP_X_FORWARDED_SERVER',
    ]

    def process_request(self, request):
        """
        Rewrites the proxy headers so that only the most
        recent proxy is used.
        """
        for field in self.FORWARDED_FOR_FIELDS:
            if field in request.META:
                if ',' in request.META[field]:
                    parts = request.META[field].split(',')
                    request.META[field] = parts[-1].strip()

class LogExceptions(object):
    def __init__(self):
        log_file = getattr(settings, 'EXCEPTION_LOG_LOCATION', '/cloud/logs/django-exception-log')

        if not log_file:
            self.logger = None
            return

        log_file = log_file + '-' + str(os.getpid())

        self.logger = logging.getLogger('DjangoExceptionLogger')
        self.logger.setLevel(logging.ERROR)
        handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=1024*1024*20, backupCount=5)
        self.logger.addHandler(handler)

    def process_exception(self, request, exception):
        if not self.logger or isinstance(exception, Http404):
            return

        self.logger.error(
              "***************************************************\n"
              "Timestamp: %s\n"
              "Exception encountered in django request:\n\t %s \n"
              "GET params: %s\n"
              "POST params: %s\n"
              "Exception %s\n"
              "Message: %s\n"
              "Traceback: \n %s\n\n"
              "***************************************************\n",
              time.strftime("%Y-%m-%d %H:%M:%S"),
              request.get_full_path(),
              request.GET,
              request.POST,
              exception.__class__.__name__,
              getattr(exception, 'message', ''),
              traceback.format_exc()
         )


def secure(func):
    """ Decorator for secure views. """
    def _secure(*args, **kwargs):
        return func(*args, **kwargs)
    _secure.is_secure = True
    _secure.__name__ = func.__name__
    return _secure


HREF_PATTERN = re.compile(r"""(?P<attribute>href|src)\s*=\s*["'](?P<url>[^"']+)["']""", re.IGNORECASE)
class SSLMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        is_secure = "https" == request.META.get("HTTP_X_FORWARDED_PROTO", "http")
        needs_secure = self._resolves_to_secure_view(request.path)
        if needs_secure != is_secure and not settings.IGNORE_HTTPS:
            return self._redirect(request, needs_secure)
        return None

    def process_response(self, request, response):
        if response['Content-Type'].find('html') >= 0:
            protocol = request.META.get("HTTP_X_FORWARDED_PROTO", "http")
            #Only deal with https.
            if protocol == "http":
                return response

            def rewrite_url(match):
                attribute = match.groupdict()["attribute"]
                split_url = urlsplit(match.groupdict()["url"])
                if split_url.scheme == 'javascript' and request.path.startswith(reverse('admin:index')):
                    return '%s="%s"' % (attribute, split_url.geturl())
                host = split_url.netloc if split_url.netloc else settings.HTTP_HOST
                request_path = request.path if request.path and request.path[-1] != "/" else request.path[:-1]
                path = split_url.path if split_url.path and split_url.path[0] == "/" else "%s/%s" % (request_path, split_url.path)
                new_url = urlunsplit((protocol, host, path, split_url[3],split_url[4]))
                return '%s="%s"' % (attribute, new_url)
            try:
                decoded_content = response.content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_content = response.content
            response.content = \
                HREF_PATTERN.sub(rewrite_url, decoded_content).encode('utf-8')
        return response

    def _redirect(self, request, needs_secure):
        protocol = needs_secure and "https" or "http"
        new_url = self._add_protocol(request, protocol)
        if settings.DEBUG and request.method == "POST":
            raise RuntimeError, "CAN'T REDIRECT SSL WITH POST DATA!!"
        return HttpResponseRedirect(new_url)

    def _add_protocol(self, request, protocol):
        return "%s://%s%s" % (protocol, get_host(request), request.get_full_path())

    def _resolves_to_secure_view(self, url):
        try:
            view_func, args, kwargs = resolve(url)
        except:
            return None
        else:
            return getattr(view_func, 'is_secure', False)


class TerminalLogging:
    def process_response(self, request, response):
        from sys import stdout
        if stdout.isatty():
            for query in connections['default'].queries :
                print "\033[1;31m[%s]\033[0m \033[1m%s\033[0m" % (query['time'],
 " ".join(query['sql'].split()))
        return response

class SourceTagCollectionMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.GET.has_key('src'):      # This is a QueryDict, so src can be multiple GET params
            url_params = request.GET.copy() # Immutable
            sources = url_params.pop('src')
            new_qs = url_params.urlencode()
            redirect = HttpResponseRedirect('%s?%s' % (request.path, new_qs))
            redirect.set_cookie(SOURCE_COOKIE, request.GET.urlencode())
            return redirect
        return None
