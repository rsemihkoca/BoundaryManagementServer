import json
from typing import List, Dict, Any
from models import Step

def load_data(file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_data(file_path: str, data: List[Dict[str, Any]]):
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
