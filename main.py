from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
import json
from typing import List, Union
from contextlib import asynccontextmanager
import os
import logging
from config import BOUNDARY_DB_FILE, MATCH_DB_FILE, BOUNDARY_API_VERSION, setup_logging, logging_config
setup_logging()

logger = logging.getLogger("app")

logger.info(f"Boundary API version: {BOUNDARY_API_VERSION}")



"""

get match bütün matched clientlerı getir güncel


boundary yarat: match işlemi table id ve kapasite lazım o kadar boundary yaratılacak camera id de lazım
boundary sil: match'i boz ve boundary'leri sil
get bounddary by camera ip
update bounday

"""

class Step(str, Enum):
    INIT = "INIT"
    OUTER = "OUTER"
    TABLE = "TABLE"
    STEP_1 = "1"
    STEP_2 = "2"
    STEP_3 = "3"
    STEP_4 = "4"
    STEP_5 = "5"
    STEP_6 = "6"
    FINAL = "FINAL"

class Match(BaseModel):
    table_id: str
    camera_ip: str
    step: Step
    capacity: int

class Boundary(BaseModel):
    table_id: str
    camera_ip: str
    boundary_type: str
    UL_coord: Tuple(int, int)
    UR_coord: Tuple(int, int)
    LR_coord: Tuple(int, int)
    LL_coord: Tuple(int, int)

class GenericResponse(BaseModel):
    success: bool
    data: Union[dict, list]

def load_matches():
    try:
        with open("matches.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_matches(matches):
    with open("matches.json", "w") as f:
        json.dump(matches, f, indent=2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return GenericResponse(success=True, data={"message": "Boundary API is running."})

@app.get("/matches", response_model=GenericResponse)
async def get_matches():
    return GenericResponse(success=True, data=load_matches())

@app.post("/matches", response_model=GenericResponse)
async def match_table_and_camera(table_id: str, camera_ip: str, capacity: int):
    if not table_id or not camera_ip or not capacity:
        raise HTTPException(status_code=400, detail="Invalid request data.")
    matches = load_matches()
    for existing_match in matches:
        if existing_match["table_id"] == table_id or existing_match["camera_ip"] == camera_ip:
            raise HTTPException(status_code=400, detail="Match already exists.")
    match = Match(table_id=table_id, camera_ip=camera_ip, step=Step.INIT, capacity=capacity)
    matches.append(match.dict())
    save_matches(matches)
    return GenericResponse(success=True, data=match.dict())

@app.put("/matches/next", response_model=GenericResponse)
async def next_step(camera_ip: str):
    matches = load_matches()
    for i, match in enumerate(matches):
        if match["camera_ip"] == camera_ip:
            next_step = get_next_step(match["step"], match["capacity"])
            matches[i]["step"] = next_step
            save_matches(matches)
            return GenericResponse(success=True, data=matches[i])
    raise HTTPException(status_code=404, detail="Match not found.")

@app.put("/matches/previous", response_model=GenericResponse)
async def previous_step(camera_ip: str):
    matches = load_matches()
    for i, match in enumerate(matches):
        if match["camera_ip"] == camera_ip:
            previous_step = get_previous_step(match["step"], match["capacity"])
            matches[i]["step"] = previous_step
            save_matches(matches)
            return GenericResponse(success=True, data=matches[i])
    raise HTTPException(status_code=404, detail="Match not found.")

def get_step_order_for_capacity(capacity: int) -> List[Step]:
    if capacity == 1:
        return [Step.INIT, Step.OUTER, Step.TABLE, Step.STEP_1, Step.FINAL]
    elif capacity == 2:
        return [Step.INIT, Step.OUTER, Step.TABLE, Step.STEP_1, Step.STEP_2, Step.FINAL]
    elif capacity == 3:
        return [Step.INIT, Step.OUTER, Step.TABLE, Step.STEP_1, Step.STEP_2, Step.STEP_3, Step.FINAL]
    elif capacity == 4:
        return [Step.INIT, Step.OUTER, Step.TABLE, Step.STEP_1, Step.STEP_2, Step.STEP_3, Step.STEP_4, Step.FINAL]
    elif capacity == 5:
        return [Step.INIT, Step.OUTER, Step.TABLE, Step.STEP_1, Step.STEP_2, Step.STEP_3, Step.STEP_4, Step.STEP_5, Step.FINAL]
    elif capacity == 6:
        return [Step.INIT, Step.OUTER, Step.TABLE, Step.STEP_1, Step.STEP_2, Step.STEP_3, Step.STEP_4, Step.STEP_5, Step.STEP_6, Step.FINAL]
    else:
        raise ValueError("Unsupported capacity")

def get_next_step(current_step: Step, capacity: int) -> Step:
    step_order = get_step_order_for_capacity(capacity)
    current_index = step_order.index(current_step)
    if current_index + 1 < len(step_order):
        return step_order[current_index + 1]
    return Step.FINAL

def get_previous_step(current_step: Step, capacity: int) -> Step:
    step_order = get_step_order_for_capacity(capacity)
    current_index = step_order.index(current_step)
    if current_index - 1 >= 0:
        return step_order[current_index - 1]
    return Step.INIT

@app.delete("/matches", response_model=dict)
async def unmatch_table_and_camera(camera_ip: str):
    matches = load_matches()
    for i, match in enumerate(matches):
        if match["camera_ip"] == camera_ip:
            deleted_match = matches.pop(i)
            save_matches(matches)
            return {"detail": "Match deleted successfully.", "deleted_match": deleted_match}
    raise HTTPException(status_code=404, detail="Match not found.")

if __name__ == "__main__":
    import uvicorn
    if not os.path.exists(BOUNDARY_DB_FILE):
        with open(BOUNDARY_DB_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(MATCH_DB_FILE):
        with open(MATCH_DB_FILE, "w") as f:
            json.dump([], f)
    uvicorn.run(app, host="0.0.0.0", port=8546, log_config=logging_config)
