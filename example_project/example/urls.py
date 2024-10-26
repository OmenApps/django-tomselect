"""URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import FormView

from .autocompletes import DemoEditionAutocompleteView, DemoMagazineAutocompleteView
from .forms import DependentForm, Form
from .views import (
    create_view,
    form_test_view,
    htmx_form_fragment_view,
    htmx_view,
    listview_view,
    model_form_edit_test_view,
    model_form_test_view,
    update_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", form_test_view, name="demo"),
    path("model/", model_form_test_view, name="demo_with_model"),
    path("model/<path:pk>/", model_form_edit_test_view, name="demo_with_model_edit"),
    path("bs4/", FormView.as_view(form_class=Form, template_name="base4.html"), name="demo-bs4"),
    path("autocomplete-edition/", DemoEditionAutocompleteView.as_view(), name="autocomplete-edition"),
    path("autocomplete-magazine/", DemoMagazineAutocompleteView.as_view(), name="autocomplete-magazine"),
    path("listview/", listview_view, name="listview"),
    path("create/", create_view, name="create"),
    path("update/<path:pk>/", update_view, name="update"),
    path("dependent/", FormView.as_view(form_class=DependentForm, template_name="base5.html"), name="dependent"),
    path(
        "dependent-bs4/", FormView.as_view(form_class=DependentForm, template_name="base4.html"), name="dependent-bs4"
    ),
    path("htmx/", htmx_view, name="htmx"),
    path("htmx-form-fragment/", htmx_form_fragment_view, name="htmx-form-fragment"),
]
