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

from .forms import FilteredForm, Form
from .views import (
    DemoEditionAutocompleteView,
    DemoMagazineAutocompleteView,
    add_view,
    form_test_view,
    listview_view,
    model_form_test_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", form_test_view, name="demo"),
    path("model/", model_form_test_view, name="demo_with_model"),
    path("bs4/", FormView.as_view(form_class=Form, template_name="base4.html"), name="demo-bs4"),
    path("autocomplete-edition/", DemoEditionAutocompleteView.as_view(), name="autocomplete-edition"),
    path("autocomplete-magazine/", DemoEditionAutocompleteView.as_view(), name="autocomplete-magazine"),
    path("listview/", listview_view, name="listview"),
    path("add/", add_view, name="add"),
    path("filtered/", FormView.as_view(form_class=FilteredForm, template_name="base5.html"), name="filtered"),
    path("filtered-bs4/", FormView.as_view(form_class=FilteredForm, template_name="base4.html"), name="filtered-bs4"),
]
