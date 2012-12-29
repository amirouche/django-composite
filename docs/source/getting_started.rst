Getting started
===============

You look forward using django-composite, but remember that 
this is **still alpha** and that you can find bugs and things can change.

They are several reasons you might want to learn more about django-composite:

- Curiousity.
- You want to know how it is designed, maybe learn new partterns for Python or 
  Django.
- You want to create widgets for your reusable application
- You want to create subs for your reusable application
- You want to know how 
  `django-composite-admin <https://github.com/django-composite/django-composite-admin>`_
  is built.
- You want to start hacking on 
  `django-composite-cms <https://github.com/django-composite/django-composite-cms>`_.

You will learn the basics of ``Sub``, ``Page`` and ``Widget``. It's not how 
django-composite is actually primarly meant to be used. The primary interest of 
django-composite is to create reusable component and reusing components from 
other applications. Of course the tutorial try to give an idea of how this
can be done, but the code won't be generic enough to be labeled as re-usable
application.

To follow this tutorial you will need the basics of Django developpement, doing
the `Django tutorial <https://docs.djangoproject.com/en/1.4/intro/tutorial01/>`_
might be enough.

.. note::

  Through the tutorial, hardcoded urls are used, in a real application you
  will want to use ``reverse``.

Poemsfreak
----------

During this tutorial we will create a mini-site with the following features::

 - home page with two menu as tabs
 - list of poems by authors aka. author detail view
 - add authors (TDB)
 - add poems to authors (TBD)
 - add comments to poems (TBD)

If it sound like a big project, don't be afraid, everything will be explained,
if you have any trouble 
`fill an issue on github <https://github.com/django-composite/django-composite/issues/new>`_.

Boot a Django project
---------------------

Now it is assumed you have Django installed, and that the ``django-admin.py`` 
or ``django-admin`` can be run from a terminal window::

  $ django-admin.py --version
  1.4.3

You will also need to install ``django-composite``, simply issue the following
command and prepend with ``sudo`` if you need superuser rights::

 $ pip install django-composite

Create a ``poemsfreak`` Django project::

 $ django-admin.py startproject poemsfreak

Go into the created directory and create a link to the django-composite 
application so that it's possible to import it from the poemsfreak project::

 $ cd poemsfreak

Create a ``main`` app::

 poemsfreak/ $ django-admin.py startapp main

Create ``static`` and ``media`` directories::

 poemsfreak/ $ mkdir static media

Open in your favorite text editor ``poemsfreak/poemsfreak/settings.py``,
proceed to the following modifications.

At the very top of the file, add the following lines::

  import os

  ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

Change the line containing ``MEDIA_ROOT`` to the following::

  MEDIA_ROOT = os.path.join(ROOT, 'media')

The line with ``MEDIA_URL`` should be::

  MEDIA_URL = 'static/'

Change the line containing ``STATIC_ROOT``::

  STATIC_ROOT = os.path.join(ROOT, 'static')

Replace ``INSTALLED_APPS`` variable by the following:

.. code-block:: python

  INSTALLED_APPS = (
      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.sites',
      'django.contrib.messages',
      'django.contrib.staticfiles',
      'django.contrib.admin',
      'composite',
      'main',
  )

Drop the ``DATABASES`` settings and put this instead:

.. code-block:: python

  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': 'db.sqlite',
          'USER': '',
          'PASSWORD': '',
          'HOST': '',
          'PORT': '',
      }
  }


Now go to ``poemsfreak/poemsfreak/urls.py`` and replace the content of the file
with the following:

.. code-block:: python

  from django.conf.urls import patterns, include, url
  from django.contrib.staticfiles.urls import staticfiles_urlpatterns

  from django.contrib import admin


  admin.autodiscover()

  urlpatterns = patterns('',
    url(r'^', include('main.urls')),
    url(r'^admin/', include(admin.site.urls)),
  )

  urlpatterns += staticfiles_urlpatterns()

Now we need to create ``main.urls`` or the server won't boot::

  poemsfreak $ cd main
  main $ touch urls.py

Open ``urls.py`` in your favorite editor add this:

.. code-block:: python

  from django.conf.urls import patterns, url

  from main.pages import Main


  urlpatterns = patterns('',
    url(r'^', include(Main().urls())),
  )

This is similar to the way admin was included in urls previously in ``poemsfreak.urls``.

In order to have a working project we will need to create two classes a ``Sub``
and a ``Page``. Open ``main/pages.py`` and paste the following code:

