from base import Page


class BootstrapPage(Page):
    """Base class for all Bootstrap pages this will embed
    minimal non-minified static files provided in Bootstrap 2.2.2
    for a responsive layout.
    If you need to add or replace default static files
    override ``__init__`` method and don't break the Internet.
    """

    css_files = ['css/bootstrap.css', 'css/bootstrap-responsive.css']
    javascript_files = ['js/jquery.js', 'js/bootstrap.js']


class OneColumn(BootstrapPage):
    """One column responsive layout using Bootstrap populated
    with rendered widgets found in ``widgets`` class property.

    If you want to customize the widget set according to ``request``'s
    attributes or anything else, you can override ``get_widgets``,
    by default ``get_widgets`` returns ``widgets`` class property.
    Mind the fact that you might also want to cache its results
    for extra speed.
    """

    widgets = list()
    template_name = 'composite/one_column.html'

    @classmethod
    def get_widgets(cls, self=None, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the column.

        This method will also be called without arguments,
        so it should always return something see ``Page.get_widgets()``.
        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return cls.widgets

    def get_context_data(self, request, *args, **kwargs):
        ctx = super(OneColumn, self).get_context_data(request, *args, **kwargs)
        widgets = list()
        for widget in self.get_widgets(self, request, *args, **kwargs):
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
        for widget in self.get_widgets(self, *args, **kwargs):
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
    template_name = 'composite/two_columns.html'

    @classmethod
    def get_first_column_widgets(cls, self=None, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the first column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return cls.first_column_widgets

    @classmethod
    def get_second_column_widgets(cls, self=None, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the second column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return cls.second_column_widgets

    @classmethod
    def get_widgets(cls, self=None, request=None, *args, **kwargs):
        for column in ('first', 'second'):
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(cls, widgets_method_name)(self, request, *args, **kwargs):
                yield widget

    def get_context_data(self, request, *args, **kwargs):
        ctx = super(TwoColumns, self).get_context_data(request, *args, **kwargs)
        for column in ('first', 'second'):
            widgets = list()
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(cls, widgets_method_name)(self, request, *args, **kwargs):
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
    template_name = 'composite/holy_grail.html'

    @classmethod
    def get_first_column_widgets(cls, self=None, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the first column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return cls.first_column_widgets

    @classmethod
    def get_second_column_widgets(cls, self=None, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the second column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return cls.second_column_widgets

    @classmethod
    def get_third_column_widgets(cls, self=None, request=None, *args, **kwargs):
        """Override this to customize the widget set used
        to render the third column.

        Since it's called for every requests, you might want
        to cache the results for extra speed."""
        return cls.third_column_widgets

    @classmethod
    def get_widgets(cls, self=None, request=None, *args, **kwargs):
        for column in ('first', 'second', 'third'):
            widgets_method_name = 'get_%s_column_widgets' % column
            for widget in getattr(cls, widgets_method_name)(self, request, *args, **kwargs):
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
