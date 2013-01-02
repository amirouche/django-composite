from django.test import TestCase

from ..views import add_url
from ..views import ViewCollection
from ..views import add_view_collection


class CollectionTests(TestCase):

    def test_add_url(self):

        application_name = 'test_collection'

        def test_view(request):
            pass

        class AddUrlTestViewCollection(ViewCollection):
            application_namespace = 'add_url'

            add_url('add_url_test/', test_view)

        urlpatterns = AddUrlTestViewCollection.include_urls('testing')
        # FIXME

    def test_add_collection(self):


        def nested_test_view(request):
            pass

        class NestedViewCollection(ViewCollection):
            application_namespace = 'collection'
            add_url('add_url_test/', nested_test_view)

        class ParentViewCollection(ViewCollection):
            application_namespace = 'parent'

            add_view_collection('test/', NestedViewCollection, 'nested')

        urlpatterns = ParentViewCollection.include_urls('instance')
        import debug
