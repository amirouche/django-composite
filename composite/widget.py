from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.exceptions import ImproperlyConfigured

from composite.utils import OrderedSet


class MetaWidget(type):

    def __new__(cls, name, bases, dct):
        cls = type.__new__(cls, name, bases, dct)
        # Cache static files
        # Add parent static files
        base = bases[0]
        try:
            css_files = base.static_files_cache['css_files']
            javascript_files = base.static_files_cache['javascript_files']
        except:
            # it is not a Widget class instance
            css_files = OrderedSet()
            javascript_files = OrderedSet()

        widget_statics = cls.get_static_files()
        map(javascript_files.add, widget_statics['javascript_files'])
        map(css_files.add, widget_statics['css_files'])

        cls.static_files_cache = {
            'css_files': css_files,
            'javascript_files': javascript_files,
        }
        return cls


class Widget(object):
    """Base class for all widgets. You must at least define
    ``template_name`` class property.

    Recursive widgets are supported through ``widgets``
    class property or if you need a more finegrained
    widget set through ``get_widgets()`` method.
    The default context inject all widgets as a ``widgets`` variable in
    the template, for more complex usecases override ``get_context_data()``."""

    __metaclass__ = MetaWidget

    javascript_files = []
    css_files = []

    template_name = None
    widgets = []

    def __init__(self, widget_id=None, template_name=None):
        self.widget_id = widget_id
        self.template_name = template_name if template_name else self.template_name

    @classmethod
    def get_static_files(cls):
        css_files = OrderedSet(cls.css_files)
        javascript_files = OrderedSet(cls.javascript_files)
        for widget in cls.widgets:
            # we need to keep this always in the same order
            # or the designer will be mad
            map(css_files.add, widget.css_files)
            map(javascript_files.add, widget.javascript_files)
            static_files = widget.get_static_files()
            map(css_files, static_files['css_files'])
            map(javascript_files.add, static_files['javascript_files'])
        return {
            'css_files': css_files,
            'javascript_files': javascript_files,
        }

    def get_widgets(self, page, request, *args, **kwargs):
        """You might want to override this to allow
        for a fine grained list of widget depending on the page
        and the request.

        Mind the fact that this is called for every request, thus
        you might want to cache the results for extra speed."""
        return self.widgets

    def get_context_data(self, request, *args, **kwargs):
        return dict(widget_id=self.widget_id)

    def get_template_names(self):
        """
        Returns a list of template names to be used for the request.
        Must return a list. May not be called if ``render`` is overridden.
        """
        if self.template_name is None:
            raise ImproperlyConfigured(
                "Widget requires either a definition of "
                "'template_name' or an implementation of 'get_template_names()'")
        else:
            return [self.template_name]

    def render(self, page, request, *args, **kwargs):
        ctx = self.get_context_data(request, *args, **kwargs)
        return self.render_widget_with_context(page, request, ctx, *args, **kwargs)

    def render_widget_with_context(self, page, request, ctx, *args, **kwargs):
        ctx = RequestContext(request, ctx)
        widgets = list()
        for widget in self.get_widgets(page, request, *args, **kwargs):
            widget = widget.render(page, request, *args, **kwargs)
            widgets.append(widget)
        ctx['widgets'] = widgets
        widget = render_to_string(self.get_template_names(), ctx)
        return widget
