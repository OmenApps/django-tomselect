"""Views for the example app."""

from typing import Optional

from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, reverse
from django.template.response import TemplateResponse

from .forms import DynamicArticleForm, FormHTMX, ModelForm
from .models import Article, Author, Category, Edition, ModelFormTestModel


def model_form_test_view(request: HttpRequest) -> HttpResponse:
    """View for the model form test page."""
    template = "base5.html"
    context = {}

    form = ModelForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
            form.save()
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect(reverse("demo_with_model"))

    context["form"] = form

    return TemplateResponse(request, template, context)


def model_form_edit_test_view(request: HttpRequest, instance_id: Optional[int] = None) -> HttpResponse:
    """View for the model form edit test page."""
    template = "base5.html"
    context = {}
    instance = None

    if instance_id:
        instance = ModelFormTestModel.objects.get(id=instance_id)

    form = ModelForm(request.POST or None, instance=instance)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
            form.save()
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect(reverse("demo_with_model"))

    context["form"] = form

    return TemplateResponse(request, template, context)


def edition_list_view(request: HttpRequest, page: int = 1) -> HttpResponse:
    """View for the edition list page."""
    template = "edition_list.html"
    context = {}

    editions = Edition.objects.all()
    paginator = Paginator(editions, 8)

    try:
        page_obj = paginator.get_page(page)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    context["page_obj"] = page_obj
    return TemplateResponse(request, template, context)


# def edition_create_view(request: HttpRequest) -> HttpResponse:
#     """View for the edition create page."""
#     # Here you would typically render a form to create a new edition
#     return TemplateResponse(request, "edition_form.html")


def create_view(request: HttpRequest) -> HttpResponse:  # pylint: disable=W0613
    """View for the create page."""
    return HttpResponse("This is a stub create page.")


def update_view(request: HttpRequest) -> HttpResponse:  # pylint: disable=W0613
    """View for the update page."""
    return HttpResponse("This is a stub update page.")


def htmx_view(request: HttpRequest) -> HttpResponse:
    """View for the htmx page."""
    template = "base5_htmx.html"
    context = {}

    return TemplateResponse(request, template, context)


def htmx_form_fragment_view(request: HttpRequest) -> HttpResponse:
    """View for the htmx form fragment page."""
    template = "base5_htmx_fragment.html"
    context = {}

    form = FormHTMX(request.POST or None)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect("/")

    context["form"] = form

    return TemplateResponse(request, template, context)


def article_list_view(request: HttpRequest, page: int = 1) -> HttpResponse:
    """View for the article list page."""
    template = "article_list.html"
    context = {}

    articles = Article.objects.all().prefetch_related("authors", "categories").select_related("magazine")

    paginator = Paginator(articles, 8)

    try:
        page_obj = paginator.get_page(page)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    context["page_obj"] = page_obj

    return TemplateResponse(request, template, context)


def article_create_view(request: HttpRequest) -> HttpResponse:
    """View for the article create page."""
    template = "article_form.html"
    context = {}

    form = DynamicArticleForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
            form.save()
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect(reverse("article-list"))

    context["form"] = form

    return TemplateResponse(request, template, context)


def article_update_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for the article update page."""
    template = "article_form.html"
    context = {}

    article = get_object_or_404(Article, pk=pk)
    form = DynamicArticleForm(request.POST or None, instance=article)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
            form.save()
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect(reverse("article-list"))

    context["form"] = form

    return TemplateResponse(request, template, context)


def article_publish_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for publishing a draft article."""
    article = get_object_or_404(Article, pk=pk)
    if article.status == Article.Status.DRAFT:
        article.status = Article.Status.ACTIVE
        article.save()
        messages.success(request, f'Article "{article.title}" has been published.')
    return redirect("article-list")


def article_archive_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for archiving an active article."""
    article = get_object_or_404(Article, pk=pk)
    if article.status == Article.Status.ACTIVE:
        article.status = Article.Status.ARCHIVED
        article.save()
        messages.success(request, f'Article "{article.title}" has been archived.')
    return redirect("article-list")


def load_subcategories(request):
    """AJAX view to load subcategories based on primary category selection."""
    primary_category_id = request.GET.get("primary_category")
    subcategories = Category.objects.filter(parent_id=primary_category_id)
    return JsonResponse({"subcategories": list(subcategories.values("id", "name"))})


def load_coauthors(request):
    """AJAX view to load potential coauthors excluding the main author."""
    main_author_id = request.GET.get("main_author")
    coauthors = Author.objects.exclude(id=main_author_id).annotate(
        article_count=Count("article"), active_articles=Count("article", filter=Q(article__status="active"))
    )
    return JsonResponse({"coauthors": list(coauthors.values("id", "name", "article_count", "active_articles"))})
