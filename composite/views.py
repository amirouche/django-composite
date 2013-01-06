"""
There is two types of composites:

- leaf composites which marks the end of the hierarchy at some point
- inner composites which are rendered via the rendering of other
  composites which can be either leafs or other inner composites.

It was the general case.

Now, most of the time the composite tree is one level deep.
Hence you will only need one inner composite which will be a called
the root composite since it's the first in the hierarchy and it's the
one you register against the url router. It can be a
``StackedCompositeView`` or ``NamespacedCompositeView`` or
if you have forms in the page your are rendering
``StackedCompositeViewWithPost`` or ``NamespacedCompositeViewWithPost``.
The remaining composites will most likely be ``LeafCompositeView``
or a generic class based view which also inherits the
``RenderableTemplateViewMixin``, except this little inheritance
leaf composite have nothing particular in their working you code
them just like you would code another class based view.

Also you can always render and process a form in a inner composite,
ie. not a leaf, but it's preferable to move the form to its own
leaf composite. Say you have the following composite hierarchy:

(TBD)

In this case ``B1`` has a form, you can use the following hierarchy
instead:

(TBD)

Where ``b`` is a leaf composite with the form from the initial ``B1``.
The code involved in writring ``B1`` is more complex that ``B2`` and ``b``
and you will be able to reuse ``b`` which is probably not the case of ``B1``.

Also you might need to mix both ``StackedCompositeView*`` and
``NamespacedCompositeView*``, the latter leading to similar code as the one
you would get using *include template tags*.
"""
from types import FunctionType

from collections import namedtuple

from django.conf.urls import url as django_url
from django.conf.urls import include
from django.conf.urls import patterns
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.template.response import TemplateResponse


class RenderableTemplateResponseMixin(object):
    """Mixin that makes a TemplateResponse or one of its subclass
    renderable in a template.
    """

    def __str__(self):
        self.render()
        return mark_safe(self.rendered_content)


class RenderableTemplateResponse(RenderableTemplateResponseMixin, TemplateResponse):
    """Renderable in template TemplateResponse

    Use this in a generic class based view as ``response_class`` to make it
    possible to be part of a composite hierarchy, it turns a generic class
    based view that inherits ``TemplateResponseMixin`` into leaf composite
    view.

    For instance:

    .. code-block:: python

       from django.views.generic import ListView

       from composite.views import RenderableTemplateResponseMixin


       class LeafCompositeListView(ListView):

           response_class = RenderableTemplateResponse

    Make it possible to use ``ListView`` as a leaf in composite hierarchy.

    See also ``LeafCompositeView``.

    If you already use another ``response_class`` you will need
    to use ``RenderableTemplateResponseMixin``.
    """
    pass


class RenderableTemplateViewMixin(object):
    """This is a way to turn a ``TemplateView``-like into a leaf composite.

    .. warning::

       It must appear before any class that inherits ``TemplateResponseMixin``.

    You can use it like this:

    .. code-block:: python

       from django.views.generic import ListView

       from composite.views import RenderableTemplateViewMixin


       class LeafCompositeListView(ListView, RenderableTemplateViewMixin):
           pass
    """
    response_class = RenderableTemplateResponse


