# Standard library imports
import json
import logging
import os
from contextlib import asynccontextmanager
from enum import Enum
from typing import List, Tuple, Union, Dict, Any
from polygon_validator import PolygonValidator
# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local imports
from config import BOUNDARY_DB_FILE, MATCH_DB_FILE, BOUNDARY_API_VERSION, setup_logging, logging_config, DefaultBoundaryCoordinates


# Setup logging
setup_logging()
logger = logging.getLogger("app")
logger.info(f"Boundary API version: {BOUNDARY_API_VERSION}")

class Step(str, Enum):
    OUTER = "OUTER"
    TABLE = "TABLE"
    STEP_1 = "1"
    STEP_2 = "2"
    STEP_3 = "3"
    STEP_4 = "4"
    STEP_5 = "5"
    STEP_6 = "6"
    FINAL = "FINAL"

class MatchTable(BaseModel):
    table_id: str
    camera_ip: str
    step: Step
    capacity: int

class Boundary(BaseModel):
    boundary_type: str
    UL_coord: Dict[str, int]
    UR_coord: Dict[str, int]
    LR_coord: Dict[str, int]
    LL_coord: Dict[str, int]

class BoundaryTable(BaseModel):
    table_id: str
    camera_ip: str
    items: List[Boundary]

class GenericResponse(BaseModel):
    success: bool
    data: Union[dict, list]

def load_data(file_path: str) -> List[dict]:
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_data(file_path: str, data: List[dict]):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def get_step_order_for_capacity(capacity: int) -> List[Step]:
    base_steps = [Step.OUTER, Step.TABLE]
    capacity_steps = [getattr(Step, f"STEP_{i}") for i in range(1, min(capacity + 1, 7))]
    return base_steps + capacity_steps + [Step.FINAL]

