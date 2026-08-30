import collections
import numpy as np

class TemporalAnalyzer:
    def __init__(self, calibration_frames=100, perclos_window_frames=150):
        """
        calibration_frames: Quantidade de frames para calcular o baseline inicial.
        perclos_window_frames: Tamanho da janela deslizante para cálculo do PERCLOS.
        """
        self.calibration_frames = calibration_frames
        self.perclos_window_frames = perclos_window_frames
        
        # Buffers circulares de histórico
        self.ear_history = collections.deque(maxlen=perclos_window_frames)
        self.mar_history = collections.deque(maxlen=perclos_window_frames)
        
        # Variáveis de Baseline (Calibração Dinâmica)
        self.baseline_ear = 0.0
        self.baseline_mar = 0.0
        
        # Controle de Estado
        self.frames_processed = 0
        self.is_calibrated = False

    def update(self, ear, mar):
        """Alimenta o buffer com as métricas do frame atual e verifica calibração."""
        self.ear_history.append(ear)
        self.mar_history.append(mar)
        
        if not self.is_calibrated:
            self.frames_processed += 1
            if self.frames_processed >= self.calibration_frames:
                # Calcula a média do período de aquecimento
                self.baseline_ear = float(np.mean(self.ear_history))
                self.baseline_mar = float(np.mean(self.mar_history))
                self.is_calibrated = True

    def get_perclos(self, closure_threshold_ratio=0.6):
        """
        Calcula o PERCLOS (Percentage of Eye Closure).
        O olho é considerado fechado se o EAR for menor que 60% do Baseline.
        """
        if not self.is_calibrated or len(self.ear_history) == 0:
            return 0.0
            
        # O limiar não é fixo, é relativo ao rosto do motorista atual
        threshold = self.baseline_ear * closure_threshold_ratio
        
        closed_frames = sum(1 for val in self.ear_history if val < threshold)
        perclos = closed_frames / len(self.ear_history)
        
        return perclos

    def get_calibration_status(self):
        """Retorna o progresso da calibração (0.0 a 1.0)."""
        if self.is_calibrated:
            return 1.0
        return self.frames_processed / self.calibration_frames