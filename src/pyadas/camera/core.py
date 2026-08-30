import cv2
import time
import mediapipe as mp
from pyadas.perception.ear import get_ear_metrics
from pyadas.perception.mar import get_mar_metric
from pyadas.perception.head_pose import get_head_pose
from pyadas.drowsiness.temporal import TemporalAnalyzer
from pyadas.driver_state.state_estimator import DriverStateEstimator
# NEW: Importar o Logger
from pyadas.telemetry.logger import TelemetryLogger

def test_camera_feed():
    cap = cv2.VideoCapture(0)
    p_time = 0

    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    analyzer = TemporalAnalyzer(calibration_frames=100, perclos_window_frames=150)
    state_estimator = DriverStateEstimator()
    # NEW: Instanciar o gravador de telemetria
    logger = TelemetryLogger(log_dir="data")
    
    print("Iniciando captura. Pressione 'q' para encerrar.")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Failed to capture video. Check the camera connection.")
            break
            
        frame = cv2.resize(frame, (1280, 720))
        h_frame, w_frame, _ = frame.shape
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)
        
        c_time = time.time()
        fps = 1 / (c_time - p_time) if (c_time - p_time) > 0 else 0
        p_time = c_time
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                
                ear_left, ear_right, ear_avg = get_ear_metrics(face_landmarks, w_frame, h_frame)
                mar = get_mar_metric(face_landmarks, w_frame, h_frame)
                yaw, pitch, roll = get_head_pose(face_landmarks, w_frame, h_frame)
                
                analyzer.update(ear_avg, mar)
                perclos = analyzer.get_perclos()
                is_calibrated = analyzer.is_calibrated
                calib_status = analyzer.get_calibration_status()
                
                current_state = state_estimator.estimate_state(is_calibrated, perclos, mar, yaw)
                
                # NEW: Gravar os dados da iteração atual no arquivo CSV
                logger.log(fps, ear_left, ear_right, ear_avg, mar, perclos, yaw, pitch, roll, "UNKNOWN", current_state)
                
                # Display Metrics
                cv2.putText(frame, f'EAR Avg: {ear_avg:.2f}', (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame, f'MAR: {mar:.2f}', (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                cv2.putText(frame, f'Yaw: {yaw:.1f}', (1000, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                if is_calibrated:
                    cv2.putText(frame, f'STATE: {current_state}', (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                    cv2.putText(frame, f'PERCLOS: {perclos*100:.1f}%', (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, f'Calibrating... {int(calib_status*100)}%', (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    cv2.putText(frame, f'STATE: {current_state}', (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 128, 128), 2)
        
        cv2.putText(frame, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("pyadas - Hardware Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_camera_feed()