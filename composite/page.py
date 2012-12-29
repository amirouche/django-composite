from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.views.generic import TemplateView

from composite.utils import OrderedSet


class MetaPage(type):

    def __new__(cls, name, bases, dct):
        cls = type.__new__(cls, name, bases, dct)
        # Cache static files and this class permissions
        # add parents static files
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

        for WidgetClass in cls.widgets:
            if isinstance(WidgetClass, (tuple, list)):
                WidgetClass = WidgetClass[0]
            widget_statics = WidgetClass.get_static_files()
            map(javascript_files.add, widget_statics['javascript_files'])
            map(css_files.add, widget_statics['css_files'])

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

    def get_widgets(self):
        try:
            for widget in self._widgets:
                yield widget
        except AttributeError:
            self._widgets = list()
            for WidgetClass in self.widgets:
                if isinstance(WidgetClass, (tuple, list)):
                    args = list(WidgetClass[1:])
                    args.insert(0, self)
                    WidgetClass = WidgetClass[0]
                else:
                    args = (self,)
                widget = WidgetClass(*args)
                self._widgets.append(widget)
                yield widget

    def get_context_data(self):
        ctx = dict(self.static_files_cache)
        ctx['body_class'] = self.body_class
        return ctx

    def get_permissions(self):
        permissions = list(self.permissions)
        for permission in permissions:
            yield permission
        for widget in self.get_widgets():
            for permission in widget.get_permissions():
                if permission not in permissions:
                    permissions.append(permission)
                    yield permission

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

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        permissions = list(self.get_permissions())
        is_superuser = self.get_is_superuser()
        is_staff = self.get_is_staff()
        if ((is_superuser
            or is_staff
            or permissions)
            and request.user.is_authenticated()):
            # superuser check
            if is_superuser and not request.user.is_superuser:
                return HttpResponseForbidden()
            # is_staff check
            if is_staff and not request.user.is_staff:
                return HttpResponseForbidden()
            # permissions checks
            for permission in permissions:
                if not request.user.has_perm(permission):
                    return HttpResponseForbidden()
        if ((is_superuser
            or is_staff
            or permissions)
            and not request.user.is_authenticated()):
            return redirect('login')

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
                response = handler()
                if response:
                    # if there is response then it can be a) a redirect
                    # b) the page fully rendered with an error form
                    # anyway it's a valid response
                    return response
            # oups! there were no such method or it wasn't the right
            # form, iterate over widgets to find a possible match
            for widget in self.get_widgets():
                handler = getattr(widget, method, None)
                if handler:
                    response = handler()
                    if response:
                        if isinstance(response, HttpResponseRedirect):
                            return response
                        # It must be string with an error form,
                        # compute the full template, with widgets
                        # in the same order as it's done in ``Page.get``
                        # but using ``reponse``
                        # This is *must* be implemented in subclass
                        return self.compute_error_page(response)
                    # else continue to iterate over widgets
        # if it steps out of the loop without returning, it's most
        # likely a programming error raise 500
        msg = 'HTTP method ``%s`` called on view class but not defined' % method
        raise RuntimeError(msg)

    def render_widgets(self):
        for widget in self.get_widgets():
            yield widget.render()

    def get(self):
        # The following line is the only difference with
        # ``TemplateView.get``, it adds ``request`` and ``*args``
        # as arguments of ``get_context_data()`` since they are
        # needed by widget classes to do the rendering
        context = self.get_context_data()
        context['widgets'] = ''.join(self.render_widgets())
        return self.render_to_response(context)
