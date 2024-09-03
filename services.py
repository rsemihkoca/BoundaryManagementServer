import json
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel
from models import MatchTable, BoundaryTable, Step, StepChangeRequest, Direction, Boundary, Quad, Coordinate
from utils import load_data, save_data, get_next_or_previous_step
from validators import PolygonValidator, IntersectionValidator
from config import BOUNDARY_DB_FILE, MATCH_DB_FILE, DefaultBoundaryCoordinates

class MatchService:
    def get_all_matches(self) -> List[MatchTable]:
        return [MatchTable(**match) for match in load_data(MATCH_DB_FILE)]

    def create_match(self, table_id: str, camera_ip: str, capacity: int) -> MatchTable:
        if not all([table_id, camera_ip, capacity]):
            raise ValueError("Invalid request data.")

        if not Step.check_capacity(capacity):
            raise ValueError(f"Invalid capacity. Must be between {Step.MIN_CAPACITY()} and {Step.MAX_CAPACITY()}.")

        matches = self.get_all_matches()
        if any(m.table_id == table_id or m.camera_ip == camera_ip for m in matches):
            raise ValueError("Match already exists.")

        new_match = MatchTable(table_id=table_id, camera_ip=camera_ip, step=Step.OUTER, capacity=capacity)
        matches.append(new_match)
        save_data(MATCH_DB_FILE, [match.model_dump() for match in matches])
        return new_match

    def change_step(self, request: StepChangeRequest, boundary_service: 'BoundaryService') -> Tuple[MatchTable, Boundary]:
        updated_boundary=None
        matches = self.get_all_matches()
        match = next((m for m in matches if m.camera_ip == request.camera_ip), None)
        if not match:
            raise ValueError("Match not found.")

        current_step = match.step
        capacity = match.capacity

        if (current_step == Step.OUTER and request.direction == Direction.previous) or \
           (current_step == Step.FINAL and request.direction == Direction.next):
            raise ValueError(f"Cannot move {request.direction} from {current_step} step.")

        if current_step == Step.FINAL:
            pass
        else:
            updated_boundary = boundary_service.update_boundary(request, current_step)

        new_step = get_next_or_previous_step(
            current_step,
            capacity,
            request.direction == Direction.next
        )
        match.step = new_step

        save_data(MATCH_DB_FILE, [m.model_dump() for m in matches])
        return match, updated_boundary

    def delete_match(self, camera_ip: str) -> MatchTable:
        matches = self.get_all_matches()
        deleted_match = next((m for m in matches if m.camera_ip == camera_ip), None)
        if deleted_match:
            matches = [m for m in matches if m.camera_ip != camera_ip]
            save_data(MATCH_DB_FILE, [m.model_dump() for m in matches])
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
        boundaries.append(new_boundary_table.model_dump())
        save_data(BOUNDARY_DB_FILE, boundaries)

    def update_boundary(self, request: StepChangeRequest, current_step: Step) -> Boundary:
        boundaries = load_data(BOUNDARY_DB_FILE)
        boundary = next((BoundaryTable(**b) for b in boundaries if b["camera_ip"] == request.camera_ip), None)
        if not boundary:
            raise ValueError("Boundary not found.")

        # Validate the polygon is convex and non-self-intersecting
        quad = Quad(
            UL_coord=request.UL_coord,
            UR_coord=request.UR_coord,
            LR_coord=request.LR_coord,
            LL_coord=request.LL_coord
        )
        valid, message = PolygonValidator(quad).is_valid_polygon()
        if not valid:
            raise ValueError(message)

        # Get the current boundary being updated
        current_boundary = next((item for item in boundary.items if item.boundary_type == current_step.value), None)
        if not current_boundary:
            raise ValueError(f"No boundary found for step {current_step.value}")

        # Perform boundary-specific validations
        self._validate_boundary_placement(boundary.items, current_step, quad)

        # Update the boundary
        current_boundary.UL_coord = request.UL_coord
        current_boundary.UR_coord = request.UR_coord
        current_boundary.LR_coord = request.LR_coord
        current_boundary.LL_coord = request.LL_coord

        updated_boundaries = [b if b["camera_ip"] != boundary.camera_ip else boundary.model_dump() for b in boundaries]
        save_data(BOUNDARY_DB_FILE, updated_boundaries)
        return current_boundary

    def _validate_boundary_placement(self, boundary_items: List[Boundary], current_step: Step, new_quad: Quad):
        if current_step == Step.OUTER:
            self._validate_outer_boundary(boundary_items, new_quad)
        elif current_step == Step.TABLE:
            self._validate_table_boundary(boundary_items, new_quad)
        else:
            self._validate_numbered_boundary(boundary_items, current_step, new_quad)

    def _validate_outer_boundary(self, boundary_items: List[Boundary], new_quad: Quad):
        for item in boundary_items:
            if item.boundary_type != "OUTER":
                other_quad = Quad(
                    UL_coord=item.UL_coord,
                    UR_coord=item.UR_coord,
                    LR_coord=item.LR_coord,
                    LL_coord=item.LL_coord
                )
                valid, message = IntersectionValidator(new_quad, other_quad).is_valid_placement()
                if not valid:
                    raise ValueError(f"OUTER boundary intersects with {item.boundary_type} boundary.")

    def _validate_table_boundary(self, boundary_items: List[Boundary], new_quad: Quad):
        outer_boundary = next((item for item in boundary_items if item.boundary_type == "OUTER"), None)
        if outer_boundary:
            outer_quad = Quad(
                UL_coord=outer_boundary.UL_coord,
                UR_coord=outer_boundary.UR_coord,
                LR_coord=outer_boundary.LR_coord,
                LL_coord=outer_boundary.LL_coord
            )
            valid, message = IntersectionValidator(new_quad, outer_quad).is_valid_placement()
            if not valid:
                raise ValueError("TABLE boundary intersects with OUTER boundary.")

    def _validate_numbered_boundary(self, boundary_items: List[Boundary], current_step: Step, new_quad: Quad):
        for item in boundary_items:
            if item.boundary_type not in [current_step.value, "TABLE"]:
                other_quad = Quad(
                    UL_coord=item.UL_coord,
                    UR_coord=item.UR_coord,
                    LR_coord=item.LR_coord,
                    LL_coord=item.LL_coord
                )
                valid, message = IntersectionValidator(new_quad, other_quad).is_valid_placement()
                if not valid:
                    raise ValueError(f"Boundary {current_step.value} intersects with {item.boundary_type} boundary.")

    def get_boundaries(self, camera_ip: str) -> dict:
        boundaries = load_data(BOUNDARY_DB_FILE)
        camera_boundaries = next((b for b in boundaries if b["camera_ip"] == camera_ip), None)
        
        if not camera_boundaries:
            raise ValueError("No boundaries found for the given camera IP.")
        
        boundary_table = BoundaryTable(**camera_boundaries)
        
        return boundary_table.model_dump(by_alias=True)

    def delete_boundaries(self, camera_ip: str):
        boundaries = load_data(BOUNDARY_DB_FILE)
        boundaries = [b for b in boundaries if b["camera_ip"] != camera_ip]
        save_data(BOUNDARY_DB_FILE, boundaries)

    def reset_boundaries(self, camera_ip: str, match_service: 'MatchService') -> Tuple[MatchTable, BoundaryTable]:
        matches = match_service.get_all_matches()
        match = next((m for m in matches if m.camera_ip == camera_ip), None)
        if not match:
            raise ValueError("No match found for the given camera IP.")

        table_id = match.table_id
        capacity = match.capacity

        match.step = Step.OUTER
        save_data(MATCH_DB_FILE, [m.model_dump() for m in matches])

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
            boundary_items.append(new_boundary)

        new_boundary_table = BoundaryTable(
            table_id=table_id,
            camera_ip=camera_ip,
            items=boundary_items
        )

        boundaries[boundary_index] = new_boundary_table.model_dump()
        save_data(BOUNDARY_DB_FILE, boundaries)

        return match, new_boundary_table