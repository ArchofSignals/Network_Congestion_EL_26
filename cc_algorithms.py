class TCPReno:
    def __init__(self, init_cwnd=1.0, init_ssthresh=64.0):
        self.cwnd = max(1.0, init_cwnd)
        self.ssthresh = init_ssthresh
        self.state = "Slow Start"

    def on_ack(self):
        """Adjusts window size upward when a packet successfully hits the destination"""
        if self.cwnd < self.ssthresh:
            # Slow Start: Exponential Growth
            self.cwnd += 1.0
            self.state = "Slow Start"
        else:
            # Congestion Avoidance: Linear Growth (AIMD Increase)
            self.cwnd += 1.0 / max(1, int(self.cwnd))
            self.state = "Congestion Avoidance"

    def on_loss(self):
        """Apply TCP Reno timeout behavior after loss detection."""
        self.ssthresh = max(2.0, self.cwnd / 2.0)
        self.cwnd = 1.0
        self.state = "Slow Start"


class UDPGenerator:
    def __init__(self, packets_per_tick=1):
        self.packets_per_tick = max(1, int(packets_per_tick))
        self.state = "UDP Streaming"

    def window_limit(self):
        return self.packets_per_tick
