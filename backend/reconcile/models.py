
from django.db import models


class Location(models.Model):
    location_id = models.CharField(max_length=50, unique=True)
    org_id = models.CharField(max_length=50, db_index=True)
    location_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.location_id} - {self.org_id}"


class SystemARecord(models.Model):
    record_id = models.CharField(max_length=100, unique=True, db_index=True)

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_a_records",
    )
    location_id_raw = models.CharField(max_length=50, blank=True)

    event_date = models.DateField(null=True, blank=True)
    event_date_raw = models.CharField(max_length=50, blank=True)

    category_code = models.CharField(max_length=100, blank=True)
    actor_id = models.CharField(max_length=100, null=True, blank=True)

    base_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    adjustment = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    total_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )

    state = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.record_id


class SystemBEntry(models.Model):
    entry_id = models.CharField(max_length=100, unique=True, db_index=True)

    # Keep the original reference and its normalized form separately.
    record_ref_raw = models.CharField(max_length=150, blank=True)
    record_ref = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_b_entries",
    )
    location_id_raw = models.CharField(max_length=50, blank=True)

    recorded_on = models.DateField(null=True, blank=True)
    recorded_on_raw = models.CharField(max_length=50, blank=True)

    # Preserve the original value, including blank or malformed values.
    value_raw = models.CharField(max_length=100, blank=True)
    value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )

    label = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.entry_id
