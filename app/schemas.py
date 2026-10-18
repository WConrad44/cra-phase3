from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class Product(BaseModel):
    manufacturer: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    affected_versions: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("affected_versions")
    @classmethod
    def validate_versions(cls, value: list[str]) -> list[str]:
        if any(not (1 <= len(v) <= 100) for v in value):
            raise ValueError("each version must be 1-100 characters")
        return value


class Reporter(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    contact: str | None = Field(default=None, max_length=200)


class Vulnerability(BaseModel):
    cve_id: str | None = None
    description: str | None = Field(default=None, max_length=10_000)

    @field_validator("cve_id")
    @classmethod
    def validate_cve(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"CVE-\d{4}-\d{4,}", value):
            raise ValueError("must match CVE-YYYY-NNNN")
        return value


class FixInfo(BaseModel):
    available_at: datetime | None = None
    description: str | None = Field(default=None, max_length=10_000)
    fixed_versions: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("available_at")
    @classmethod
    def timestamp_must_have_offset(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamp must include a UTC offset")
        return value


class TicketCreate(BaseModel):
    source: Source
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    product: Product
    reporter: Reporter | None = None
    member_states: list[str] = Field(default_factory=list)
    vulnerability: Vulnerability | None = None
    severity: Severity | None = None
    fix: FixInfo | None = None

    @field_validator("member_states")
    @classmethod
    def validate_member_states(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("member_states must be unique")
        for code in value:
            if not re.fullmatch(r"[A-Z]{2}", code):
                raise ValueError("member_states must contain two-letter uppercase country codes")
        return value


class TriageDecision(str, Enum):
    actively_exploited = "actively_exploited"
    not_actively_exploited = "not_actively_exploited"
    invalid = "invalid"


class TriageRequest(BaseModel):
    decision: TriageDecision
    reason: str = Field(min_length=1, max_length=10_000)
    aware_at: datetime | None = None

    @field_validator("aware_at")
    @classmethod
    def timestamp_must_have_offset(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamp must include a UTC offset")
        return value


class ClockSetRequest(BaseModel):
    now: datetime

    @field_validator("now")
    @classmethod
    def timestamp_must_have_offset(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include a UTC offset")
        return value


class Obligation(BaseModel):
    status: Literal[
        "not_applicable", "awaiting_fix", "pending", "overdue", "submitted", "submitted_late"
    ]
    due_at: datetime | None = None
    submitted_at: datetime | None = None
    reference: str | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    source: str
    title: str
    description: str
    product: dict
    reporter: dict | None
    member_states: list[str]
    vulnerability: dict | None
    severity: str | None
    fix: dict | None
    state: Literal["received", "reportable", "closed"]
    resolution: str | None
    received_at: datetime
    aware_at: datetime | None
    obligations: dict[str, Obligation]
    next_due_at: datetime | None


class ErrorItem(BaseModel):
    field: str
    message: str


class ProblemDetails(BaseModel):
    title: str
    status: int
    detail: str | None = None
    errors: list[ErrorItem] | None = None
