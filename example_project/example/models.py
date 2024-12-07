"""Models for the example project."""

from django.db import models


class SearchQueryset(models.QuerySet):
    """A queryset providing a search method."""

    def search(self, q):
        """Return a queryset filtered by the search term."""
        return self.filter(name__icontains=q)


class Edition(models.Model):
    """A model representing an edition of a magazine."""

    name = models.CharField("Name", max_length=50)
    year = models.CharField("Year", max_length=50)
    pages = models.CharField("Pages", max_length=50)
    pub_num = models.CharField("Publication Number", max_length=50)

    magazine = models.ForeignKey("Magazine", on_delete=models.SET_NULL, blank=True, null=True)

    objects = SearchQueryset.as_manager()

    class Meta:  # pylint: disable=R0903
        """Meta options for the model."""

        verbose_name = "Edition"
        verbose_name_plural = "Editions"
        ordering = ["magazine", "name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["year"]),
        ]

    def __str__(self) -> str:
        """Return the name of the edition."""
        return str(self.name)


class Magazine(models.Model):
    """A model representing a magazine."""

    class AcceptsNewArticles(models.TextChoices):
        """Choices for the accepts_new_articles field."""

        YES = "yes", "Yes"
        NO = "no", "No"
        MAYBE = "maybe", "Maybe"

    name = models.CharField("Name", max_length=50)
    accepts_new_articles = models.CharField(
        "Accepts New Articles",
        max_length=10,
        choices=AcceptsNewArticles.choices,
        default=AcceptsNewArticles.YES,
    )

    class Meta:  # pylint: disable=R0903
        """Meta options for the model."""

        verbose_name = "Magazine"
        verbose_name_plural = "Magazines"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        """Return the name of the magazine."""
        return str(self.name)


class ModelFormTestModel(models.Model):
    """A model for testing the TomSelectField in a model form."""

    name = models.CharField("Name", max_length=50)

    tomselect = models.ForeignKey(
        Edition,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tomselect_test_model_instances",
    )
    tomselect_tabular = models.ForeignKey(
        Edition,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tomselect_tabular_test_model_instances",
    )
    tomselect_multiple = models.ManyToManyField(
        Edition,
        blank=True,
        related_name="tomselect_multiple_test_model_instances",
    )
    tomselect_tabular_multiple_with_value_field = models.ManyToManyField(
        Edition,
        blank=True,
        related_name="tomselect_tabular_multiple_with_value_field_test_model_instances",
    )

    class Meta:  # pylint: disable=R0903
        """Meta options for the model."""

        verbose_name = "Model Form Test Model"
        verbose_name_plural = "Model Form Test Models"

    def __str__(self) -> str:
        """Return the name of the model instance."""
        return str(self.name)


class Category(models.Model):
    """A model representing an article category."""

    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    class Meta:
        """Meta options for the model."""

        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Author(models.Model):
    """A model representing an article author."""

    name = models.CharField(max_length=100)
    bio = models.TextField()

    class Meta:
        """Meta options for the model."""

        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Article(models.Model):
    """A model representing an article in a magazine."""

    class Status(models.TextChoices):
        """Choices for the status field."""

        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=200)
    authors = models.ManyToManyField("Author")
    categories = models.ManyToManyField("Category")
    magazine = models.ForeignKey("Magazine", on_delete=models.CASCADE)
    edition = models.ForeignKey("Edition", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        """Meta options for the model."""

        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title
