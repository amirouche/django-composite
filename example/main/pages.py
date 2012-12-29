from composite import Sub
from composite.bootstrap import BootstrapPage

from models import Author

from widgets import Tabs
from widgets import HeroUnit
from widgets import MenuItem
from widgets import Accordion


def menu():
    yield MenuItem('Home', '/', False)
    yield MenuItem('Edit', '/edit', False)
    yield MenuItem('About', '/about', False)


def menu_is_active(tabs, item):
    if tabs.page().name == item.title.lower():
        return True
    elif (tabs.page().name == 'author-detail'
          and item.title.lower() == 'home'):
        return True
    return False


def authors():
    for author in Author.objects.all():
        yield MenuItem(author.name, '/%s' % author.pk, False)


def authors_is_active(tabs, item):
    if tabs.page().name == 'author-detail':
        url = '/%s' % tabs.args[0]
        if item.url == url:
            return True
    return False


class Home(BootstrapPage):

    name = 'home'
    path = r'^$'

    widgets = (
        HeroUnit,
        (Tabs, menu, menu_is_active),
        (Tabs, authors, authors_is_active),
    )


def author_poems(pk):
    author = Author.objects.get(pk=pk)
    return author.poem_set.all()


class AuthorDetailView(BootstrapPage):

    name = 'author-detail'
    path = r'^(\d+)$'

    widgets = (
        HeroUnit,
        (Tabs, menu, menu_is_active),
        (Tabs, authors, authors_is_active),
        (Accordion, author_poems),
    )


class Main(Sub):

    views = [Home, AuthorDetailView]
