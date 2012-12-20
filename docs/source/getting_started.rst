Getting started
===============


You look forward using django-composite, but remember that 
this is still alpha and that you can find bugs and things can change.

They are several reasons you might want to learn more about django-composite:

- You want to know it is designed, maybe learn new partterns for Python or 
  Django. Just by curiousity.
- You want to create new widgets for your Django project
- You want to create new layouts for your Django project
- You want to create subs for your Django application and/or project
- You want to know how 
  `django-composite-admin <https://github.com/django-composite/django-composite-admin>`_
  is built.
- You want to start hacking on 
  `django-composite-cms <https://github.com/django-composite/django-composite-cms>`_.


This is basic tutorial getting up and running a Django project using only 
django-composite `Page` class for views. if you don't know Django
everything is explained from ground up so that you at the end of the tutorial
you have a working Django project.

Boot a Django project
---------------------

First things first you need Django 1.4.3 installed on your machine, if this is
not the case review Django official 
`documentation on know how to install Django <https://docs.djangoproject.com/en/1.4/intro/install/>`_.

Now we assume you have Django installed, and that the ``django-admin.py`` or 
``django-admin`` can be run from a terminal window::

  $ django-admin.py --version
  1.4.3

Create a directory ``haiku-project`` that will contain all the sources of the 
project with the following command::

  $ mkdir haiku-project

Now you will need ``git`` to fetch the last revision of django-composite 
sources, inside ``haiku-project``, clone the git repository::

 $ cd haiku-project
 haiku-project/ $ git clone https://github.com/django-composite/django-composite

Create a ``haiku`` Django project::

 haiku-project/ $ django-admin.py startproject haiku

Go into the created directory and create a link to the django-composite 
application so that it's possible to import it from the haiku project::

 haiku-project/ $ cd haiku
 haiku/ $ ln -s ../django-composite/composite

Create a ``main`` app::

 haiku/ $ django-admin.py startapp main

Create ``static`` and ``media`` directories::

 haiku/ $ mkdir static media

Open in favorite text editor ``haiku-project/haiku/haiku/settings.py``, proceed
to the following modifications.

At the very top of the file, add the following lines::

  import os

  ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ..))

Change the line containing ``MEDIA_ROOT`` to the following::

  MEDIA_ROOT = os.path.join(ROOT, 'media')

The line with ``MEDIA_URL`` should be::

  MEDIA_URL = 'static/'

Change the line containing ``STATIC_ROOT``::

  STATIC_ROOT = os.path.join(ROOT, 'static')

Replace ``INSTALLED_APPS`` variable by the following::

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