.. code-block:: python:

   from composite import Sub
   from composite.bootstrap import BootstrapPage


   class Home(BootstrapPage):
       path = r'^$'


   class Main(Sub):

      views = (Home,)

You can now run the Django development server and enjoy your first composite
page::

  poemsfreak $ python manage.py runserver

Go to `http://127.0.0.1:8000/<http://127.0.0.1:8000/>`_ and you actually
see a blank page, not very interesting...

Models
------

Open ``models.py`` and replace the content with what follows:

.. code-block:: python

   from django.db import models


   class Author(models.Model):
       name = models.CharField(max_length=255)

       def __str__(self):
           return self.name

   class Poem(models.Model):
       title = models.CharField(max_length=255)
       body = models.TextField()
       author = models.ForeignKey(Author)

       def __str__(self):
           return self.title


   class Comment(models.Model):
       name = models.CharField(max_length=255)
       body = models.TextField()
       poem = models.ForeignKey(Poem)

       def __str__(self):
           return '%s @ %s' % (self.name, self.poem.title)

Don't forget to syncdb::

  python manage.py syncdb

Register those models against the admin in ``main/admin.py``:

.. code-block:: python

  from django.contrib import admin

  from models import Author
  from models import Comment
  from models import Poem


  admin.site.register(Author)
  admin.site.register(Comment)
  admin.site.register(Poem)


Your first widget
-----------------

We will create a widget that will evolve based on
`twitter bootstrap toggle tabs <http://twitter.github.com/bootstrap/components.html#navs>`_.
Create a ``widgets.py`` file in ``main`` directory, and paste the following:

.. code-block:: python

   from composite import Widget


   class Tabs(Widget):

       template_name = 'main/widgets/tabs.html'

Widgets are in a way partial views and look very similar to ``Page`` and
``TemplateView``. Create ``main/templates/main/widgets/tabs.html`` and
paste the following:

.. code-block:: html

   <ul class="nav nav-tabs">
        <li class="active">
            <a href="#">Home</a>
        </li>
        <li><a href="#">Edit</a></li>
        <li><a href="#">About</a></li>
   </ul>

This is a really minimal widget, but we can already use it in ``Home``,
go back to ``pages.py`` and add a ``widgets`` class attribute to ``Home`` 
so that it looks like the following:

.. code-block:: python

   from widgets import Tab


   class Home(BootstrapPage):
       name = 'home'
       path = r'^$'
       widgets = ((Tab,),)

``name`` will be used to register the page to the url router.

``path`` is used to compute the url of the view. In this
case since ``Home`` is registred in ``Main`` Sub class and given 
``Index`` has a no ``path`` attribute which means it is hooked directly where it 
is included in urlpatterns, it means that ``IndexPage`` is rendered for 
`http://127.0.0.1:8000/<http://127.0.0.1:8000/>`_. 

The third attribute ``widgets`` tells to Django which widgets should be
included in the template.

The widget is not very useful as is, we want to be able to change the menu from
Python code. For that matter we will override ``get_context_data`` as follow:

.. code-block:: python

   from composite import Widget


   class MenuItem(object):

       def __init__(self, title, url, active):
           self.title = title
           self.url = url
           self.active = active

   class Tabs(Widget):

       template_name = 'main/widgets/tabs.html'

       def get_context_data(self, request, *args, **kwargs):
           ctx = super(Tabs, self).get_context_data(request, *args, **kwargs)
           items = (
               MenuItem('Home', '/', True),
               MenuItem('Edit', '/edit', False),
               MenuItem('About', '/about', False),
           )
           ctx['items'] = items
           return ctx

This is similar to how you work with a ``TemplateView``.

So the ``items`` variable is a list of ``MenuItem``, easy enough, replace
the content of ``main/templates/main/widgets/tabs.html`` with the following
code:

.. code-block:: html

   <ul id="{{ widget_id }}" class="nav nav-tabs">
      {% for item in items %}
          <li {% if item.active %}class="active"{% endif %}><a href="{{ item.url }}">{{ item.title }}</a></li>
      {% endfor %}
   </ul>

Reload the page and... It's exactly the same as before. As is, the widget is
not useful because you can not configure it from outside the class. For that
matter ``Page.widgets`` has another syntax, it can take a tuple instead of a
``Widget``, the first element must be a tuple anything after it is passed to
the ``Widget`` constructor. Update ``widgets`` to look like the following

