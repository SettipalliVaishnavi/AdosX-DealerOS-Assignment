import csv
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from reconcile.models import Location, SystemARecord, SystemBEntry


DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def clean(value):
    return str(value or "").strip()


def parse_amount(value):
    raw = clean(value)
    if not raw:
        return None

    try:
        return Decimal(raw.replace(",", "").replace("₹", "").strip())
    except (InvalidOperation, ValueError):
        return None


def parse_date(value):
    raw = clean(value)
    if not raw:
        return None

    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
        "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass

    return None


def normalize_ref(value):
    raw = clean(value).upper()
    compact = re.sub(r"[\s_-]+", "", raw)

    if compact.isdigit():
        number = compact
    elif compact.startswith("REC") and compact[3:].isdigit():
        number = compact[3:]
    else:
        return None

    return "REC-" + number.zfill(4)


class Command(BaseCommand):
    help = "Import DealerOS CSV datasets"

    def handle(self, *args, **options):
        files = {
            "locations": DATA_DIR / "locations.csv",
            "system_a": DATA_DIR / "system_a.csv",
            "system_b": DATA_DIR / "system_b.csv",
        }

        for name, path in files.items():
            if not path.exists():
                self.stderr.write(f"Missing {name} file: {path}")
                return

        locations = self.import_locations(files["locations"])
        records = self.import_system_a(files["system_a"])
        entries = self.import_system_b(files["system_b"])

        self.stdout.write(self.style.SUCCESS("Import completed!"))
        self.stdout.write(f"Locations: {locations}")
        self.stdout.write(f"System A: {records}")
        self.stdout.write(f"System B: {entries}")

    def read_csv(self, path):
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                yield {key.strip(): clean(value) for key, value in row.items() if key}

    @transaction.atomic
    def import_locations(self, path):
        count = 0

        for row in self.read_csv(path):
            location_id = clean(row.get("location_id"))
            if not location_id:
                self.stderr.write("Skipped location with blank ID")
                continue

            Location.objects.update_or_create(
                location_id=location_id,
                defaults={
                    "org_id": clean(row.get("org_id")),
                    "location_name": clean(row.get("location_name")),
                },
            )
            count += 1

        return count

    @transaction.atomic
    def import_system_a(self, path):
        count = 0

        for row in self.read_csv(path):
            record_id = clean(row.get("record_id"))
            if not record_id:
                self.stderr.write("Skipped System A row with blank ID")
                continue

            location_id = clean(row.get("location_id"))
            location = Location.objects.filter(
                location_id=location_id
            ).first()

            SystemARecord.objects.update_or_create(
                record_id=record_id,
                defaults={
                    "location": location,
                    "location_id_raw": location_id,
                    "event_date": parse_date(row.get("event_date")),
                    "event_date_raw": clean(row.get("event_date")),
                    "category_code": clean(row.get("category_code")),
                    "actor_id": clean(row.get("actor_id")) or None,
                    "base_value": parse_amount(row.get("base_value")),
                    "adjustment": parse_amount(row.get("adjustment")),
                    "total_value": parse_amount(row.get("total_value")),
                    "state": clean(row.get("state")),
                },
            )
            count += 1

        return count

    @transaction.atomic
    def import_system_b(self, path):
        count = 0

        for row in self.read_csv(path):
            entry_id = clean(row.get("entry_id"))
            if not entry_id:
                self.stderr.write("Skipped System B row with blank ID")
                continue

            location_id = clean(row.get("location_id"))
            raw_ref = clean(row.get("record_ref"))
            location = Location.objects.filter(
                location_id=location_id
            ).first()

            SystemBEntry.objects.update_or_create(
                entry_id=entry_id,
                defaults={
                    "record_ref_raw": raw_ref,
                    "record_ref": normalize_ref(raw_ref),
                    "location": location,
                    "location_id_raw": location_id,
                    "recorded_on": parse_date(row.get("recorded_on")),
                    "recorded_on_raw": clean(row.get("recorded_on")),
                    "value_raw": clean(row.get("value")),
                    "value": parse_amount(row.get("value")),
                    "label": clean(row.get("label")),
                },
            )
            count += 1

        return count
