"""Models for the example project."""

import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, F, Q, Value
from django.db.models.functions import Concat


class SearchQueryset(models.QuerySet):
    """A queryset providing a search method."""

    def search(self, q):
        """Return a queryset filtered by the search term."""
        return self.filter(name__icontains=q)


class ArticleStatus(models.TextChoices):
    """Choices for the status field of the Article model.

    Used to demonstrate the AutocompleteIterablesView.
    """

    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
    PUBLISHED = "published", "Published"
    PENDING = "pending", "Pending"
    LOCKED = "locked", "Locked"
    ON_HOLD = "on_hold", "On Hold"
    ON_REVIEW = "on_review", "On Review"
    MODIFIED = "modified", "Modified"
    MODERATED = "moderated", "Moderated"
    NEW = "new", "New"
    NEEDS_REVIEW = "needs_review", "Needs Review"
    BLOCKED = "blocked", "Blocked"
    BANNED = "banned", "Banned"
    VERIFIED = "verified", "Verified"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELED = "canceled", "Canceled"
    APPROVED = "approved", "Approved"
    ACCEPTED = "accepted", "Accepted"
    SUBMITTED = "submitted", "Submitted"
    SAVED = "saved", "Saved"
    DELETED = "deleted", "Deleted"
    DENIED = "denied", "Denied"
    FLAGGED = "flagged", "Flagged"
    GRANTED = "granted", "Granted"
    GOOD = "good", "Good"
    HIDDEN = "hidden", "Hidden"
    HIGHLIGHTED = "highlighted", "Highlighted"
    HOLD = "hold", "Hold"
    JUNK = "junk", "Junk"
    KICKED = "kicked", "Kicked"
    KILLED = "killed", "Killed"
    INACTIVE = "inactive", "Inactive"
    IN_PROGRESS = "in_progress", "In Progress"
    UNPUBLISHED = "unpublished", "Unpublished"
    UNVERIFIED = "unverified", "Unverified"
    YES = "yes", "Yes"
    YET_TO_BE_PUBLISHED = "yet_to_be_published", "Yet to be Published"
    TO_BE_REVIEWED = "to_be_reviewed", "To Be Reviewed"
    TRASHED = "trashed", "Trashed"
    TROUBLED = "troubled", "Troubled"
    REJECTED = "rejected", "Rejected"
    REMOVED = "removed", "Removed"
    EDITED = "edited", "Edited"
    ERROR = "error", "Error"
    WAITING = "waiting", "Waiting"
    WORKING = "working", "Working"
    QUEUED = "queued", "Queued"
    QUESTIONABLE = "questionable", "Questionable"
    UNCONFIRMED = "unconfirmed", "Unconfirmed"
    REVERTED = "reverted", "Reverted"
    REVIEWED = "reviewed", "Reviewed"
    EXPIRED = "expired", "Expired"
    WIP = "wip", "WIP"
    BETA = "beta", "Beta"


class ArticlePriority(models.IntegerChoices):
    """Choices for the priority field of the Article model.

    Used to demonstrate the AutocompleteIterablesView.
    """

    LOW = 1, "Low"
    MEDIUM = 2, "Medium"
    HIGH = 3, "High"
    CRITICAL = 4, "Critical"
    URGENT = 5, "Urgent"
    IMMEDIATE = 6, "Immediate"
    NONE = 7, "None"
    IMMENSE = 8, "Immense"
    EXTREME = 9, "Extreme"
    MAXIMUM = 10, "Maximum"
    TOTAL = 11, "Total"
    ABSOLUTE = 12, "Absolute"
    ALPHA = 13, "Alpha"
    GAMMA = 14, "Gamma"
    MASTER = 15, "Master"
    MAJOR = 16, "Major"
    MINOR = 17, "Minor"
    NORMAL = 18, "Normal"
    CRUCIAL = 19, "Crucial"
    NADA = 20, "Nada"
    MINISCULE = 21, "Miniscule"
    MICRO = 22, "Micro"
    EXCESSIVE = 23, "Excessive"
    OVERWHELMING = 24, "Overwhelming"
    IMMENSELY_HIGH = 25, "Immensely High"
    OVERLY_HIGH = 26, "Overly High"
    ENORMOUS = 27, "Enormous"
    GIGANTIC = 28, "Gigantic"
    TOMORROW = 29, "Tomorrow"
    LATER = 30, "Later"
    CANT_BE_BOTHERED = 31, "Can't Be Bothered"
    NOT_IMPORTANT = 32, "Not Important"
    WHO_CARES = 33, "Who Cares"
    NON_EUCLEDIAN = 34, "Non-Eucledian"


class EmbargoTimeframe(models.TextChoices):
    """Choices for the embargo_timeframe field of the Article model."""

    PRE_RELEASE = "pre", "Pre-Release (2 weeks)"
    STANDARD = "std", "Standard (1 month)"
    EXTENDED = "extd", "Extended (3 months)"
    EXTREME = "extr", "Extreme (6 months)"


# A list of years for the Edition model
# Used to demonstrate the AutocompleteIterablesView
edition_year = [
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
]

# A list of word count ranges for the Edition model
# Used to demonstrate the AutocompleteIterablesView
word_count_range = (
    (0, 100),
    (100, 200),
    (200, 300),
    (300, 400),
    (400, 500),
    (500, 600),
    (600, 700),
    (700, 800),
    (800, 900),
    (900, 1000),
    (1000, 1100),
    (1100, 1200),
    (1200, 1300),
    (1300, 1400),
    (1400, 1500),
    (1500, 1600),
    (1600, 1700),
    (1700, 1800),
    (1800, 1900),
    (1900, 2000),
)


