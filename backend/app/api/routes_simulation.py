from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.simulation import SimulationRequest, SimulationResult
from ..services import simulation_service

router = APIRouter(tags=["simulation"])


@router.post("/simulation/run", response_model=SimulationResult)
def run_simulation(body: SimulationRequest, db: Session = Depends(get_db)) -> SimulationResult:
    if body.use_llm and body.num_cases > 10:
        raise HTTPException(status_code=422, detail="AI simulation is limited to 10 cases.")
    return simulation_service.run_simulation(
        num_cases=body.num_cases, seed=body.seed, db=db, persist=body.persist,
        use_llm=body.use_llm,
    )
