from widget import Widget


class Tag(Widget):

    def __init__(self, name, widget_id=None, classes=None, *widgets):
        super(Tag, self).__init__(widget_id)
        self.widgets = widgets
        self.classes = classes
        self.name = name

    def render(self, request, *args, **kwargs):
        # render opening tag
        widget = '<%s' % self.name
        if self.widget_id:
            widget += ' id="%s' % self.widget_id
        if self.classes:
            classes = ' '.join(self.classes)
            widget += ' class="%s"' % classes
        # render subwigets and closing tag
        subwidgets = self.render_subwidgets(request, *args, **kwargs)
        widget += '>%s</%s>' % (subwidgets, self.name)
        return widget


class Div(Tag):

    def __init__(self, widget_id=None, classes=None, *widgets):
        super(Div, self).__init__('div', widget_id, classes, *widgets)


class String(Widget):

    def __init__(self, string):
        self.string = string

    def render(self, request, *args, **kwargs):
        return self.string
