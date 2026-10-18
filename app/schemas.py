from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}"
    r"T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:\d{2})$"
)


EU_MEMBER_STATES = {
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
}


def validate_timestamp_string(value):
    if value is None:
        return value

    if isinstance(value, str):
        if not TIMESTAMP_PATTERN.fullmatch(value):
            raise ValueError(
                "timestamp must include seconds "
                "and a UTC offset"
            )

    return value


class Source(str, Enum):
    external_researcher = "external_researcher"
    customer = "customer"
    internal = "internal"
    scanner = "scanner"
    csirt = "csirt"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Sensitivity(str, Enum):
    clear = "CLEAR"
    green = "GREEN"
    amber = "AMBER"
    amber_strict = "AMBER+STRICT"
    red = "RED"


class Product(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    manufacturer: str = Field(
        min_length=1,
        max_length=200,
    )

    name: str = Field(
        min_length=1,
        max_length=200,
    )

    affected_versions: list[str] = Field(
        default_factory=list,
        max_length=50,
    )

    @field_validator(
        "affected_versions"
    )
    @classmethod
    def validate_versions(
        cls,
        value: list[str],
    ) -> list[str]:

        if any(
            not (1 <= len(v) <= 100)
            for v in value
        ):
            raise ValueError(
                "each version must be "
                "1-100 characters"
            )

        return value


class Reporter(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    name: str | None = Field(
        default=None,
        max_length=200,
    )

    contact: str | None = Field(
        default=None,
        max_length=200,
    )


class Vulnerability(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    cve_id: str | None = None

    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )

    @field_validator("cve_id")
    @classmethod
    def validate_cve(
        cls,
        value: str | None,
    ) -> str | None:

        if (
            value is not None
            and not re.fullmatch(
                r"CVE-\d{4}-\d{4,}",
                value,
            )
        ):
            raise ValueError(
                "must match CVE-YYYY-NNNN"
            )

        return value


class Exploit(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )


class Mitigations(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    taken: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )

    for_users: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )


class FixInfo(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    available_at: datetime | None = None

    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )

    fixed_versions: list[str] = Field(
        default_factory=list,
        max_length=50,
    )

    @field_validator(
        "available_at",
        mode="before",
    )
    @classmethod
    def validate_available_at_format(
        cls,
        value,
    ):
        return validate_timestamp_string(
            value
        )

    @field_validator(
        "available_at"
    )
    @classmethod
    def timestamp_must_have_offset(
        cls,
        value: datetime | None,
    ) -> datetime | None:

        if (
            value is not None
            and value.tzinfo is None
        ):
            raise ValueError(
                "timestamp must include "
                "a UTC offset"
            )

        return value

    @field_validator(
        "fixed_versions"
    )
    @classmethod
    def validate_fixed_versions(
        cls,
        value: list[str],
    ) -> list[str]:

        if any(
            not (1 <= len(v) <= 100)
            for v in value
        ):
            raise ValueError(
                "each version must be "
                "1-100 characters"
            )

        return value


class TicketCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    source: Source

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str = Field(
        min_length=1,
        max_length=10_000,
    )

    product: Product

    reporter: Reporter | None = None

    member_states: list[str] = Field(
        default_factory=list
    )

    vulnerability: Vulnerability | None = None

    exploit: Exploit | None = None

    mitigations: Mitigations | None = None

    impact: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )

    malicious_actor: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )

    sensitivity: Sensitivity | None = None

    severity: Severity | None = None

    fix: FixInfo | None = None

    @field_validator(
        "member_states"
    )
    @classmethod
    def validate_member_states(
        cls,
        value: list[str],
    ) -> list[str]:

        if len(value) != len(set(value)):
            raise ValueError(
                "member_states must be unique"
            )

        for code in value:
            if code not in EU_MEMBER_STATES:
                raise ValueError(
                    "member_states must contain "
                    "valid EU member-state codes"
                )

        return value


class TriageDecision(str, Enum):
    actively_exploited = (
        "actively_exploited"
    )

    not_actively_exploited = (
        "not_actively_exploited"
    )

    invalid = "invalid"


class TriageRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    decision: TriageDecision

    reason: str = Field(
        min_length=1,
        max_length=10_000,
    )

    aware_at: datetime | None = None

    @field_validator(
        "aware_at",
        mode="before",
    )
    @classmethod
    def validate_aware_at_format(
        cls,
        value,
    ):
        return validate_timestamp_string(
            value
        )

    @field_validator("aware_at")
    @classmethod
    def timestamp_must_have_offset(
        cls,
        value: datetime | None,
    ) -> datetime | None:

        if (
            value is not None
            and value.tzinfo is None
        ):
            raise ValueError(
                "timestamp must include "
                "a UTC offset"
            )

        return value


class ClockSetRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    now: datetime

    @field_validator(
        "now",
        mode="before",
    )
    @classmethod
    def validate_now_format(
        cls,
        value,
    ):
        return validate_timestamp_string(
            value
        )

    @field_validator("now")
    @classmethod
    def timestamp_must_have_offset(
        cls,
        value: datetime,
    ) -> datetime:

        if value.tzinfo is None:
            raise ValueError(
                "timestamp must include "
                "a UTC offset"
            )

        return value


class Obligation(BaseModel):
    status: Literal[
        "not_applicable",
        "awaiting_fix",
        "pending",
        "overdue",
        "submitted",
        "submitted_late",
    ]

    due_at: str | None = None
    submitted_at: str | None = None
    reference: str | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow"
    )

    id: str
    source: str
    title: str
    description: str
    product: dict

    reporter: dict | None = None

    member_states: list[str]

    vulnerability: dict | None = None

    exploit: dict | None = None

    mitigations: dict | None = None

    impact: str | None = None

    malicious_actor: str | None = None

    sensitivity: str | None = None

    severity: str | None = None

    fix: dict | None = None

    state: Literal[
        "received",
        "reportable",
        "closed",
    ]

    resolution: str | None

    received_at: str

    aware_at: str | None

    obligations: dict[
        str,
        Obligation,
    ]

    next_due_at: str | None


class ErrorItem(BaseModel):
    field: str
    message: str


class ProblemDetails(BaseModel):
    title: str
    status: int
    detail: str | None = None
    errors: list[ErrorItem] | None = None


class SystemTestSetupRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=200,
    )

    setup: dict = Field(
        default_factory=dict
    )


class SessionResponse(BaseModel):
    session_id: str


class CoverageMeasure(BaseModel):
    covered: int | None
    total: int | None

    basis: str = Field(
        min_length=1
    )


class SystemCoverageReport(BaseModel):
    code: CoverageMeasure


class SystemTestReportResponse(BaseModel):
    session_id: str
    coverage: SystemCoverageReport