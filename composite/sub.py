from django.conf.urls import patterns, url, include


class Sub(object):

    def __init__(self):
        self.resources = []

    def register(self, resource):
        self.resources.append(resource)

    def urls(self):
        urls = list()
        for resource in self.resources:
            try:  # it might be another sub
                pattern = (resource.path, include(resource.urls()))
            except:  # it is not
                try:  # it might have options
                    pattern = (resource.path, resource, resource.options, resource.name)
                except:  # it has not
                    pattern = (resource.path, resource, name=resource.name)


# That is all :)
