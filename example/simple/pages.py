from composite.widget import Widget
from composite.pages import OneColumn

from simple.models import Article


class ArticleList(Widget):

    css_files = ['css/article_list.css']
    template_name = 'simple/article_list.html'

    def get_context_data(self, page=None, request=None, *args, **kwargs):
        ctx = super(ArticleList, self).get_context_data(page, request, *args, **kwargs)
        # Tips: A more realistic example would use a lazy
        # queryset as argument of the widget
        if self.widget_id == 'head':
            ctx['objects'] = Article.objects.all()[:5]
        else:
            ctx['objects'] = Article.objects.all()[5:10]
        return ctx


class Frontpage(OneColumn):

    css_files = ['css/frontpage.css']

    widgets = [
        ArticleList('head'),
        ArticleList('foot'),
    ]
