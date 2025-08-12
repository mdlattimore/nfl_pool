from allauth.account.views import PasswordChangeView
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    def get_success_url(self):
        # redirect to home, profile, or wherever you want
        return reverse_lazy('dashboard')  # or '/' if that's your root view