class LeafCompositeView(RenderableTemplateViewMixin, TemplateView):
    """A TemplateView class that can be rendered in a template
    and from which inherits other composite classes.

    Use this class when you don't need to render sub-composites
    hence the name *leaf composite*.

    This class and any other subclass are called composite views.

    Since it's a ``TemplateView`` it takes a ``template_name``
    class attribute that is used to render the template, you
    can also override ``get_template_names(self)``.

    Just like a ``TemplateView`` the class is populated with the
    dictionary returned by ``get_context_data(self, **kwargs)``
    which only contains ``self`` the view object.

    There is nothing specific to this class except it accepts
    a parent object parameter in its constructor and use a
    ``RenderableTemplateResponse`` as ``response_class`` so that
    you can render it and its subclasses easly in templates"""

    parent = None

    def __init__(self, **initkwargs):
        """Takes a ``parent`` argument the parent composite view object"""
        # This is done here because the view is not called using the normal
        # ``View.as_view`` method see ``__call__``.
        self.parent = initkwargs.pop('parent', None)
        for key in initkwargs:
            if key in self.http_method_names:
                raise TypeError("You tried to pass in the %s method name as a "
                                "keyword argument to %s(). Don't do that."
                                % (key, self.__class__.__name__))
            if not hasattr(self, key):
                msg = "%s() received an invalid keyword %r" % (
                    self.__class__.__name__,
                    key
                )
                raise TypeError(msg)
        super(LeafCompositeView, self).__init__(**initkwargs)

    def __call__(self, request, *args, **kwargs):
        # It's not possible to use ``View.as_view`` as is so that a
        # subcomposite can correctly handle a request so it's done here.
        # There is no problem regarding threadsafety since subcomposite are
        # instantiated on a per request basis
        # The problem is regarding the override of the ``request.method``
        # that is done based on the composite class view which is not
        # accessible when you use ``as_view``
        # so we do ``as_view.view`` work here
        if hasattr(self, 'get') and not hasattr(self, 'head'):
            self.head = self.get
        return self.dispatch(request, *args, **kwargs)

    def root(self):
        """Returns the root composite view object"""
        current = self
        while current.parent:
            current = current.parent
        return current


class AbstractCompositeView(LeafCompositeView):
    """Abstract class you have to subclass to create a composite class
    that can render other composites.

    see ``CompositeHierarchyHasPostMixin``."""

    def composites_responses(self, request, *args, **kwargs):
        """Must return a map-like object with the responses of the sub
        composites or an ``HttpResponseRedirect``.

        If this method doesn't return ``HttpResponseRedirect`` it is assumed
        that the template can be rendered with the map-like object of
        responses as values. Regarding the responses, the convention is to be
        able to render them with the template render syntax ``{{ composite }}``
        so the responses can be a string or string-like,
        see ``RenderableTemplateResponseMixin``.
        """
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        """Retrieve the context, retrieve the responses from subcomposites
        if one of them is a redirect it's returned else all the responses
        are added to the context of template and the template rendered.
        """
        context = self.get_context_data(**kwargs)
        responses = self.composites_responses(request, *args, **kwargs)
        if isinstance(responses, HttpResponseRedirect):
            return responses
        else:
            context.update(responses)
            return self.render_to_response(context)


class CompositeHierarchyHasPostMixin(object):
    """Must be added to any inner composite class, ie. not leafs, that
    participate in POST requests.

    I did not find a way to reliably guess if there is a ``post`` method
    in a hierarchy of composites given the fact that composites can
    be different depending on the request (for instance based on
    user permissions).

    Instead a hierarchy that has at least one composite
    with a ``post`` method must have every inner composites classes inherit
    from this mixin.

    If you create your own composite class, you also need to take care
    of the fact that a composite can receive a POST request in
    ``composites_responses`` and switch to a ``GET`` if the subcomposite
    has no ``post`` method. This is done for you in ``StackedCompositeView``
    and ``NamespacedCompositeView``.

    This is most useful if you use class based generic views provided by
    Django if you are used to use your own classes you probably only need
    to use ``*ViewWithPost`` classes

    This does nothing big magic, it forwards the request to ``get``
    because in the case where the composite did not override the ``post``
    method it is the same logic than ``get``. Otherwise, if the composite
    needs to process a submitted form, it must:

    - check that it's really the form it is concerned about or call ``get``
    - process the form return a redirect if it is good
    - handle the rendering of the subcomposites, don't forget to put the form
      in context before rendering
    - return the response

    It can look like:

    .. code-block:: python

       def post(self, request, *args, **kwargs):
           if '_this_composite_submit_button_name' in request.POST:
               form = ActionForm(request.POST)
               if form.is_valid():
                   # do things interesting here
                   return redirect('index')
               else:  # bad thing happens
                   # here the code is similar to ``get`` except
                   # you have to override the form that is
                   # returned by ``get_context_data``
                   # and don't need to care about redirects since
                   # at this point you know to which composite the form
                   # was submitted to, namely ``self``.
                   context = self.get_context_data(**kwargs)
                   responses = self.get_composites_responses(request, *args, **kwargs)
                   context.update(responses)
                   context['form'] = form  # form with errors
                   return self.render_to_response(context)

           else:  # the submitted form is for another composite
               return self.get(request, *args, **kwargs)
    """

    def post(self, request, *args, **kwargs):
        """If this is not overriden, the response is the same as a ``GET``
           so forward to ``get``"""
        return self.get(request, *args, **kwargs)


