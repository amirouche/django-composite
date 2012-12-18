from django.conf.urls import patterns, url, include


class Sub(object):

    def __init__(self):
        self.resources = []

    def register(self, resource):
        resource.sub = self
        self.resources.append(resource)

    def urls(self):
        urls = []
        for resource in self.resources:
            try:  # it might be another sub
                urls.append(url(resource.path, include(resource.urls())))
            except AttributeError, e:  # it is not
                print self, resource, e
                try:  # it might have options
                    urls.append(url(resource.path, resource.as_view(), resource.options, resource.name))
                except AttributeError:  # it has not
                    urls.append(url(resource.path, resource.as_view(), name=resource.name))
        urlpatterns = patterns('', *urls)
        return urlpatterns, self.app_name, self.name

# That is all :)
