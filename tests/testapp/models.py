from django.db import models


class SearchQueryset(models.QuerySet):
    """A queryset providing a customized search method."""

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
        ordering = ["magazine", "name"]

    def __str__(self):
        return self.name


class Magazine(models.Model):
    name = models.CharField("Name", max_length=50)

    def __str__(self):
        return self.name
