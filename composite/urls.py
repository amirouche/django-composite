from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url as django_url

from collections import namedtuple

UrlInfo = namedtuple('UrlInfo', ('path', 'view', 'initkwargs', 'name'))
CollectionInfo = namedtuple('CollectionInfo', ('path', 'collection_class', 'instance_namespace', 'initkwargs'))


class UrlCollection(object):

    application_namespace = None

    def __init__(self, application_namespace=None, instance_namespace=None):
        self.urls = list()
        self.instance_namespace = instance_namespace
        self._application_namespace = application_namespace if application_namespace else self.application_namespace

    def add_view(self, path, view, initkwargs=None, name=None):
        initkwargs = initkwargs if initkwargs else dict()
        url = UrlInfo(path, view, initkwargs, name)
        self.urls.append(url)

    def add_collection(self, path, collection_class=None, instance_namespace=None, initkwargs=None):
        initkwargs = initkwargs if initkwargs else dict()
        url = CollectionInfo(path, collection_class, instance_namespace, initkwargs)
        self.urls.append(url)

    def include_urls(self):
        urls = list()
        for url in self.urls:
            if isinstance(url, UrlInfo):
                if hasattr(url.view, 'as_view'):
                    urls.append(django_url(url.path, url.view.as_view(**url.initkwargs), name=url.name))
                else:
                    urls.append(django_url(url.path, url.view, url.initkwargs, url.name))
            else:
                collection = url.collection_class(instance_namespace=url.instance_namespace, **url.initkwargs)
                include_urls = collection._include_urls()
                urls.append((url.path, include_urls))
        return include(patterns('', *urls), self._application_namespace, self.instance_namespace)
