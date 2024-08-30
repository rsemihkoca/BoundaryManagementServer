import io
import logging
import json
import requests
import os
from typing import List, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from starlette.responses import StreamingResponse, JSONResponse
from config import BOUNDARY_DB_FILE, MATCH_DB_FILE, BOUNDARY_API_VERSION, setup_logging, logging_config
from enum import Enum
from colorama import init, Fore, Style
from contextlib import asynccontextmanager



from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
import json
from typing import List
from datetime import datetime

import sys

setup_logging()



logger = logging.getLogger("app")  # Replace with your logger name

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
    STEP_7 = "7"
    STEP_8 = "8"
    FINAL = "FINAL"

class Match(BaseModel):
    table_id: str
    camera_ip: str
    step: Step
    capacity: int

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
    # Prepare Database
    yield
    # Shutdown


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return GenericResponse(success=True, data={"message": "Boundary API is running."})

@app.get("/matches", response_model=List[Match])
async def get_matches():
    return load_matches()


@app.post("/matches", response_model=GenericResponse)
async def create_match(table_id: str, camera_ip: str, capacity: int):

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

@app.put("/matches}", response_model=Match)
async def update_match(table_id: str, camera_ip: str, step: Step):
    matches = load_matches()
    for i, match in enumerate(matches):
        if match["table_id"] == table_id and match["camera_ip"] == camera_ip:
            matches[i] = updated_match.dict()
            save_matches(matches)
            return updated_match
    
    raise HTTPException(status_code=404, detail="Match not found.")

@app.delete("/matches/{table_id}/{camera_ip}", response_model=dict)
async def delete_match(table_id: str, camera_ip: str):
    matches = load_matches()
    for i, match in enumerate(matches):
        if match["table_id"] == table_id and match["camera_ip"] == camera_ip:
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
