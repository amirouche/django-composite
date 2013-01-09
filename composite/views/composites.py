from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.admin.util import get_fields_from_path
from django.contrib.admin.util import lookup_needs_distinct
from django.contrib.admin.filters import FieldListFilter
from django.contrib.admin.helpers import ActionForm
from django.contrib.admin.helpers import checkbox
from django.forms.models import modelformset_factory
from django.forms.models import modelform_factory
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy
from django.utils.translation import ungettext
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.http import urlencode
from django.shortcuts import redirect
from django.contrib import messages
from django.db import models

from base import StackedCompositeView
from .base import LeafCompositeView

# Changelist settings
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
TO_FIELD_VAR = 't'
IS_POPUP_VAR = 'pop'
ERROR_FLAG = 'e'

IGNORED_PARAMS = (
    ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, TO_FIELD_VAR)

# Text to display within change-list table cells if the value is blank.
EMPTY_CHANGELIST_VALUE = ugettext_lazy('(None)')


class RequestOperationsMixin(object):

    # FIXME: move this into a function

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None:
            new_params = dict()
        if remove is None:
            remove = list()
        params = dict(self.request.GET.items())
        for r in remove:
            for k in list(params):
                if k.startswith(r):
                    del params[k]
        for k, v in new_params.items():
            if v is None:
                if k in params:
                    del params[k]
            else:
                params[k] = v
        return '?%s' % urlencode(params)


