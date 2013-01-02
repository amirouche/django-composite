import sys

from types import MethodType
from types import FunctionType

from collections import namedtuple

from django.conf.urls import url as django_url
from django.conf.urls import include
from django.conf.urls import patterns
from django.views.generic import TemplateView
from django.template.response import TemplateResponse

from utils import OrderedSet


class AutoRenderTemplateResponse(TemplateResponse):
    """Reponse that can rendered in a template"""

    def __str__(self):
        self.render()
        return self.content


class MetaComposite(type):

    def __new__(meta, name, bases, attrs):
        cls = type.__new__(meta, name, bases, attrs)

        cls.css_files = OrderedSet()
        cls.javascript_files = OrderedSet()

        for base in bases:
            for attr_name in ['css_files', 'javascript_files']:
                attr = getattr(cls, attr_name)
                try:
                    map(attr.add, attrs[attr_name])
                except KeyError:
                    pass

        try:
            composites = cls.composites_class()
        except AttributeError:
            pass
        else:
            has_post = False
            for composite in composites:
                map(cls.javascript_files.add, composite.javascript_files)
                map(cls.css_files.add, composite.css_files)

                if hasattr(composite, 'post'):
                    has_post = True

            if has_post:
                def post(self, request, *args, **kwargs):
                    context = self.get_context_data(**kwargs)
                    context.update(self.get_composites_responses(request, *args, **kwargs))
                    return self.render_to_response(context)
                cls.post = MethodType(post, None, cls)

        return cls


class Composite(TemplateView):

    __metaclass__ = MetaComposite

    response_class = AutoRenderTemplateResponse

    css_files = []
    javascript_files = []

    def __init__(self, parent=None, *args, **kwargs):
        super(Composite, self).__init__(**kwargs)
        self.parent = parent
        self.get_composites()

    def __call__(self, request, *args, **kwargs):
        if hasattr(self, 'get') and not hasattr(self, 'head'):
            self.head = self.get
        return self.dispatch(request, *args, **kwargs)

    def get_context_data(self):
        context = super(Composite, self).get_context_data()
        context['css_files'] = self.css_files
        context['javascript_files'] = self.javascript_files
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update(self.get_composites_responses(request, *args, **kwargs))
        return self.render_to_response(context)


class StackedComposite(Composite):

    composites = list()

    @classmethod
    def composites_class(self):
        for CompositeClass in self.composites:
            if isinstance(CompositeClass, (tuple, list)):
                yield CompositeClass[0]
            else:
                yield CompositeClass

    def get_composites(self):
        try:
            return self._composites
        except AttributeError:
            self._composites = list()
            for CompositeClass in self.composites:
                if isinstance(CompositeClass, (tuple, list)):
                    args = list(CompositeClass[1:])
                    args.insert(0, self)
                    CompositeClass = CompositeClass[0]
                else:
                    args = (self,)
                composite = CompositeClass(*args)
                self._composites.append(composite)
            return self._composites

    def get_composites_responses(self, request, *args, **kwargs):
        responses = list()
        for composite in self.get_composites():
            response = composite(request, *args, **kwargs)
            responses.append(response)
        context = dict(composites=responses)
        return context


ViewInfo = namedtuple('ViewInfo', ('path', 'view', 'initkwargs', 'name'))
ViewCollectionInfo = namedtuple('ViewCollectionInfo', ('path', 'collection_class', 'instance_namespace', 'initkwargs'))

# borrowed from zope.interface.declarations._interface
def add_url(path, view, initkwargs=None, name=None):
    # XXX: comment taken from zope.interface:
    # This entire approach is invalid under Py3K.  Don't even try to fix
    # the coverage for this block there. :(
    frame = sys._getframe(1)
    locals = frame.f_locals

    # Try to make sure we were called from a class def. In 2.2.0 we can't
    # check for __module__ since it doesn't seem to be added to the locals
    # until later on.
    if locals is frame.f_globals or '__module__' not in locals:
        raise TypeError("url can be used only from a class url.")

    if 'urls' not in locals:
        locals['urls'] = list()
    initkwargs = initkwargs if initkwargs else dict()
    view = ViewInfo(path, view, initkwargs, name)
    locals['urls'].append(view)


def add_view_collection(path, collection_class, instance_namespace=None, initkwargs=None):
    frame = sys._getframe(1)
    locals = frame.f_locals

    # Try to make sure we were called from a class def. In 2.2.0 we can't
    # check for __module__ since it doesn't seem to be added to the locals
    # until later on.
    if locals is frame.f_globals or '__module__' not in locals:
        raise TypeError("url can be used only from a class url.")

    if 'urls' not in locals:
        locals['urls'] = list()

    initkwargs = initkwargs if initkwargs else dict()
    url = ViewCollectionInfo(path, collection_class, instance_namespace, initkwargs)
    locals['urls'].append(url)


class ViewCollection(object):

    application_namespace = None

    def __init__(self, instance_namespace=None):
        self.instance_namespace = instance_namespace

    @classmethod
    def include_urls(cls, instance_namespace=None, **kwargs):
        return cls(instance_namespace, **kwargs)._include_urls()

    def _include_urls(self):
        urls = list()
        for url in self.urls:
            if isinstance(url, ViewInfo):
                if type(url.view) == FunctionType:
                    urls.append(django_url(url.path, url.view, url.initkwargs, url.name))
                else:
                    urls.append(django_url(url.path, url.view, url.initkwargs, url.name))

            else:
                include_urls = url.collection_class.include_urls(url.instance_namespace, **url.initkwargs)
                urls.append((url.path, include_urls))
        return include(patterns('', *urls), self.application_namespace, self.instance_namespace)
