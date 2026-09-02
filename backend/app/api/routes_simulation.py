from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.simulation import SimulationRequest, SimulationResult
from ..services import simulation_service

router = APIRouter(tags=["simulation"])


@router.post("/simulation/run", response_model=SimulationResult)
def run_simulation(body: SimulationRequest, db: Session = Depends(get_db)) -> SimulationResult:
    return simulation_service.run_simulation(
        num_cases=body.num_cases, seed=body.seed, db=db, persist=body.persist
    )
