"""Views for the example app."""

from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from example_project.example.forms import (
    AuthorForm,
    CategoryForm,
    EditionForm,
    MagazineForm,
)
from example_project.example.models import (
    Article,
    ArticleStatus,
    Author,
    Category,
    Edition,
    Magazine,
)


def index_view(request):
    """View for the index page."""
    template = "example/base_with_bootstrap5.html"
    context = {}

    messages.info(request, "Welcome to the Django Tom Select Demo!")
    return TemplateResponse(request, template, context)


def author_list_view(request: HttpRequest, page: int = 1) -> HttpResponse:
    """View for the author list page."""
    template = "example/crud/author_list.html"
    context = {}

    authors = Author.objects.all()
    paginator = Paginator(authors, 20)

    try:
        page_obj = paginator.get_page(page)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    context["page_obj"] = page_obj
    return TemplateResponse(request, template, context)


def author_create_view(request):
    """View for creating a new author."""
    template = "example/crud/author_form.html"
    context = {}

    form = AuthorForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(request, f"Author {form.cleaned_data['name']!r} has been created.")
            return redirect("author-list")
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def author_update_view(request, pk):
    """View for updating an existing author."""
    template = "example/crud/author_form.html"
    context = {}

    author = get_object_or_404(Author, pk=pk)
    form = AuthorForm(request.POST or None, instance=author)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(request, f"Author {form.cleaned_data['name']!r} has been updated.")
            return redirect("author-list")
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def author_delete_view(request, pk):
    """View for deleting an existing author."""
    template = "example/crud/author_confirm_delete.html"
    context = {}

    author = get_object_or_404(Author, pk=pk)

    if request.method == "POST":
        name = author.name
        author.delete()
        messages.success(request, f"Author {name!r} has been deleted.")
        return redirect("author-list")

    context["author"] = author
    return TemplateResponse(request, template, context)


def category_list_view(request: HttpRequest, page: int = 1) -> HttpResponse:
    """View for the category list page."""
    template = "example/crud/category_list.html"
    context = {}

    categories = Category.objects.all()
    paginator = Paginator(categories, 20)

    try:
        page_obj = paginator.get_page(page)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    context["page_obj"] = page_obj
    return TemplateResponse(request, template, context)


def category_create_view(request):
    """View for creating a new category."""
    template = "example/crud/category_form.html"
    context = {}

    form = CategoryForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(request, f"Category {form.cleaned_data['name']!r} has been created.")
            return redirect("category-list")
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def category_detail_view(request, pk):
    """View for displaying the details of a category."""
    template = "example/crud/category_detail.html"
    context = {}

    category = get_object_or_404(Category, pk=pk)
    context["category"] = category

    return TemplateResponse(request, template, context)


def category_update_view(request, pk):
    """View for updating an existing category."""
    template = "example/crud/category_form.html"
    context = {}

    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)

    if request.POST:
        if form.is_valid():
            # Check for circular parent relationships
            parent = form.cleaned_data.get("parent")
            if parent and (parent.pk == category.pk or parent.parent_id == category.pk):
                form.add_error("parent", "Cannot create circular parent relationships")
                messages.error(
                    request,
                    "Cannot create circular parent relationships. Please correct the errors below.",
                )
            else:
                form.save()
                messages.success(request, f"Category {form.cleaned_data['name']!r} has been updated.")
                return redirect("category-list")
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def category_delete_view(request, pk):
    """View for deleting an existing category."""
    template = "example/crud/category_confirm_delete.html"
    context = {}

    category = get_object_or_404(Category, pk=pk)

    # Check if category has children
    if category.children.exists():
        messages.error(
            request,
            "Cannot delete category with subcategories. Please delete or reassign subcategories first.",
        )
        return redirect("category-list")

    if request.method == "POST":
        name = category.name
        category.delete()
        messages.success(request, f"Category {name!r} has been deleted.")
        return redirect("category-list")

    context["category"] = category
    return TemplateResponse(request, template, context)


def magazine_list_view(request: HttpRequest, page: int = 1) -> HttpResponse:
    """View for the magazine list page."""
    template = "example/crud/magazine_list.html"
    context = {}

    magazines = Magazine.objects.all()
    paginator = Paginator(magazines, 20)

    try:
        page_obj = paginator.get_page(page)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    context["page_obj"] = page_obj
    return TemplateResponse(request, template, context)