class StackedCompositeView(AbstractCompositeView):
    """Populates a template context with a list of composites in
    ``composites`` variable.

    It does not define a default template, you must provide one,
    the simplest template looks like:

    .. code-block:: html

       {% for composite in composites %}
           {{ composite }}
       {% endfor %}

    Composites are instantiated in order from ``self.composites``
    It must be an iterable over items that can be of two kinds:

    - class objects that inherits ``LeafCompositeView``
    - tuples with a composite view class by a dictionary that are
      used to initialize the composite class

    A StackedComposite subclass can look like:

    .. code-block:: python

       from composite.views import StackedCompositeView


       class Dashboard(StackedCompositeView):

           template = 'example_app/dashboard.html'
           composites = (
               (WelcomeMessage, dict(hello='Hello you', greeting='How are you?'))
               LastestArticles,
            )

    It assumed that ``WelcomeMessage`` takes other keywords
    arguments besides the parent composite which in this
    case will be a ``Dashboard`` object, which means ``WelcomeMessage``
    is instantiated like this:

    .. code-block:: python

       welcome_message = WelcomeMessage(parent=self, hello='Hello you', greeting='How are you?')

    Where ``self`` is the ``Dashboard`` object for which the composite is
    instantiated for.

    If you need anything more than that, you will need to override
    ``_composites(self, request, *args, **kwargs)`` method.

    .. warning::

       A ``StackedCompositeView`` doesn't offer any particular machinery
       to work with forms.
       This class doesn't handle post request as a root node or an inner
       node, see ``StackedCompositeViewWithPost`` if you want to use forms.
    """

    composites = list()

    def _composites(self, request, *args, **kwargs):
        """Generator over instantiated sub composite classes"""
        for CompositeClass in self.composites:
            if isinstance(CompositeClass, (tuple, list)):
                initkwargs = CompositeClass[1]
                initkwargs['parent'] = self
                CompositeClass = CompositeClass[0]
            else:
                initkwargs = dict(parent=self)
            composite = CompositeClass(**initkwargs)
            yield composite

    def composites_responses(self, request, *args, **kwargs):
        """Returns a dictionary with a ``composites`` key populated
        with the answers of every composites.
        """
        responses = list()
        for composite in self._composites(request, *args, **kwargs):
            response = composite(request, *args, **kwargs)
            responses.append(response)
        context = dict(composites=responses)
        return context


class StackedCompositeViewWithPost(StackedCompositeView, CompositeHierarchyHasPostMixin):
    """If there is at least one post method in your composite hierarchy you
    must use this class if you want to render stacked composites

    It's not the prefered method but you can also handle form with this class
    refer to ``CompositeHierarchyHasPostMixin`` documentation.
    """

    def composites_responses(self, request, *args, **kwargs):
        """Returns a dictionary with a ``composites`` key populated
        with the answers of every composites.
        """
        responses = list()
        for composite in self._composites(request, *args, **kwargs):
            # if the request is POST and the composite has no post method
            # it should be rendered as a GET so switch POST with GET
            # when it happens
            # This assumes the developper correctly inherited every inner
            # composite with ``CompositeHierarchyHasPostMixin`` or one
            # of its subclass, if it not the case the following code
            # will turn the request from GET to POST and will never hit
            # the ``post`` method that should process the form.
            # All this can bring some headaches...
            # If you are this developper, cheers :)
            switched_method = False
            if request.method == 'POST' and not hasattr(composite, 'post'):
                request.method = 'GET'
                switched_method = True
            response = composite(request, *args, **kwargs)
            if (request.method == 'POST'
                and isinstance(response, HttpResponseRedirect)):
                return response
            if switched_method:
                request.method = 'POST'
            responses.append(response)
        context = dict(composites=responses)
        return context


