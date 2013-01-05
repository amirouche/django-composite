from types import FunctionType

from collections import namedtuple

from django.conf.urls import url as django_url
from django.conf.urls import include
from django.conf.urls import patterns
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.template.response import TemplateResponse

from utils import OrderedSet


class AutoRenderTemplateResponse(TemplateResponse):
    """Response that can be rendered in a template"""

    def __str__(self):
        self.render()
        return mark_safe(self.rendered_content)


class MetaComposite(type):

    def __new__(meta, name, bases, attrs):
        cls = type.__new__(meta, name, bases, attrs)

        cls.css_files = OrderedSet()
        cls.javascript_files = OrderedSet()

        for base in bases:
            for attr_name in ['css_files', 'javascript_files']:
                attr = getattr(cls, attr_name)
                map(attr.add, getattr(base, attr_name, list()))
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
                # if the composite has no post but a sub composite
                # has the parent composite must dispatch the request
                # to all sub composites so that the composite
                # that has a post method can have chance to answer
                # the sub composites that have not post method are
                # handled in get_composites_responses
                def post(self, request, *args, **kwargs):
                    context = self.get_context_data(**kwargs)
                    responses = self.get_composites_responses(request, *args, **kwargs)
                    for response in responses['composites']:
                        if isinstance(response, HttpResponseRedirect):
                            return response
                    context.update(responses)
                    return self.render_to_response(context)
                cls.post = post
        return cls


class Composite(TemplateView):

    __metaclass__ = MetaComposite

    response_class = AutoRenderTemplateResponse

    css_files = []
    javascript_files = []

    def __init__(self, parent=None, *args, **kwargs):
        super(Composite, self).__init__(**kwargs)
        self.parent = parent

    def __call__(self, request, *args, **kwargs):
        if hasattr(self, 'get') and not hasattr(self, 'head'):
            self.head = self.get
        return self.dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Composite, self).get_context_data(**kwargs)
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
            # process request
            # if the request is POST and the composite has not post method
            # it should be rendered as a GET so switch POST with GET
            # when it happens
            switched_method = False
            if request.method == 'POST' and not hasattr(composite, 'post'):
                request.method = 'GET'
                switched_method = True
            response = composite(request, *args, **kwargs)
            if switched_method:
                request.method = 'POST'
            responses.append(response)
        context = dict(composites=responses)
        return context


ViewInfo = namedtuple('ViewInfo', ('path', 'view', 'initkwargs', 'name'))
ViewCollectionInfo = namedtuple('ViewCollectionInfo', ('path', 'collection_class', 'instance_namespace', 'initkwargs'))


class ViewCollection(object):

    application_namespace = None

    def __init__(self, instance_namespace=None):
        self.urls = list()
        self.instance_namespace = instance_namespace
        self.collections = list()
        self.views = list()

    def add_view(self, path, view, initkwargs=None, name=None):
        initkwargs = initkwargs if initkwargs else dict()
        url = ViewInfo(path, view, initkwargs, name)
        self.urls.append(url)

    def add_collection(self, path, collection_class=None, instance_namespace=None, initkwargs=None):
        initkwargs = initkwargs if initkwargs else dict()
        url = ViewCollectionInfo(path, collection_class, instance_namespace, initkwargs)
        self.urls.append(url)

    def _include_urls(self):
        urls = list()
        for url in self.urls:
            if isinstance(url, ViewInfo):
                if isinstance(url.view, FunctionType):
                    urls.append(django_url(url.path, url.view, url.initkwargs, url.name))
                else:
                    view = url.view()
                    view.collection = self
                    self.views.append(view)
                    urls.append(django_url(url.path, view, url.initkwargs, url.name))
            else:
                collection = url.collection_class(url.instance_namespace, **url.initkwargs)
                collection.collection = self
                self.collections.append(collection)
                include_urls = collection._include_urls()
                urls.append((url.path, include_urls))
        return include(patterns('', *urls), self.application_namespace, self.instance_namespace)