market_tier_choices = [
    (1, "Tier 1"),
    (2, "Tier 2"),
    (3, "Tier 3"),
]


class EmbargoRegion(models.Model):
    """A model representing a region with embargo information."""

    name = models.CharField(max_length=100)
    market_tier = models.IntegerField(choices=market_tier_choices)
    content_restrictions = models.TextField(help_text="Special content restrictions for this region")
    typical_embargo_days = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Typical embargo period in days for this region",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return the name of the region with its market tier."""
        return f"{self.name} (Tier {self.market_tier})"


class Edition(models.Model):
    """A model representing an edition of a magazine."""

    name = models.CharField("Name", max_length=50)
    year = models.CharField("Year", max_length=50)
    pages = models.CharField("Pages", max_length=50)
    pub_num = models.CharField("Publication Number", max_length=50)

    magazine = models.ForeignKey(
        "Magazine",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class CategoryQuerySet(models.QuerySet):
    """Queryset for the Category model."""

    def with_header_data(self):
        """Annotate the queryset with parent information and article counts."""
        return self.annotate(
            parent_name=F("parent__name"),
            full_path=Concat(
                "parent__name",
                Value(" → "),
                "name",
            ),
            direct_articles=Count("article"),
            total_articles=Count(
                "article",
                filter=Q(article__categories=F("id")) | Q(article__categories__parent=F("id")),
            ),
        ).select_related("parent")


class Category(models.Model):
    """A model representing an article category."""

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(CategoryQuerySet)()

    class Meta:
        """Meta options for the model."""

        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        """Return the name of the category."""
        return self.name


class AuthorQuerySet(models.QuerySet):
    """Queryset for the Author model."""

    def with_details(self):
        """Return a queryset of authors with article count annotations."""
        return self.annotate(
            article_count=Count("article"),
            active_articles=Count("article", filter=Q(article__status="active")),
        ).distinct()


class Author(models.Model):
    """A model representing an article author."""

    name = models.CharField(max_length=100)
    bio = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(AuthorQuerySet)()

    class Meta:
        """Meta options for the model."""

        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        """Return the name of the author."""
        return self.name


class Article(models.Model):
    """A model representing an article in a magazine."""

    title = models.CharField(max_length=200)
    word_count = models.PositiveSmallIntegerField()
    authors = models.ManyToManyField("Author")
    categories = models.ManyToManyField("Category")
    magazine = models.ForeignKey("Magazine", on_delete=models.CASCADE)
    edition = models.ForeignKey(
        "Edition",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=30,
        choices=ArticleStatus.choices,
        default=ArticleStatus.DRAFT,
    )
    priority = models.IntegerField(
        choices=ArticlePriority.choices,
        default=ArticlePriority.NORMAL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Normally we would use auto_now=True, but setting manually for the example
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta options for the model."""

        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        """Return the title of the article."""
        return self.title


class PublishingMarket(models.Model):
    """Represents geographic markets for publishing operations.

    Creates a three-level hierarchy: Region -> Country -> City/Market
    """

    name = models.CharField(
        max_length=100,
        help_text="Name of the market. Either a region, country, or city/market.",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    market_size = models.IntegerField(
        default=0,
        help_text="Market size in millions of potential readers",
    )
    active_publications = models.IntegerField(
        default=0,
        help_text="Number of active publications in this market",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for the model."""

        ordering = ["name"]
        verbose_name = "Publishing Market"
        verbose_name_plural = "Publishing Markets"

    def __str__(self):
        """Return the name of the market."""
        return self.name


class PublicationTag(models.Model):
    """Represents a tag/keyword for publications with validation rules."""

    name = models.CharField(max_length=50, unique=True)
    usage_count = models.IntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate the tag name follows our rules."""
        # Convert to lowercase for consistency
        self.name = self.name.lower().strip()

        # Check length (min 2 chars, max 50)
        if len(self.name) < 2:
            raise ValidationError("Tag must be at least 2 characters long")

        # No special characters except hyphen and underscore
        if not all(c.isalnum() or c in "-_" for c in self.name):
            raise ValidationError("Tags can only contain letters, numbers, hyphens, and underscores")

        # No consecutive special characters
        if "--" in self.name or "__" in self.name:
            raise ValidationError("Tags cannot contain consecutive special characters")

        # Must start and end with alphanumeric
        if not self.name[0].isalnum() or not self.name[-1].isalnum():
            raise ValidationError("Tags must start and end with a letter or number")

    def __str__(self):
        """Return the name of the tag."""
        return self.name


class ModelWithUUIDPk(models.Model):
    """A model with a UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        """Meta options for the model."""

        verbose_name = "Model with UUID PK"
        verbose_name_plural = "Models with UUID PK"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                name="unique_name_constraint",
            ),
        ]

    def __str__(self):
        """Return the name of the model."""
        return self.name


class ModelWithPKIDAndUUIDId(models.Model):
    """A model with a UUID field as a non-primary key."""

    pkid = models.AutoField(primary_key=True)
    id = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        """Meta options for the model."""

        verbose_name = "Model with UUID ID"
        verbose_name_plural = "Models with UUID ID"
        ordering = ["name"]

    def __str__(self):
        """Return the name of the model."""
        return self.name
