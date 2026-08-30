import csv
import time
import os
from datetime import datetime

class TelemetryLogger:
    def __init__(self, log_dir="data"):
        # Garante que a pasta de destino exista
        os.makedirs(log_dir, exist_ok=True)
        
        # Cria um arquivo com timestamp para não sobrescrever sessões antigas
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = os.path.join(log_dir, f"session_{timestamp_str}.csv")
        
        self.headers = [
            "timestamp", "fps", "ear_left", "ear_right", "ear_average",
            "mar", "perclos", "yaw", "pitch", "roll", "gaze_direction", "driver_state"
        ]
        
        # Inicializa o arquivo e escreve o cabeçalho
        with open(self.filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.headers)

    def log(self, fps, ear_l, ear_r, ear_avg, mar, perclos, yaw, pitch, roll, gaze, state):
        """Grava uma nova linha de telemetria no arquivo."""
        current_timestamp = time.time()
        row = [
            f"{current_timestamp:.3f}",
            int(fps),
            f"{ear_l:.3f}",
            f"{ear_r:.3f}",
            f"{ear_avg:.3f}",
            f"{mar:.3f}",
            f"{perclos:.3f}",
            f"{yaw:.1f}",
            f"{pitch:.1f}",
            f"{roll:.1f}",
            gaze,
            state
        ]
        
        # Abre em modo append para adicionar a linha sem apagar o histórico
        with open(self.filepath, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)