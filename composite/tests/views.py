import os

from django.test import TestCase
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from ..views import RenderableTemplateResponseMixin
from ..views import NamespacedCompositeViewWithPost
from ..views import CompositeHierarchyHasPostMixin
from ..views import StackedCompositeViewWithPost
from ..views import RenderableTemplateViewMixin
from ..views import RenderableTemplateResponse
from ..views import NamespacedCompositeView
from ..views import AbstractCompositeView
from ..views import StackedCompositeView
from ..views import LeafCompositeView


TEST_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')


class RenderableTemplateResponseMixinTests(TestCase):

    class TestTemplateResponse(RenderableTemplateResponseMixin):

        def __init__(self, expected_output):
            self.expected_output = expected_output

        def render(self):
            self.rendered_content = self.expected_output

    def test_unicode_method_returns_rendered_template(self):
        test_template_response = self.TestTemplateResponse('rendered content')
        self.assertEqual(str(test_template_response), 'rendered content')

    def test_rendered_content_is_safe(self):
        pass  # FIXME


class RenderableTemplateResponseTests(TestCase):

    def test_unicode_method_returns_rendered_template(self):
        request = HttpRequest()
        template_name = 'hello.html'
        template_response = RenderableTemplateResponse(request, template_name)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertEqual(str(template_response), 'hello\n')

    def test_rendered_content_is_safe(self):
        pass  # FIXME


class RenderableTemplateViewMixinTests(TestCase):

    class TestTemplateView(RenderableTemplateViewMixin, TemplateView):
        pass

    def test_renderable_template_response(self):
        request = HttpRequest()
        request.method = 'GET'
        view = self.TestTemplateView.as_view(template_name='hello.html')
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            response = view(request)
            self.assertEqual(str(response), 'hello\n')

    def test_rendered_content_is_safe(self):
        pass  # FIXME


class LeafCompositeViewTests(TestCase):

    def test_root_has_parent(self):
        class MockParentableClass(object):
            parent = None
        parent = MockParentableClass()
        leaf = LeafCompositeView(parent=parent)
        self.assertEqual(leaf.root(), parent)

    def test_composite_is_root(self):
        leaf = LeafCompositeView()
        self.assertEqual(leaf.root(), leaf)

    def test_has_renderable_response_class(self):
        response_class = LeafCompositeView.response_class
        self.assertTrue(issubclass(response_class, RenderableTemplateResponseMixin))


class AbstractCompositeViewTests(TestCase):

    def test_composite_responses_raise_not_implemented_error(self):
        request = HttpRequest()
        composite = AbstractCompositeView()
        self.assertRaises(NotImplementedError, composite.composites_responses, request)

    def test_get_redirects(self):
        class RedirectComposite(AbstractCompositeView):

            def composites_responses(self, request, *args, **kwargs):
                return HttpResponseRedirect('/index')

        view = RedirectComposite.as_view(template_name='hello.html')
        request = HttpRequest()
        request.method = 'GET'
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            response = view(request)
        self.assertTrue(isinstance(response, HttpResponseRedirect))

    def test_get_render_composites(self):
        class StringLeafCompositeView(LeafCompositeView):

            template_name = 'string.html'
            string = None

            def get_context_data(self, **kwargs):
                kwargs['string'] = self.string
                return super(StringLeafCompositeView, self).get_context_data(**kwargs)

        class SimpleComposite(AbstractCompositeView):

            template_name = 'stacked_composite.html'

            def composites_responses(self, request, *args, **kwargs):
                view = StringLeafCompositeView.as_view(parent=self, string='hello')
                one = view(request)
                view = StringLeafCompositeView.as_view(parent=self, string='world')
                two = view(request)
                return dict(composites=(one, two))

        view = SimpleComposite.as_view()
        request = HttpRequest()
        request.method = 'GET'
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertEqual(str(response), 'hello\nworld\n\n')


