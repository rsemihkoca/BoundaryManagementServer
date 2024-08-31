from fastapi import Depends
from services import MatchService, BoundaryService

def get_match_service() -> MatchService:
    return MatchService()

def get_boundary_service() -> BoundaryService:
    return BoundaryService()