class SortableTable(LeafCompositeView, RequestOperationsMixin):
    template_name = 'composite/sortable_table.html'

    list_per_page = 100
    list_max_show_all = 100
    list_display = (unicode,)
    ordering = ()
    list_select_related = ()
    search_fields = ()

    def __init__(
            self,
            **kwargs
        ):
        self.model_class = kwargs.pop('model_class')
        self.queryset = kwargs.pop('queryset', None)
        self.filter = kwargs.pop('filter', None)
        super(SortableTable, self).__init__(**kwargs)

    def get_ordering(self):
        params = dict(self.request.GET.items())
        if ORDER_VAR in params:
            # Clear ordering and used params
            ordering = []
            order_params = params[ORDER_VAR].split('.')
            for p in order_params:
                try:
                    none, pfx, idx = p.rpartition('-')
                    field_name = self.list_display[int(idx)]
                    order_field = self.get_ordering_field(field_name)
                    if not order_field:
                        continue  # No 'admin_order_field', skip it
                    ordering.append(pfx + order_field)
                except (IndexError, ValueError):
                    continue  # Invalid ordering specified, skip it.
        else:
            ordering = list(self._get_default_ordering())

        # Ensure that the primary key is systematically present in the list of
        # ordering fields so we can guarantee a deterministic order across all
        # database backends.
        pk_name = self.model_class._meta.pk.name
        if not (set(ordering) & set(['pk', '-pk', pk_name, '-' + pk_name])):
            # The two sets do not intersect, meaning the pk isn't present. So
            # we add it.
            ordering.append('-pk')

        return ordering

    def _queryset(self):
        (filter_specs, has_filters, use_distinct) = self.filter.get_filters()

        # Then, we let every list filter modify the queryset to its liking.
        if self.queryset:
            qs = self.queryset
        else:
            qs = self.model_class.objects.all()
        for filter_spec in filter_specs:
            new_qs = filter_spec.queryset(self.request, qs)
            if new_qs is not None:
                qs = new_qs

        # Use select_related() if one of the list_display options is a field
        # with a relationship and the provided queryset doesn't already have
        # select_related defined.
        if not qs.query.select_related:
            if self.list_select_related:
                qs = qs.select_related()
            else:
                for field_name in self.list_display:
                    try:
                        field = self.model_class._meta.get_field(field_name)
                    except models.FieldDoesNotExist:
                        pass
                    else:
                        if isinstance(field.rel, models.ManyToOneRel):
                            qs = qs.select_related()
                            break

        # Set ordering.
        ordering = self.get_ordering()
        qs = qs.order_by(*ordering)

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        search_query = self.request.GET.get(SEARCH_VAR, '')
        if self.search_fields and search_query:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in self.search_fields]
            for bit in self.query.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                qs = qs.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.lookup_opts, search_spec):
                        use_distinct = True
                        break

        if use_distinct:
            return qs.distinct()
        else:
            return qs

    def get_results(self):
        full_result_count = self.model_class.objects.count()
        q = self._queryset()
        if ALL_VAR in self.request.GET:
            objects = q[self.list_max_show_all:]
        else:
            paginator = Paginator(q, self.list_per_page)
            page = self.request.GET.get(PAGE_VAR)
            try:
                objects = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                objects = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999),
                # deliver last page of results.
                objects = paginator.page(paginator.num_pages)
        paginator = objects
        can_show_all = len(objects) < self.list_max_show_all
        objects = list(self.items(objects))  # FIXME: template engine doesn't
                                             # like generators
        return dict(
            full_result_count=full_result_count,
            can_show_all=can_show_all,
            objects=objects,
            paginator=objects,
        )

    def _get_default_ordering(self):
        """Returns default ordering based on instance configuration falling
        back to model default order"""
        ordering = []
        if self.ordering:
            ordering = self.ordering
        elif self.model_class._meta.ordering:
            ordering = self.model_class._meta.ordering
        return ordering

    def get_ordering_field(self, field_name):
        """
        Returns the proper model field name corresponding to the given
        field_name to use for ordering. field_name may either be the name of a
        proper model field or the name of a method (on the admin or model) or a
        callable with the 'admin_order_field' attribute. Returns None if no
        proper model field name can be matched.
        """
        try:
            field = self.model_class._meta.get_field(field_name)
            return field.name
        except models.FieldDoesNotExist:
            # See whether field_name is a name of a non-field
            # that allows sorting.
            if callable(field_name):
                attr = field_name
            elif hasattr(self, field_name):
                attr = getattr(self, field_name)
            else:
                attr = getattr(self.model_class, field_name)
            return getattr(attr, 'admin_order_field', None)

    def get_ordering_field_columns(self):
        """
        Returns a SortedDict of ordering field column numbers and asc/desc
        """
        params = dict(self.request.GET.items())
        ordering = self._get_default_ordering()
        # We must cope with more than one column having the same underlying
        # sort field, so we base things on column numbers.
        ordering_fields = SortedDict()

        if ORDER_VAR not in params:
            # for ordering specified on ChangeList or model Meta, we don't know
            # the right column numbers absolutely, because there might be more
            # than one column associated with that ordering, so we guess.
            for field in ordering:
                if field.startswith('-'):
                    field = field[1:]
                    order_type = 'desc'
                else:
                    order_type = 'asc'
                for index, attr in enumerate(self.list_display):
                    if self.get_ordering_field(attr) == field:
                        ordering_fields[index] = order_type
                        break
        else:
            for p in params[ORDER_VAR].split('.'):
                none, pfx, idx = p.rpartition('-')
                try:
                    idx = int(idx)
                except ValueError:
                    continue  # skip it
                ordering_fields[idx] = 'desc' if pfx == '-' else 'asc'
        return ordering_fields

    def get_sort_infos(self, i):
        ordering_field_columns = self.get_ordering_field_columns()
        order_type = ''
        new_order_type = 'asc'
        sort_priority = 0
        sorted = False

        # Is it currently being sorted on?
        if i in ordering_field_columns.keys():
            sorted = True
            order_type = ordering_field_columns[i].lower()
            sort_priority = list(ordering_field_columns).index(i) + 1
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[order_type]

        # build new ordering param
        o_list_primary = []  # URL for making this field the primary sort
        o_list_remove = []  # URL for removing this field from sort
        o_list_toggle = []  # URL for toggling order type for this field
        make_qs_param = lambda t, n: ('-' if t == 'desc' else '') + str(n)

        for j, ot in ordering_field_columns.items():
            if j == i:  # Same column
                param = make_qs_param(new_order_type, j)
                # We want clicking on this header to bring the ordering
                # to the front
                o_list_primary.insert(0, param)
                o_list_toggle.append(param)
                # o_list_remove - omit
            else:
                param = make_qs_param(ot, j)
                o_list_primary.append(param)
                o_list_toggle.append(param)
                o_list_remove.append(param)

        if i not in ordering_field_columns:
            o_list_primary.insert(0, make_qs_param(new_order_type, i))
        ascending = order_type == 'asc'
        url_primary = self.get_query_string({ORDER_VAR: '.'.join(o_list_primary)})
        url_remove = self.get_query_string({ORDER_VAR: '.'.join(o_list_remove)})
        url_toggle = self.get_query_string({ORDER_VAR: '.'.join(o_list_toggle)})
        return dict(
            sortable=True,
            sorted=sorted,
            ascending=ascending,
            sort_priority=sort_priority,
            url_primary=url_primary,
            url_remove=url_remove,
            url_toggle=url_toggle,
        )

    def headers(self):
        for i, item in enumerate(self.list_display):
            if item is unicode:
                yield dict(text='', sortable=False)
            elif callable(item):
                text = getattr(item, 'verbose_name', item.__name__)
                infos = dict(text=text, sortable=False)
                if hasattr(item, 'admin_order_field'):
                     infos.update(self.get_sort_infos(i))
                yield infos
            elif item in self.model_class._meta.get_all_field_names():
                infos = self.get_sort_infos(i)
                text = getattr(self.model_class, 'verbose_name', item)
                infos['text'] = text
                yield infos
            elif hasattr(self.model_class, item):
                attr = getattr(self.model_class, item)
                text = getattr(attr, '__name__', item)
                infos = dict(text=text)
                if hasattr(attr, 'admin_order_field'):
                    infos.update(self.get_sort_infos(i))
                else:
                    infos['sortable'] = False
                yield infos
            else:
                yield dict(text=item, sortable=False)

    def item(self, object):
        for item in self.list_display:
            if item is unicode:
                yield unicode(object)
            elif callable(item):
                yield item(object)
            elif item in self.model_class._meta.get_all_field_names():
                field = self.model_class._meta.get_field_by_name(item)[0]
                if len(field.choices):
                    method_name = 'get_%s_display' % item
                    display_method = getattr(object, method_name)()
                    yield display_method
                else:
                    yield getattr(object, item)
            elif hasattr(self.model_class, item):
                attr = getattr(object, item)
                if callable(attr):
                    yield attr()
                else:
                    yield attr
            else:
                raise Exception("Couldn't render %s in list_display" % item)

    def items(self, objects):
        for object in objects:
            yield list(self.item(object))  # FIXME

    def get_context_data(self, **kwargs):
        context = super(SortableTable, self).get_context_data(**kwargs)
        context['headers'] = list(self.headers())  # FIXME
        context.update(self.get_results())
        num_sorted_fields = 0
        for h in self.headers():
            if h['sortable'] and h['sorted']:
                num_sorted_fields += 1
        context['num_sorted_fields'] = num_sorted_fields
        return context


