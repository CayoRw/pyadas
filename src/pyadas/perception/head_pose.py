import cv2
import numpy as np

# Generic 3D face model coordinates
# Points: Nose tip, Chin, Right Eye Outer, Left Eye Outer, Right Mouth, Left Mouth
FACE_3D_MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),             # Nose tip
    (0.0, -330.0, -65.0),        # Chin
    (225.0, 170.0, -135.0),      # Right eye outer corner
    (-225.0, 170.0, -135.0),     # Left eye outer corner
    (150.0, -150.0, -125.0),     # Right mouth corner
    (-150.0, -150.0, -125.0)     # Left mouth corner
], dtype=np.float64)

# Corresponding MediaPipe landmark indices
FACE_2D_INDICES = [1, 152, 33, 263, 61, 291]

def get_head_pose(face_landmarks, frame_width, frame_height):
    """
    Estimates the head pose (Yaw, Pitch, Roll) using cv2.solvePnP.
    Returns the angles in degrees.
    """
    image_points = []
    for idx in FACE_2D_INDICES:
        x = face_landmarks.landmark[idx].x * frame_width
        y = face_landmarks.landmark[idx].y * frame_height
        image_points.append((x, y))
        
    image_points = np.array(image_points, dtype=np.float64)
    
    # Fake camera internals (assuming no lens distortion for the prototype)
    focal_length = frame_width
    center = (frame_width / 2, frame_height / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
         [0, focal_length, center[1]],
         [0, 0, 1]], dtype=np.float64
    )
    dist_coeffs = np.zeros((4, 1))
    
    success, rotation_vector, translation_vector = cv2.solvePnP(
        FACE_3D_MODEL_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )
    
    if not success:
        return 0.0, 0.0, 0.0
        
    # Convert rotation vector to rotation matrix
    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    
    # Decompose the projection matrix to extract Euler angles
    proj_matrix = np.hstack((rotation_matrix, translation_vector))
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)
    
    pitch = euler_angles[0][0]
    yaw = euler_angles[1][0]
    roll = euler_angles[2][0]
    
    # Normalização de Gimbal Lock para o sistema de coordenadas do OpenCV
    if pitch > 0:
        pitch = 180 - pitch
    else:
        pitch = pitch + 180
        
    # Correção de espelhamento: se a matriz inverteu, corrigimos Yaw e Roll
    if euler_angles[0][0] > 0:
        yaw = -yaw
        roll = -roll

    return yaw, pitch, roll