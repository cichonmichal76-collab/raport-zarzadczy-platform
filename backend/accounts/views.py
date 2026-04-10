from django.contrib.auth.views import LoginView


class AppLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if response.status_code in (301, 302) and response.has_header("Location"):
            response["Location"] = "/bi/"
        return response
