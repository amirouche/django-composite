from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin


from simple.pages import Frontpage
from forms.pages import FormsExample

admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^frontpage/$', Frontpage.as_view(), name='frontpage'),
    url(r'^forms/$', FormsExample.as_view(), name='form'),
    url(r'^admin/', include(admin.site.urls)),
)


urlpatterns += staticfiles_urlpatterns()
