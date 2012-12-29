from composite import Widget


class MenuItem(object):

    def __init__(self, title, url, active):
        self.title = title
        self.url = url
        self.active = active


class Tabs(Widget):

    template_name = 'main/widgets/tabs.html'

    def __init__(self, parent, items, is_active):
        super(Tabs, self).__init__(parent)
        self.items = list()
        for item in items():
            if is_active(self, item):
                item.active = True
            self.items.append(item)

    def get_context_data(self):
        ctx = super(Tabs, self).get_context_data()
        ctx['items'] = self.items
        return ctx


class Accordion(Widget):

    template_name = 'main/widgets/accordion.html'

    def __init__(self, parent, items):
        super(Accordion, self).__init__(parent)
        pk = self.page().args[0]
        self.items = items(pk)

    def get_context_data(self):
        ctx = super(Accordion, self).get_context_data()
        ctx['items'] = self.items
        return ctx


class HeroUnit(Widget):

    template_name = 'main/widgets/herounit.html'
