import json
from typing import List, Tuple, Dict, Any
from models import MatchTable, BoundaryTable, Step, StepChangeRequest, Direction, Boundary, Coordinate
from utils import load_data, save_data, get_next_or_previous_step
from validators import PolygonValidator, IntersectionValidator
from config import BOUNDARY_DB_FILE, MATCH_DB_FILE, DefaultBoundaryCoordinates

class MatchService:
    def get_all_matches(self) -> List[Dict[str, Any]]:
        return load_data(MATCH_DB_FILE)

    def create_match(self, table_id: str, camera_ip: str, capacity: int) -> MatchTable:
        if not all([table_id, camera_ip, capacity]):
            raise ValueError("Invalid request data.")

        if not Step.check_capacity(capacity):
            raise ValueError(f"Invalid capacity. Must be between {Step.MIN_CAPACITY()} and {Step.MAX_CAPACITY()}.")

        matches = self.get_all_matches()
        if any(m["table_id"] == table_id or m["camera_ip"] == camera_ip for m in matches):
            raise ValueError("Match already exists.")

        new_match = MatchTable(table_id=table_id, camera_ip=camera_ip, step=Step.OUTER, capacity=capacity)
        matches.append(new_match.dict())
        save_data(MATCH_DB_FILE, matches)
        return new_match

    def change_step(self, request: StepChangeRequest, boundary_service: 'BoundaryService') -> Tuple[Dict[str, Any], Dict[str, Any]]:
        matches = self.get_all_matches()
        match = next((m for m in matches if m["camera_ip"] == request.camera_ip), None)
        if not match:
            raise ValueError("Match not found.")

        current_step = Step(match["step"])
        capacity = match["capacity"]

        if (current_step == Step.OUTER and request.direction == Direction.previous) or \
           (current_step == Step.FINAL and request.direction == Direction.next):
            raise ValueError(f"Cannot move {request.direction} from {current_step} step.")

        updated_boundary = boundary_service.update_boundary(request, current_step)

        new_step = get_next_or_previous_step(
            current_step,
            capacity,
            request.direction == Direction.next
        )
        match["step"] = new_step

        save_data(MATCH_DB_FILE, matches)
        return match, updated_boundary

    def delete_match(self, camera_ip: str) -> Dict[str, Any]:
        matches = self.get_all_matches()
        deleted_match = next((m for m in matches if m["camera_ip"] == camera_ip), None)
        if deleted_match:
            matches = [m for m in matches if m["camera_ip"] != camera_ip]
            save_data(MATCH_DB_FILE, matches)
            return deleted_match
        raise ValueError("Match not found.")

