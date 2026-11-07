from django import forms


class CheckoutForm(forms.Form):
    checkout_token = forms.UUIDField(widget=forms.HiddenInput)
    full_name = forms.CharField(max_length=255, strip=True)
    email = forms.EmailField(max_length=254)
    address = forms.CharField(max_length=2000, strip=True, widget=forms.Textarea)
