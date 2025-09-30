from django import forms

class SimpleItemForm(forms.Form):
    item_name = forms.CharField(max_length=100)
    storage = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea, required=False)