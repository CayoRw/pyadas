import cv2
import time
import mediapipe as mp
import numpy as np

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QImage, QPixmap, QFont
# NEW: Importação do QComboBox para o seletor de câmera
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QGridLayout, QComboBox)

from pyadas.perception.ear import get_ear_metrics
from pyadas.perception.mar import get_mar_metric
from pyadas.perception.head_pose import get_head_pose
from pyadas.drowsiness.temporal import TemporalAnalyzer
from pyadas.driver_state.state_estimator import DriverStateEstimator
from pyadas.telemetry.logger import TelemetryLogger

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QGridLayout, QComboBox, 
                               QCheckBox, QFileDialog)
import os

class VideoAcquisitionThread(QThread):
    frame_ready = Signal(QImage)
    telemetry_ready = Signal(dict)

    # NEW: O inicializador agora aceita o índice da câmera
    def __init__(self, camera_index=0):
        super().__init__()
        self.running = False
        self.camera_index = camera_index
        
        self.analyzer = TemporalAnalyzer(calibration_frames=100, perclos_window_frames=150)
        self.state_estimator = DriverStateEstimator()
        self.logger = TelemetryLogger(log_dir="data")
        
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True,
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def run(self):
        self.running = True
        # NEW: Inicia a câmera com o índice escolhido na interface
        cap = cv2.VideoCapture(self.camera_index)
        p_time = 0

        while self.running and cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            frame = cv2.resize(frame, (1280, 720))
            h_frame, w_frame, _ = frame.shape
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.mp_face_mesh.process(frame_rgb)
            
            c_time = time.time()
            fps = 1 / (c_time - p_time) if (c_time - p_time) > 0 else 0
            p_time = c_time
            
            telemetry = {
                "fps": int(fps), "ear": 0.0, "mar": 0.0, "perclos": 0.0,
                "yaw": 0.0, "pitch": 0.0, "roll": 0.0,
                "state": "NO_FACE", "calib_status": 0.0, "is_calibrated": False
            }

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image=frame_rgb,
                        landmark_list=face_landmarks,
                        connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                    )
                    
                    ear_left, ear_right, ear_avg = get_ear_metrics(face_landmarks, w_frame, h_frame)
                    mar = get_mar_metric(face_landmarks, w_frame, h_frame)
                    yaw, pitch, roll = get_head_pose(face_landmarks, w_frame, h_frame)
                    
                    self.analyzer.update(ear_avg, mar)
                    perclos = self.analyzer.get_perclos()
                    is_calibrated = self.analyzer.is_calibrated
                    calib_status = self.analyzer.get_calibration_status()
                    
                    current_state = self.state_estimator.estimate_state(is_calibrated, perclos, mar, yaw)
                    
                    # Adiciona a verificação do logger
                    if self.logger is not None:
                        self.logger.log(fps, ear_left, ear_right, ear_avg, mar, perclos, yaw, pitch, roll, "UNKNOWN", current_state)
                                            
                    telemetry.update({
                        "ear": ear_avg, "mar": mar, "perclos": perclos,
                        "yaw": yaw, "pitch": pitch, "roll": roll,
                        "state": current_state, "calib_status": calib_status,
                        "is_calibrated": is_calibrated
                    })
            
            self.telemetry_ready.emit(telemetry)

            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_ready.emit(q_img)

        cap.release()

    def stop(self):
        self.running = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyadas - Driver Monitoring System")
        self.resize(1200, 700)
        
        self.log_directory = "data" # Diretório padrão
        self.setup_ui()
        self.video_thread = None

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # --- Lado Esquerdo: Câmera e Controles ---
        cam_layout = QVBoxLayout()
        self.lbl_video = QLabel("Câmera Desligada")
        self.lbl_video.setAlignment(Qt.AlignCenter)
        self.lbl_video.setStyleSheet("background-color: black; color: white; font-size: 20px;")
        self.lbl_video.setMinimumSize(800, 600)
        
        control_layout = QHBoxLayout()
        
        self.combo_camera = QComboBox()
        self.combo_camera.addItems(["Câmera 0", "Câmera 1", "Câmera 2", "Câmera 3"])
        self.combo_camera.setMinimumHeight(45)
        self.combo_camera.setStyleSheet("font-size: 14px;")
        
        self.btn_start = QPushButton("Start Monitoring")
        self.btn_start.setMinimumHeight(45)
        self.btn_start.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.btn_start.clicked.connect(self.toggle_monitoring)
        
        control_layout.addWidget(self.combo_camera, stretch=1)
        control_layout.addWidget(self.btn_start, stretch=4)
        
        # NEW: Controles de Salvamento do CSV
        csv_control_layout = QHBoxLayout()
        
        self.check_save_csv = QCheckBox("Gravar sessão em CSV")
        self.check_save_csv.setChecked(True)
        self.check_save_csv.setStyleSheet("font-size: 12px; font-weight: bold;")
        
        self.btn_choose_dir = QPushButton("Escolher Pasta")
        self.btn_choose_dir.clicked.connect(self.choose_directory)
        
        self.lbl_dir_path = QLabel(f"Pasta Atual: {os.path.abspath(self.log_directory)}")
        self.lbl_dir_path.setStyleSheet("font-size: 10px; color: gray;")
        
        csv_control_layout.addWidget(self.check_save_csv)
        csv_control_layout.addWidget(self.btn_choose_dir)
        csv_control_layout.addWidget(self.lbl_dir_path, stretch=1)
        
        cam_layout.addWidget(self.lbl_video, stretch=1)
        cam_layout.addLayout(csv_control_layout)
        cam_layout.addLayout(control_layout)
        
        # --- Lado Direito: Painel de Telemetria (RÍGIDO) ---
        right_panel = QWidget()
        right_panel.setFixedWidth(350)
        panel_layout = QVBoxLayout(right_panel)
        panel_layout.setSpacing(20)
        panel_layout.setContentsMargins(10, 0, 0, 0)
        
        self.lbl_state = self._create_panel_label("STATE: IDLE", 24, bold=True)
        self.lbl_state.setStyleSheet("color: gray;")
        self.lbl_state.setWordWrap(True)
        self.lbl_state.setMinimumHeight(70)
        
        self.lbl_calib = self._create_panel_label("Status: Waiting", 14)
        
        metrics_frame = QFrame()
        metrics_frame.setFrameShape(QFrame.StyledPanel)
        metrics_layout = QGridLayout(metrics_frame)
        
        self.lbl_ear = self._create_panel_label("EAR: 0.00")
        self.lbl_mar = self._create_panel_label("MAR: 0.00")
        self.lbl_perclos = self._create_panel_label("PERCLOS: 0.0%")
        self.lbl_yaw = self._create_panel_label("Yaw: 0.0°")
        self.lbl_fps = self._create_panel_label("FPS: 0")
        
        metrics_layout.addWidget(self.lbl_ear, 0, 0)
        metrics_layout.addWidget(self.lbl_mar, 1, 0)
        metrics_layout.addWidget(self.lbl_perclos, 2, 0)
        metrics_layout.addWidget(self.lbl_yaw, 3, 0)
        metrics_layout.addWidget(self.lbl_fps, 4, 0)
        
        panel_layout.addWidget(self.lbl_state)
        panel_layout.addWidget(self.lbl_calib)
        panel_layout.addWidget(metrics_frame)
        panel_layout.addStretch()
        
        main_layout.addLayout(cam_layout, stretch=1)
        main_layout.addWidget(right_panel)

    def _create_panel_label(self, text, size=16, bold=False):
        lbl = QLabel(text)
        font = QFont("Arial", size)
        font.setBold(bold)
        lbl.setFont(font)
        return lbl

    def choose_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta para Salvar CSV")
        if dir_path:
            self.log_directory = dir_path
            self.lbl_dir_path.setText(f"Pasta Atual: {os.path.abspath(self.log_directory)}")

    def toggle_monitoring(self):
        if self.video_thread is None or not self.video_thread.isRunning():
            cam_idx = self.combo_camera.currentIndex()
            
            self.video_thread = VideoAcquisitionThread(camera_index=cam_idx)
            
            # Repassa a escolha do usuário para a thread de vídeo
            if not self.check_save_csv.isChecked():
                self.video_thread.logger = None # Desliga o logger se a checkbox estiver desmarcada
            else:
                 self.video_thread.logger = TelemetryLogger(log_dir=self.log_directory)
            
            self.video_thread.frame_ready.connect(self.update_image)
            self.video_thread.telemetry_ready.connect(self.update_telemetry)
            self.video_thread.start()
            
            self.combo_camera.setEnabled(False)
            self.check_save_csv.setEnabled(False)
            self.btn_choose_dir.setEnabled(False)
            self.btn_start.setText("Stop Monitoring")
            self.btn_start.setStyleSheet("background-color: #ff4c4c; font-weight: bold; font-size: 14px;")
        else:
            self.video_thread.stop()
            self.combo_camera.setEnabled(True)
            self.check_save_csv.setEnabled(True)
            self.btn_choose_dir.setEnabled(True)
            self.btn_start.setText("Start Monitoring")
            self.btn_start.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.lbl_video.clear()
            self.lbl_video.setText("Câmera Desligada")
            self.lbl_state.setText("STATE: IDLE")
            self.lbl_state.setStyleSheet("color: gray;")

    def update_image(self, q_img):
        pixmap = QPixmap.fromImage(q_img).scaled(
            self.lbl_video.width(), self.lbl_video.height(), Qt.KeepAspectRatio
        )
        self.lbl_video.setPixmap(pixmap)

    def update_telemetry(self, data):
        self.lbl_ear.setText(f"EAR: {data['ear']:.2f}")
        self.lbl_mar.setText(f"MAR: {data['mar']:.2f}")
        self.lbl_perclos.setText(f"PERCLOS: {data['perclos']*100:.1f}%")
        self.lbl_yaw.setText(f"Yaw: {data['yaw']:.1f}°")
        self.lbl_fps.setText(f"FPS: {data['fps']}")
        
        if data['is_calibrated']:
            self.lbl_calib.setText("Status: CALIBRATED")
            self.lbl_calib.setStyleSheet("color: green; font-weight: bold;")
        else:
            pct = int(data['calib_status'] * 100)
            self.lbl_calib.setText(f"Calibrating... {pct}%")
            self.lbl_calib.setStyleSheet("color: orange; font-weight: bold;")
            
        state = data['state']
        self.lbl_state.setText(f"STATE:\n{state}")
        
        if state == "ALERT":
            self.lbl_state.setStyleSheet("color: green;")
        elif state in ["DROWSY", "YAWNING", "DISTRACTED"]:
            self.lbl_state.setStyleSheet("color: orange;")
        elif state == "POTENTIAL_MICROSLEEP":
            self.lbl_state.setStyleSheet("color: red;")
        else:
            self.lbl_state.setStyleSheet("color: gray;")
            
    def closeEvent(self, event):
        if self.video_thread is not None and self.video_thread.isRunning():
            self.video_thread.stop()
        event.accept()