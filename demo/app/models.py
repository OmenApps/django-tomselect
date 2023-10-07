from django.db import models


class SearchQueryset(models.QuerySet):
    """A queryset providing a search method."""

    def search(self, q):
        return self.filter(name__icontains=q)


class Edition(models.Model):
    name = models.CharField("Name", max_length=50)
    year = models.CharField("Year", max_length=50)
    pages = models.CharField("Pages", max_length=50)
    pub_num = models.CharField("Publication Number", max_length=50)

    magazine = models.ForeignKey("Magazine", on_delete=models.SET_NULL, blank=True, null=True)

    objects = SearchQueryset.as_manager()

    class Meta:
        verbose_name = "Edition"
        verbose_name_plural = "Editions"

    def __str__(self):
        return self.name


class Magazine(models.Model):
    name = models.CharField("Name", max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Magazine"
        verbose_name_plural = "Magazines"


class ModelFormTestModel(models.Model):
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

    class Meta:
        verbose_name = "Model Form Test Model"
        verbose_name_plural = "Model Form Test Models"

    def __str__(self):
        return self.name