class BoundaryService:
    def create_boundaries(self, table_id: str, camera_ip: str, capacity: int):
        boundaries = load_data(BOUNDARY_DB_FILE)
        boundary_items = []
        for boundary_type in ["OUTER", "TABLE"] + [str(i) for i in range(1, capacity + 1)]:
            default_coords = DefaultBoundaryCoordinates.get_default_coordinates(boundary_type, capacity)
            new_boundary = Boundary(
                boundary_type=boundary_type,
                UL_coord=Coordinate(**default_coords["UL"]),
                UR_coord=Coordinate(**default_coords["UR"]),
                LR_coord=Coordinate(**default_coords["LR"]),
                LL_coord=Coordinate(**default_coords["LL"])
            )
            boundary_items.append(new_boundary)
        
        new_boundary_table = BoundaryTable(
            table_id=table_id,
            camera_ip=camera_ip,
            items=boundary_items
        )
        boundaries.append(new_boundary_table.dict())
        save_data(BOUNDARY_DB_FILE, boundaries)

    def update_boundary(self, request: StepChangeRequest, current_step: Step) -> Dict[str, Any]:
        boundaries = load_data(BOUNDARY_DB_FILE)
        boundary = next((b for b in boundaries if b["camera_ip"] == request.camera_ip), None)
        if not boundary:
            raise ValueError("Boundary not found.")

        # Validate the polygon is convex and non-self-intersecting
        new_coords = [
            request.UL_coord.to_tuple(),
            request.UR_coord.to_tuple(),
            request.LR_coord.to_tuple(),
            request.LL_coord.to_tuple()
        ]
        valid, message = PolygonValidator(*new_coords).is_valid_polygon()
        if not valid:
            raise ValueError(message)

        # Get the current boundary being updated
        current_boundary = next((item for item in boundary["items"] if item["boundary_type"] == current_step.value), None)
        if not current_boundary:
            raise ValueError(f"No boundary found for step {current_step.value}")

        # Perform boundary-specific validations
        self._validate_boundary_placement(boundary["items"], current_step, new_coords)

        # Update the boundary
        current_boundary.update({
            "UL_coord": request.UL_coord.dict(),
            "UR_coord": request.UR_coord.dict(),
            "LR_coord": request.LR_coord.dict(),
            "LL_coord": request.LL_coord.dict()
        })

        save_data(BOUNDARY_DB_FILE, boundaries)
        return current_boundary

    def _validate_boundary_placement(self, boundary_items: List[Boundary], current_step: Step, new_coords: List[Tuple[int, int]]):
        if current_step == Step.OUTER:
            self._validate_outer_boundary(boundary_items, new_coords)
        elif current_step == Step.TABLE:
            self._validate_table_boundary(boundary_items, new_coords)
        else:
            self._validate_numbered_boundary(boundary_items, current_step, new_coords)

    def _validate_outer_boundary(self, boundary_items: List[Boundary], new_coords: List[Tuple[int, int]]):
        for item in boundary_items:
            if item["boundary_type"] != "OUTER":
                other_coords = [
                    Coordinate(**item["UL_coord"]).to_tuple(),
                    Coordinate(**item["UR_coord"]).to_tuple(),
                    Coordinate(**item["LR_coord"]).to_tuple(),
                    Coordinate(**item["LL_coord"]).to_tuple()
                ]
                valid, message = IntersectionValidator(*new_coords, *other_coords).is_valid_placement()
                if not valid:
                    raise ValueError(f"OUTER boundary intersects with {item['boundary_type']} boundary.")

    def _validate_table_boundary(self, boundary_items: List[Boundary], new_coords: List[Tuple[int, int]]):
        outer_boundary = next((item for item in boundary_items if item["boundary_type"] == "OUTER"), None)
        if outer_boundary:
            outer_coords = [
                Coordinate(**outer_boundary["UL_coord"]).to_tuple(),
                Coordinate(**outer_boundary["UR_coord"]).to_tuple(),
                Coordinate(**outer_boundary["LR_coord"]).to_tuple(),
                Coordinate(**outer_boundary["LL_coord"]).to_tuple()
            ]
            valid, message = IntersectionValidator(*new_coords, *outer_coords).is_valid_placement()
            if not valid:
                raise ValueError("TABLE boundary intersects with OUTER boundary.")

    def _validate_numbered_boundary(self, boundary_items: List[Boundary], current_step: Step, new_coords: List[Tuple[int, int]]):
        for item in boundary_items:
            if item["boundary_type"] not in [current_step.value, "TABLE"]:
                other_coords = [
                    Coordinate(**item["UL_coord"]).to_tuple(),
                    Coordinate(**item["UR_coord"]).to_tuple(),
                    Coordinate(**item["LR_coord"]).to_tuple(),
                    Coordinate(**item["LL_coord"]).to_tuple()
                ]
                valid, message = IntersectionValidator(*new_coords, *other_coords).is_valid_placement()
                if not valid:
                    raise ValueError(f"Boundary {current_step.value} intersects with {item['boundary_type']} boundary.")

    def get_boundaries(self, camera_ip: str) -> Dict[str, Any]:
        boundaries = load_data(BOUNDARY_DB_FILE)
        camera_boundaries = next((b for b in boundaries if b["camera_ip"] == camera_ip), None)
        if not camera_boundaries:
            raise ValueError("No boundaries found for the given camera IP.")
        return camera_boundaries

    def delete_boundaries(self, camera_ip: str):
        boundaries = load_data(BOUNDARY_DB_FILE)
        boundaries = [b for b in boundaries if b["camera_ip"] != camera_ip]
        save_data(BOUNDARY_DB_FILE, boundaries)

    def reset_boundaries(self, camera_ip: str, match_service: 'MatchService') -> Tuple[Dict[str, Any], Dict[str, Any]]:
        matches = match_service.get_all_matches()
        match = next((m for m in matches if m["camera_ip"] == camera_ip), None)
        if not match:
            raise ValueError("No match found for the given camera IP.")

        table_id = match["table_id"]
        capacity = match["capacity"]

        match["step"] = Step.OUTER.value
        save_data(MATCH_DB_FILE, matches)

        boundaries = load_data(BOUNDARY_DB_FILE)
        boundary_index = next((i for i, b in enumerate(boundaries) if b["camera_ip"] == camera_ip), None)
        if boundary_index is None:
            raise ValueError("No boundaries found for the given camera IP.")

        boundary_items = []
        for boundary_type in ["OUTER", "TABLE"] + [str(i) for i in range(1, capacity + 1)]:
            default_coords = DefaultBoundaryCoordinates.get_default_coordinates(boundary_type, capacity)
            new_boundary = Boundary(
                boundary_type=boundary_type,
                UL_coord=Coordinate(**default_coords["UL"]),
                UR_coord=Coordinate(**default_coords["UR"]),
                LR_coord=Coordinate(**default_coords["LR"]),
                LL_coord=Coordinate(**default_coords["LL"])
            )
            boundary_items.append(new_boundary.dict())

        new_boundary_table = BoundaryTable(
            table_id=table_id,
            camera_ip=camera_ip,
            items=boundary_items
        )

        boundaries[boundary_index] = new_boundary_table.dict()
        save_data(BOUNDARY_DB_FILE, boundaries)

        return match, new_boundary_table.dict()