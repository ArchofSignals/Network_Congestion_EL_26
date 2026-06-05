import pandas as pd

class MetricsManager:
    def __init__(self):
        self.history = []

    def log_tick(self, tick, cwnd, ssthresh, queue_length, drops, throughput, state):
        self.history.append({
            "Tick": tick,
            "CWND (Window Size)": cwnd,
            "SSThresh": ssthresh,
            "Router Queue Fill": queue_length,
            "Packet Drops": drops,
            "Throughput (Pkts/Tick)": throughput,
            "CC State": state
        })

    def get_dataframe(self):
        return pd.DataFrame(self.history)
        
    def clear(self):
        self.history = []