"""Views for the example app."""

import logging
from datetime import timedelta

from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from django.core.exceptions import ValidationError as _ValidationError

from django_tomselect.query import parse_query as _parse_query

from example_project.example.autocompletes import (
    ArticleAdvancedTokenQueryView as _ArticleAdvancedTokenQueryView,
)
from example_project.example.autocompletes import ArticleTokenQueryView as _ArticleTokenQueryView
from example_project.example.forms import (
    ArticleAdvancedTokenSearchForm,
    ArticleBulkActionForm,
    ArticleTokenSearchForm,
    ConstantFilterByForm,
    DynamicArticleForm,
    EditionYearForm,
    GitHubUserPickerForm,
    InlineCreateTagForm,
    MarketSelectionForm,
    MultipleFilterByForm,
    RichArticleSelectForm,
    RichAuthorMultiSelectForm,
    SpotlightForm,
    WordCountForm,
)
from example_project.example.models import Article, ArticleStatus, Author, PublicationTag, Spotlight

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


def article_bulk_action_view(request):  # noqa: C901
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


def _build_author_summary(authors_qs):
    """Aggregate stats across a queryset of selected authors for the summary card.

    Bounded by however many authors the user selected, so a few extra queries are
    fine.
    """
    authors_list = list(authors_qs)
    count = len(authors_list)
    if count == 0:
        return {
            "count": 0,
            "total_articles": 0,
            "shared_categories": [],
            "magazines_count": 0,
            "names": [],
            "peer_ranks": [],
        }

    articles_qs = Article.objects.filter(authors__in=authors_list).distinct()
    total_articles = articles_qs.count()
    magazines_count = articles_qs.values("magazine").distinct().count()

    # Shared categories: categories appearing on the selected authors' articles.
    # Ranked by how many of the selected authors share each category (when
    # multiple authors are selected) or by total occurrences (single author).
    from collections import Counter

    category_share_counter: Counter = Counter()
    for author in authors_list:
        seen_for_author: set[str] = set()
        for article in author.article_set.all():
            for category in article.categories.all():
                if category.name not in seen_for_author:
                    seen_for_author.add(category.name)
                    category_share_counter[category.name] += 1
    shared_categories = [name for name, _count in category_share_counter.most_common(3)]

    # Global peer rank by article_count
    rank_ids = list(
        Author.objects.annotate(article_count=Count("article", distinct=True))
        .order_by("-article_count", "name")
        .values_list("id", flat=True)
    )
    rank_map = {pk: i + 1 for i, pk in enumerate(rank_ids)}
    peer_ranks = [(author.name, rank_map.get(author.id, 0)) for author in authors_list]

    return {
        "count": count,
        "total_articles": total_articles,
        "shared_categories": shared_categories,
        "magazines_count": magazines_count,
        "names": [author.name for author in authors_list],
        "peer_ranks": peer_ranks,
    }


def rich_author_multi_select_demo(request):
    """View demonstrating three multi-select widgets sharing one rich autocomplete.

    On POST, renders an unbound form (so the widgets start clean - the item
    template carries only the author name and would otherwise show partial data
    for retained selections) and adds a per-widget summary card to the context
    for every field that had selections.
    """
    template = "example/advanced_demos/rich_author_multi_select.html"
    if request.method == "POST":
        bound = RichAuthorMultiSelectForm(request.POST)
        context = {"form": RichAuthorMultiSelectForm()}
        if bound.is_valid():
            for field_name in ("authors_full", "authors_slim", "authors_stats"):
                authors_qs = bound.cleaned_data.get(field_name)
                if authors_qs:
                    context[f"{field_name}_summary"] = _build_author_summary(authors_qs)
        else:
            context["form"] = bound
        return TemplateResponse(request, template, context)
    return TemplateResponse(request, template, {"form": RichAuthorMultiSelectForm()})


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


