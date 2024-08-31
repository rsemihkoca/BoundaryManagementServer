import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse

from config import BOUNDARY_API_VERSION, setup_logging, logging_config
from models import GenericResponse, StepChangeRequest, MatchTable, BoundaryTable
from services import MatchService, BoundaryService
from dependencies import get_match_service, get_boundary_service

# Setup logging
setup_logging()
logger = logging.getLogger("app")
logger.info(f"Boundary API version: {BOUNDARY_API_VERSION}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan, title="Boundary API", version=BOUNDARY_API_VERSION)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=GenericResponse(
            success=False,
            data={"detail": str(exc.detail)},
            status_code=exc.status_code
        ).dict()
    )

@app.get("/")
def read_root():
    return GenericResponse(success=True, data={"message": "Boundary API is running."})

@app.get("/matches", response_model=GenericResponse)
async def get_matches(match_service: MatchService = Depends(get_match_service)):
    matches = match_service.get_all_matches()
    return GenericResponse(success=True, data=matches)

@app.post("/matches", response_model=GenericResponse)
async def match_table_and_camera(
    table_id: str,
    camera_ip: str,
    capacity: int,
    match_service: MatchService = Depends(get_match_service),
    boundary_service: BoundaryService = Depends(get_boundary_service)
):
    try:
        new_match = match_service.create_match(table_id, camera_ip, capacity)
        boundary_service.create_boundaries(table_id, camera_ip, capacity)
        return GenericResponse(success=True, data=new_match.dict())
    except ValueError as e:
        return GenericResponse(success=False, data={"detail": str(e)}, status_code=400)

@app.put("/matches/change_step", response_model=GenericResponse)
async def change_step(
    request: StepChangeRequest,
    match_service: MatchService = Depends(get_match_service),
    boundary_service: BoundaryService = Depends(get_boundary_service)
):
    try:
        updated_match, updated_boundary = match_service.change_step(request, boundary_service)
        return GenericResponse(success=True, data={
            "updated_match": updated_match,
            "updated_boundary": updated_boundary
        })
    except ValueError as e:
        return GenericResponse(success=False, data={"detail": str(e)}, status_code=400)

@app.delete("/matches", response_model=GenericResponse)
async def unmatch_table_and_camera(
    camera_ip: str,
    match_service: MatchService = Depends(get_match_service),
    boundary_service: BoundaryService = Depends(get_boundary_service)
):
    try:
        deleted_match = match_service.delete_match(camera_ip)
        boundary_service.delete_boundaries(camera_ip)
        return GenericResponse(success=True, data={
            "detail": "Match and related boundaries deleted successfully.",
            "deleted_match": deleted_match
        })
    except ValueError as e:
        return GenericResponse(success=False, data={"detail": str(e)}, status_code=404)

@app.get("/boundaries/{camera_ip}", response_model=GenericResponse)
async def get_boundaries(
    camera_ip: str,
    boundary_service: BoundaryService = Depends(get_boundary_service)
):
    try:
        boundaries = boundary_service.get_boundaries(camera_ip)
        return GenericResponse(success=True, data=boundaries)
    except ValueError as e:
        return GenericResponse(success=False, data={"detail": str(e)}, status_code=404)

@app.post("/boundaries/{camera_ip}/reset", response_model=GenericResponse)
async def reset_boundaries(
    camera_ip: str,
    match_service: MatchService = Depends(get_match_service),
    boundary_service: BoundaryService = Depends(get_boundary_service)
):
    try:
        updated_match, updated_boundaries = boundary_service.reset_boundaries(camera_ip, match_service)
        return GenericResponse(success=True, data={
            "message": "Boundaries reset successfully",
            "updated_match": updated_match,
            "updated_boundaries": updated_boundaries
        })
    except ValueError as e:
        return GenericResponse(success=False, data={"detail": str(e)}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_config=logging_config)
