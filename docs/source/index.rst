.. django-composite documentation master file, created by
   sphinx-quickstart on Wed Dec 19 19:08:56 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-composite's documentation!
============================================

«Simple things should be simple, complex things should be possible» Alan Kay

`django-composite <https://github.com/django-composite/django-composite>`_ is a
framework on top of the ``TemplateView`` class based view
that offers new patterns to create reusable components for
Django applications. It's bundled with a Twitter Bootstrap
theme, with several predefined widgets.

It's super easy and super powerful! Check out those Django applications
for example usages:

- `django-composite-admin <https://github.com/django-composite/django-composite-admin>`_ 
  is an admin application, similar in purpose to Django 
  admin contrib application built from scratch for extensibility.
  It takes advantage of Bootstrap 2 to refresh the look'n'feel 
  and be responsive.
- `django-composite-cms <https://github.com/django-composite/django-composite-cms>`_ is a cms.
- `Your Django application or project here ?... <mailto:amirouche.boubekki+composite@gmail.com>`_


Features
--------

``composite.Widget``
^^^^^^^^^^^^^^^^^^^^

- ``Widget`` is python class.
- It *roughly* similar in purpose to Django's
  `TemplateView <https://docs.djangoproject.com/en/dev/ref/class-based-views/base/#django.views.generic.base.TemplateView>`_ but it's not a view
- A very simple widget is a class that inherits ``Widget`` class
  and define a ``template_name`` class property.
- It can deal with permissions and static files.
- A ``Widget`` class can contain other widgets, just add them 
  in a list as ``widgets`` class property, they will be rendered 
  and made available as ``widgets`` in the template.
- It can process requests on its own.
- You can quickly boot your project or application with the bundled 
  bootstrap widgets.

Check out the documentation about widgets to know more.

``composite.Page``
^^^^^^^^^^^^^^^^^^

- ``Page`` is python class
- It inherits Django 
  `TemplateView <https://docs.djangoproject.com/en/dev/ref/class-based-views/base/#django.views.generic.base.TemplateView>`_
  but customize it heavily
- Any page can be added to the url router
- A very simple page is a class that inherits ``Page`` and 
  define the class property ``template_name``.
- It can deal with permissions and static files.
- A page can be made of several widgets refer. It can be as 
  simple as a list of widget class instances.

Check out the documentation about pages to know more.

``composite.Sub``
^^^^^^^^^^^^^^^^^

- A ``Sub`` is python class
- It offers a new pattern to create reusable apps, allowing to break an app
  down into several SubApplication (hence the name)
- Secure together a set of pages or other subs so that there are
  easy to add to a project
- It makes easier to configure a project for a feature bundled with
  a ``Sub``
- Any ``Page`` class can be added to a ``Sub`` instance, it will
  have a reference to the ``Sub`` it is part of via ``Page.sub``
- a ``Sub`` instance can be added to another ``Sub`` instance, and it will
   have a reference to its parent ``Sub`` via ``Sub.sub``.
- You inherit any ``Sub`` to add features or configure it.
- You can hook in your project or application several instance of 
  the same ``Sub`` class

Check out the documentation about subs to know more.


Dependencies
------------

- Tested with Django 1.4.3


How to contribute
-----------------

- `Star <https://github.com/django-composite/django-composite/star>`_, watch and `tweet <http://twitter.com/home?status=https://github.com/django-composite/django-composite>`_ about it.
- Use ``Sub`` classes in an existing or new application. Mind the fact
  that you won't have to change existing code, if you already use
  `class-based-views <https://docs.djangoproject.com/en/dev/topics/class-based-views/>`_.
- `Create an issue <https://github.com/django-composite/django-composite/issues/new>`_ if you want a new feature or you find a bug.
- Fork, **create a new widget class**, and pull.
- Fork, **create a new page class**, and pull.
- `Read the code and provide feedback <https://github.com/django-composite/django-composite/commits/master>`_.
- Shim in the issue list, discuss or fix those that interest you.
- Also check out `django-composite-admin <https://github.com/django-composite/django-composite-admin>`_

Links
-----

- `forge <https://github.com/django-composite/django-composite>`_
- `documentation <https://django-composite.readthedocs.org/en/latest/>`_

Contents:

.. toctree::
   :maxdepth: 2

   getting_started
   advanced
   bootstrap

Thanks for using django-composite.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
