"""Evaluation API endpoint."""

from fastapi import APIRouter, HTTPException

from atticus.logging import log_event
from eval.runner import run_evaluation

from ..dependencies import LoggerDep, SettingsDep
from ..schemas import EvalResponse

router = APIRouter()


@router.post("/eval/run", response_model=EvalResponse)
async def run_eval(settings: SettingsDep, logger: LoggerDep) -> EvalResponse:
    result = run_evaluation(settings=settings)
    log_event(logger, "eval_api_complete", metrics=result.metrics, deltas=result.deltas)
    threshold = settings.eval_regression_threshold / 100.0
    if any(delta < -threshold for delta in result.deltas.values()):
        raise HTTPException(
            status_code=400, detail={"metrics": result.metrics, "deltas": result.deltas}
        )
    return EvalResponse(
        metrics=result.metrics,
        deltas=result.deltas,
        summary_csv=str(result.summary_csv),
        summary_json=str(result.summary_json),
        summary_html=str(result.summary_html),
    )
