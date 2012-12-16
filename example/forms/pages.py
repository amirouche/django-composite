from django.shortcuts import redirect
from django import forms

from hydro.pages import HolyGrail
from hydro.widget import Widget


class ValidableForm(forms.Form):
    form_name = forms.CharField(widget=forms.HiddenInput(), initial='ValidableForm', required=True)


class ValidableFormWidget(Widget):

    template_name = 'forms/forms.html'
    css_files = ['css/forms.css']

    def get_context_data(self, page=None, request=None, *args, **kwargs):
        ctx = super(ValidableFormWidget, self).get_context_data(page, request, *args, **kwargs)
        ctx['form'] = ValidableForm()
        return ctx

    def post(self, page, request, *args, **kwargs):
        form = ValidableForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['form_name'] == 'ValidableForm':
                return redirect('index')
        # else the submitted form wasn't this one


class AnotherValidableFormWidget(Widget):


    template_name = 'forms/forms.html'
    css_files = ['css/forms.css']

    def get_context_data(self, page=None, request=None, *args, **kwargs):
        ctx = super(AnotherValidableFormWidget, self).get_context_data(page, request, *args, **kwargs)
        ctx['form'] = AnotherValidableForm()
        return ctx

    def post(self, page, request, *args, **kwargs):
        form = AnotherValidableForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['form_name'] == 'AnotherValidableForm':
                return redirect('index')
        # else the submitted form wasn't this one


class AnotherValidableForm(forms.Form):
    form_name = forms.CharField(widget=forms.HiddenInput(), initial='AnotherValidableForm', required=True)


class ImpossibleFormMission(forms.Form):
    form_name = forms.CharField(widget=forms.HiddenInput(), initial='MissionImpossibleForm', required=True)
    hidden = forms.BooleanField(widget=forms.HiddenInput(), required=True)


class ImpossibleFormMissionWidget(Widget):

    template_name = 'forms/forms.html'
    css_files = ['css/forms.css']

    def get_context_data(self, page=None, request=None, *args, **kwargs):
        ctx = super(ImpossibleFormMissionWidget, self).get_context_data(page, request, *args, **kwargs)
        ctx['form'] = ImpossibleFormMission()
        return ctx

    def post(self, page, request, *args, **kwargs):
        form = ImpossibleFormMission(request.POST)
        if form.is_valid():
            raise RuntimeException('This should never validate!')
        else:
            ctx = super(ImpossibleFormMissionWidget, self).get_context_data(page, request, *args, **kwargs)
            ctx['form'] = form
            ctx['errors'] = True
            return self.render_widget_with_context(page, request, ctx, *args, **kwargs)


class FormsExample(HolyGrail):

    first_column_widgets = [ValidableFormWidget('ValidableFormWidget')]
    second_column_widgets = [AnotherValidableFormWidget('AnotherValidableFormWidget')]
    third_column_widgets = [ImpossibleFormMissionWidget('ImpossibleFormMissionWidget')]

    css_files = ['css/forms.css']

    def get_context_data(self, request, *args, **kwargs):
        ctx = super(FormsExample, self).get_context_data(request, *args, **kwargs)
        ctx['form'] = AnotherValidableFormWidget()
        return ctx
