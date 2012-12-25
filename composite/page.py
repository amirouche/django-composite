from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.views.generic import TemplateView

from composite.utils import OrderedSet


class MetaPage(type):

    def __new__(cls, name, bases, dct):
        cls = type.__new__(cls, name, bases, dct)
        # Cache static files and permissions
        # Add parents static files
        for base in bases:
            try:
                css_files = OrderedSet(base.static_files_cache['css_files'])
                javascript_files = OrderedSet(base.static_files_cache['javascript_files'])
                permissions = list(base.permissions)
            except:
                # this is not a Page class instance
                css_files = OrderedSet()
                javascript_files = OrderedSet()
                permissions = list()

        # add current class static files and permissions
        try:
            map(css_files.add, dct['css_files'])
        except KeyError:
            pass
        try:
            map(javascript_files.add, dct['javascript_files'])
        except KeyError:
            pass
        try:
            permissions.extend(dct['permissions'])
        except KeyError:
            pass

        for widget in cls.get_widgets():
            widget.parent = cls
            widget_statics = widget.get_static_files()
            map(javascript_files.add, widget_statics['javascript_files'])
            map(css_files.add, widget_statics['css_files'])
            permissions.extend(widget.get_permissions())

        cls.static_files_cache = {
            'css_files': css_files,
            'javascript_files': javascript_files,
        }
        cls.permissions = permissions
        return cls


class Page(TemplateView):
    """Base class for all page class

    If you want to add to any subclass extra javascript and/or css
    files, define respectivly ``javascript_files`` and/or ``css_files``
    properties they will be added after any static file provided
    by a parent class.

    Mind the fact that this class is not fully efficient if you
    generate it for each requests. RTFC.
    """

    __metaclass__ = MetaPage

    is_staff = False
    is_superuser = False
    permissions = []

    javascript_files = list()
    css_files = list()
    body_class = None
    widgets = []

    name = None
    path = r'^'

    @classmethod
    def get_widgets(cls, self=None, request=None, *args, **kwargs):
        """It must be an iterable over the widgets
        of the page.

        It is used to compute all the static files that
        must be included in the page *whatever* the request is.
        If ``request`` is not provided, it must return all the widgets the
        page can possibly render.
        """
        return cls.widgets

    def get_context_data(self, request, *args, **kwargs):
        ctx = dict(self.static_files_cache)
        ctx['body_class'] = self.body_class
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if ((self.is_superuser
            or self.is_staff
            or self.permissions)
            and request.user.is_authenticated()):
            # superuser check
            if self.is_superuser and not request.user.is_superuser:
                return HttpResponseForbidden()
            # is_staff check
            if self.is_staff and not request.user.is_staff:
                return HttpResponseForbidden()
            # permissions checks
            for permission in self.permissions:
                if not request.user.has_perm(permission):
                    return HttpResponseForbidden()
        if ((self.is_superuser
            or self.is_staff
            or self.permissions)
            and not request.user.is_authenticated()):
            return redirect('login')

        self.request = request
        self.args = args
        self.kwargs = kwargs
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
            for widget in self.get_widgets(self, request, *args, **kwargs):
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
                        return self.compute_error_page(response, request, *args, **kwargs)
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
