from math import atan
from typing import Tuple

class PolygonValidator:
    def __init__(self, UL:Tuple[int,int], UR:Tuple[int,int], LR:Tuple[int,int], LL:Tuple[int,int],):
        self.points = [UL, UR, LR, LL]

    def check_convex(self):
        def cross_product_sign(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        n = len(self.points)
        if n < 3:
            return False  # A polygon can't have less than 3 sides

        sign = 0
        for i in range(n):
            cp_sign = cross_product_sign(self.points[i], self.points[(i + 1) % n], self.points[(i + 2) % n])
            if cp_sign != 0:
                if sign == 0:
                    sign = cp_sign
                elif sign * cp_sign < 0:
                    return False  # Non-convex

        return True

    def check_self_intersecting(self):
        def do_lines_intersect(p1, p2, q1, q2):
            def orientation(p, q, r):
                val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
                if val == 0:
                    return 0  # collinear
                elif val > 0:
                    return 1  # clockwise
                else:
                    return 2  # counterclockwise

            o1 = orientation(p1, p2, q1)
            o2 = orientation(p1, p2, q2)
            o3 = orientation(q1, q2, p1)
            o4 = orientation(q1, q2, p2)

            if o1 != o2 and o3 != o4:
                return True

            return False

        n = len(self.points)
        for i in range(n):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                if do_lines_intersect(self.points[i], self.points[(i + 1) % n], self.points[j], self.points[(j + 1) % n]):
                    return True

        return False

    def check_duplicate_points(self):
        return len(self.points) != len(set(self.points))

    def is_valid_polygon(self):
        if self.check_duplicate_points():
            return False, "Polygon has duplicate points."

        if self.check_self_intersecting():
            return False, "Polygon is self-intersecting."

        if not self.check_convex():
            return False, "Polygon is not convex."

        return True, "Polygon is valid."

# Example usage:
case1 = {
    'UL': (1, 3),
    'UR': (4, 3),
    'LR': (0, 0),
    'LL': (2, 2)
}

case2 = {
    'UL': (0, 0),
    'UR': (4, 0),
    'LR': (0, 4),
    'LL': (4, 4)
}

case3 = {
    'UL': (0, 0),
    'UR': (4, 0),
    'LR': (4, 4),
    'LL': (0, 4)
}

case4 = {
    'UL': (0, 4),
    'UR': (10, 2),
    'LR': (9, 4),
    'LL': (10, 0)
}

case5 = {
    'UL': (2, 5),
    'UR': (6, 8),
    'LR': (3, 5),
    'LL': (4, 0)
}

"""
Case 1 is valid: False
Case 2 is valid: False
Case 3 is valid: True
Case 4 is valid: False
Case 5 is valid: False
"""
cases = [case1, case2, case3, case4, case5]

for i, case in enumerate(cases, 1):
    valid, message = PolygonValidator(case["UL"], case["UR"], case["LR"], case["LL"]).is_valid_polygon()
    print(f"Case {i}: {message} is valid {valid}")
