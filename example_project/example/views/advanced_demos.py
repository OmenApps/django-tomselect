"""Views for the example app."""

import logging
from datetime import timedelta

from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from example_project.example.forms import (
    ArticleBulkActionForm,
    ConstantFilterByForm,
    DynamicArticleForm,
    EditionYearForm,
    MarketSelectionForm,
    MultipleFilterByForm,
    RichArticleSelectForm,
    WordCountForm,
)
from example_project.example.models import Article, ArticleStatus

logger = logging.getLogger(__name__)


def market_selection_view(request):
    """View for displaying the market selection form."""
    template = "example/advanced_demos/market_selection.html"
    context = {}

    context["form"] = MarketSelectionForm()
    return TemplateResponse(request, template, context)


def article_list_view(request: HttpRequest, page: int = 1) -> HttpResponse:
    """View for the article list page."""
    template = "example/advanced_demos/article_list.html"
    context = {}

    edition_year = request.GET.get("year")
    word_count = request.GET.get("word_count")

    articles = Article.objects.all().prefetch_related("authors", "categories").select_related("magazine")

    # Filter articles by edition year if provided
    if edition_year:
        articles = articles.filter(edition__year=edition_year)

    # Filter articles by word count range if provided
    if word_count:
        try:
            # Convert string representation of tuple back to range values
            range_str = word_count.strip("()").split(",")
            min_count = int(range_str[0])
            max_count = int(range_str[1])
            articles = articles.filter(word_count__gte=min_count, word_count__lte=max_count)
        except (ValueError, IndexError):
            pass

    paginator = Paginator(articles, 8)

    try:
        page_obj = paginator.get_page(page)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    context["page_obj"] = page_obj
    context["edition_year_form"] = EditionYearForm(initial={"year": edition_year})
    context["word_count_form"] = WordCountForm(initial={"word_count": word_count})
    return TemplateResponse(request, template, context)


def article_create_view(request: HttpRequest) -> HttpResponse:
    """View for the article create page."""
    template = "example/advanced_demos/article_form.html"
    context = {}

    form = DynamicArticleForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(request, f"Article {form.cleaned_data['title']!r} has been created.")
        else:
            messages.error(request, "Please correct the errors below.")

        return HttpResponseRedirect(reverse("article-list"))

    context["form"] = form
    return TemplateResponse(request, template, context)


def article_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for the article detail page."""
    template = "example/advanced_demos/article_detail.html"
    context = {}

    article = get_object_or_404(Article, pk=pk)
    context["article"] = article
    return TemplateResponse(request, template, context)


def article_update_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for the article update page."""
    template = "example/advanced_demos/article_form.html"
    context = {}

    article = get_object_or_404(Article, pk=pk)
    form = DynamicArticleForm(request.POST or None, instance=article)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(request, f"Article {form.cleaned_data['title']!r} has been updated.")
            return HttpResponseRedirect(reverse("article-list"))
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def article_bulk_action_view(request):
    """View for bulk article management."""
    template = "example/advanced_demos/bulk_action.html"
    context = {}

    # Get current filter values from GET parameters
    date_range = request.GET.get("date_range", "all")
    main_category = request.GET.get("main_category")
    status = request.GET.get("status")

    # Build queryset with filters
    articles = Article.objects.all()

    if date_range != "all":
        now = timezone.now()
        date_filters = {
            "today": now.date(),
            "week": now - timedelta(days=7),
            "month": now - timedelta(days=30),
            "quarter": now - timedelta(days=90),
            "year": now - timedelta(days=365),
        }
        if date_range in date_filters:
            if date_range == "today":
                articles = articles.filter(created_at__date=date_filters[date_range])
            else:
                articles = articles.filter(created_at__gte=date_filters[date_range])

    if main_category:
        articles = articles.filter(categories__id=main_category)

    if status:
        articles = articles.filter(status=status)

    if request.method == "POST":
        form = ArticleBulkActionForm(request.POST)
        if form.is_valid():
            selected_articles = form.cleaned_data["selected_articles"]
            action = form.cleaned_data["action"]

            if selected_articles:
                try:
                    # Convert selected_articles to a queryset if it isn't already
                    if not isinstance(selected_articles, models.QuerySet):
                        article_ids = [art.id for art in selected_articles]
                        selected_articles = Article.objects.filter(id__in=article_ids)

                    if action == "publish":
                        selected_articles.update(status=ArticleStatus.PUBLISHED)
                        messages.success(
                            request,
                            _("{} articles published successfully").format(selected_articles.count()),
                        )

                    elif action == "archive":
                        selected_articles.update(status=ArticleStatus.ARCHIVED)
                        messages.success(
                            request,
                            _("{} articles archived successfully").format(selected_articles.count()),
                        )

                    elif action == "change_category":
                        target_category = form.cleaned_data["target_category"]
                        if target_category:
                            for article in selected_articles:
                                article.categories.clear()
                                article.categories.add(target_category)
                            messages.success(
                                request,
                                _("Category updated for {} articles").format(selected_articles.count()),
                            )

                    elif action == "assign_author":
                        target_author = form.cleaned_data["target_author"]
                        if target_author:
                            for article in selected_articles:
                                article.authors.add(target_author)
                            messages.success(
                                request,
                                _("Author assigned to {} articles").format(selected_articles.count()),
                            )

                    # Redirect to preserve filters
                    url = f"{reverse('article-bulk-action')}?{request.GET.urlencode()}"
                    return HttpResponseRedirect(url)

                except Exception as e:
                    messages.error(request, f"Error performing bulk action: {str(e)}")
        else:
            messages.error(request, "Please correct the form errors: %s" % form.errors)
    else:
        # Initialize form with current filter values
        form = ArticleBulkActionForm(
            initial={"date_range": date_range, "main_category": main_category, "status": status}
        )

    # Pagination
    paginator = Paginator(articles.distinct(), 20)
    page = request.GET.get("page", 1)

    try:
        articles_page = paginator.page(page)
    except PageNotAnInteger:
        articles_page = paginator.page(1)
    except EmptyPage:
        articles_page = paginator.page(paginator.num_pages)

    context.update(
        {
            "form": form,
            "page_obj": articles_page,
            "paginator": paginator,
            "is_paginated": paginator.num_pages > 1,
            "articles": articles_page,
            # Add current filter values to context
            "current_filters": {"date_range": date_range, "main_category": main_category, "status": status},
        }
    )

    return TemplateResponse(request, template, context)


