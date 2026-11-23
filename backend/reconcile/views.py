from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from reconcile.models import Location
from reconcile.services import filter_and_sort_disagreements


@require_GET
def organizations(request):
    orgs = (
        Location.objects
        .values_list("org_id", flat=True)
        .distinct()
        .order_by("org_id")
    )

    return JsonResponse({"organizations": list(orgs)})


@require_GET
def disagreements(request):
    org_id = request.GET.get("org", "").strip()
    reason = request.GET.get("reason", "").strip() or None
    sort = request.GET.get("sort", "-value").strip()

    if not org_id:
        return JsonResponse(
            {"error": "The org query parameter is required."},
            status=400,
        )

    valid_orgs = set(
        Location.objects.values_list("org_id", flat=True).distinct()
    )

    if org_id not in valid_orgs:
        return JsonResponse(
            {"error": "Invalid organization."},
            status=400,
        )

    allowed_reasons = {
        "MISSING_IN_B",
        "ORPHAN_IN_B",
        "DUPLICATE_IN_B",
        "VALUE_MISMATCH",
        "DATE_MISMATCH",
        "LOCATION_MISMATCH",
    }

    if reason and reason not in allowed_reasons:
        return JsonResponse(
            {"error": "Invalid disagreement reason."},
            status=400,
        )

    if sort not in ("value", "-value"):
        return JsonResponse(
            {"error": "Sort must be value or -value."},
            status=400,
        )

    items = filter_and_sort_disagreements(
        org_id=org_id,
        reason=reason,
        sort=sort,
    )

    output = []

    for item in items:
        output.append({
            "reason": item["reason"],
            "record_id": item["record_id"],
            "location": item["location"],
            "system_a_value": (
                str(item["system_a_value"])
                if item["system_a_value"] is not None else None
            ),
            "system_b_value": (
                str(item["system_b_value"])
                if item["system_b_value"] is not None else None
            ),
            "difference": (
                str(item["difference"])
                if item["difference"] is not None else None
            ),
        })

    return JsonResponse({
        "organization": org_id,
        "count": len(output),
        "disagreements": output,
    })
