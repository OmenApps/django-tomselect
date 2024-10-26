"""View tests for the django-tomselect package."""

import json
from unittest.mock import Mock, patch
from urllib.parse import quote, urlencode

import pytest
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import Permission
from django.db.models.sql.where import NothingNode
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.test import Client
from django.urls import reverse

from django_tomselect.views import (
    FILTERBY_VAR,
    PAGE_SIZE,
    PAGE_VAR,
    SEARCH_VAR,
    AutocompleteView,
)
from example_project.example.models import Edition, Magazine, ModelFormTestModel
