import os

from django.test import TestCase
from django.http import HttpRequest

from ..views import Composite
from ..views import StackedComposite


class CompositeTests(TestCase):

    def test_static_files_extends_unique_in_order(self):

        class Parent(Composite):

            css_files = ['first.css']
            javascript_files = ['first.js']

            def get_composites(self):
                return []

        class Child(Parent):

            css_files = ['second.css', 'first.css']
            javascript_files = ['second.js', 'first.js']

        self.assertEqual(Child.css_files, ['first.css', 'second.css'])
        self.assertEqual(Child.javascript_files, ['first.js', 'second.js'])

    def test_composite_include_static_files_in_context_data(self):
        class Parent(Composite):

            css_files = ['first.css']
            javascript_files = ['first.js']

            def get_composites(self):
                return []

        class Child(Parent):

            css_files = ['second.css', 'first.css']
            javascript_files = ['second.js', 'first.js']

        composite = Child()
        context = composite.get_context_data()
        self.assertEqual(context['javascript_files'], ['first.js', 'second.js'])
        self.assertEqual(context['css_files'], ['first.css', 'second.css'])

    def test_composite_includes_sub_composites_statics(self):

        class SubComposite(Composite):

            css_files = ['sub.css']
            javascript_files = ['sub.js']

        class TestComposite(Composite):

            css_files = ['parent.css']
            javascript_files = ['parent.js']

            @classmethod
            def composites_class(self):
                yield SubComposite

        self.assertEqual(TestComposite.javascript_files, ['parent.js', 'sub.js'])
        self.assertEqual(TestComposite.css_files, ['parent.css', 'sub.css'])


