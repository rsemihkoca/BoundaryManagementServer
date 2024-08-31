import matplotlib.pyplot as plt

class IntersectionValidator:
    def __init__(self, quad1, quad2):
        self.quad1 = quad1
        self.quad2 = quad2

    @staticmethod
    def orientation(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if val == 0:
            return 0  # Collinear
        return 1 if val > 0 else 2  # Clockwise or Counterclockwise

    @staticmethod
    def on_segment(p, q, r):
        return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
                q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

    @staticmethod
    def line_intersection(line1, line2):
        x1, y1 = line1[0]
        x2, y2 = line1[1]
        x3, y3 = line2[0]
        x4, y4 = line2[1]
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return None  # Lines are parallel
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (x, y)
        return None

    def find_intersections(self):
        edges1 = [
            (self.quad1['UL'], self.quad1['UR']),
            (self.quad1['UR'], self.quad1['LR']),
            (self.quad1['LR'], self.quad1['LL']),
            (self.quad1['LL'], self.quad1['UL'])
        ]
        edges2 = [
            (self.quad2['UL'], self.quad2['UR']),
            (self.quad2['UR'], self.quad2['LR']),
            (self.quad2['LR'], self.quad2['LL']),
            (self.quad2['LL'], self.quad2['UL'])
        ]

        intersections = []
        for edge1 in edges1:
            for edge2 in edges2:
                point = self.line_intersection(edge1, edge2)
                if point:
                    intersections.append(point)
        return intersections

    def is_valid_placement(self):
        intersections = self.find_intersections()
        if not intersections:
            return True, "The placement is valid. The quadrilaterals do not intersect."
        else:
            return False, f"The placement is not valid. The quadrilaterals intersect at {len(intersections)} point(s): {intersections}"

    def plot_and_save(self, filename='quadrilateral_intersection.png'):
        fig, ax = plt.subplots(figsize=(10, 10))

        # Plot quad1
        quad1_x = [self.quad1['UL'][0], self.quad1['UR'][0], self.quad1['LR'][0], self.quad1['LL'][0], self.quad1['UL'][0]]
        quad1_y = [self.quad1['UL'][1], self.quad1['UR'][1], self.quad1['LR'][1], self.quad1['LL'][1], self.quad1['UL'][1]]
        ax.plot(quad1_x, quad1_y, 'b-', label='Quadrilateral 1')

        # Plot quad2
        quad2_x = [self.quad2['UL'][0], self.quad2['UR'][0], self.quad2['LR'][0], self.quad2['LL'][0], self.quad2['UL'][0]]
        quad2_y = [self.quad2['UL'][1], self.quad2['UR'][1], self.quad2['LR'][1], self.quad2['LL'][1], self.quad2['UL'][1]]
        ax.plot(quad2_x, quad2_y, 'r-', label='Quadrilateral 2')

        # Find and plot intersection points
        intersections = self.find_intersections()
        if intersections:
            x_points, y_points = zip(*intersections)
            ax.scatter(x_points, y_points, color='green', s=50, label='Intersection Points')
            for i, (x, y) in enumerate(intersections):
                ax.annotate(f'P{i+1}', (x, y), xytext=(5, 5), textcoords='offset points')

        # Set labels and title
        ax.set_xlabel('X-axis')
        ax.set_ylabel('Y-axis')
        ax.set_title('Quadrilateral Intersection Visualization')

        # Add legend
        ax.legend()

        # Show grid
        ax.grid(True)

        # Add text about intersection
        plt.figtext(0.5, 0.01, f"Number of intersection points: {len(intersections)}", ha="center", fontsize=12, bbox={"facecolor":"orange", "alpha":0.5, "pad":5})

        # Save the plot as an image file
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close(fig)  # Close the figure to free up memory

        print(f"Plot saved as {filename}")
        return intersections

# Example usage
quad1 = {
    'UL': (0, 6),
    'UR': (4, 8),
    'LR': (3, 4),
    'LL': (1, 2)
}

quad2 = {
    'UL': (5, 5),
    'UR': (9, 7),
    'LR': (8, 3),
    'LL': (6, 1)
}

#is_valid, message = IntersectionValidator(quad1, quad2).is_valid_placement()

    # Check if the placement is valid
"""     is_valid, message = visualizer
    print(message)
    
    # Plot and save the visualization
    intersection_points = visualizer.plot_and_save()
    print("Intersection points:", intersection_points) """