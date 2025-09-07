from django import forms


class CustomSignupForm(forms.Form):
    first_name = forms.CharField(max_length=30, label="First Name",
                                 required=True)
    last_name = forms.CharField(max_length=30, label="Last Name", required=True)

    def signup(self, request, user):
        """
        Called by Allauth after the user instance is created.
        Here we set first_name and last_name.
        """
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
        return user
