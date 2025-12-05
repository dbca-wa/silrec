from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import F, Max, Min, Q
#from django.contrib.postgres.fields import JSONField
from django.db.models.functions import Cast
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.contrib.gis.db.models import MultiPolygonField
from django.contrib.gis.db.models.fields import PolygonField
from django.contrib.gis.db.models.functions import Area
from django.db import connection

import re
import json
import geopandas as gpd
from rest_framework import serializers
from reversion.models import Version

from dirtyfields import DirtyFieldsMixin

from silrec.components.main.models import (
    Document,
    ApplicationType,
    SecureFileField,
    RevisionedMixin,
)
#from silrec.components.forest_blocks.models import (
#    Polygon,
#)


def update_proposal_doc_filename(instance, filename):
    return f"proposals/{instance.proposal.id}/documents/{filename}"

def update_proposal_comms_log_filename(instance, filename):
    return f"proposals/{instance.log_entry.proposal.id}/{filename}"


class AdditionalDocumentType(RevisionedMixin):
    name = models.CharField(max_length=255, null=True, blank=True)
    help_text = models.CharField(max_length=255, null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Additional Document Type"
        app_label = "silrec"
        ordering = ["name"]


class DefaultDocument(Document):
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    visible = models.BooleanField(
        default=True
    )  # to prevent deletion on file system, hidden and still be available in history

    class Meta:
        app_label = "silrec"
        abstract = True

    def delete(self):
        if self.can_delete:
            return super().delete()
        logger.info(
            "Cannot delete existing document object after Application has been submitted "
            "(including document submitted before Application pushback to status Draft): {}".format(
                self.name
            )
        )

class ProposalDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="supporting_documents", on_delete=models.CASCADE
    )
    _file = SecureFileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "silrec"
        verbose_name = "Application Document"


class ShapefileDocumentQueryset(models.QuerySet):
    """Using a custom manager to make sure shapfiles are removed when a bulk .delete is called
    as having multiple files with the shapefile extensions in the same folder causes issues.
    """

    def delete(self):
        for obj in self:
            obj._file.delete()
        super().delete()


class ShapefileDocument(Document):
    objects = ShapefileDocumentQueryset.as_manager()

    proposal = models.ForeignKey(
        "Proposal", related_name="shapefile_documents", on_delete=models.CASCADE
    )
    _file = SecureFileField(upload_to=update_proposal_doc_filename, max_length=500)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    def delete(self):
        if self.can_delete:
            self._file.delete()
            return super().delete()
        logger.info(
            "Cannot delete existing document object after Proposal has been submitted "
            "(including document submitted before Proposal pushback to status Draft): {}".format(
                self.name
            )
        )

    class Meta:
        app_label = "silrec"


class ProposalAdditionalDocumentType(models.Model):
    proposal = models.ForeignKey(
        'Proposal', on_delete=models.CASCADE, related_name="additional_document_types"
    )
    additional_document_type = models.ForeignKey(
        AdditionalDocumentType, on_delete=models.CASCADE
    )

    class Meta:
        app_label = "silrec"


