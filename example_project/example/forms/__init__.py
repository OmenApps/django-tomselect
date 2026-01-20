"""Forms package for the example project."""

from example_project.example.forms.advanced_demos import (
    ArticleBulkActionForm,
    ConstantFilterByForm,
    DynamicArticleForm,
    EditionYearForm,
    MarketSelectionForm,
    MultipleFilterByForm,
    RichArticleSelectForm,
    WordCountForm,
)
from example_project.example.forms.basic_demos import (
    Bootstrap4StylingForm,
    Bootstrap5StylingForm,
    Bootstrap5StylingHTMXForm,
    CategoryModelForm,
    CategoryModelFormset,
    DefaultStylingForm,
    EditionFormset,
    EditionFormsetForm,
    MultipleHeavySelectorsForm,
)
from example_project.example.forms.crud import (
    AuthorForm,
    CategoryForm,
    EditionForm,
    MagazineForm,
)
from example_project.example.forms.intermediate_demos import (
    DynamicTagField,
    EmbargoForm,
    ExcludeByPrimaryAuthorForm,
    FilterByMagazineForm,
    FilterByCategoryForm,
    RangePreviewForm,
    TaggingForm,
    WeightedAuthorSearchForm,
)
from example_project.example.forms.oddball_model_forms import (
    PKIDUUIDModelForm,
    UUIDModelForm,
)

__all__ = [
    # Advanced demos
    "ArticleBulkActionForm",
    "ConstantFilterByForm",
    "DynamicArticleForm",
    "EditionYearForm",
    "MarketSelectionForm",
    "MultipleFilterByForm",
    "RichArticleSelectForm",
    "WordCountForm",
    # Basic demos
    "Bootstrap4StylingForm",
    "Bootstrap5StylingForm",
    "Bootstrap5StylingHTMXForm",
    "CategoryModelForm",
    "CategoryModelFormset",
    "DefaultStylingForm",
    "EditionFormset",
    "EditionFormsetForm",
    "MultipleHeavySelectorsForm",
    # CRUD forms
    "AuthorForm",
    "CategoryForm",
    "EditionForm",
    "MagazineForm",
    # Intermediate demos
    "DynamicTagField",
    "EmbargoForm",
    "ExcludeByPrimaryAuthorForm",
    "FilterByMagazineForm",
    "FilterByCategoryForm",
    "RangePreviewForm",
    "TaggingForm",
    "WeightedAuthorSearchForm",
    # Oddball model forms
    "PKIDUUIDModelForm",
    "UUIDModelForm",
]