class NamespacedCompositeView(AbstractCompositeView):
    """Populates a template context with several named composite
    based on the ``composites`` dictionary property.

    It does not define a default template, you must provide one.
    Given the following ``NamespacedCompositeView``:

    .. code-block:: python

    class HolyGrailView(NamespacedCompositeView):

        template_name = 'holygrail.html'

        composites = dict(
            main=(LeafCompositeView, dict(template_name='main.html')),
            sidebar=(LeafCompositeView, dict(template_name='sidebar.html')),
            ads=(LeafCompositeView, dict(template_name='ads.html')),
        )

    A minimal ``holygrail.html`` will looks like:

    .. code-block:: python

       <div id="main">
            {{ main }}
       </div>
       <div id="sidebar">
            {{ sidebar }}
       </div>
       <div id="ads">
            {{ ads }}
       </div>

    class HolyGrailView(NamespacedCompositeView):

        composites = dict(
            first=(LeafCompositeView, dict(template_name='first.html')),
            second=(LeafCompositeView, dict(template_name='second.html')),
            third=(LeafCompositeView, dict(template_name='third.html')),
        )


    ``composites`` values can be of two kinds:

    - class objects that inherits ``LeafCompositeView``
    - tuples with a composite view class and a dictionary
      used to initialize the composite class

    .. warning::

       A ``NamespacedCompositeView`` doesn't offer any particular machinery
       to work with forms.
       This class doesn't handle post request as a root node or an inner
       node, see ``NamespacedCompositeViewWithPost`` if you want to use forms.
    """

    composites = dict()

    def _composites(self, request, *args, **kwargs):
        """Generator over instantiated sub composite classes and name"""
        for name, CompositeClass in self.composites.items():
            if isinstance(CompositeClass, (tuple, list)):
                initkwargs = CompositeClass[1]
                initkwargs['parent'] = self
                CompositeClass = CompositeClass[0]
            else:
                initkwargs = dict(parent=self)
            composite = CompositeClass(**initkwargs)
            yield name, composite

    def composites_responses(self, request, *args, **kwargs):
        """Returns a dictionary that has the same keys as ``composites``
        but  with the answers of each composites as value.
        """
        responses = dict()
        for name, composite in self._composites(request, *args, **kwargs):
            response = composite(request, *args, **kwargs)
            responses[name] = response
        return responses


class NamespacedCompositeViewWithPost(NamespacedCompositeView, CompositeHierarchyHasPostMixin):
    """If there is at least one post method in your composite hierarchy you
    must use this class if you want to render namespaced composites.

    It's not the prefered method but you can also handle form this class
    refer to ``CompositeHierarchyHasPostMixin`` documentation.
    """

    def composites_responses(self, request, *args, **kwargs):
        """Returns a dictionary with a ``composites`` key populated
        with the answers of every composites.
        """
        responses = dict()
        for name, composite in self._composites(request, *args, **kwargs):
            # if the request is POST and the composite has no post method
            # it should be rendered as a GET so switch POST with GET
            # when it happens
            # This assumes the developper correctly inherited every inner
            # composite with ``CompositeHierarchyHasPostMixin`` or one
            # of its subclass, if it not the case the following code
            # will turn the request from GET to POST and will never hit
            # the ``post`` method that should process the form.
            # All this can bring some headaches...
            # If you are this developper, cheers :)
            switched_method = False
            if request.method == 'POST' and not hasattr(composite, 'post'):
                request.method = 'GET'
                switched_method = True
            response = composite(request, *args, **kwargs)
            if (request.method == 'POST'
                and isinstance(response, HttpResponseRedirect)):
                return response
            if switched_method:
                request.method = 'POST'
            responses[name] = response
        return responses


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