def get_next_or_previous_step(current_step: Step, capacity: int, move_forward: bool) -> Step:
    step_order = get_step_order_for_capacity(capacity)
    current_index = step_order.index(current_step)
    new_index = current_index + (1 if move_forward else -1)
    return step_order[min(max(new_index, 0), len(step_order) - 1)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    for file_path in [BOUNDARY_DB_FILE, MATCH_DB_FILE]:
        if not os.path.exists(file_path):
            save_data(file_path, [])
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return GenericResponse(success=True, data={"message": "Boundary API is running."})

@app.get("/matches", response_model=GenericResponse)
async def get_matches():
    return GenericResponse(success=True, data=load_data(MATCH_DB_FILE))

@app.post("/matches", response_model=GenericResponse)
async def match_table_and_camera(table_id: str, camera_ip: str, capacity: int):
    if not all([table_id, camera_ip, capacity]):
        raise HTTPException(status_code=400, detail="Invalid request data.")

    matches = load_data(MATCH_DB_FILE)
    if any(m["table_id"] == table_id or m["camera_ip"] == camera_ip for m in matches):
        raise HTTPException(status_code=400, detail="Match already exists.")

    new_match = MatchTable(table_id=table_id, camera_ip=camera_ip, step=Step.OUTER, capacity=capacity)
    matches.append(new_match.dict())
    save_data(MATCH_DB_FILE, matches)

    boundaries = load_data(BOUNDARY_DB_FILE)
    boundary_items = []
    for boundary_type in ["OUTER", "TABLE"] + [str(i) for i in range(1, capacity + 1)]:
        default_coords = DefaultBoundaryCoordinates.get_default_coordinates(boundary_type, capacity)
        new_boundary = Boundary(
            boundary_type=boundary_type,
            UL_coord=default_coords["UL"],
            UR_coord=default_coords["UR"],
            LR_coord=default_coords["LR"],
            LL_coord=default_coords["LL"]
        )
        boundary_items.append(new_boundary)
    
    new_boundary_table = BoundaryTable(
        table_id=table_id,
        camera_ip=camera_ip,
        items=boundary_items
    )
    boundaries.append(new_boundary_table.dict())
    save_data(BOUNDARY_DB_FILE, boundaries)

    return GenericResponse(success=True, data=new_match.dict())

class Direction(str, Enum):
    next = "next"
    previous = "previous"

@app.put("/matches/{direction}", response_model=GenericResponse)
async def change_step(direction: Direction, camera_ip: str):
    if direction not in Direction:
        raise HTTPException(status_code=400, detail="Invalid direction. Use 'next' or 'previous'.")

    matches = load_data(MATCH_DB_FILE)
    for i, match in enumerate(matches):
        if match["camera_ip"] == camera_ip:
            new_step = get_next_or_previous_step(
                Step(match["step"]),
                match["capacity"],
                direction == "next"
            )
            matches[i]["step"] = new_step
            save_data(MATCH_DB_FILE, matches)
            return GenericResponse(success=True, data=matches[i])
    raise HTTPException(status_code=404, detail="Match not found.")

@app.delete("/matches", response_model=GenericResponse)
async def unmatch_table_and_camera(camera_ip: str):
    matches = load_data(MATCH_DB_FILE)
    boundaries = load_data(BOUNDARY_DB_FILE)

    deleted_match = next((m for m in matches if m["camera_ip"] == camera_ip), None)
    if deleted_match:
        matches = [m for m in matches if m["camera_ip"] != camera_ip]
        boundaries = [b for b in boundaries if b["camera_ip"] != camera_ip]
        save_data(MATCH_DB_FILE, matches)
        save_data(BOUNDARY_DB_FILE, boundaries)
        return GenericResponse(success=True, data={
            "detail": "Match and related boundaries deleted successfully.",
            "deleted_match": deleted_match
        })

    raise HTTPException(status_code=404, detail="Match not found.")

@app.get("/boundaries/{camera_ip}", response_model=GenericResponse)
async def get_boundaries(camera_ip: str):
    # Validation: Check if camera_ip is provided
    if not camera_ip:
        raise HTTPException(status_code=400, detail="Camera IP is required.")

    # Check if the camera has a match
    matches = load_data(MATCH_DB_FILE)
    camera_match = next((m for m in matches if m["camera_ip"] == camera_ip), None)

    if not camera_match:
        raise HTTPException(status_code=404, detail="No match found for the given camera IP.")

    boundaries = load_data(BOUNDARY_DB_FILE)
    camera_boundaries = next((b for b in boundaries if b["camera_ip"] == camera_ip), None)

    if not camera_boundaries:
        raise HTTPException(status_code=404, detail="No boundaries found for the given camera IP.")

    return GenericResponse(success=True, data=camera_boundaries)


@app.post("/boundaries/{camera_ip}/reset", response_model=GenericResponse)
async def reset_boundaries(camera_ip: str):
    # Validation: Check if camera_ip is provided
    if not camera_ip:
        raise HTTPException(status_code=400, detail="Camera IP is required.")

    # Check if the camera has a match
    matches = load_data(MATCH_DB_FILE)
    match_index = next((i for i, m in enumerate(matches) if m["camera_ip"] == camera_ip), None)

    if match_index is None:
        raise HTTPException(status_code=404, detail="No match found for the given camera IP.")

    # Get the match details
    match = matches[match_index]
    table_id = match["table_id"]
    capacity = match["capacity"]

    # Update match status to OUTER
    matches[match_index]["step"] = Step.OUTER.value
    save_data(MATCH_DB_FILE, matches)

    # Reset boundaries
    boundaries = load_data(BOUNDARY_DB_FILE)
    boundary_index = next((i for i, b in enumerate(boundaries) if b["camera_ip"] == camera_ip), None)

    if boundary_index is None:
        raise HTTPException(status_code=404, detail="No boundaries found for the given camera IP.")

    # Remove existing boundaries and add default coordinates
    boundary_items = []
    for boundary_type in ["OUTER", "TABLE"] + [str(i) for i in range(1, capacity + 1)]:
        default_coords = DefaultBoundaryCoordinates.get_default_coordinates(boundary_type, capacity)
        new_boundary = Boundary(
            boundary_type=boundary_type,
            UL_coord=default_coords["UL"],
            UR_coord=default_coords["UR"],
            LR_coord=default_coords["LR"],
            LL_coord=default_coords["LL"]
        )
        boundary_items.append(new_boundary.dict())

    new_boundary_table = BoundaryTable(
        table_id=table_id,
        camera_ip=camera_ip,
        items=boundary_items
    )

    boundaries[boundary_index] = new_boundary_table.dict()
    save_data(BOUNDARY_DB_FILE, boundaries)

    return GenericResponse(success=True, data={
        "message": "Boundaries reset successfully",
        "updated_match": matches[match_index],
        "updated_boundaries": new_boundary_table.dict()
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_config=logging_config)