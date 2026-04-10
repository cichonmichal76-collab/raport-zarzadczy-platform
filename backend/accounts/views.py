from django.contrib.auth.views import LoginView


class AppLoginView(LoginView):
    template_name = "registration/login.html"
