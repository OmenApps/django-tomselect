# Introduction to the Example Project

The example project demonstrates how to use the `django-tomselect` package in a Django project. It consists of a number of basic, intermediate, and advanced implementations all using the theme of publishing articles in a magazine.

## Prerequisites

- Python 3.10+
- Django 4.2+
- `django-tomselect` package
- Basic understanding of Django forms and views

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/OmenApps/django-tomselect.git
    ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Example Project

1. Navigate to the `example_app` directory:

   ```bash
   cd example_app
   ```

2. Apply the migrations:

   ```bash
   python manage.py migrate
   ```

3. Create the example data:

   ```bash
   python manage.py create_examples
   ```

4. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

5. Run the Django development server:

   ```bash
    python manage.py runserver 0.0.0.0:8000
    ```

6. Open the browser and go to `http://localhost:8000/` to view the example project.


## Basic Examples

- [Default Styling](default.md)
- [Bootstrap 4 Styling](bs4.md)
- [Bootstrap 5 Styling](bs5.md)
- [HTMX Integration](htmx.md)

## Intermediate Examples

- [Filter by Magazine](filter_by_magazine.md)
- [Filter by Category](filter_by_category.md)
- [Exclude by Primary Author](exclude_by_primary_author.md)
- [View Range Based Data](view_range_based_data.md)
- [Tagging](tagging.md)
- [Custom Content Display](custom_content_display.md)
- [Weighted Author Search](weighted_author_search.md)

## Advanced Examples

- [Three-Level Filter-By](three_level_filter_by.md)
- [Rich Article Select](rich_article_select.md)
- [Article List and Create](article_list_and_create.md)
- [Article Bulk Actions](article_bulk_actions.md)