def article_token_search_view(request):
    """Token-style article filter demo backed by ArticleTokenQueryView.

    Demonstrates the canonical wiring for :class:`TomSelectTokenField`:

    1. ``form.is_valid()`` runs parser-level validation (unknown operators,
       caps, ``allow_free_text=False``, ``Operator.max_count``/``min_count``).
    2. ``apply()`` runs against the parent ``Article`` queryset; ORM coercion
       errors (typed-but-not-selected values for id-based operators) raise
       ``ValidationError`` which is surfaced via ``form.add_error("q", e)``.
    """
    template = "example/advanced_demos/article_token_search.html"

    form = ArticleTokenSearchForm(request.GET or None)
    articles = Article.objects.none()

    if not request.GET:
        articles = Article.objects.all().distinct()[:50]
    elif form.is_valid():
        q = form.cleaned_data.get("q", "") or ""
        if q:
            parsed = _parse_query(q, _ArticleTokenQueryView)
            try:
                qs = parsed.apply(Article.objects.all())
                articles = qs.distinct()[:50]
            except _ValidationError as exc:
                form.add_error("q", exc)
        else:
            articles = Article.objects.all().distinct()[:50]

    return TemplateResponse(request, template, {"form": form, "articles": articles})


def article_advanced_token_search_view(request):
    """Token-style article filter with date/range/comparison operators.

    Companion to :func:`article_token_search_view`. The simple demo uses only
    ``filter_lookup`` (equality / ``__in``); this one exercises
    :attr:`~django_tomselect.autocompletes.Operator.q_translator` callables,
    which receive ``(op, list[values])`` and return an arbitrary ``Q`` object.

    Comparison/range syntax (``>500``, ``100..2000``, etc.) lives inside the
    token value because the tokenizer only understands ``key:value``.
    """
    template = "example/advanced_demos/article_advanced_token_search.html"

    form = ArticleAdvancedTokenSearchForm(request.GET or None)
    articles = Article.objects.none()

    if not request.GET:
        articles = Article.objects.all().distinct()[:50]
    elif form.is_valid():
        q = form.cleaned_data.get("q", "") or ""
        if q:
            parsed = _parse_query(q, _ArticleAdvancedTokenQueryView)
            try:
                qs = parsed.apply(Article.objects.all())
                articles = qs.distinct()[:50]
            except _ValidationError as exc:
                form.add_error("q", exc)
        else:
            articles = Article.objects.all().distinct()[:50]

    return TemplateResponse(request, template, {"form": form, "articles": articles})


def github_user_picker_view(request: HttpRequest) -> HttpResponse:
    """External-API-backed autocomplete demo.

    No model, no queryset — the autocomplete view talks directly to GitHub's
    ``/search/users`` endpoint. Selecting a user stores the login string in a
    plain ``CharField``.
    """
    if request.method == "POST":
        form = GitHubUserPickerForm(request.POST)
        if form.is_valid():
            selected = form.cleaned_data.get("github_user") or ""
            return TemplateResponse(
                request,
                "example/advanced_demos/github_user_picker.html",
                {"form": form, "selected": selected, "submitted": True},
            )
    else:
        form = GitHubUserPickerForm()

    return TemplateResponse(
        request,
        "example/advanced_demos/github_user_picker.html",
        {"form": form, "selected": None, "submitted": False},
    )


_SESSION_PANEL_KEY = "demo_inline_create_tags"


def inline_create_tag_demo(request: HttpRequest) -> HttpResponse:
    """Page view for the HTMX inline-create demo."""
    form = InlineCreateTagForm()
    session_tags: list[str] = list(request.session.get(_SESSION_PANEL_KEY) or [])

    if request.method == "POST":
        form = InlineCreateTagForm(request.POST)
        if form.is_valid():
            chosen = form.cleaned_data.get("tags") or []
            # No-op persistence at submit time — the HTMX create endpoint already
            # persisted any new tags. We just clear the session panel.
            request.session[_SESSION_PANEL_KEY] = []
            return TemplateResponse(
                request,
                "example/advanced_demos/inline_create_tag.html",
                {"form": InlineCreateTagForm(), "submitted": chosen, "session_tags": []},
            )

    return TemplateResponse(
        request,
        "example/advanced_demos/inline_create_tag.html",
        {"form": form, "submitted": None, "session_tags": session_tags},
    )


