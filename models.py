from enum import Enum
from typing import List, Dict, Union
from pydantic import BaseModel

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

    @classmethod
    def MAX_CAPACITY(cls) -> int:
        return int(cls.STEP_6)

    @classmethod
    def MIN_CAPACITY(cls) -> int:
        return int(cls.STEP_1)

    @classmethod
    def check_capacity(cls, capacity: int) -> bool:
        return cls.MIN_CAPACITY() <= capacity <= cls.MAX_CAPACITY()

class Direction(str, Enum):
    next = "next"
    previous = "previous"


class Coordinate(BaseModel):
    x: int
    y: int

    def to_tuple(self) -> tuple[int, int]:
        return self.x, self.y

class Quad(BaseModel):
    UL_coord: Coordinate
    UR_coord: Coordinate
    LR_coord: Coordinate
    LL_coord: Coordinate    

class MatchTable(BaseModel):
    table_id: str
    camera_ip: str
    step: Step
    capacity: int

class Boundary(Quad):
    boundary_type: str

class BoundaryTable(BaseModel):
    table_id: str
    camera_ip: str
    items: List[Boundary]
    
    class Config:
        allow_population_by_field_name = True

class GenericResponse(BaseModel):
    success: bool
    data: Union[dict, list]
    status_code: int = 200

class StepChangeRequest(Quad):
    direction: Direction
    camera_ip: str