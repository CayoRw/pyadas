import math

# MediaPipe inner lip indices
# Horizontal corners: 78 (left), 308 (right)
# Vertical center: 13 (top), 14 (bottom)

def _euclidean_distance(p1, p2):
    """Calculates the 2D Euclidean distance between two points."""
    return math.dist(p1, p2)

def get_mar_metric(face_landmarks, frame_width, frame_height):
    """
    Computes the Mouth Aspect Ratio (MAR) using the inner lips.
    Formula: MAR = ||p13 - p14|| / ||p78 - p308||
    """
    def _extract_pixel_coord(index):
        return (face_landmarks.landmark[index].x * frame_width, 
                face_landmarks.landmark[index].y * frame_height)

    # Extract coordinates
    p_left = _extract_pixel_coord(78)
    p_right = _extract_pixel_coord(308)
    p_top = _extract_pixel_coord(13)
    p_bottom = _extract_pixel_coord(14)

    # Calculate distances
    horizontal_dist = _euclidean_distance(p_left, p_right)
    vertical_dist = _euclidean_distance(p_top, p_bottom)
    
    # Avoid division by zero
    if horizontal_dist == 0:
        return 0.0
        
    mar = vertical_dist / horizontal_dist
    return mar