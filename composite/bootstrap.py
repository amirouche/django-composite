from django import forms
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy

from page import Page
from widget import Widget


class BootstrapPage(Page):
    """Base class for all Bootstrap pages this will embed
    minimal non-minified static files provided in Bootstrap 2.2.2
    for a responsive layout.
    If you need to add or replace default static files
    override ``__init__`` method and don't break the Internet.
    """

    css_files = ['css/bootstrap.css', 'css/bootstrap-responsive.css']
    javascript_files = ['js/jquery.js', 'js/bootstrap.js']
    template_name = 'composite/bootstrap/base.html'


class LoginForm(forms.Form):
    name = forms.CharField(widget=forms.HiddenInput(), initial='LoginForm', required=True)
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255, widget=forms.PasswordInput())

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                message = ugettext_lazy("Please enter the correct username and password.")
                raise forms.ValidationError(message)
            elif not self.user_cache.is_active:
                message = ugettext_lazy("Sorry, this account is desactivated.")
                raise forms.ValidationError(message)
        return self.cleaned_data


class Login(Widget):

    template_name = 'composite/widgets/login.html'

    def __init__(self, redirect_name):
        super(Login, self).__init__()
        self.redirect_name = redirect_name

    def get_context_data(self, page, request, *args, **kwargs):
        ctx = super(Login, self).get_context_data(page, request, *args, **kwargs)
        form = LoginForm()
        ctx['form'] = form
        return ctx

    def post(self, page, request, *args, **kwargs):
        if ('name' in request.POST and
            request.POST['name'] == 'LoginForm'):
            form = LoginForm(request.POST)
            if form.is_valid():
                login(request, form.user_cache)
                return redirect(self.redirect_name)
            else:
                # check if it was the submitted form with form.name
                pass
        # else the submitted form wasn't this one
