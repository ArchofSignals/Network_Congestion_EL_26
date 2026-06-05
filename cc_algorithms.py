class TCPReno:
    def __init__(self, init_cwnd=1.0, init_ssthresh=64.0):
        self.cwnd = init_cwnd
        self.ssthresh = init_ssthresh
        self.state = "Slow Start" # Can be "Slow Start" or "Congestion Avoidance"

    def on_ack(self):
        """Adjusts window size upward when a packet successfully hits the destination"""
        if self.cwnd < self.ssthresh:
            # Slow Start: Exponential Growth
            self.cwnd += 1.0
            self.state = "Slow Start"
        else:
            # Congestion Avoidance: Linear Growth (AIMD Increase)
            self.cwnd += 1.0 / int(self.cwnd)
            self.state = "Congestion Avoidance"

    def on_loss(self):
        """Adjusts window size downward when a drop is detected (Multiplicative Decrease)"""
        self.ssthresh = max(2.0, self.cwnd / 2.0)
        self.cwnd = 1.0  # Reset to 1 (or ssthresh for fast recovery, 1 simulates Tahoe reset)
        self.state = "Slow Start"