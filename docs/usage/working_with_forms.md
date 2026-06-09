# Working with Forms

Integrating `django_tomselect` into your forms is straightforward and leverages the familiar patterns of standard Django forms and ModelForms. Whether you’re working with simple stand-alone forms or complex model-backed forms with dynamic fields and validation, `django_tomselect` fits naturally into the Django form ecosystem.

## Basic Form Integration

You can start using `django_tomselect` fields in regular Django forms without any additional configuration beyond defining the widget in the field. For example, to create a form that allows users to filter results based on a selected `Magazine`:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect import TomSelectConfig

class MagazineFilterForm(forms.Form):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            placeholder="Select a magazine...",
            preload="focus",
            highlight=True,
        )
    )
```

This form can be used to filter data in a view or dynamically update a portion of a page with JavaScript. The TomSelect widget handles autocompletion, pagination, and other interactive features automatically.

## Working with ModelForms

When dealing with database-backed models, `ModelForm` provides a more integrated solution. By using `TomSelectModelChoiceField` or `TomSelectModelMultipleChoiceField`, you can seamlessly integrate autocompletes into your forms:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectModelMultipleChoiceField
from django_tomselect import TomSelectConfig
from .models import Article

class ArticleForm(forms.ModelForm):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        )
    )
    authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            placeholder="Select authors...",
            max_items=None,  # Allow any number of authors
        )
    )

    class Meta:
        model = Article
        fields = ["title", "magazine", "authors"]
```

ModelForms automatically populate initial values from the provided model instance, and saving the form updates the related database records as normal.

## Handling Initial Values

`django_tomselect` handles initial values just like any other Django form field. For ModelForms, the field will display the current related objects, so if you’re editing an existing `Article`:

```python
from django.shortcuts import get_object_or_404, TemplateResponse, redirect

def article_edit_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    form = ArticleForm(request.POST or None, instance=article)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("article-list")

    return TemplateResponse(request, "article_form.html", {"form": form})
```

When loading this form, the `magazine` and `authors` fields will be pre-filled with the article’s current magazine and authors, allowing users to adjust the selection as needed.

## Dynamic Form Fields

A powerful feature of `django_tomselect` is the ability to dynamically update form fields based on other fields’ values-also known as dependent or chained fields. For example, you might want the `edition` field to show only editions from the currently selected `magazine`.

```python
class DynamicArticleForm(forms.ModelForm):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        )
    )
    edition = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),  # Filter editions by selected magazine
        ),
        required=False,
    )

    class Meta:
        model = Article
        fields = ["title", "magazine", "edition"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set the initial value for 'edition' if the instance already has a related edition
        if self.instance and self.instance.magazine and self.instance.edition:
            self.fields["edition"].initial = self.instance.edition.pk
```

In this scenario, when the `magazine` field changes, the widget triggers the `edition` field to refresh its options via AJAX, ensuring users see only editions relevant to the chosen magazine.

## Form Validation

`django_tomselect` fields integrate with Django’s form validation system. You can write custom clean methods or field-specific validators just like any other form field. The following example ensures the selected `primary_author` is not also chosen as a contributing author:

```python
class AuthorArticleForm(forms.ModelForm):
    primary_author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
        )
    )
    contributing_authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),
        )
    )

    class Meta:
        model = Article
        fields = ["title", "primary_author", "contributing_authors"]

    def clean(self):
        cleaned_data = super().clean()
        primary = cleaned_data.get("primary_author")
        contributors = cleaned_data.get("contributing_authors", [])

        if primary and primary in contributors:
            raise forms.ValidationError(
                "The primary author cannot also be a contributing author."
            )
        return cleaned_data
```

## Form Rendering

Since `django_tomselect` fields are just Django form fields with a special widget, you can render them using all the standard approaches:

```html
<!-- Default rendering with form.as_p, as_ul, or as_table -->
{{ form.as_p }}

<!-- Render an individual field with labels, errors, and help text -->
<div class="mb-3">
    <label for="{{ form.magazine.id_for_label }}" class="form-label">
        {{ form.magazine.label }}
    </label>
    {{ form.magazine }}
    {% if form.magazine.errors %}
        <div class="invalid-feedback d-block">
            {{ form.magazine.errors }}
        </div>
    {% endif %}
    {% if form.magazine.help_text %}
        <small class="form-text text-muted">
            {{ form.magazine.help_text }}
        </small>
    {% endif %}
</div>
```

TomSelect’s JavaScript and CSS are automatically included based on your configuration. By combining this rendering flexibility with Django’s robust form ecosystem, you can easily integrate powerful autocomplete and selection features into even the most complex forms.
