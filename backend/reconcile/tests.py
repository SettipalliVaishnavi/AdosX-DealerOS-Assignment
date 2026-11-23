from decimal import Decimal
from datetime import date

from django.test import TestCase

from reconcile.models import Location, SystemARecord, SystemBEntry
from reconcile.services import get_disagreements


class ReconciliationTests(TestCase):

    def setUp(self):
        self.loc_a = Location.objects.create(
            location_id="TEST-LOC-A",
            org_id="TEST-ORG-A",
            location_name="Test Location A",
        )

        self.loc_b = Location.objects.create(
            location_id="TEST-LOC-B",
            org_id="TEST-ORG-B",
            location_name="Test Location B",
        )

    def create_a(
        self,
        record_id="REC-TEST-001",
        location=None,
        total="100.00",
        state="COMPLETED",
        event_date=date(2026, 11, 20),
    ):
        location = location or self.loc_a

        return SystemARecord.objects.create(
            record_id=record_id,
            location=location,
            location_id_raw=location.location_id,
            event_date=event_date,
            event_date_raw=str(event_date),
            category_code="TEST",
            actor_id="ACTOR-1",
            base_value=Decimal(total),
            adjustment=Decimal("0.00"),
            total_value=Decimal(total),
            state=state,
        )

    def create_b(
        self,
        entry_id="ENTRY-TEST-001",
        record_ref="REC-TEST-001",
        location=None,
        value="100.00",
        recorded_on=date(2026, 11, 20),
    ):
        location = location or self.loc_a

        return SystemBEntry.objects.create(
            entry_id=entry_id,
            record_ref_raw=record_ref or "",
            record_ref=record_ref,
            location=location,
            location_id_raw=location.location_id,
            recorded_on=recorded_on,
            recorded_on_raw=str(recorded_on),
            value_raw="" if value is None else str(value),
            value=None if value is None else Decimal(value),
            label="TEST",
        )

    def test_missing_in_system_b(self):
        self.create_a()

        results = get_disagreements("TEST-ORG-A")

        self.assertTrue(
            any(
                item["reason"] == "MISSING_IN_B"
                and item["record_id"] == "REC-TEST-001"
                for item in results
            )
        )

    def test_orphan_in_system_b(self):
        self.create_b(
            record_ref="REC-NOT-IN-A",
        )

        results = get_disagreements("TEST-ORG-A")

        self.assertTrue(
            any(
                item["reason"] == "ORPHAN_IN_B"
                and item["record_id"] == "REC-NOT-IN-A"
                for item in results
            )
        )

    def test_value_mismatch(self):
        self.create_a(total="100.00")
        self.create_b(value="80.00")

        results = get_disagreements("TEST-ORG-A")

        mismatch = next(
            item for item in results
            if item["reason"] == "VALUE_MISMATCH"
        )

        self.assertEqual(
            mismatch["system_a_value"],
            Decimal("100.00"),
        )
        self.assertEqual(
            mismatch["system_b_value"],
            Decimal("80.00"),
        )

    def test_duplicate_entries_not_summing_to_a_total(self):
        self.create_a(total="100.00")

        self.create_b(
            entry_id="ENTRY-DUP-1",
            value="100.00",
        )

        self.create_b(
            entry_id="ENTRY-DUP-2",
            value="100.00",
        )

        results = get_disagreements("TEST-ORG-A")

        self.assertTrue(
            any(item["reason"] == "DUPLICATE_IN_B" for item in results)
        )

    def test_valid_split_entries_are_not_disagreements(self):
        self.create_a(total="100.00")

        self.create_b(
            entry_id="ENTRY-SPLIT-1",
            value="40.00",
        )

        self.create_b(
            entry_id="ENTRY-SPLIT-2",
            value="60.00",
        )

        results = get_disagreements("TEST-ORG-A")

        self.assertFalse(
            any(
                item["record_id"] == "REC-TEST-001"
                for item in results
            )
        )

    def test_date_mismatch(self):
        self.create_a(
            event_date=date(2026, 11, 20),
        )

        self.create_b(
            recorded_on=date(2026, 11, 21),
        )

        results = get_disagreements("TEST-ORG-A")

        self.assertTrue(
            any(item["reason"] == "DATE_MISMATCH" for item in results)
        )

    def test_blank_system_b_value_is_unknown_not_zero(self):
        self.create_a(total="100.00")
        self.create_b(value=None)

        results = get_disagreements("TEST-ORG-A")

        mismatch = next(
            item for item in results
            if item["reason"] == "VALUE_MISMATCH"
        )

        self.assertIsNone(mismatch["system_b_value"])

    def test_voided_record_is_not_reported(self):
        self.create_a(state="VOIDED")
        self.create_b()

        results = get_disagreements("TEST-ORG-A")

        self.assertFalse(
            any(
                item["record_id"] == "REC-TEST-001"
                for item in results
            )
        )

    def test_tenant_isolation_hides_foreign_location_and_value(self):
        self.create_a(
            record_id="REC-CROSS-TENANT",
            location=self.loc_a,
            total="500.00",
        )

        self.create_b(
            entry_id="ENTRY-CROSS-TENANT",
            record_ref="REC-CROSS-TENANT",
            location=self.loc_b,
            value="999.00",
        )

        results = get_disagreements("TEST-ORG-A")

        cross_tenant = next(
            item for item in results
            if item["record_id"] == "REC-CROSS-TENANT"
        )

        self.assertEqual(
            cross_tenant["reason"],
            "LOCATION_MISMATCH",
        )

        self.assertEqual(
            cross_tenant["location"],
            "Test Location A",
        )

        self.assertIsNone(cross_tenant["system_b_value"])

        self.assertNotEqual(
            cross_tenant["location"],
            "Test Location B",
        )

    def test_other_organization_does_not_see_foreign_a_record(self):
        self.create_a(
            record_id="REC-PRIVATE-A",
            location=self.loc_a,
        )

        results = get_disagreements("TEST-ORG-B")

        self.assertFalse(
            any(
                item["record_id"] == "REC-PRIVATE-A"
                for item in results
            )
        )
