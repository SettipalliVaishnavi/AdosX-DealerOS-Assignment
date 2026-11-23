from collections import defaultdict
from decimal import Decimal

from reconcile.models import Location, SystemARecord, SystemBEntry


ZERO = Decimal("0.00")


def get_disagreements(org_id):
    """
    Compare System A and System B records for one organization.

    Tenant ownership is determined only through Location.org_id.
    Foreign-tenant values and location details are never returned.
    """

    locations = {
        loc.location_id: loc
        for loc in Location.objects.all()
    }

    a_records = list(
        SystemARecord.objects.select_related("location").all()
    )

    b_entries = list(
        SystemBEntry.objects.select_related("location").all()
    )

    a_by_ref = {}
    for record in a_records:
        a_by_ref[record.record_id] = record

    b_by_ref = defaultdict(list)
    for entry in b_entries:
        if entry.record_ref:
            b_by_ref[entry.record_ref].append(entry)

    results = []

    def add_result(reason, record_id, location_name,
                   a_value=None, b_value=None, difference=None):
        results.append({
            "reason": reason,
            "record_id": record_id,
            "location": location_name,
            "system_a_value": a_value,
            "system_b_value": b_value,
            "difference": difference,
            "sort_value": (
                a_value if a_value is not None
                else b_value if b_value is not None
                else ZERO
            ),
        })

    def money(value):
        return value if value is not None else None

    # Compare records owned by the requested organization.
    for record in a_records:
        a_location = locations.get(record.location_id_raw)

        if not a_location or a_location.org_id != org_id:
            continue

        location_name = a_location.location_name
        matching_entries = b_by_ref.get(record.record_id, [])

        # A matching B entry exists in another organization.
        foreign_entries = [
            entry for entry in matching_entries
            if not entry.location
            or entry.location.org_id != org_id
        ]

        own_entries = [
            entry for entry in matching_entries
            if entry.location
            and entry.location.org_id == org_id
        ]

        if foreign_entries and not own_entries:
            add_result(
                "LOCATION_MISMATCH",
                record.record_id,
                location_name,
                money(record.total_value),
                None,
                None,
            )
            continue

        # No B entry exists anywhere.
        if not matching_entries:
            if record.state.upper() != "VOIDED":
                add_result(
                    "MISSING_IN_B",
                    record.record_id,
                    location_name,
                    money(record.total_value),
                    None,
                    None,
                )
            continue

        # A has been voided: retain the source data but do not
        # treat its B entry as a normal financial disagreement.
        if record.state.upper() == "VOIDED":
            continue

        # Do not reveal foreign-tenant entries.
        if not own_entries:
            continue

        # Multiple entries may be a valid split.
        if len(own_entries) > 1:
            if any(entry.value is None for entry in own_entries):
                add_result(
                    "DUPLICATE_IN_B",
                    record.record_id,
                    location_name,
                    money(record.total_value),
                    None,
                    None,
                )
                continue

            b_total = sum(
                (entry.value for entry in own_entries),
                ZERO
            )

            if record.total_value is not None and b_total == record.total_value:
                # Valid split: no disagreement.
                pass
            else:
                add_result(
                    "DUPLICATE_IN_B",
                    record.record_id,
                    location_name,
                    money(record.total_value),
                    b_total,
                    (
                        record.total_value - b_total
                        if record.total_value is not None else None
                    ),
                )
                continue

        else:
            b_total = own_entries[0].value

            if record.total_value is None or b_total is None:
                add_result(
                    "VALUE_MISMATCH",
                    record.record_id,
                    location_name,
                    money(record.total_value),
                    money(b_total),
                    None,
                )
            elif record.total_value != b_total:
                add_result(
                    "VALUE_MISMATCH",
                    record.record_id,
                    location_name,
                    money(record.total_value),
                    money(b_total),
                    record.total_value - b_total,
                )

        # Check date mismatch only for a single B entry.
        if len(own_entries) == 1:
            entry = own_entries[0]

            if (
                record.event_date
                and entry.recorded_on
                and record.event_date != entry.recorded_on
            ):
                add_result(
                    "DATE_MISMATCH",
                    record.record_id,
                    location_name,
                    money(record.total_value),
                    money(entry.value),
                    None,
                )

            # Location mismatch within the same organization.
            if record.location_id_raw != entry.location_id_raw:
                add_result(
                    "LOCATION_MISMATCH",
                    record.record_id,
                    location_name,
                    money(record.total_value),
                    money(entry.value),
                    None,
                )

    # Find B entries that have no corresponding A record.
    for entry in b_entries:
        b_location = locations.get(entry.location_id_raw)

        if not b_location or b_location.org_id != org_id:
            continue

        if not entry.record_ref or entry.record_ref not in a_by_ref:
            add_result(
                "ORPHAN_IN_B",
                entry.record_ref or entry.record_ref_raw,
                b_location.location_name,
                None,
                money(entry.value),
                None,
            )

    return results


def filter_and_sort_disagreements(
    org_id,
    reason=None,
    sort="-value",
):
    results = get_disagreements(org_id)

    if reason:
        results = [
            item for item in results
            if item["reason"] == reason
        ]

    reverse = sort.startswith("-")

    results.sort(
        key=lambda item: item["sort_value"],
        reverse=reverse,
    )

    return results