class ChangeList(SortableTable):

    template_name = 'composite/changelist.html'

    list_editable = ()

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

    def form_class(self, **kwargs):
        """
        Returns a Form class for use in the Formset on the changelist page.
        """
        defaults = {
            'formfield_callback': self.formfield_for_dbfield,
        }
        defaults.update(kwargs)
        return modelform_factory(self.model_class, **defaults)

    def formset_class(self, **kwargs):
        """
        Returns a FormSet class for use on the changelist page if list_editable
        is used.
        """
        defaults = {
            'formfield_callback': self.formfield_for_dbfield,
        }
        defaults.update(kwargs)
        FormSet = modelformset_factory(
            self.model_class,
            self.form_class(),
            extra=0,
            fields=self.list_editable,
            **defaults
        )
        return FormSet

    def formset(self):
        qs = self._queryset()
        FormSet = self.formset_class()
        if self.request.method == 'POST':
            formset = FormSet(self.request.POST, self.request.FILES, queryset=qs)
        else:
            formset = FormSet(queryset=qs)
        return formset

    def get_context_data(self):
        context = super(ChangeList, self).get_context_data()
        context['formset'] = self.formset()
        return context

    def items(self, objects):
        for i, object in enumerate(objects):
            yield list(self.item(object, i))  # FIXME

    def item(self, object, i):
        formset = self.formset()
        form = formset.forms[i]
        fields = super(ChangeList, self).item(object)
        for name, field in zip(self.list_display, fields):
            if name in self.list_editable:  # Use formset.form instead
                field = form[name]
                field = mark_safe(force_text(field.errors) + force_text(field))
                yield field
            else:
                yield field

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # FIXME: catch action failed

        # Handle POSTed bulk-edit data.
        if (request.method == 'POST'
            and self.list_editable
            and '_save' in request.POST):
            formset = self.formset()
            if formset.is_valid():
                changecount = 0
                for form in formset.forms:
                    if form.has_changed():
                        # FIXME: add hook
                        # cf. django/contrib/admin/options.py:changelist_view
                        obj = form.save()
                        obj.save()
                        # form.save_m2m()
                        # change_msg = self.construct_change_message(request, form, None)
                        # self.log_change(request, obj, change_msg)
                        changecount += 1

                if changecount:
                    meta = self.model_class._meta
                    if changecount == 1:
                        name = force_text(meta.verbose_name)
                    else:
                        name = force_text(meta.verbose_name_plural)
                    msg = ungettext("%(count)s %(name)s was changed successfully.",
                                    "%(count)s %(name)s were changed successfully.",
                                    changecount) % {'count': changecount,
                                                    'name': name,
                                                    'obj': force_text(obj)}
                    messages.info(request, msg)
                url = '%s%s' % (
                    self.request.get_full_path(),
                    self.request.META['QUERY_STRING']
                )
                return redirect(url)
        return self.render_to_response(context)


