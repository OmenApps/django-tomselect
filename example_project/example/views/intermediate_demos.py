"""Views for the example app."""

import logging

from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from example_project.example.forms import (
    EmbargoForm,
    ExcludeByPrimaryAuthorForm,
    FilterByCategoryForm,
    FilterByMagazineForm,
    RangePreviewForm,
    TaggingForm,
    WeightedAuthorSearchForm,
)
from example_project.example.models import (
    Article,
    EmbargoTimeframe,
    PublicationTag,
    word_count_range,
)

logger = logging.getLogger(__name__)


def filter_by_magazine_demo(request: HttpRequest) -> HttpResponse:
    """View for the filter_by demo page."""
    template = "example/intermediate_demos/filter_by_magazine.html"
    context = {}

    context["form"] = FilterByMagazineForm()
    return TemplateResponse(request, template, context)


def filter_by_category_demo(request: HttpRequest) -> HttpResponse:
    """View for the filter_by demo page."""
    template = "example/intermediate_demos/filter_by_category.html"
    context = {}

    context["form"] = FilterByCategoryForm()
    return TemplateResponse(request, template, context)


def exclude_by_primary_author_demo(request: HttpRequest) -> HttpResponse:
    """View for the exclude_by demo page."""
    template = "example/intermediate_demos/exclude_by.html"
    context = {}

    context["form"] = ExcludeByPrimaryAuthorForm()
    return TemplateResponse(request, template, context)


def tagging_view(request):
    """View for managing publication tags."""
    template = "example/intermediate_demos/tagging_publication.html"
    context = {}
    if request.method == "POST":
        form = TaggingForm(request.POST)
        if form.is_valid():
            tags = form.cleaned_data["tags"]
            # Update usage counts
            for tag in tags:
                tag.usage_count += 1
                tag.save()

            template = "example/intermediate_demos/tagging_success.html"
            context["tags"] = tags
            return TemplateResponse(request, template, context)
    else:
        form = TaggingForm()

    existing_tags = PublicationTag.objects.all().order_by("-usage_count", "name")

    context["form"] = form
    context["existing_tags"] = existing_tags
    return TemplateResponse(request, template, context)


def get_range_statistics():
    """Get article counts for each word count range."""
    stats = []

    for start, end in word_count_range:
        # Create range filter
        range_filter = Q(word_count__gte=start) & Q(word_count__lt=end)
        count = Article.objects.filter(range_filter).count()

        stats.append({"range": f"{start:,}-{end:,}", "count": count, "range_tuple": (start, end)})

    return stats


def get_detailed_range_statistics(start, end, bin_size=10):
    """Get detailed article counts within a range, binned by specified size."""
    stats = []

    # Create bins for the range
    for bin_start in range(start, end, bin_size):
        bin_end = min(bin_start + bin_size, end)

        # Create range filter for this bin
        range_filter = Q(word_count__gte=bin_start) & Q(word_count__lt=bin_end)
        count = Article.objects.filter(range_filter).count()

        stats.append(
            {
                "range": f"{bin_start:,}-{bin_end:,}",
                "count": count,
                "bin_start": bin_start,
                "bin_end": bin_end,
            }
        )

    return stats


def range_preview_demo(request):
    """View demonstrating range selection with preview.

    Provides the form and loads update_range_preview via HTMX.
    """
    template = "example/intermediate_demos/range_preview.html"
    context = {}

    context["form"] = RangePreviewForm()
    return TemplateResponse(request, template, context)


def update_range_preview(request):
    """HTMX endpoint for updating the visualization."""
    template = "example/intermediate_demos/range_preview_bars.html"
    context = {}

    selected_value = request.GET.get("word_count")

    if selected_value:
        try:
            # Parse the selected range from "(start, end)" format
            selected_value = selected_value.strip("()")
            start, end = map(int, selected_value.split(","))

            # Get detailed statistics for the selected range
            stats = get_detailed_range_statistics(start, end)
            range_label = f"{start:,}-{end:,}"
            is_detail_view = True
            total_articles = sum(item["count"] for item in stats)
        except (ValueError, TypeError) as e:
            logger.warning("Error parsing range: %s", e)
            stats = get_range_statistics()
            range_label = None
            is_detail_view = False
            total_articles = sum(item["count"] for item in stats)
    else:
        # Show overall statistics if no range selected
        stats = get_range_statistics()
        range_label = None
        is_detail_view = False
        total_articles = sum(item["count"] for item in stats)

    max_count = max((item["count"] for item in stats), default=0)

    context["data"] = stats
    context["selected_range"] = range_label
    context["max_count"] = max_count
    context["is_detail_view"] = is_detail_view
    context["total_articles"] = total_articles
    return TemplateResponse(request, template, context)


def embargo_management_view(request):
    """View for managing embargoes."""
    template = "example/intermediate_demos/embargo_management.html"
    context = {}

    form = EmbargoForm()

    if request.method == "POST":
        form = EmbargoForm(request.POST)
        if form.is_valid():
            region = form.cleaned_data["region"]
            timeframe = form.cleaned_data["timeframe"]

            def get_timeframe_display(timeframe):
                """Get the display value for the timeframe."""
                return dict(EmbargoTimeframe.choices)[timeframe]

            messages.success(
                request,
                f"Embargo for {region} set to {get_timeframe_display(timeframe)}.",
            )
            return redirect("custom-content")

    context["form"] = form
    return TemplateResponse(request, template, context)


def weighted_author_search_demo(request):
    """View demonstrating weighted author search results."""
    template = "example/intermediate_demos/weighted_author_search.html"
    context = {}

    context["form"] = WeightedAuthorSearchForm()
    return TemplateResponse(request, template, context)
