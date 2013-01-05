from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.contrib.auth.views import redirect_to_login


class LoginRequiredMixin(object):

    login_url_name = 'login'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect_to_login(request.get_full_path(), reverse(self.login_url_name))
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class PermissionRequiredMixin():

    login_url_name = 'login'

    is_staff = False
    is_superuser = False

    def get_permissions_required(self):
        return self.permissions_required

    def dispatch(self, request, *args, **kwargs):
        has_permission = request.user.has_perm(self.get_permissions_required())

        if not has_permission:
            return redirect_to_login(request.get_full_path(), reverse(self.login_url_name))

        if self.is_staff and not request.user.is_staff:
            return HttpResponseForbidden
        if self.is_superuser and not request.user.is_staff:
            return HttpResponseForbidden

        return super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)
