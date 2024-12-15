# Tagging Publications

## Example Overview

- **Objective**: This example demonstrates how to implement tagging functionality in a Django form using `django_tomselect`. Users can create new tags dynamically or select from existing ones. The tags are validated and saved to the database with support for autocomplete and real-time updates.
  - **Problem Solved**: It simplifies tagging workflows by enabling users to create and reuse tags seamlessly while ensuring data validation.
  - **Features Highlighted**:
    - Support for dynamic tag creation with the `create` feature.
    - Real-time autocomplete of existing tags using `django_tomselect`.

- **Use Case**:
  - Content management systems where articles or products require tagging for organization and filtering.
  - Applications requiring user-generated metadata to categorize or describe entities.

- **Visual Elements**:
  *(Placeholders for images or GIFs)*:
  - `![Screenshot: Tag Input Field](path-to-image)`
  - `![GIF: Adding Tags Dynamically](path-to-gif)`

## Key Code Segments

### Forms
The form uses a custom `DynamicTagField`, a subclass of `TomSelectMultipleChoiceField`, to allow dynamic creation and selection of tags.

```python
class DynamicTagField(TomSelectMultipleChoiceField):
    """A custom field that allows new values to be created on the fly."""

    def clean(self, value):
        """Override to allow values that aren't in the autocomplete results yet."""
        if not value:
            if self.required:
                raise ValidationError(self.error_messages["required"], code="required")
            return []

        # Convert all values to strings
        str_values = [str(v) for v in value]

        # We don't need to validate against autocomplete results
        # since we allow new values to be created
        return str_values


class TaggingForm(forms.Form):
    """Form for managing publication tags with validation."""

    tags = DynamicTagField(
        config=TomSelectConfig(
            url="autocomplete-publication-tag",
            value_field="value",
            label_field="label",
            placeholder="Enter tags...",
            highlight=True,
            create=True,
            minimum_query_length=2,
            max_items=10,
            plugin_dropdown_header=PluginDropdownHeader(
                title="Publication Tags",
                extra_columns={"usage_count": "Usage Count", "created_at": "Created"},
            ),
            plugin_remove_button=PluginRemoveButton(
                title="Remove tag", label="×", class_name="remove-tag"
            ),
        ),
        help_text=(
            "Enter or select tags. Tags must be 2-50 characters long, "
            "contain only letters, numbers, hyphens, and underscores, "
            "and start/end with letters or numbers."
        ),
    )

    def clean_tags(self):
        """Validate tags and create/update them in the database."""
        tag_names = self.cleaned_data.get("tags", [])

        if len(tag_names) < 1:
            raise ValidationError("Please add at least one tag")

        if len(tag_names) > 10:
            raise ValidationError("Maximum 10 tags allowed")

        # Check for duplicates (case-insensitive)
        lower_names = [name.lower() for name in tag_names]
        if len(lower_names) != len(set(lower_names)):
            raise ValidationError("Duplicate tags are not allowed")

        # Process each tag
        tags = []
        for name in tag_names:
            # Clean the tag name
            name = name.lower().strip()

            # Validate the tag format
            if len(name) < 2:
                raise ValidationError(f"Tag '{name}' is too short")

            if not all(c.isalnum() or c in "-_" for c in name):
                raise ValidationError(f"Tag '{name}' contains invalid characters")

            if "--" in name or "__" in name:
                raise ValidationError(
                    f"Tag '{name}' contains consecutive special characters"
                )

            if not name[0].isalnum() or not name[-1].isalnum():
                raise ValidationError(
                    f"Tag '{name}' must start and end with a letter or number"
                )

            # Try to get existing tag or create new one
            tag, _ = PublicationTag.objects.get_or_create(
                name=name,
                defaults={
                    "is_approved": True,
                },
            )
            tags.append(tag)

        return tags
```

**Explanation**:
- The `DynamicTagField` allows users to add new tags on the fly.
- The `clean_tags` method ensures all tags are validated and saved to the database.

**Repository Link**: [View TaggingForm Code](#)

### Templates
The form is rendered in the `tagging_publication.html` template, providing an intuitive interface for managing tags.

```html
<form method="post">
    {% csrf_token %}
    <div class="mb-3">
        {{ form.tags }}
        {% if form.tags.errors %}
            <div class="alert alert-danger mt-2">
                {{ form.tags.errors }}
            </div>
        {% endif %}
    </div>
    <button type="submit" class="btn btn-primary">Save Tags</button>
</form>

{% if existing_tags %}
<div class="existing-tags">
    <h3 class="h5 mb-3">Existing Tags</h3>
    <table class="table table-hover">
        <thead class="table-light">
            <tr>
                <th>Tag</th>
                <th>Usage Count</th>
                <th>Created</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for tag in existing_tags %}
            <tr>
                <td>{{ tag.name }}</td>
                <td>{{ tag.usage_count }}</td>
                <td>{{ tag.created_at|date:"M j, Y" }}</td>
                <td>{{ tag.is_approved|yesno:"Approved,Pending" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}
```

**Key Elements**:
- Includes error handling to display validation messages for invalid tags.
- Lists existing tags in a table for user reference.

**Repository Link**: [View Template Code](#)

### Autocomplete Views
The `autocomplete-publication-tag` endpoint provides tag suggestions based on user input.

```python
class AutocompletePublicationTag(AutocompleteModelView):
    model = PublicationTag
    search_lookups = ["name__icontains"]
```

**Repository Link**: [View Autocomplete Code](#)

### Dependencies
- Models: A `PublicationTag` model with fields like `name`, `usage_count`, and `is_approved`.
- Autocomplete URLs: Ensure `autocomplete-publication-tag` is properly configured.

## Design and Implementation Notes

- **Key Features**:
  - `create` feature allows users to add new tags dynamically.
  - Validation ensures only valid tags are added, preventing duplicates or invalid formats.

- **Design Decisions**:
  - The `DynamicTagField` simplifies the addition of new tags while reusing existing logic.
  - Error messages and validation rules provide clear feedback to users.

- **Alternative Approaches**:
  - Use a static list of tags for smaller applications (less flexible).
  - Implement custom JavaScript for tag creation and validation (more complex).

- **Potential Extensions**:
  - Add a feature to merge duplicate tags.
  - Introduce tagging suggestions based on user behavior or frequently used tags.
