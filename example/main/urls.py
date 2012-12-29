from django.conf.urls import patterns, url, include

from main.pages import Main


urlpatterns = patterns('',
    url(r'^', include(Main().urls())),
)
