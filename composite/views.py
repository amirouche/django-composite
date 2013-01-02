from types import MethodType

from django.views.generic import TemplateView
from django.conf.urls import patterns, url, include
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


def duplicate(view, name):
    """create a new class based on ``view`` and append ``name`` to its name"""
    name = '%s%s' % (view.__name__, name)
    duplicate = type(name, (view,), dict())
    return duplicate


class ClassBasedViewCollection(object):

    application_namespace = None

    def __init__(self, instance_namespace=None):
        self.urlpatterns = patterns()
        self.instance_namespace = instance_namespace

    def add_view(self, path, view, name=None):
        # duplicate the view so that it possible to reference
        # the collection in the view without risks
        new_view = duplicate(view, type(self).__name__)
        new_view.collection = self
        self.urlpatterns += patterns(url(path, view, name=name))

    def add_collection(self, path, collection):
        self.urlpatterns += patterns(path, collection.include_urlpatterns())

    def include_urlpatterns(self):
        return include((self.urlpatterns, self.application_namespace, self.instance_namespace))