class CompositeHierarchyHasPostMixinTests(TestCase):
    # This is a utility class there nothing to test
    # except the fact that POST are served as GET
    # It the same test as AbstractCompositeViewTests.test_get_render_composites
    # except the request is done with POST

    def test_post_served_as_get(self):
        class StringLeafCompositeView(LeafCompositeView):

            template_name = 'string.html'
            string = None

            def get_context_data(self, **kwargs):
                kwargs['string'] = self.string
                return super(StringLeafCompositeView, self).get_context_data(**kwargs)

        class SimpleComposite(AbstractCompositeView, CompositeHierarchyHasPostMixin):

            template_name = 'stacked_composite.html'

            def composites_responses(self, request, *args, **kwargs):
                # override request method since subcomposites do not handle
                # the POST
                request.method = 'GET'
                one = StringLeafCompositeView.as_view(parent=self, string='hello')
                one = one(request)
                two = StringLeafCompositeView.as_view(parent=self, string='world')
                two = two(request)
                return dict(composites=(one, two))

        view = SimpleComposite.as_view()
        request = HttpRequest()
        request.method = 'POST'
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertEqual(str(response), 'hello\nworld\n\n')


class StackedCompositeViewTests(TestCase):

    def test__composites(self):
        class SubCompositeOne(LeafCompositeView):
            pass

        class SubCompositeTwo(LeafCompositeView):
            pass

        class TestComposite(StackedCompositeView):
            composites = (SubCompositeOne, SubCompositeTwo)
        composites = list(TestComposite()._composites(None))
        self.assertEqual(len(composites), 2)

    def test__composites_with_tuple_syntax(self):
        class BaseSubComposite(LeafCompositeView):

            args1 = None
            args2 = None

        class SubCompositeOne(BaseSubComposite):
            pass

        class SubCompositeTwo(BaseSubComposite):
            pass

        class TestComposite(StackedCompositeView):
            composites = (
                (SubCompositeOne, dict(args1='foo', args2='bar')),
                (SubCompositeTwo, dict(args1='spam', args2='egg')),
            )

        composites = list(TestComposite()._composites(None))
        self.assertEqual(len(composites), 2)

    def test_composites_class_with_both_syntax(self):
        class SubCompositeOne(LeafCompositeView):
            pass

        class SubCompositeTwo(LeafCompositeView):

            args1 = None
            args2 = None

        class TestComposite(StackedCompositeView):
            composites = (
                SubCompositeOne,
                (SubCompositeTwo, dict(args1='spam', args2='egg')),
            )
        composites = list(TestComposite()._composites(None))
        self.assertEqual(len(composites), 2)

    def test_get_composites_responses(self):
        class FixedResponseValue(LeafCompositeView):

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class TestComposite(StackedCompositeView):
            composites = (
                (FixedResponseValue, dict(response='foo & bar')),
                (FixedResponseValue, dict(response='spam & egg')),
            )

        composite = TestComposite()
        request = HttpRequest()
        request.method = 'GET'
        context_responses = composite.composites_responses(request)
        responses = context_responses['composites']
        self.assertEqual(responses, ['foo & bar', 'spam & egg'])

    def test_composite_get(self):
        class FixedResponseValue(LeafCompositeView):

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class TestComposite(StackedCompositeView):
            template_name = 'stacked_composite.html'

            composites = (
                (FixedResponseValue, dict(response='foo & bar')),
                (FixedResponseValue, dict(response='spam & egg')),
            )
        request = HttpRequest()
        request.method = 'GET'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertEqual(str(response), 'foo &amp; barspam &amp; egg\n')


