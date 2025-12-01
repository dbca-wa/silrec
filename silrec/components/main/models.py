from django.db import models
from django.core.files.storage import FileSystemStorage
from silrec import settings
#from django.contrib.gis.db.models import GeometryField

import os


class RevisionedMixin(models.Model):
    """
    A model tracked by reversion through the save method.
    """

    def save(self, **kwargs):
        from reversion import revisions

        if kwargs.pop("no_revision", False):
            super().save(**kwargs)
        else:
            with revisions.create_revision():
                if "version_user" in kwargs:
                    revisions.set_user(kwargs.pop("version_user", None))
                if "version_comment" in kwargs:
                    # Increment the lodgement sequence on every save with a version comment.
                    # Versions are only commented on concluding saves (e.g. on submit),
                    # typically when the status changes, i.e. the first save of a new status
                    # is also the first version to use the incremented sequence.
                    if hasattr(self, "lodgement_sequence"):
                        self.lodgement_sequence += 1
                    revisions.set_comment(kwargs.pop("version_comment", ""))
                super().save(**kwargs)

    def reverse_fk_versions(self, reverse_attr, **kwargs):
        """
        Returns a list of a model's one-to-many foreign key relation versions
        selected by filter expression. E.g. because Proposal is a property of
        ProposalGeometry, there is a 1:N relation Proposal -> ProposalGeometry
        and a reverse foreign key lookup of proposal geometries would always
        return all geometries belonging to a proposal id even though some did
        not exist at a specific version of the proposal.
        This function returns only those versions that existed a certain revision
        id.

        Args:
            reverse_attr (str):
                The attribute in the model to query for
            lookup (dict, optional):
                The filter expression to apply, e.g. `{'__lte':1234}`,
                Defaults to empty dict `{}`, i.e. no filter applies.
                Does not get used when `lookup_filter=` is used
            lookup_filter (Q-expression, optional):
                A Q-expression to filter `reverse_attr` queryset

        Examples:
            - geometry_versions = model_instance.reverse_fk_versions(
                "proposalgeometry",
                lookup={"__lte": 1234})
            - geometry_versions = model_instance.reverse_fk_versions(
                "proposalgeometry",
                lookup_filter=Q(revision_id__lte=1234)), i.e. can
                add negation and more complex expressions
        """

        # How to filter the revision table
        lookup = kwargs.get("lookup", {})
        lookup_filter = kwargs.get("lookup_filter", None)
        if not lookup_filter:
            # The lookup filter to apply
            lookup_filter = Q(
                **{f"revision_id{k}": f"{v}" for k, v in iter(lookup.items())}
            )

        # Reverse foreign key queryset
        if hasattr(self, reverse_attr):
            reverse_fk_qs = getattr(self, reverse_attr).all()
        else:
            raise ValidationError(
                f"{self.__class__.__name__} has no attribute {reverse_attr}"
            )

        # A list of filtered attribute versions
        rfk_versions = []
        for obj in reverse_fk_qs:
            version = [
                p
                for p in Version.objects.get_for_object(obj)
                .select_related("revision")
                .filter(lookup_filter)
            ]
            rfk_versions += version

        return list(set(rfk_versions))

    @property
    def created_date(self):
        return Version.objects.get_for_object(self).last().revision.date_created

    @property
    def modified_date(self):
        return Version.objects.get_for_object(self).first().revision.date_created

    class Meta:
        abstract = True


upload_protected_files_storage = FileSystemStorage(
    location=settings.PROTECTED_MEDIA_ROOT, base_url="/protected_media"
)

class SecureFileField(models.FileField):
    def __init__(self, *args, **kwargs):
        kwargs["storage"] = upload_protected_files_storage
        super().__init__(*args, **kwargs)


class Document(models.Model):
    name = models.CharField(
        max_length=255, blank=True, verbose_name="name", help_text=""
    )
    description = models.TextField(blank=True, verbose_name="description", help_text="")
    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "silrec"
        abstract = True

    @property
    def path(self):
        # return self.file.path
        # return self._file.path
        # comment above line to fix the error "The '_file' attribute has no
        # file associated with it." when adding comms log entry.
        if self._file:
            return self._file.path
        else:
            return ""

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.name or self.filename


class ApplicationType(models.Model):
    ECOLOGICAL_THINNING = 'Ecological_Thinning'
    OTHER = 'Other'

    APPLICATION_TYPES = (
        (ECOLOGICAL_THINNING, 'Ecological Thinning'),
        (OTHER, 'Other'),
    )

    # name = models.CharField(max_length=64, unique=True)
    name = models.CharField(
        verbose_name='Application Type name',
        max_length=64,
        choices=APPLICATION_TYPES,
    )
    order = models.PositiveSmallIntegerField(default=0)
    visible = models.BooleanField(default=True)
    searchable = models.BooleanField(default=True)

    class Meta:
        app_label = 'silrec'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class SystemMaintenance(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def duration(self):
        """Duration of system maintenance (in mins)"""
        return (
            int((self.end_date - self.start_date).total_seconds() / 60.0)
            if self.end_date and self.start_date
            else ""
        )
        # return (datetime.now(tz=tz) - self.start_date).total_seconds()/60.

    duration.short_description = "Duration (mins)"

    class Meta:
        app_label = "silrec"
        verbose_name_plural = "System maintenance"

    def __str__(self):
        return "System Maintenance: {} ({}) - starting {}, ending {}".format(
            self.name, self.description, self.start_date, self.end_date
        )


