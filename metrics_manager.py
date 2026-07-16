import pandas as pd

class MetricsManager:
    COLUMNS = [
        "Tick",
        "CWND (Window Size)",
        "SSThresh",
        "Router Queue Fill",
        "Packet Drops",
        "Throughput (Pkts/Tick)",
        "CC State"
    ]

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
        return pd.DataFrame(self.history, columns=self.COLUMNS)

    def clear(self):
        self.history = []
