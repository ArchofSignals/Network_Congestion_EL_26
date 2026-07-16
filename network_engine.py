import random

class Packet:
    def __init__(self, sequence_number, data, sent_time):
        self.sequence_number = sequence_number
        self.data = data
        self.sent_time = sent_time


class Router:
    def __init__(self, buffer_size):
        self.buffer_size = buffer_size
        self.queue = []

    def arrive(self, packet):
        if len(self.queue) < self.buffer_size:
            self.queue.append(packet)
            return True # Successfully queued
        return False # Packet dropped (Buffer Overflow)

    def process_queue(self, service_rate):
        """Removes packets from queue based on router processing speed"""
        processed = []
        for _ in range(min(service_rate, len(self.queue))):
            processed.append(self.queue.pop(0))
        return processed

class NetworkLink:
    def __init__(self, loss_rate=0.01):
        self.loss_rate = loss_rate

    def transmits_successfully(self):
        # Simulates random background wireless/hardware packet drop
        return random.random() > self.loss_rate


def transmit_tick(router, link, outgoing_packets, service_rate):
    """Move one simulation tick through router enqueue, service, and lossy link."""
    enqueue_drops = []
    for packet in outgoing_packets:
        if not router.arrive(packet):
            enqueue_drops.append(packet)

    delivered = []
    link_drops = []
    for packet in router.process_queue(service_rate):
        if link.transmits_successfully():
            delivered.append(packet)
        else:
            link_drops.append(packet)

    return delivered, enqueue_drops + link_drops
