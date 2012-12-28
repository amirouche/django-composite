#!/usr/bin/env python
import os

from setuptools import setup, find_packages


def long_description():
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'README.rst')
    try:
        with open(path) as f:
            return f.read()
    except:
        return ''


__doc__ = long_description()


setup(
    name='django-composite',
    version='0.1',
    url='https://github.com/django-composite/django-composite',
    license='BSD',
    author='Amirouche Boubekki',
    author_email='amirouche.boubekki@gmail.com',
    description='Django application for compositing with bootstrap integration',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=['django==1.4', 'blueprints'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
    ],
)
