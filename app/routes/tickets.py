from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import clock
from ..auth import require_actor, require_token
from ..database import get_db
from ..models import Ticket
from ..schemas import TicketCreate, TicketResponse, TriageDecision, TriageRequest
from ..services.tickets import create_ticket, serialize_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=201, dependencies=[Depends(require_token), Depends(require_actor)])
def submit_ticket(body: TicketCreate, db: Session = Depends(get_db)):
    try:
        ticket = create_ticket(db, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return serialize_ticket(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse, dependencies=[Depends(require_token)])
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Unknown ticket")
    return serialize_ticket(ticket)


@router.post("/{ticket_id}/triage", response_model=TicketResponse, dependencies=[Depends(require_token), Depends(require_actor)])
def triage_ticket(ticket_id: str, body: TriageRequest, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Unknown ticket")
    if ticket.state != "received":
        raise HTTPException(status_code=409, detail="Ticket has already been triaged")

    if body.decision == TriageDecision.actively_exploited:
        if body.aware_at is None:
            raise HTTPException(status_code=422, detail="aware_at is required for actively_exploited")
        try:
            aware_at = clock.normalize_utc(body.aware_at)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if aware_at > clock.now():
            raise HTTPException(status_code=422, detail="aware_at cannot be in the future")
        ticket.state = "reportable"
        ticket.resolution = None
        ticket.aware_at = aware_at
    else:
        if body.aware_at is not None:
            raise HTTPException(status_code=422, detail="aware_at must be omitted for non-reportable decisions")
        ticket.state = "closed"
        ticket.resolution = body.decision.value
        ticket.aware_at = None

    ticket.triage_reason = body.reason
    db.commit()
    db.refresh(ticket)
    return serialize_ticket(ticket)