class ProposalType(models.Model):
    PROPOSAL_TYPE_NEW = "new"
    PROPOSAL_TYPE_RENEWAL = "renewal"
    PROPOSAL_TYPE_AMENDMENT = "amendment"
    PROPOSAL_TYPE_MIGRATION = "migration"
    PROPOSAL_TYPES = [
        (PROPOSAL_TYPE_NEW, "New Proposal"),
        (PROPOSAL_TYPE_AMENDMENT, "Amendment"),
        (PROPOSAL_TYPE_RENEWAL, "Renewal"),
        (PROPOSAL_TYPE_MIGRATION, "Migration"),
    ]

    # class ProposalType(RevisionedMixin):
    code = models.CharField(max_length=30, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        # return 'id: {} code: {}'.format(self.id, self.code)
        return self.description

    class Meta:
        app_label = "silrec"


#class ProposalManager(models.Manager):
#    def get_queryset(self):
#        return (
#            super()
#            .get_queryset()
#            .select_related(
#                "proposal_type", "org_applicant", "application_type", "approval"
#            )
#        )

class Proposal(RevisionedMixin, DirtyFieldsMixin):
    #objects = ProposalManager()

    MODEL_PREFIX = "P"

    PROCESSING_STATUS_DRAFT = "draft"
    PROCESSING_STATUS_AMENDMENT_REQUIRED = "amendment_required"
    PROCESSING_STATUS_WITH_ASSESSOR = "with_assessor"
    PROCESSING_STATUS_WITH_ASSESSOR_TREATMENTS = "with_assessor_treatments"
    PROCESSING_STATUS_WITH_ASSESSOR_TASKS = "with_assessor_tasks"
    PROCESSING_STATUS_WITH_REVIEWER = "with_reviewer"
    PROCESSING_STATUS_REVIEW_COMPLETED = "review_Completed"
    PROCESSING_STATUS_DECLINED = "declined"
    PROCESSING_STATUS_DISCARDED = "discarded"
    PROCESSING_STATUS_TEMP = "temp"
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_DRAFT, "Draft"),
        (PROCESSING_STATUS_AMENDMENT_REQUIRED, "Amendment Required"),
        (PROCESSING_STATUS_WITH_ASSESSOR, "With Assessor"),
        (PROCESSING_STATUS_WITH_ASSESSOR_TREATMENTS, "With Assessor (Treatments)"),
        (PROCESSING_STATUS_WITH_ASSESSOR_TASKS, "With Assessor (Tasks)"),
        (PROCESSING_STATUS_WITH_REVIEWER, "With Reviewer"),
        (PROCESSING_STATUS_REVIEW_COMPLETED, "Review Completed"),
        (PROCESSING_STATUS_DECLINED, "Declined"),
        (PROCESSING_STATUS_DISCARDED, "Discarded"),
        (PROCESSING_STATUS_TEMP, "Temporary"),
    )

    COMPLIANCE_CHECK_STATUS_CHOICES = (
        ("not_checked", "Not Checked"),
        ("awaiting_returns", "Awaiting Returns"),
        ("completed", "Completed"),
        ("accepted", "Accepted"),
    )

    REVIEW_STATUS_CHOICES = (
        ("not_reviewed", "Not Reviewed"),
        ("awaiting_amendments", "Awaiting Amendments"),
        ("amended", "Amended"),
        ("accepted", "Accepted"),
    )

    proposal_type = models.ForeignKey(
        ProposalType, blank=True, null=True, on_delete=models.SET_NULL
    )
    proposed_issuance_approval = models.JSONField(blank=True, null=True)
    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    lodgement_date = models.DateTimeField(blank=True, null=True)
    submitter = models.IntegerField(null=True)  # EmailUserRO
#    assigned_officer = models.IntegerField(null=True)  # EmailUserRO
#    assigned_approver = models.IntegerField(null=True)  # EmailUserRO
#    approved_by = models.IntegerField(null=True)  # EmailUserRO
    processing_status = models.CharField(
        "Processing Status",
        max_length=35,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_CHOICES[0][0],
    )
    prev_processing_status = models.CharField(max_length=30, blank=True, null=True)
