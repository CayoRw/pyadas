class DriverStateEstimator:
    def __init__(self):
        # Thresholds baseados nas métricas calculadas e calibração dinâmica
        self.perclos_drowsy_threshold = 0.20       # > 20% do tempo de olhos fechados = sonolência
        self.perclos_microsleep_threshold = 0.60   # > 60% = potencial microssono
        self.mar_yawning_threshold = 0.40          # MAR alto
        self.yaw_distracted_threshold = 30.0       # Cabeça virada mais que 30 graus

    def estimate_state(self, is_calibrated, perclos, mar, yaw):
        """
        Determina o estado atual do motorista com base nas métricas consolidadas.
        Prioriza estados críticos (Microsleep > Drowsy > Yawning > Distracted).
        """
        if not is_calibrated:
            return "UNKNOWN"

        state = "ALERT"

        # 1. Distração (Prioridade baixa, a cabeça virada pode afetar MAR/EAR)
        if abs(yaw) > self.yaw_distracted_threshold:
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