@require_GET
def article_filtered_table(request):
    """Return the filtered articles table HTML with OOB updates."""
    template = "example/advanced_demos/articles_table.html"

    # Get filter values
    date_range = request.GET.get("date_range", "all")
    main_category = request.GET.get("main_category")
    status = request.GET.get("status")

    # Build queryset with filters
    articles = Article.objects.all()

    if date_range != "all":
        now = timezone.now()
        date_filters = {
            "today": now.date(),
            "week": now - timedelta(days=7),
            "month": now - timedelta(days=30),
            "quarter": now - timedelta(days=90),
            "year": now - timedelta(days=365),
        }
        if date_range in date_filters:
            if date_range == "today":
                articles = articles.filter(created_at__date=date_filters[date_range])
            else:
                articles = articles.filter(created_at__gte=date_filters[date_range])

    if main_category:
        articles = articles.filter(categories__id=main_category)

    if status:
        articles = articles.filter(status=status)

    articles = articles.distinct()

    # Pagination
    paginator = Paginator(articles, 20)
    page = request.GET.get("page", 1)

    try:
        articles_page = paginator.page(page)
    except PageNotAnInteger:
        articles_page = paginator.page(1)
    except EmptyPage:
        articles_page = paginator.page(paginator.num_pages)

    context = {
        "articles": articles_page,
        "is_paginated": paginator.num_pages > 1,
        "page_obj": articles_page,
        "paginator": paginator,
        "current_filters": {"date_range": date_range, "main_category": main_category, "status": status},
    }

    return TemplateResponse(request, template, context)


def rich_article_select_demo(request):
    """View demonstrating rich article selection interface."""
    template = "example/advanced_demos/rich_article_select.html"
    context = {}

    context["form"] = RichArticleSelectForm()
    return TemplateResponse(request, template, context)


def multiple_filter_by_demo(request):
    """View demonstrating filter_by with multiple field-based filters.

    This demo shows how to filter articles by both magazine AND status,
    combining multiple filter conditions with AND logic.
    """
    template = "example/advanced_demos/multiple_filter_by.html"
    context = {}

    context["form"] = MultipleFilterByForm()
    return TemplateResponse(request, template, context)


def constant_filter_by_demo(request):
    """View demonstrating filter_by with constant values.

    This demo shows how to always filter to a specific value (e.g., only
    published articles) while allowing additional field-based filters.
    """
    template = "example/advanced_demos/constant_filter_by.html"
    context = {}

    context["form"] = ConstantFilterByForm()
    return TemplateResponse(request, template, context)
