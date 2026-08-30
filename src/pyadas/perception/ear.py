import math

# MediaPipe Face Mesh indices for the eyes
# Order: [Corner Inner/Outer, Top 1, Top 2, Corner Outer/Inner, Bottom 2, Bottom 1]
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

def _euclidean_distance(p1, p2):
    """Calculates the 2D Euclidean distance between two points."""
    return math.dist(p1, p2)

def _calculate_single_eye_ear(eye_points):
    """
    Computes the Eye Aspect Ratio for a single eye.
    Formula: EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    """
    # Vertical distances
    v1 = _euclidean_distance(eye_points[1], eye_points[5])
    v2 = _euclidean_distance(eye_points[2], eye_points[4])
    
    # Horizontal distance
    h = _euclidean_distance(eye_points[0], eye_points[3])
    
    # Avoid division by zero in case of extreme tracking anomalies
    if h == 0:
        return 0.0
        
    ear = (v1 + v2) / (2.0 * h)
    return ear

def get_ear_metrics(face_landmarks, frame_width, frame_height):
    """
    Extracts the left, right, and average EAR from the detected face landmarks.
    """
    def _extract_pixel_coords(indices):
        # Converts normalized coordinates (0.0 to 1.0) into absolute pixel values
        return [(face_landmarks.landmark[i].x * frame_width, 
                 face_landmarks.landmark[i].y * frame_height) for i in indices]

    right_eye_coords = _extract_pixel_coords(RIGHT_EYE_INDICES)
    left_eye_coords = _extract_pixel_coords(LEFT_EYE_INDICES)

    ear_right = _calculate_single_eye_ear(right_eye_coords)
    ear_left = _calculate_single_eye_ear(left_eye_coords)
    
    ear_avg = (ear_right + ear_left) / 2.0

    return ear_left, ear_right, ear_avg