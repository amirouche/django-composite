from django.core.urlresolvers import reverse

from widget import Widget


class Tag(Widget):

    def __init__(self, name, widget_id=None, classes=None, *widgets, **attrs):
        super(Tag, self).__init__(widget_id)
        self.widgets = widgets
        self.classes = classes
        self.name = name
        self.attributes = attrs

    def render(self, request, *args, **kwargs):
        # render opening tag
        widget = '<%s' % self.name
        if self.widget_id:
            widget += ' id="%s' % self.widget_id
        if self.classes:
            classes = ' '.join(self.classes)
            widget += ' class="%s"' % classes
        if self.attributes:
            for key, value in self.attributes.items():
                widget += ' %s="%s"' % (key, value)
        # render subwigets and closing tag
        subwidgets = self.render_subwidgets(request, *args, **kwargs)
        widget += '>%s</%s>' % (subwidgets, self.name)
        return widget


class Div(Tag):

    def __init__(self, widget_id=None, classes=None, *widgets, **attrs):
        super(Div, self).__init__('div', widget_id, classes, *widgets, **attrs)


class String(Widget):

    def __init__(self, string):
        self.string = string

    def render(self, request, *args, **kwargs):
        return self.string


class Link(Tag):

    def __init__(self, url, widget_id=None, classes=None, *widgets, **attrs):
        if not url.startswith('#'):
            url = reverse(url)
        extra = dict(href=url)
        extra.update(attrs)
        super(Link, self).__init__('a', widget_id, classes, *widgets, **extra)
