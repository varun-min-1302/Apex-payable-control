from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from backend.api.deps import get_db, get_current_user
from backend.database.models.identity import User
from backend.database.models.ap import ControlRun, ControlResult
from backend.api.schemas.control_schemas import ControlRunOut, ControlResultOut

router = APIRouter(prefix="/controls", tags=["Control Engine Execution"])

@router.get("/runs", response_model=list[ControlRunOut])
def list_control_runs(
    invoice_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List historical control runs with summary metrics."""
    stmt = (
        select(ControlRun)
        .where(ControlRun.tenant_id == current_user.tenant_id)
        .options(selectinload(ControlRun.results))
        .order_by(desc(ControlRun.started_at))
    )

    if invoice_id:
        stmt = stmt.where(ControlRun.invoice_id == invoice_id)
    if status_filter:
        stmt = stmt.where(ControlRun.status == status_filter.upper())

    stmt = stmt.offset(offset).limit(limit)
    runs = db.execute(stmt).scalars().all()

    result = []
    for r in runs:
        res_outs = [ControlResultOut.model_validate(cr) for cr in r.results]
        result.append(
            ControlRunOut(
                id=r.id,
                tenant_id=r.tenant_id,
                invoice_id=r.invoice_id,
                invoice_revision_id=r.invoice_revision_id,
                run_number=r.run_number,
                status=r.status,
                ruleset_version=r.ruleset_version,
                started_at=r.started_at,
                completed_at=r.completed_at,
                results=res_outs
            )
        )
    return result

@router.get("/runs/{run_id}", response_model=ControlRunOut)
def get_control_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full evaluation breakdown of a specific control run including all 18 rules."""
    stmt = (
        select(ControlRun)
        .where(ControlRun.tenant_id == current_user.tenant_id, ControlRun.id == run_id)
        .options(selectinload(ControlRun.results))
    )
    run = db.execute(stmt).scalars().first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control run not found.")

    res_outs = [ControlResultOut.model_validate(cr) for cr in run.results]
    return ControlRunOut(
        id=run.id,
        tenant_id=run.tenant_id,
        invoice_id=run.invoice_id,
        invoice_revision_id=run.invoice_revision_id,
        run_number=run.run_number,
        status=run.status,
        ruleset_version=run.ruleset_version,
        started_at=run.started_at,
        completed_at=run.completed_at,
        results=res_outs
    )