#    review_status = models.CharField(
#        "Review Status",
#        max_length=30,
#        choices=REVIEW_STATUS_CHOICES,
#        default=REVIEW_STATUS_CHOICES[0][0],
#    )
    previous_application = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL
    )
    #proposed_decline_status = models.BooleanField(default=False)
    # Special Fields
    title = models.CharField(max_length=255, null=True, blank=True)
    application_type = models.ForeignKey(ApplicationType, on_delete=models.PROTECT)

    shapefile_json = models.JSONField('Source/Submitter (multi) polygon geometry', blank=True, null=True)
    geojson_data_hist = models.JSONField('History Polygons that intersect Source Polygons', blank=True, null=True)
    geojson_data_processed = models.JSONField('Source Polygon intersected with hist and split (multi) polygon geometry', blank=True, null=True)
    geojson_data_processed_iters = models.JSONField('Source Polygon intersected with hist and split (multi) polygon geometry', blank=True, null=True)
    migrated = models.BooleanField(default=False)

    class Meta:
        app_label = "silrec"
        verbose_name = "Proposal"

    def save(self, *args, **kwargs):
        # Clear out the cached
        #cache.delete(settings.CACHE_KEY_MAP_PROPOSALS)

        # Store the original values of fields we want to keep track of in
        # django reversion before they are overwritten by super() below
        original_processing_status = self._original_state['processing_status']
        #original_assessor_data = self._original_state['assessor_data']
        #original_comment_data = self._original_state['comment_data']

        super().save(*args, **kwargs)

        if self.lodgement_number == '':
            self.lodgement_number = 'P{0:06d}'.format(self.pk)
            self.save()

        # If the processing_status has changed then add a reversion comment
        # so we have a way of filtering based on the status changing
        if self.processing_status != original_processing_status:
            self.save(version_comment=f'processing_status: {self.processing_status}')

    @property
    def submitter_obj(self):
        return User.objects.get(id=self.submitter)

    @property
    def can_user_view(self):
        return True

    @property
    def shp_to_gdf(self):
        return gpd.read_file(json.dumps(self.shapefile_json))


class ProposalGeometryManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(area=Area(Cast("polygon", PolygonField(geography=True))))
        )


class ProposalGeometry(models.Model):
    SOURCE_CHOICE_APPLICANT = "proponent"
    SOURCE_CHOICE_ASSESSOR = "assessor"
    SOURCE_CHOICES = (
        (SOURCE_CHOICE_APPLICANT, "Proponent"),
        (SOURCE_CHOICE_ASSESSOR, "Assessor"),
    )

    objects = ProposalGeometryManager()

    proposal = models.ForeignKey(
        Proposal, on_delete=models.CASCADE, related_name="proposalgeometry"
    )
    polygon = PolygonField(srid=4326, blank=True, null=True)
    intersects = models.BooleanField(default=False)
    copied_from = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True
    )
    drawn_by = models.IntegerField(blank=True, null=True)  # EmailUserRO
    source_type = models.CharField(
        max_length=255, blank=True, choices=SOURCE_CHOICES, default=SOURCE_CHOICES[0][0],
    )
    source_name = models.CharField(max_length=255, blank=True)
    locked = models.BooleanField(default=False)

    class Meta:
        app_label = "silrec"

    @property
    def area_sqm(self):
        if not hasattr(self, "area") or not self.area:
            logger.warning(f"ProposalGeometry: {self.id} has no area")
            return None
        return self.area.sq_m

    @property
    def area_sqhm(self):
        if not hasattr(self, "area") or not self.area:
            logger.warning(f"ProposalGeometry: {self.id} has no area")
            return None
        return self.area.sq_m / 10000


class AmendmentReason(models.Model):
    reason = models.CharField("Reason", max_length=125)

    class Meta:
        app_label = "silrec"
        verbose_name = "Proposal Amendment Reason"  # display name in Admin
        verbose_name_plural = "Proposal Amendment Reasons"

    def __str__(self):
        return self.reason

class ProposalRequest(models.Model):
    proposal = models.ForeignKey(
        Proposal, related_name="proposalrequest_set", on_delete=models.CASCADE
    )
    subject = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True)
    # fficer = models.ForeignKey(EmailUser, null=True, on_delete=models.SET_NULL)
    officer = models.IntegerField(null=True)  # EmailUserRO

    def __str__(self):
        return f"{self.subject} - {self.text}"

    class Meta:
        app_label = "silrec"


