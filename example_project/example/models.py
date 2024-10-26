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

    def __str__(self) -> str:
        """Return the name of the edition."""
        return str(self.name)


class Magazine(models.Model):
    """A model representing a magazine."""

    name = models.CharField("Name", max_length=50)

    class Meta:  # pylint: disable=R0903
        """Meta options for the model."""

        verbose_name = "Magazine"
        verbose_name_plural = "Magazines"

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
