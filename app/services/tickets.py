from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from .. import clock
from ..models import Ticket
from ..schemas import TicketCreate
from .deadlines import calculate_deadlines


def _loads(value: str | None):
    return json.loads(value) if value else None


def _utc_string(value: datetime | None) -> str | None:
    if value is None:
        return None

    value = clock.normalize_utc(value)

    return (
        value
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _fix_available(ticket: Ticket) -> datetime | None:
    fix = _loads(ticket.fix_json)

    if not fix or not fix.get("available_at"):
        return None

    return datetime.fromisoformat(
        fix["available_at"].replace("Z", "+00:00")
    )


def _status(
    due_at: datetime | None,
    current: datetime,
    *,
    awaiting_fix: bool = False,
) -> str:
    if awaiting_fix:
        return "awaiting_fix"

    if due_at is None:
        return "not_applicable"

    return "overdue" if current > due_at else "pending"


def serialize_ticket(ticket: Ticket) -> dict:
    current = clock.now()

    product = _loads(ticket.product_json) or {}
    reporter = _loads(ticket.reporter_json)
    member_states = _loads(ticket.member_states_json) or []
    vulnerability = _loads(ticket.vulnerability_json)
    fix = _loads(ticket.fix_json)

    if ticket.state != "reportable" or ticket.aware_at is None:
        obligations = {
            "early_warning": {
                "status": "not_applicable",
                "due_at": None,
                "submitted_at": None,
                "reference": None,
            },
            "notification": {
                "status": "not_applicable",
                "due_at": None,
                "submitted_at": None,
                "reference": None,
            },
            "final_report": {
                "status": "not_applicable",
                "due_at": None,
                "submitted_at": None,
                "reference": None,
            },
        }

        next_due = None

    else:
        deadlines = calculate_deadlines(
            ticket.aware_at,
            _fix_available(ticket),
        )

        early_status = _status(
            deadlines["early_warning"],
            current,
        )

        notification_status = _status(
            deadlines["notification"],
            current,
        )

        final_status = _status(
            deadlines["final_report"],
            current,
            awaiting_fix=deadlines["final_report"] is None,
        )

        obligations = {
            "early_warning": {
                "status": early_status,
                "due_at": _utc_string(
                    deadlines["early_warning"]
                ),
                "submitted_at": None,
                "reference": None,
            },
            "notification": {
                "status": notification_status,
                "due_at": _utc_string(
                    deadlines["notification"]
                ),
                "submitted_at": None,
                "reference": None,
            },
            "final_report": {
                "status": final_status,
                "due_at": _utc_string(
                    deadlines["final_report"]
                ),
                "submitted_at": None,
                "reference": None,
            },
        }

        pending_dates = []

        if (
            early_status in {"pending", "overdue"}
            and deadlines["early_warning"] is not None
        ):
            pending_dates.append(
                deadlines["early_warning"]
            )

        if (
            notification_status in {"pending", "overdue"}
            and deadlines["notification"] is not None
        ):
            pending_dates.append(
                deadlines["notification"]
            )

        if (
            final_status in {"pending", "overdue"}
            and deadlines["final_report"] is not None
        ):
            pending_dates.append(
                deadlines["final_report"]
            )

        next_due = (
            min(pending_dates)
            if pending_dates
            else None
        )

    return {
        "id": ticket.id,
        "source": ticket.source,
        "title": ticket.title,
        "description": ticket.description,
        "product": product,
        "reporter": reporter,
        "member_states": member_states,
        "vulnerability": vulnerability,
        "severity": ticket.severity,
        "fix": fix,
        "state": ticket.state,
        "resolution": ticket.resolution,
        "received_at": _utc_string(
            ticket.received_at
        ),
        "aware_at": _utc_string(
            ticket.aware_at
        ),
        "obligations": obligations,
        "next_due_at": _utc_string(
            next_due
        ),
    }


def create_ticket(
    db: Session,
    data: TicketCreate,
) -> Ticket:
    current = clock.now()

    fix = (
        data.fix.model_dump(mode="json")
        if data.fix
        else None
    )

    if (
        data.fix
        and data.fix.available_at is not None
    ):
        if (
            clock.normalize_utc(
                data.fix.available_at
            )
            > current
        ):
            raise ValueError(
                "fix.available_at cannot be in the future"
            )

    ticket = Ticket(
        id=f"t_{uuid.uuid4().hex[:12]}",
        source=data.source.value,
        title=data.title,
        description=data.description,
        product_json=json.dumps(
            data.product.model_dump(mode="json")
        ),
        reporter_json=(
            json.dumps(
                data.reporter.model_dump(mode="json")
            )
            if data.reporter
            else None
        ),
        member_states_json=json.dumps(
            data.member_states
        ),
        vulnerability_json=(
            json.dumps(
                data.vulnerability.model_dump(
                    mode="json"
                )
            )
            if data.vulnerability
            else None
        ),
        severity=(
            data.severity.value
            if data.severity
            else None
        ),
        fix_json=(
            json.dumps(fix)
            if fix
            else None
        ),
        state="received",
        resolution=None,
        received_at=current,
        aware_at=None,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket