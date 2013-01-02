from django.utils.decorators import method_decorator
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class PermissionRequiredMixin(object):

    def get_permissions_required(self):
        return self.permissions_required

    def dispatch(self, request, *args, **kwargs):
        has_permission = request.user.has_perm(self.get_permissions_required())

        if not has_permission:
            return redirect_to_login(request.get_full_path())

        return super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)
