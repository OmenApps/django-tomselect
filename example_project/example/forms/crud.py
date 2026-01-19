"""Forms for the example project demonstrating TomSelectConfig usage."""

from django import forms

from example_project.example.models import Author, Category, Edition, Magazine


class AuthorForm(forms.ModelForm):
    """Form for creating and editing authors."""

    class Meta:
        """Meta options for the model form."""

        model = Author
        fields = ["name", "bio"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control mb-3"}),
            "bio": forms.Textarea(attrs={"class": "form-control mb-3", "rows": 4}),
        }


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories."""

    class Meta:
        """Meta options for the model form."""

        model = Category
        fields = ["name", "parent"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control mb-3"}),
            "parent": forms.Select(attrs={"class": "form-control mb-3"}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize the form and adjust parent field queryset."""
        super().__init__(*args, **kwargs)
        self.fields["parent"].required = False

        # If we're editing an existing category
        if self.instance.pk:
            # Exclude the current category and its children from parent choices
            descendants = Category.objects.filter(parent=self.instance)
            self.fields["parent"].queryset = Category.objects.exclude(
                pk__in=[self.instance.pk] + [desc.pk for desc in descendants]
            )

        self.fields["parent"].empty_label = "No Parent (Root Category)"


class MagazineForm(forms.ModelForm):
    """Form for creating and editing magazines."""

    class Meta:
        """Meta options for the model form."""

        model = Magazine
        fields = ["name", "accepts_new_articles"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control mb-3"}),
            "accepts_new_articles": forms.Select(attrs={"class": "form-control mb-3"}),
        }


class EditionForm(forms.ModelForm):
    """Form for creating and editing editions."""

    class Meta:
        """Meta options for the model form."""

        model = Edition
        fields = ["name", "year", "pages", "pub_num", "magazine"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control mb-3"}),
            "year": forms.TextInput(attrs={"class": "form-control mb-3", "type": "number"}),
            "pages": forms.TextInput(attrs={"class": "form-control mb-3", "type": "number"}),
            "pub_num": forms.TextInput(attrs={"class": "form-control mb-3"}),
            "magazine": forms.Select(attrs={"class": "form-control mb-3"}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize the form and set magazine field to required."""
        super().__init__(*args, **kwargs)
        self.fields["magazine"].required = True
