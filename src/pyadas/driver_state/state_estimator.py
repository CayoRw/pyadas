class DriverStateEstimator:
    def __init__(self):
        # Thresholds baseados nas métricas calculadas e calibração dinâmica
        self.perclos_drowsy_threshold = 0.20       
        self.perclos_microsleep_threshold = 0.60   
        self.mar_yawning_threshold = 0.40          
        self.yaw_distracted_threshold = 30.0       
        
        # --- Alteração: Filtro Temporal (Debounce) ---
        self.distracted_frames = 0
        self.alert_frames = 0
        self.FRAMES_TO_CHANGE = 10  # Exige ~10 frames consistentes para trocar o estado
        self.is_distracted = False

    def estimate_state(self, is_calibrated, perclos, mar, yaw):
        """
        Determina o estado atual do motorista com base nas métricas consolidadas.
        Prioriza estados críticos (Microsleep > Drowsy > Yawning > Distracted).
        """
        if not is_calibrated:
            return "UNKNOWN"

        state = "ALERT"

        # 1. Distração com Filtro Temporal
        if abs(yaw) > self.yaw_distracted_threshold:
            self.distracted_frames += 1
            self.alert_frames = 0  # Zera o contador oposto
        else:
            self.alert_frames += 1
            self.distracted_frames = 0 # Zera o contador oposto

        # Só altera a "memória" do estado se a condição se sustentar
        if self.distracted_frames >= self.FRAMES_TO_CHANGE:
            self.is_distracted = True
        elif self.alert_frames >= self.FRAMES_TO_CHANGE:
            self.is_distracted = False

        if self.is_distracted:
             state = "DISTRACTED"
             return state # Retorna cedo pois a rotação extrema distorce o cálculo dos olhos/boca

        # 2. Bocejo
        if mar > self.mar_yawning_threshold:
            state = "YAWNING"

        # 3. Sonolência / Fadiga (Sobrescreve bocejo se estiverem ocorrendo juntos)
        if perclos >= self.perclos_microsleep_threshold:
            state = "POTENTIAL_MICROSLEEP"
        elif perclos >= self.perclos_drowsy_threshold:
            state = "DROWSY"

        return state