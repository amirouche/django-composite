from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from hydro.utils import OrderedSet


class Page(TemplateView):
    """Base class for all page class

    If you want to add to any subclass extra javascript and/or css
    files, define respectivly ``javascript_files`` and/or ``css_files``
    properties they will be added after any static file provided
    by a parent class.

    Mind the fact that this class is not fully efficient if you
    generate it for each requests. RTFC.
    """
    javascript_files = []
    css_files = []
    body_class = None

    def __init__(self, body_class=None):
        self.body_class = body_class if body_class else self.body_class

        # Cache static files
        # XXX: This is not the most efficient way to do this
        # it populates class properties in an instance method
        # so it's done for every class instantiation
        # which must only be done when is hooked in the url router
        # XXX: if in the future they are usecases for page
        # classes instantiated for every requests, one can move
        # this code in a metaclass and rework ``get_widgets``
        # so that it can be called from the metaclass.
        if not hasattr(self, 'static_files_cache'):
            css_files = OrderedSet()
            javascript_files = OrderedSet()
        else:
            css_files = OrderedSet(self.static_files_cache['css_files'])
            javascript_files = OrderedSet(self.static_files_cache['javascript_files'])
        for widget in self.get_widgets():
            widget_statics = widget.get_static_files()
            map(javascript_files.add, widget_statics['javascript_files'])
            map(css_files.add, widget_statics['css_files'])
        self.static_files_cache = {
            'css_files': css_files,
            'javascript_files': javascript_files,
        }

    def get_widgets(self, request=None, *args, **kwargs):
        """It must be an iterable over the widgets
        of the page.

        It is used to compute all the static files that
        must be included in the page *whatever* the request is.
        If ``request`` is not provided, it must return all the widgets the
        page can possibly render.

        You must override this method in a subclass."""
        raise NotImplementedError()

    def get_context_data(self, request, *args, **kwargs):
        ctx = dict(self.static_files_cache)
        ctx['body_class'] = self.body_class
        return ctx

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        # Same purpose method as ``django.views.base.View.dispatch``
        # but we defer to error handler only if the ``request.method``
        # method is defined nowhere in the page or its widgets
        # otherwise it's a a programming error and not a
        # 405 error, so 500 will be raised
        # It trys to dispatch to the page and to every
        # widgets contained in the page, the first method that
        # exists and returns something, then this something *must*
        # be a redirect if the form was succesfully submitted then
        # response is sent to user; otherwise it must be string
        # which must be the rendered page or the rendered widget
        # with an error form, if so it needs to compute the response.
        # ie. return a form error in a page.
        # If there is several forms in the page, only return something
        # if that was the submitted form.
        # Tips: You can know which form was submitted using an hidden
        # field with the name of the form for every form in the page
        # and check the name of the form thanks to this field in the
        # widget ``request.method`` method and do the appropriate thing.
        method = request.method.lower()
        if method not in self.http_method_names:
            # not allowed method
            handler = self.http_method_not_allowed
            return handler(request, *args, **kwargs)
        else:
            # look for method on the current page
            handler = getattr(self, method, None)
            if handler:
                response = handler(request, *args, **kwargs)
                if response:
                    # if there is response then it can be a) a redirect
                    # b) the page fully rendered with an error form
                    # anyway it's a valid response
                    return response
            # oups! there were no such method or it wasn't the right
            # form, iterate over widgets to find a possible match
            for widget in self.get_widgets(request, *args, **kwargs):
                handler = getattr(widget, method, None)
                if handler:
                    response = handler(self, request, *args, **kwargs)
                    if response:
                        if isinstance(response, HttpResponseRedirect):
                            return response
                        # It must be string with an error form,
                        # compute the full template, with widgets
                        # in the same order as it's done in ``Page.get``
                        # but using ``reponse``
                        # This is *must* be implemented in subclass
                        return self.compute_error_page(response, widget, request, *args, **kwargs)
                    # else continue to iterate over widgets
        # if it steps out of the loop without returning, it's most
        # likely a programming error raise 500
        msg = 'HTTP method ``%s`` called on view class but not defined' % method
        raise RuntimeError(msg)

    def get(self, request, *args, **kwargs):
        # The following line is the only difference with
        # ``TemplateView.get``, it adds ``request`` and ``*args``
        # as arguments of ``get_context_data()`` since they are
        # needed by widget classes to do the rendering
        context = self.get_context_data(request, *args, **kwargs)
        r = self.render_to_response(context)
        return r


class BootstrapPage(Page):
    """Base class for all Bootstrap pages this will embed
    minimal non-minified static files provided in Bootstrap 2.2.2
    for a responsive layout.
    If you need to add or replace default static files
    override ``__init__`` method and don't break the Internet.
    """

    def __init__(self, body_class=None):
        self.static_files_cache = {
            'css_files': OrderedSet(),
            'javascript_files': OrderedSet(),
        }
        self.static_files_cache['css_files'].add('css/bootstrap.css')
        self.static_files_cache['css_files'].add('css/bootstrap-responsive.css')
        self.static_files_cache['javascript_files'].add('js/jquery.js')
        self.static_files_cache['javascript_files'].add('js/bootstrap.js')
        super(BootstrapPage, self).__init__(body_class)