class StackedCompositeViewWithPostTests(TestCase):

    def test_post_fully_rendered(self):
        """When the ``StackedCompositeViewWithPost`` is an inner composite
           and that the POST is handled by a another branch of the
           tree the request is still POST but should be answered
           as if it was a GET"""

        class FixedResponseValue(LeafCompositeView):

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class TestComposite(StackedCompositeViewWithPost):
            template_name = 'stacked_composite.html'

            composites = (
                (FixedResponseValue, dict(response='foo & bar')),
                (FixedResponseValue, dict(response='spam & egg')),
            )
        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertEqual(str(response), 'foo &amp; barspam &amp; egg\n')

    def test_post_handled_by_subcomposite(self):
        """If a POST request is submitted to a composite with subcomposite
        that has the subcomposite must answer with its post method"""

        class LeafCompositeWithPost(LeafCompositeView):

            template_name = 'hello.html'

            def post(self, request, *args, **kwargs):
                return 'response from post'

        class TestComposite(StackedCompositeViewWithPost):
            template_name = 'stacked_composite.html'

            composites = (
                LeafCompositeWithPost,
            )

        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)

        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertTrue(str(response), 'response_from_post')

    def test_post_with_several_subcomposite(self):
        """Same test as above except there is several subcomposite
        each subcomposite returns a response, which are rendered
        in the response"""

        class LeafCompositeWithPost(LeafCompositeView):

            template_name = 'hello.html'

            def post(self, request, *args, **kwargs):
                return 'response from post'

        class FixedResponseValue(LeafCompositeView):

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class TestComposite(StackedCompositeViewWithPost):
            template_name = 'stacked_composite.html'

            composites = (
                LeafCompositeWithPost,
                (FixedResponseValue, dict(response='another subcomposite')),
            )

        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            expected = 'response_from_post\nanother subcomposite\n\n'
            self.assertTrue(str(response), expected)

    def test_post_request_redirect(self):
        """If a POST request is submitted subcomposite can return a redirect
        if it is the case the response must be forwared"""

        class LeafCompositeRedirectOnPost(LeafCompositeView):

            template_name = 'hello.html'

            def post(self, request, *args, **kwargs):
                return HttpResponseRedirect('index')

        class TestComposite(StackedCompositeViewWithPost):
            template_name = 'stacked_composite.html'

            composites = (
                LeafCompositeRedirectOnPost,
            )

        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertTrue(isinstance(response, HttpResponseRedirect))

    def test_post_request_redirect_wiht_several_subcomposites(self):
        """If a POST request is submitted subcomposite can return a redirect
        if it is the case the response must be forwared even if other sub
        composites were rendered"""

        class FixedResponseValue(LeafCompositeView):

            template_name = 'hello.html'

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class LeafCompositeRedirectOnPost(LeafCompositeView):

            template_name = 'hello.html'

            def post(self, request, *args, **kwargs):
                return HttpResponseRedirect('index')

        class TestComposite(StackedCompositeViewWithPost):
            template_name = 'stacked_composite.html'

            composites = (
                (FixedResponseValue, dict(response='whatever')),
                LeafCompositeRedirectOnPost,
            )

        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertTrue(isinstance(response, HttpResponseRedirect))


class NamespacedCompositeViewTests(TestCase):

    def test__composites(self):
        class SubCompositeOne(LeafCompositeView):
            pass

        class SubCompositeTwo(LeafCompositeView):
            pass

        class TestComposite(NamespacedCompositeView):
            composites = dict(one=SubCompositeOne, two=SubCompositeTwo)

        composites = dict(TestComposite()._composites(None)).keys()
        self.assertEqual(len(composites), 2)

    def test__composites_with_tuple_syntax(self):
        class BaseSubComposite(LeafCompositeView):

            args1 = None
            args2 = None

        class SubCompositeOne(BaseSubComposite):
            pass

        class SubCompositeTwo(BaseSubComposite):
            pass

        class TestComposite(NamespacedCompositeView):
            composites = dict(
                one=(SubCompositeOne, dict(args1='foo', args2='bar')),
                two=(SubCompositeTwo, dict(args1='spam', args2='egg')),
            )

        composites = dict(TestComposite()._composites(None)).keys()
        self.assertEqual(len(composites), 2)

    def test_composites_class_with_both_syntax(self):
        class SubCompositeOne(LeafCompositeView):
            pass

        class SubCompositeTwo(LeafCompositeView):

            args1 = None
            args2 = None

        class TestComposite(NamespacedCompositeView):
            composites = dict(
                one=SubCompositeOne,
                two=(SubCompositeTwo, dict(args1='spam', args2='egg')),
            )
        composites = dict(TestComposite()._composites(None)).keys()
        self.assertEqual(len(composites), 2)

    def test_get_composites_responses(self):
        class FixedResponseValue(LeafCompositeView):

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class TestComposite(NamespacedCompositeView):
            composites = dict(
                one=(FixedResponseValue, dict(response='foo & bar')),
                two=(FixedResponseValue, dict(response='spam & egg')),
            )

        composite = TestComposite()
        request = HttpRequest()
        request.method = 'GET'
        responses = composite.composites_responses(request)
        self.assertEqual(responses, dict(one='foo & bar', two='spam & egg'))

    def test_composite_get(self):
        class FixedResponseValue(LeafCompositeView):

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class TestComposite(NamespacedCompositeView):
            template_name = 'namespaced_composite_test.html'

            composites = dict(
                one=(FixedResponseValue, dict(response='foo & bar')),
                two=(FixedResponseValue, dict(response='spam & egg')),
            )
        request = HttpRequest()
        request.method = 'GET'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertEqual(str(response), 'foo &amp; bar\nspam &amp; egg\n')