.. code-block:: python

   widgets = (
          (
              Tabs,
              MenuItem('Home', '/', True),
              MenuItem('Edit', '/edit', False),
              MenuItem('About', '/about', False),
          ),
          (
              Tabs,
              MenuItem('W.B. Yeats', '#', False),
              MenuItem('E.A. Poe', '#', False),
              MenuItem('C. Baudelaire', '#', False),
          ),
   )

Override ``Widget`` constructor with the following method:

.. code-block:: python

   def __init__(self, parent, *items):
       super(Tabs, self).__init__(parent)
       self.items = items

``Tabs.get_context_data`` becomes::

.. code-block:: python

   def get_context_data(self):
       ctx = super(Tabs, self).get_context_data()
       ctx['items'] = self.items
       return ctx

Refresh the page. Woot! There is another tabs widget with different content.

The items from the second menu needs to be pulled from the database. For
that matter change again ``Tabs.__init__`` so that it takes two functions. The
first will return an iterable over ``MenuItem``, the second will help determine
which item is active:

.. code-block:: python

   def __init__(self, parent, items, is_active):
       super(Tabs, self).__init__(parent)
       for item in items:
           if is_active(item):
               item.active = True
               break
       self.items = items

In ``pages.py`` define before ``Home``, those two generator functions:

.. code-block:: python

   def menu():
       yield MenuItem('Home', '/', False)
       yield MenuItem('Admin', '/', False)
       yield MenuItem('About', '/', False)

   def menu_is_active(tabs, item):
       return tabs.page().name == item.title.lower()

   def authors():
       for author in Author.objects.all():
           yield MenuItem(author.name, '/%s' % author.pk, False)

   def authors_is_active(tabs, item):
       if tabs.page().name == 'author-detail':
           url = '/%s' % tabs.args[0]
           if item.url == url:
               return True
       return False

Then you can update ``Home.widgets`` as follow::

.. code-block:: python

   widgets = (
        (Tabs, menu, menu_is_active),
        (Tabs, authors, authors_is_active),
   )

It's more readable and more powerful, win/win modification.

Add several authors with the 
`admin <http://127.0.0.1:8000/admin/main/section/add/>`_ and hit refresh.

Authors detail page View
------------------------

Right now when you click on an author, you get a 404 error, in this part we
will fix that.

Create a ``AuthorDetailView`` that inherits ``BootstrapPage``:

.. code-block:: python

   class AuthorDetailView(BootstrapPage):
       name = 'author-detail'
       path = r'^(\d+)$'

       widgets = (
           (Tabs, menu, menu_is_active),
           (Tabs, authors, authors_is_active),
       )

Don't forget to add the new page in ``Main.views``.

Hit `http://127.0.0.1:8000/1<http://127.0.0.1:8000/1>`_ and see what happens.

It lakes some poems, doesn't it ? We could go on, and use the ``Tabs`` to show
a list of poems and then create a ``PoemDetailView`` but it would consume a
lot of bits! So instead we will create a new widget based the accordion from 
bootstrap and simply show all the poems for an author in its details view.

First let's create a new widget class name ``Accordion`` in ``widgets.py``::

.. warning::

  This accordion implementation as widget is not portable. It can only be 
  included once per page and the items should have ``pk``, ``title`` and
  ``body`` properties defined.

.. code-block:: python

   class Accordion(Widget):

       template_name = 'main/widgets/accordion.html'

       def __init__(self, parent, items):
           super(Tabs, self).__init__(parent)
           pk = self.page().args[0]
           self.items = items(pk)

       def get_context_data(self):
           ctx = super(Tabs, self).get_context_data()
           ctx['items'] = self.items
           return ctx

No need for explanation, this is pretty similar to what we've done previously.

.. code-block:: html

   <div class="accordion" id="#accordion">
    {% for item in items %}
        <div class="accordion-group">
            <div class="accordion-heading">
                <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion" href="#collapse{{ item.pk }}">
                    {{ item.title }}
                </a>
            </div>
            <div id="collapse{{ title.pk }}" class="accordion-body collapse">
                <div class="accordion-inner">
                     {{ item.body }}
                </div>
            </div>
        </div>
    {% endfor %}
   </div>

Done.

We need now a function to fetch the authors poems:

.. code-block:: python

   def author_poems(pk):
       author = Author.objects.get(pk=pk)
       return author.poem_set.all()

I take it, that now you know how to add such widget to a page. If you really
don't know you can have a look at the 
`example app <https://github.com/django-composite/django-composite/tree/master/example>`_. admin/admin will help you enter the admin.
