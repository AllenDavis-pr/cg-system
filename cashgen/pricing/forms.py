from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "base_margin", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Category name"}),
            "base_margin": forms.NumberInput(attrs={"step": "0.01", "placeholder": "0.30"}),
            "description": forms.Textarea(attrs={"placeholder": "Optional description", "rows": 2}),
        }