class StackedCompositeTest(TestCase):

    def test_composites_class(self):
        class SubCompositeOne(Composite):
            pass

        class SubCompositeTwo(Composite):
            pass

        class TestComposite(StackedComposite):
            composites = (SubCompositeOne, SubCompositeTwo)

        self.assertEqual(tuple(TestComposite.composites_class()), (SubCompositeOne, SubCompositeTwo))

    def test_composites_class_with_tuple_syntax(self):
        class SubCompositeOne(Composite):
            pass

        class SubCompositeTwo(Composite):
            pass

        class TestComposite(StackedComposite):
            composites = (
                (SubCompositeOne, 'foo', 'bar'),
                (SubCompositeTwo, 'spam', 'egg'),
            )

        self.assertEqual(tuple(TestComposite.composites_class()), (SubCompositeOne, SubCompositeTwo))

    def test_composites_class_with_both_syntax(self):
        class SubCompositeOne(Composite):
            pass

        class SubCompositeTwo(Composite):
            pass

        class TestComposite(StackedComposite):
            composites = (
                SubCompositeOne,
                (SubCompositeTwo, 'spam', 'egg'),
            )

        self.assertEqual(tuple(TestComposite.composites_class()), (SubCompositeOne, SubCompositeTwo))

    def test_get_composites(self):
        class DummySubComposite(Composite):

            def get_composites(self):
                return []

        class SubCompositeOne(DummySubComposite):
            pass

        class SubCompositeTwo(DummySubComposite):
            pass

        class TestComposite(StackedComposite):
            composites = (
                SubCompositeOne,
                SubCompositeTwo,
            )

        composite = TestComposite()
        composites = composite.get_composites()
        self.assertTrue(isinstance(composites[0], SubCompositeOne))
        self.assertTrue(isinstance(composites[1], SubCompositeTwo))

    def test_get_composites_with_tuple_syntax(self):
        class DummySubComposite(Composite):

            def get_composites(self):
                return []

        class SubCompositeOne(DummySubComposite):
            pass

        class SubCompositeTwo(DummySubComposite):
            pass

        class TestComposite(StackedComposite):
            composites = (
                (SubCompositeOne, 'foo', 'bar'),
                (SubCompositeTwo, 'spam', 'egg'),
            )

        composite = TestComposite()
        composites = composite.get_composites()
        self.assertTrue(isinstance(composites[0], SubCompositeOne))
        self.assertTrue(isinstance(composites[1], SubCompositeTwo))

    def test_get_composites_with_both_syntax(self):
        class DummySubComposite(Composite):

            def get_composites(self):
                return []

        class SubCompositeOne(DummySubComposite):
            pass

        class SubCompositeTwo(DummySubComposite):
            pass

        class TestComposite(StackedComposite):
            composites = (
                SubCompositeOne,
                (SubCompositeTwo, 'spam', 'egg'),
            )

        composite = TestComposite()
        composites = composite.get_composites()
        self.assertTrue(isinstance(composites[0], SubCompositeOne))
        self.assertTrue(isinstance(composites[1], SubCompositeTwo))

    def test_sub_composites_has_parent(self):
        class DummySubComposite(Composite):

            def get_composites(self):
                return []

        class SubCompositeOne(DummySubComposite):
            pass

        class SubCompositeTwo(DummySubComposite):
            pass

        class TestComposite(StackedComposite):
            composites = (
                SubCompositeOne,
                (SubCompositeTwo, 'spam', 'egg'),
            )

        composite = TestComposite()
        composites = composite.get_composites()
        for sub_composite in composites:
            self.assertEqual(sub_composite.parent, composite)

    def test_get_composites_responses(self):
        class FixedResponseValue(Composite):

            def __init__(self, parent, response, **kwargs):
                super(FixedResponseValue, self).__init__(parent, **kwargs)
                self.response = response

            def get_composites(self):
                return []

            def render_to_response(self, context, **response_kwargs):
                return self.response

            def get_composites_responses(self, request, *args, **kwargs):
                return dict()  # there is not sub composite so no responses

        class TestComposite(StackedComposite):
            composites = (
                (FixedResponseValue, 'foo & bar'),
                (FixedResponseValue, 'spam & egg'),
            )

        composite = TestComposite()
        request = HttpRequest()
        request.method = 'GET'
        context_responses = composite.get_composites_responses(request)
        responses = context_responses['composites']
        self.assertEqual(responses, ['foo & bar', 'spam & egg'])

    def test_composite_get(self):
        class FixedResponseValue(Composite):

            def __init__(self, parent, response, **kwargs):
                super(FixedResponseValue, self).__init__(parent, **kwargs)
                self.response = response

            def get_composites(self):
                return []

            def render_to_response(self, context, **response_kwargs):
                return self.response

            def get_composites_responses(self, request, *args, **kwargs):
                return dict()  # there is not sub composite so no responses

        class TestComposite(StackedComposite):
            template_name = 'stacked.html'

            composites = (
                (FixedResponseValue, 'foo & bar'),
                (FixedResponseValue, 'spam & egg'),
            )
        request = HttpRequest()
        request.method = 'GET'
        composite = TestComposite()

        # this is done in View.as_view.view
        composite.request = request
        composite.args = list()
        composite.kwargs = dict()

        TEST_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            response = composite.get(request)
            response.render()
        self.assertEqual(response.content, 'foo & bar spam & egg \n')

    def test_composite_post(self):
        class FixedResponseValue(Composite):

            def __init__(self, parent, response, **kwargs):
                super(FixedResponseValue, self).__init__(parent, **kwargs)
                self.response = response

            def get_composites(self):
                return []

            def get_composites_responses(self, request, *args, **kwargs):
                return dict()  # there is not sub composite so no responses

            def post(self, request):
                return self.response

        class TestComposite(StackedComposite):
            template_name = 'stacked.html'

            composites = (
                (FixedResponseValue, 'response for post from sub composite'),
            )

        request = HttpRequest()
        request.method = 'POST'
        composite = TestComposite()

        # this is done in View.as_view.view
        composite.request = request
        composite.args = list()
        composite.kwargs = dict()

        TEST_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            response = composite.post(request)
            response.render()
        self.assertEqual(response.content, 'response for post from sub composite \n')