class NamespacedCompositeViewWithPostTests(TestCase):

    def test_post_fully_rendered(self):
        """When the ``StackedCompositeViewWithPost`` is an inner composite
           and that the POST is handled by a another branch of the
           tree the request is still POST but should be answered
           as if it was a GET"""

        class FixedResponseValue(LeafCompositeView):

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class TestComposite(NamespacedCompositeViewWithPost):
            template_name = 'namespaced_composite_test.html'

            composites = dict(
                one=(FixedResponseValue, dict(response='foo & bar')),
                two=(FixedResponseValue, dict(response='spam & egg')),
            )
        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertEqual(str(response), 'foo &amp; bar\nspam &amp; egg\n')

    def test_post_with_several_subcomposite(self):
        """Same test as above except there is several subcomposite
        each subcomposite returns a response, which are rendered
        in the response"""

        class LeafCompositeWithPost(LeafCompositeView):

            template_name = 'hello.html'

            def post(self, request, *args, **kwargs):
                return 'response from post'

        class FixedResponseValue(LeafCompositeView):

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class TestComposite(NamespacedCompositeViewWithPost):
            template_name = 'namespaced_composite_test.html'

            composites = dict(
                one=LeafCompositeWithPost,
                two=(FixedResponseValue, dict(response='another subcomposite')),
            )

        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            expected = 'response_from_post\nanother subcomposite\n\n'
            self.assertTrue(str(response), expected)

    def test_post_request_redirect(self):
        """If a POST request is submitted subcomposite can return a redirect
        if it is the case the response must be forwared"""

        class LeafCompositeRedirectOnPost(LeafCompositeView):

            template_name = 'hello.html'

            def post(self, request, *args, **kwargs):
                return HttpResponseRedirect('index')

        class TestComposite(NamespacedCompositeViewWithPost):
            template_name = 'stacked_composite.html'

            composites = dict(one=LeafCompositeRedirectOnPost)

        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertTrue(isinstance(response, HttpResponseRedirect))

    def test_post_request_redirect_wiht_several_subcomposites(self):
        """If a POST request is submitted subcomposite can return a redirect
        if it is the case the response must be forwared even if other sub
        composites were rendered"""

        class FixedResponseValue(LeafCompositeView):

            template_name = 'hello.html'

            response = None

            def render_to_response(self, context, **response_kwargs):
                return self.response

        class LeafCompositeRedirectOnPost(LeafCompositeView):

            template_name = 'hello.html'

            def post(self, request, *args, **kwargs):
                return HttpResponseRedirect('index')

        class TestComposite(NamespacedCompositeViewWithPost):
            template_name = 'stacked_composite.html'

            composites = dict(
                one=(FixedResponseValue, dict(response='whatever')),
                two=LeafCompositeRedirectOnPost,
            )

        request = HttpRequest()
        request.method = 'POST'
        view = TestComposite.as_view()
        response = view(request)
        with self.settings(TEMPLATE_DIRS=(TEST_TEMPLATE_DIR,)):
            self.assertTrue(isinstance(response, HttpResponseRedirect))