class Filter(StackedCompositeView, RequestOperationsMixin):

    template_name = 'composite/filter.html'

    list_filter = ()

    def __init__(self,  **kwargs):
        self.model_class = kwargs.pop('model_class', None)
        super(Filter, self).__init__(**kwargs)

    def _composites(self, request, *args, **kwargs):
        for spec in self.filter_specs:
            class SpecFilterComposite(LeafCompositeView):

                template_name = spec.template

                def get_context_data(self, **kwargs):
                    ctx = super(SpecFilterComposite, self).get_context_data(**kwargs)
                    ctx['title'] = spec.title
                    ctx['choices'] = list(spec.choices(self.parent))
                    ctx['spec'] = spec
                    return ctx

            spec_composite = SpecFilterComposite(parent=self)
            yield spec_composite

    def get_filters(self):
        lookup_params = dict(self.request.GET.items())
        use_distinct = False

        filter_specs = []
        list_filters = self.list_filter
        if list_filters:
            for list_filter in list_filters:
                if callable(list_filter):
                    # This is simply a custom list filter class.
                    spec = list_filter(
                        self.request,
                        lookup_params,
                        self.model_class,
                        self,
                    )
                else:
                    field_path = None
                    if isinstance(list_filter, (tuple, list)):
                        # This is a custom FieldListFilter class for a given
                        # field.
                        field, field_list_filter_class = list_filter
                    else:
                        # This is simply a field name, so use the default
                        # FieldListFilter class that has been registered for
                        # the type of the given field.
                        field, field_list_filter_class = list_filter, FieldListFilter.create
                    if not isinstance(field, models.Field):
                        field_path = field
                        field = get_fields_from_path(self.model_class, field_path)[-1]
                    spec = field_list_filter_class(
                        field,
                        self.request,
                        lookup_params,
                        self.model_class,
                        self,
                        field_path=field_path
                    )
                    # Check if we need to use distinct()
                    use_distinct = (
                        use_distinct or
                        lookup_needs_distinct(
                            self.model_class._meta,
                            field_path
                        )
                    )
                if spec and spec.has_output():
                    filter_specs.append(spec)
        self.filter_specs = filter_specs
        return filter_specs, bool(filter_specs), use_distinct
