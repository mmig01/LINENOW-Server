# forms.py
from allauth.account.forms import SignupForm
from django import forms
from utils.turnstile import verify_turnstile_token

class CustomSignupForm(SignupForm):
    phone_number = forms.CharField(max_length=15, required=True)
    name = forms.CharField(max_length=50, required=True)
    turnstile_token = forms.CharField(widget=forms.HiddenInput(), required=True)

    def clean(self):
        cleaned_data = super().clean()
        turnstile_token = cleaned_data.get('turnstile_token')

        # Turnstile 토큰 검증
        if not verify_turnstile_token(turnstile_token):
            raise forms.ValidationError("Turnstile verification failed. Please try again.")
        return cleaned_data