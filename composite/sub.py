from django.conf.urls import patterns, url, include


class Sub(object):

    application_namespace = None
    instance_namespace = None

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
            except AttributeError:  # it is not
                try:  # it might have options
                    urls.append(url(resource.path, resource.as_view(), resource.options, resource.name))
                except AttributeError:  # it has not
                    urls.append(url(resource.path, resource.as_view(), name=resource.name))
        urlpatterns = patterns('', *urls)
        return urlpatterns, self.application_namespace, self.instance_namespace

# That is all :)
