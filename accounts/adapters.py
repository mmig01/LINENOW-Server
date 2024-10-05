from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import authenticate

class CustomUserAccountAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        """
        Saves a new `User` instance using information provided in the
        signup form.
        """
        from allauth.account.utils import user_field

        user = super().save_user(request, user, form, False)
        user_field(user, 'phone_number', request.data.get('phone_number'))
        user_field(user, 'name', request.data.get('name'))
        user_field(user, 'username', request.data.get('phone_number'))
        user.save()
        return user