class AmendmentRequest(ProposalRequest):
    STATUS_CHOICE_REQUESTED = "requested"
    STATUS_CHOICE_AMENDED = "amended"
    STATUS_CHOICES = (
        (STATUS_CHOICE_REQUESTED, "Requested"),
        (STATUS_CHOICE_AMENDED, "Amended"),
    )

    status = models.CharField(
        "Status", max_length=30, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )
    reason = models.ForeignKey(
        AmendmentReason, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        app_label = "silrec"


class SQLReport(models.Model):
    """Model for storing SQL query reports with dynamic WHERE clauses"""

    # Report Type options
    REPORT_TYPES = [
        ('polygon', 'Polygon Analysis'),
        ('cohort', 'Cohort Analysis'),
        ('treatment', 'Treatment Analysis'),
        ('operation', 'Operation Analysis'),
        ('custom', 'Custom Report'),
    ]

    # Export Format options
    EXPORT_FORMATS = [
        ('excel', 'Excel (.xlsx)'),
        ('csv', 'CSV (.csv)'),
        ('pdf', 'PDF (.pdf)'),
        ('shapefile', 'Shapefile (.shp)'),
    ]

    # Operator choices for WHERE clauses
    OPERATOR_CHOICES = [
        ('=', 'Equals'),
        ('!=', 'Not Equals'),
        ('>', 'Greater Than'),
        ('<', 'Less Than'),
        ('>=', 'Greater Than or Equal'),
        ('<=', 'Less Than or Equal'),
        ('LIKE', 'Contains'),
        ('NOT LIKE', 'Does Not Contain'),
        ('IN', 'In List'),
        ('NOT IN', 'Not In List'),
        ('IS NULL', 'Is Null'),
        ('IS NOT NULL', 'Is Not Null'),
        ('BETWEEN', 'Between'),
        ('YEAR', 'Year Equals'),
        ('MONTH', 'Month Equals'),
        ('DATE', 'Date Equals'),
    ]

    name = models.CharField(max_length=255, unique=True, help_text="Report name for dropdown selection")
    description = models.TextField(blank=True, help_text="Description of what this report shows")

    # Main SQL Query
    base_sql = models.TextField(
        help_text="Main SQL query without WHERE clause. Use {where_clause} placeholder. Example: SELECT * FROM table {where_clause}"
    )

    # Dynamic WHERE clauses configuration
    where_clauses = models.JSONField(
        default=list,
        blank=True,
        help_text="""
        JSON array of WHERE clause definitions. Example:
        [
            {
                "field": "year",
                "operator": "YEAR",
                "parameter_name": "year",
                "label": "Select Year",
                "field_type": "select",
                "options_query": "SELECT DISTINCT EXTRACT(YEAR FROM date_column) FROM table ORDER BY 1 DESC",
                "default_value": "2024",
                "required": true
            },
            {
                "field": "supply",
                "operator": "=",
                "parameter_name": "supply",
                "label": "Select Supply",
                "field_type": "select",
                "options_query": "SELECT DISTINCT supply FROM compartments ORDER BY supply",
                "required": true
            }
        ]
        """
    )

    # ORDER BY clause
    order_by = models.TextField(
        blank=True,
        help_text="ORDER BY clause. Example: region ASC, district DESC"
    )

    # Report metadata
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='custom')
    export_formats = models.JSONField(
        default=list,
        help_text="JSON list of allowed export formats: ['excel', 'csv', 'pdf', 'shapefile']"
    )

    # Display options
    columns = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of column definitions for display. If empty, all columns will be shown."
    )

    # Permissions
    allowed_groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        help_text="User groups that can run this report"
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports'
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'SQL Report'
        verbose_name_plural = 'SQL Reports'

    def __str__(self):
        return f"{self.name} ({self.report_type})"

    def clean(self):
        """Validate the SQL and JSON configurations"""
        super().clean()

        # Validate base SQL contains placeholder
        if '{where_clause}' not in self.base_sql:
            raise ValidationError(
                "Base SQL must contain '{where_clause}' placeholder for WHERE clause insertion"
            )

        # Validate WHERE clauses JSON
        if self.where_clauses:
            try:
                for clause in self.where_clauses:
                    if not all(k in clause for k in ['field', 'operator', 'parameter_name', 'label', 'field_type']):
                        raise ValidationError(
                            "Each WHERE clause must have 'field', 'operator', 'parameter_name', 'label', and 'field_type'"
                        )

                    # Validate field_type
                    valid_field_types = ['select', 'multiselect', 'text', 'number', 'date', 'year', 'month']
                    if clause['field_type'] not in valid_field_types:
                        raise ValidationError(
                            f"Invalid field_type '{clause['field_type']}'. Must be one of {valid_field_types}"
                        )

                    # Validate operator
                    valid_operators = [op[0] for op in self.OPERATOR_CHOICES]
                    if clause['operator'] not in valid_operators:
                        raise ValidationError(
                            f"Invalid operator '{clause['operator']}'. Must be one of {valid_operators}"
                        )
            except (TypeError, KeyError) as e:
                raise ValidationError(f"Invalid WHERE clauses configuration: {str(e)}")

        # Validate export formats
        if self.export_formats:
            valid_formats = [fmt[0] for fmt in self.EXPORT_FORMATS]
            for fmt in self.export_formats:
                if fmt not in valid_formats:
                    raise ValidationError(
                        f"Invalid export format '{fmt}'. Must be one of {valid_formats}"
                    )

    def get_full_sql(self, parameters=None):
        """Generate full SQL with WHERE clause based on parameters"""
        where_clauses = []
        query_params = []

        if parameters and self.where_clauses:
            for clause in self.where_clauses:
                param_name = clause['parameter_name']
                if param_name in parameters and parameters[param_name]:
                    field = clause['field']
                    operator = clause['operator']
                    value = parameters[param_name]

                    # Handle different operators
                    if operator == 'YEAR':
                        where_clauses.append(f"EXTRACT(YEAR FROM {field}) = %s")
                        query_params.append(value)
                    elif operator == 'MONTH':
                        where_clauses.append(f"EXTRACT(MONTH FROM {field}) = %s")
                        query_params.append(value)
                    elif operator == 'DATE':
                        where_clauses.append(f"DATE({field}) = %s")
                        query_params.append(value)
                    elif operator == 'IN':
                        if isinstance(value, list):
                            placeholders = ','.join(['%s'] * len(value))
                            where_clauses.append(f"{field} IN ({placeholders})")
                            query_params.extend(value)
                        else:
                            where_clauses.append(f"{field} = %s")
                            query_params.append(value)
                    elif operator == 'LIKE':
                        where_clauses.append(f"{field} ILIKE %s")
                        query_params.append(f"%{value}%")
                    elif operator == 'BETWEEN':
                        if isinstance(value, list) and len(value) == 2:
                            where_clauses.append(f"{field} BETWEEN %s AND %s")
                            query_params.extend(value)
                    elif operator in ['IS NULL', 'IS NOT NULL']:
                        where_clauses.append(f"{field} {operator}")
                    else:
                        where_clauses.append(f"{field} {operator} %s")
                        query_params.append(value)

        # Build WHERE clause
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        else:
            where_clause = ""

        # Add ORDER BY if specified
        order_by_clause = f"ORDER BY {self.order_by}" if self.order_by else ""

        # Build full SQL
        full_sql = self.base_sql.format(where_clause=where_clause)
        if order_by_clause:
            full_sql += " " + order_by_clause

        return full_sql, query_params

    def get_parameter_options(self, parameter_name):
        """Get dynamic options for a parameter from its options_query"""
        for clause in self.where_clauses:
            if clause['parameter_name'] == parameter_name and 'options_query' in clause:
                from django.db import connection
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(clause['options_query'])
                        return [row[0] for row in cursor.fetchall()]
                except Exception:
                    return []
        return []

    @property
    def formatted_sql(self):
        """Return formatted SQL for display"""
        return self.base_sql.format(where_clause="WHERE ...") + (f" ORDER BY {self.order_by}" if self.order_by else "")

    def get_available_fields(self):
        """Extract field names from the SQL query"""
        fields = []

        try:
            # Remove comments from SQL
            sql = re.sub(r'--.*$', '', self.base_sql, flags=re.MULTILINE)
            sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

            # Extract SELECT clause (everything between SELECT and FROM)
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
            if not select_match:
                return []

            select_clause = select_match.group(1)

            # Split by commas, handling nested parentheses
            in_parentheses = 0
            current_field = ""
            for char in select_clause:
                if char == '(':
                    in_parentheses += 1
                elif char == ')':
                    in_parentheses -= 1

                if char == ',' and in_parentheses == 0:
                    # End of field
                    field = self._extract_field_name(current_field.strip())
                    if field:
                        fields.append(field)
                    current_field = ""
                else:
                    current_field += char

            # Add the last field
            if current_field:
                field = self._extract_field_name(current_field.strip())
                if field:
                    fields.append(field)

            # Also try to extract table aliases for better display
            from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP BY|\s+ORDER BY|$)',
                                  sql, re.IGNORECASE | re.DOTALL)
            if from_match:
                from_clause = from_match.group(1)
                # Extract table aliases (e.g., "table t" or "table AS t")
                table_aliases = re.findall(r'(\w+)(?:\s+AS)?\s+(\w+)\b', from_clause, re.IGNORECASE)
                table_dict = {alias: table for table, alias in table_aliases}

                # Update fields with table aliases if available
                for i, field in enumerate(fields):
                    if '.' in field:
                        table_part, column_part = field.split('.', 1)
                        if table_part in table_dict:
                            fields[i] = f"{table_part}.{column_part}"

        except Exception as e:
            print(f"Error extracting fields from SQL: {e}")
            import traceback
            traceback.print_exc()

        # Remove duplicates and sort
        return sorted(list(set(f for f in fields if f)))

    def _extract_field_name(self, field_expression):
        """Extract field name from a SQL expression"""
        # Remove "DISTINCT" keyword
        field_expression = re.sub(r'^DISTINCT\s+', '', field_expression, flags=re.IGNORECASE)

        # Handle COUNT(DISTINCT ...) differently
        if re.match(r'COUNT\s*\(.*DISTINCT.*\)', field_expression, re.IGNORECASE):
            # Just return the entire expression for complex aggregates
            return field_expression

        # Remove aggregate functions (keep the column inside)
        field_expression = re.sub(r'^\w+\(([^)]+)\)', r'\1', field_expression, flags=re.IGNORECASE)

        # Remove "AS alias" or just alias after whitespace
        field_expression = re.split(r'\s+(?:AS\s+)?\w+$', field_expression, flags=re.IGNORECASE)[0]

        # Remove extra whitespace
        field_expression = field_expression.strip()

        # If it's a simple column name or table.column, return it
        if re.match(r'^(\w+\.)?\w+$', field_expression):
            return field_expression

        return None

    def get_table_fields(self):
        """Get fields from actual database tables in the query"""
        fields = []
        try:
            # Extract table names from FROM and JOIN clauses
            sql = self.base_sql.upper()

            # Get all table references (simplified)
            table_patterns = [
                r'FROM\s+(\w+(?:\.\w+)?)\s+(\w+)',
                r'JOIN\s+(\w+(?:\.\w+)?)\s+(\w+)\s+ON',
                r'FROM\s+(\w+(?:\.\w+)?)',
                r'JOIN\s+(\w+(?:\.\w+)?)'
            ]

            tables = []
            for pattern in table_patterns:
                matches = re.findall(pattern, sql, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if isinstance(match, tuple):
                        tables.extend([m for m in match if m])
                    else:
                        tables.append(match)

            # Remove duplicates
            tables = list(set(tables))

            # Get columns from each table
            for table in tables:
                try:
                    # Try to get actual columns from database
                    with connection.cursor() as cursor:
                        cursor.execute(f"""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = %s
                            ORDER BY ordinal_position
                        """, [table.split('.')[-1]])  # Remove schema if present
                        columns = [row[0] for row in cursor.fetchall()]

                    for column in columns:
                        fields.append(f"{table}.{column}")

                except Exception as e:
                    print(f"Could not get columns for table {table}: {e}")
                    # Fallback: just add the table reference
                    fields.append(f"{table}.*")

        except Exception as e:
            print(f"Error extracting table fields: {e}")

        return fields