@require_POST
def publication_tag_create_htmx(request: HttpRequest) -> JsonResponse:
    """Server-side endpoint for the inline-create flow.

    Validates a slug-safe tag name and calls ``get_or_create`` for the tag.
    Auto-approves the tag so it appears in subsequent autocomplete responses.

    Response contract (consumed by the demo's JS bridge):
    - success / duplicate: ``{"action": "select", "value": <name>, "label": <name>, "is_new": <bool>}``
    - failure:             ``{"action": "error", "error": "<message>"}``

    Both responses use HTTP 200 — the JS bridge inspects ``action`` to decide
    branches. ``label`` and ``value`` are both the tag name so the value space
    matches ``PublicationTagAutocompleteView``.

    DEMO NOTE: this endpoint deliberately has no authentication or rate
    limiting — it's a wiring demo, not a production tag-creation endpoint. In
    a real app you'd want ``login_required``, a permission check, and
    throttling (e.g. django-ratelimit or DRF throttles) before turning user
    input into auto-approved persisted rows.
    """
    name = (request.POST.get("name") or "").strip().lower()

    if not name:
        return JsonResponse({"action": "error", "error": _("Please type a tag name.")})

    # All further validation (min length, allowed chars, consecutive
    # separators, alphanumeric edges, max length) is delegated to
    # ``PublicationTag.full_clean()`` below so the endpoint can never
    # accept a value the model would reject.

    existing = PublicationTag.objects.filter(name=name).first()
    if existing is not None:
        # Auto-approve existing unapproved tags so the autocomplete surfaces them
        # immediately. Demo-only convenience — see the auth/permission note above.
        if not existing.is_approved:
            existing.is_approved = True
            existing.save(update_fields=["is_approved", "updated_at"])
        return JsonResponse({
            "action": "select",
            "value": existing.name,
            "label": existing.name,
            "is_new": False,
        })

    # Brand-new tag: validate via the model's own clean() so we honor its
    # rules (consecutive separators forbidden, must start/end alphanumeric,
    # min 2 chars). full_clean() also enforces max_length=50.
    from django.core.exceptions import ValidationError as DjangoValidationError

    tag = PublicationTag(name=name, is_approved=True, usage_count=0)
    try:
        tag.full_clean()
    except DjangoValidationError as exc:
        msgs = []
        # exc.messages exists on most paths; fall back to str(exc) otherwise.
        msgs.extend(getattr(exc, "messages", None) or [str(exc)])
        return JsonResponse({"action": "error", "error": msgs[0] if msgs else _("Invalid tag.")})
    tag.save()

    # Track ONLY newly-created tags in the session. The panel's "Tags
    # created this session" heading should match its contents — picking an
    # existing tag is selection, not creation, and the chip in the field
    # is already its UI affordance.
    session_tags = list(request.session.get(_SESSION_PANEL_KEY) or [])
    if name not in session_tags:
        session_tags.append(name)
        request.session[_SESSION_PANEL_KEY] = session_tags

    return JsonResponse({
        "action": "select",
        "value": tag.name,
        "label": tag.name,
        "is_new": True,
    })


def tag_session_panel_htmx(request: HttpRequest) -> HttpResponse:
    """Returns the HTMX OOB partial showing tags created in this session."""
    session_tags: list[str] = list(request.session.get(_SESSION_PANEL_KEY) or [])
    return TemplateResponse(
        request,
        "example/advanced_demos/_tag_session_panel.html",
        {"session_tags": session_tags},
    )


def gfk_picker_view(request: HttpRequest) -> HttpResponse:
    """Generic Foreign Key picker demo.

    On submit, persists a :class:`Spotlight` row using the resolved
    ``(content_type, object_id)`` from the form field. The optional
    ``?scope=`` query param narrows the picker to a single operator key.
    """
    scope = (request.GET.get("scope") or "").strip() or None
    if scope not in (None, "article", "author", "magazine"):
        scope = None

    if request.method == "POST":
        form = SpotlightForm(request.POST, scope=scope)
        if form.is_valid():
            ct, obj_id, _obj = form.fields["featured"]._gfk_resolved
            Spotlight.objects.create(
                title=form.cleaned_data["title"],
                content_type=ct,
                object_id=obj_id,
            )
            target = reverse("gfk-picker")
            if scope:
                target = f"{target}?scope={scope}"
            return HttpResponseRedirect(target)
    else:
        form = SpotlightForm(scope=scope)

    spotlights = (
        Spotlight.objects.select_related("content_type")
        .order_by("-featured_at")[:25]
    )

    return TemplateResponse(
        request,
        "example/advanced_demos/gfk_picker.html",
        {"form": form, "spotlights": spotlights, "scope": scope or ""},
    )