class OneColumn(BootstrapPage):
    """One column responsive layout using Bootstrap populated
    with rendered widgets found in ``widgets`` class property.

    If you want to customize the widget set according to ``request``'s
    attributes or anything else, you can override ``get_widgets``,
    by default ``get_widgets`` returns ``widgets`` class property.
    Mind the fact that you might also want to cache its results
    for extra speed.
    """

    widgets = []
    template_name = 'hydro/one_column.html'

    def get_widgets(self, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the column.

        This method will also be called without arguments,
        so it should always return something see ``Page.get_widgets()``.
        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return self.widgets

    def get_context_data(self, request, *args, **kwargs):
        ctx = super(OneColumn, self).get_context_data(request, *args, **kwargs)
        widgets = list()
        for widget in self.get_widgets():
            widget = widget.render(self, request, *args, **kwargs)
            widgets.append(widget)
        ctx['widgets'] = widgets
        return ctx

    def compute_error_page(partial_response, submitted_widget, request, *args, **kwargs):
        # Similar to ``OneColumn.get_context_data`` + ``Page.get``
        # but replace the response of the submitted widget by the answer
        # returned previously in the method ``request.method`` of the widget
        # in ``Page.dispatch()``
        # Compute context of the page
        ctx = super(OneColumn, self).get_context_data(request, *args, **kwargs)
        widgets = list()
        for widget in self.get_widgets():
            if widget == submitted_widget:
                widget = partial_response
            else:
                widget = widget.render(self, request, *args, **kwargs)
            widgets.append(widget)
        ctx['widgets'] = widgets
        # Create response object and send to client
        return self.render_to_response(ctx)


class TwoColumns(BootstrapPage):
    """Two columns responsive layout using Bootstrap populated
    with rendered widgets found in ``first_column_widgets`` and
    ``second_widgets_column`` class properties.

    If you want to customize the widget sets according to ``request``'s
    attributes or anything else, you can override ``get_first_column_widgets``
    and/or ``get_second_column_widgets``
    by default they respectivly return ``first_column_widgets`` and
    ``second_column_widgets`` class properties.
    Mind the fact that you might also want to cache their results
    for extra speed.
    """

    first_column_widgets = []
    second_column_widgets = []
    template_name = 'hydro/two_columns.html'

    def get_first_columns_widgets(self, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the first column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return self.first_column_widgets

    def get_second_columns_widgets(self, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the second column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return self.second_column_widgets

    def get_widgets(self, request=None, *args, **kwargs):
        for column in ('first', 'second'):
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(self, widgets_method_name)(request):
                yield widget

    def get_context_data(self, request, *args, **kwargs):
        ctx = super(TwoColumns, self).get_context_data(request, *args, **kwargs)
        for column in ('first', 'second'):
            widgets = list()
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(self, widgets_method_name)():
                widget = widget.render(self, request, *args, **kwargs)
                widgets.append(widget)
            ctx['%s_column_widgets' % column] = widgets
        return ctx

    def compute_error_page(partial_response, submitted_widget, request, *args, **kwargs):
        # Similar to ``OneColumn.compute_error_page`` but for two
        # columns
        ctx = super(OneColumn, self).get_context_data(request, *args, **kwargs)
        widgets = list()
        ctx = super(TwoColumns, self).get_context_data(request, *args, **kwargs)
        for column in ('first', 'second'):
            widgets = list()
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(self, widgets_method_name)():
                if widget == submitted_widget:
                    widget = partial_response
                else:
                    widget = widget.render(self, request, *args, **kwargs)
                widgets.append(widget)
            ctx['%s_column_widgets' % column] = widgets
        # Create response object and send to client
        return self.render_to_response(ctx)


class HolyGrail(BootstrapPage):
    """Three columns responsive layout using Bootstrap populated
    with rendered widgets found in ``first_column_widgets``,
    ``second_widgets_column`` and ``third_widgets_column`` class properties.

    If you want to customize the widget sets according to ``request``'s
    attributes or anything else, you can override ``get_first_column_widgets``
    and/or ``get_second_column_widgets`` and/or ``get_third_column_widgets``
    by default they respectivly return ``first_column_widgets``,
    ``second_column_widgets`` and ``third_column_widgets`` class properties.
    Mind the fact that you might also want to cache their results
    for extra speed.
    """

    first_column_widgets = []
    second_column_widgets = []
    third_column_widgets = []
    template_name = 'hydro/holy_grail.html'

    def get_first_column_widgets(self, request, *args, **kwargs):
        """Override this to customize the widget set used
        to render the first column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return self.first_column_widgets

    def get_second_column_widgets(self, request, *args, **kwargs):
        """Override this to customize the widget set used
        to render the second column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return self.second_column_widgets

    def get_third_column_widgets(self, request, *args, **kwargs):
        """Override this to customize the widget set used
        to render the third column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return self.third_column_widgets

    def get_widgets(self, request=None, *args, **kwargs):
        for column in ('first', 'second', 'third'):
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(self, widgets_method_name)(request):
                yield widget

    def get_context_data(self, request, *args, **kwargs):
        ctx = super(HolyGrail, self).get_context_data(request, *args, **kwargs)
        for column in ('first', 'second', 'third'):
            widgets = list()
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(self, widgets_method_name)(self, request, *args, **kwargs):
                widget = widget.render(self, request, *args, **kwargs)
                widgets.append(widget)
            ctx['%s_column_widgets' % column] = widgets
        return ctx

    def compute_error_page(self, partial_response, submitted_widget, request, *args, **kwargs):
        # Similar to ``OneColumn.cmpute_error_page`` but for two
        # columns
        widgets = list()
        ctx = super(HolyGrail, self).get_context_data(request, *args, **kwargs)
        for column in ('first', 'second', 'third'):
            widgets = list()
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(self, widgets_method_name)(self, request, *args, **kwargs):
                if widget == submitted_widget:
                    widget = partial_response
                else:
                    widget = widget.render(self, request, *args, **kwargs)
                widgets.append(widget)
            ctx['%s_column_widgets' % column] = widgets
       # Create response object and send to client
        return self.render_to_response(ctx)