def magazine_create_view(request):
    """View for creating a new magazine."""
    template = "example/crud/magazine_form.html"
    context = {}

    form = MagazineForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(request, f"Magazine {form.cleaned_data['name']!r} has been created.")
            return redirect("magazine-list")
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def magazine_update_view(request, pk):
    """View for updating an existing magazine."""
    template = "example/crud/magazine_form.html"
    context = {}

    magazine = get_object_or_404(Magazine, pk=pk)
    form = MagazineForm(request.POST or None, instance=magazine)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(request, f"Magazine {form.cleaned_data['name']!r} has been updated.")
            return redirect("magazine-list")
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def magazine_delete_view(request, pk):
    """View for deleting an existing magazine."""
    template = "example/crud/magazine_confirm_delete.html"
    context = {}

    magazine = get_object_or_404(Magazine, pk=pk)

    # Check if magazine has editions
    if magazine.edition_set.exists():
        messages.error(
            request,
            "Cannot delete magazine with editions. Please delete all editions first.",
        )
        return redirect("magazine-list")

    if request.method == "POST":
        name = magazine.name
        magazine.delete()
        messages.success(request, f"Magazine {name!r} has been deleted.")
        return redirect("magazine-list")

    context["magazine"] = magazine
    return TemplateResponse(request, template, context)


def edition_list_view(request: HttpRequest, page: int = 1) -> HttpResponse:
    """View for the edition list page."""
    template = "example/crud/edition_list.html"
    context = {}

    editions = Edition.objects.all()
    paginator = Paginator(editions, 20)

    try:
        page_obj = paginator.get_page(page)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    context["page_obj"] = page_obj
    return TemplateResponse(request, template, context)


def edition_create_view(request):
    """View for creating a new edition."""
    template = "example/crud/edition_form.html"
    context = {}

    form = EditionForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Edition {form.cleaned_data['name']!r} has been created for magazine "
                f"{form.cleaned_data['magazine'].name!r}.",
            )
            return redirect("edition-list")
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def edition_update_view(request, pk):
    """View for updating an existing edition."""
    template = "example/crud/edition_form.html"
    context = {}

    edition = get_object_or_404(Edition, pk=pk)
    form = EditionForm(request.POST or None, instance=edition)

    if request.POST:
        if form.is_valid():
            form.save()
            messages.success(request, f"Edition {form.cleaned_data['name']!r} has been updated.")
            return redirect("edition-list")
        else:
            messages.error(request, "Please correct the errors below.")

    context["form"] = form
    return TemplateResponse(request, template, context)


def edition_delete_view(request, pk):
    """View for deleting an existing edition."""
    template = "example/crud/edition_confirm_delete.html"
    context = {}

    edition = get_object_or_404(Edition, pk=pk)

    # Check if edition has articles
    if edition.article_set.exists():
        messages.error(
            request,
            "Cannot delete edition with articles. Please delete or reassign articles first.",
        )
        return redirect("edition-list")

    if request.method == "POST":
        name = edition.name
        magazine_name = edition.magazine.name if edition.magazine else "No Magazine"
        edition.delete()
        messages.success(
            request,
            f"Edition {name!r} from magazine {magazine_name!r} has been deleted.",
        )
        return redirect("edition-list")

    context["edition"] = edition
    return TemplateResponse(request, template, context)


def article_publish_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for publishing a draft article."""
    article = get_object_or_404(Article, pk=pk)
    if article.status == ArticleStatus.DRAFT:
        article.status = ArticleStatus.ACTIVE
        article.save()
        messages.success(request, f"Article {article.title!r} has been published.")
    return redirect("article-list")


def article_archive_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for archiving an article."""
    article = get_object_or_404(Article, pk=pk)
    if article.status in [ArticleStatus.ACTIVE, ArticleStatus.CANCELED, ArticleStatus.PUBLISHED]:
        article.status = ArticleStatus.ARCHIVED
        article.save()
        messages.success(request, f"Article {article.title!r} has been archived.")
    return redirect("article-list")


def article_cancel_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for canceling any article not yet published."""
    article = get_object_or_404(Article, pk=pk)
    if not article.status == ArticleStatus.PUBLISHED:
        article.status = ArticleStatus.CANCELED
        article.save()
        messages.success(request, f"Article {article.title!r} has been canceled.")
    return redirect("article-list")
