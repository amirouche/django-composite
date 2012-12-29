from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.exceptions import ImproperlyConfigured

from composite.utils import OrderedSet


class MetaWidget(type):

    def __new__(cls, name, bases, dct):
        cls = type.__new__(cls, name, bases, dct)
        # Cache static files
        # Add parent static files
        for base in bases:
            try:
                css_files = OrderedSet(base.static_files_cache['css_files'])
                javascript_files = OrderedSet(base.static_files_cache['javascript_files'])
                permissions = list(base.permissions)
            except:
                # it is not a Widget class instance
                css_files = OrderedSet()
                javascript_files = OrderedSet()
                permissions = list()

        widget_statics = cls.get_static_files()
        map(javascript_files.add, widget_statics['javascript_files'])
        map(css_files.add, widget_statics['css_files'])

        cls.static_files_cache = {
            'css_files': css_files,
            'javascript_files': javascript_files,
        }

        cls.permissions = permissions

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

    is_staff = False
    is_superuser = False
    permissions = []

    javascript_files = []
    css_files = []

    template_name = None
    widgets = []

    def __init__(self, parent):
        self.parent = parent
        self.request = parent.request
        self.args = parent.args
        self.kwargs = parent.kwargs

    def get_widgets(self):
        try:
            for widget in self._widgets:
                yield widget
        except AttributeError:
            self._widgets = list()
            for WidgetClass in self.widgets:
                if isinstance(WidgetClass, (tuple, list)):
                    args = WidgetClass[1:]
                    args.insert(0, self)
                    WidgetClass = WidgetClass[0]
                else:
                    args = (self,)
                widget = WidgetClass(*args)
                self._widgets.append(widget)
                yield widget

    def get_is_superuser(self):
        if self.is_superuser:
            return True
        else:
            for widget in self.get_widgets():
                if widget.is_superuser:
                    return True

    def get_is_staff(self):
        if self.is_staff:
            return True
        else:
            for widget in self.get_widgets():
                if widget.is_staff:
                    return True

    def page(self):
        widget = self
        while hasattr(widget, 'parent'):
            widget = widget.parent
        return widget

    def get_permissions(self):
        """Used internally to compute permissions.

        To know the permissions associated with this widget,
        use ``permissions`` property on the widget"""
        permissions = list(self.permissions)
        for permission in permissions:
            yield permissions
        for widget in self.get_widgets():
            for permission in widget.get_permissions():
                if permission not in permissions:
                    yield permission
                    permissions.append(permission)

    @classmethod
    def get_static_files(cls):
        css_files = OrderedSet(cls.css_files)
        javascript_files = OrderedSet(cls.javascript_files)
        for WidgetClass in cls.widgets:
            if isinstance(WidgetClass, (tuple, list)):
                WidgetClass = WidgetClass[0]
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

    def get_context_data(self):
        return dict()

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

    def render(self):
        ctx = self.get_context_data()
        return self.render_widget_with_context(ctx)

    def render_subwidgets(self):
        for widget in self.get_widgets():
            yield widget.render()

    def render_widget_with_context(self, ctx):
        ctx['widgets'] = self.render_subwidgets()
        ctx = RequestContext(self.request, ctx)
        widget = render_to_string(self.get_template_names(), ctx)
        return widget
