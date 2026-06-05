# 🌐 Adaptive Multi-Node Network Congestion Control Simulator

A modular, high-fidelity, discrete-event network simulator built in Python to evaluate and visualize transport-layer congestion control protocols over lossy wireless links.

This project simulates a bottleneck network topology with interactive multi-node capabilities, enabling three physical machines (or local browser instances) to collaborate as a **Sender Node**, an **Admin Router Node**, and a **Receiver Node** with an independent data integrity validator.

## 🏛️ System Architecture

The project is strictly split into 4 decoupled, interconnected modules to maintain a clean Object-Oriented design and adhere to professional software engineering standards:

```
├── network_engine.py   # Infrastructure: Hosts, packets, links, and finite queue router
├── cc_algorithms.py    # Protocol Logic: Classic AIMD / TCP Reno Congestion Control Math
├── metrics_manager.py  # Telemetry: In-memory logs and Pandas-driven analytical dataframes
└── main.py             # UI Orchestration: Streamlit Multi-Node Web Dashboard
```

```
                 +-------------------+
                 |      main.py      |  (Multi-Node Web UI & Orchestrator)
                 +---------+---------+
                           |
         +-----------------+-----------------+
         |                                   |
+--------v----------+             +----------v----------+
| network_engine.py |             |   cc_algorithms.py  |
| (Queue/Link Drop) |             |  (TCP Reno / AIMD)  |
+--------+----------+             +----------+----------+
         |                                   |
         +-----------------+-----------------+
                           |
                 +---------v---------+
                 |metrics_manager.py |  (Time-Series Telemetry Recorder)
                 +-------------------+
```

### Module Descriptions

1. **`network_engine.py` (The Infrastructure)**
    
    - Manages simulated physical hardware components.
        
    - Models the `Packet` payload class carrying generic binary data blocks.
        
    - Implements a finite-capacity `Router` buffer queue to simulate **Tail-Drop congestion/overflow**.
        
    - Implements a `NetworkLink` leveraging probabilistic model calculations (`random` seed) to simulate ambient, wireless packet interference drops.
        
2. **`cc_algorithms.py` (The Congestion Logic)**
    
    - Houses the algebraic calculations behind **TCP Reno-style AIMD** (Additive Increase / Multiplicative Decrease).
        
    - Dictates the dynamic growth of the Congestion Window ($CWND$):
        
        - **Slow Start Phase (**$CWND < SSThresh$**):** Exponential growth (doubling transport capacity per cycle).
            
        - **Congestion Avoidance Phase (**$CWND \ge SSThresh$**):** Linear, highly cautious growth ($CWND += 1 / CWND$).
            
        - **Fast Recovery Phase:** Multiplicative reduction cutting the threshold ($SSThresh = CWND / 2$) and resetting the window size back to baseline on congestion loss.
            
3. **`metrics_manager.py` (The Data Aggregator)**
    
    - Performs tick-by-tick state tracking during the simulation loop.
        
    - Compiles instantaneous measurements of Congestion Window, SSThresh, queue saturation levels, successful throughput rate, and active dropping occurrences.
        
    - Compiles this state into standard Pandas DataFrames, ready for streaming chart visualizations.
        
4. **`main.py` (The Conductor & UI)**
    
    - Implements a secure cross-PC shared memory database via Streamlit caching to allow separate computers on the same network to interact in real-time.
        
    - Dynamically renders user interfaces based on role query parameters (`role=admin`, `role=sender`, `role=receiver`).
        

## ⚙️ Supported Protocols

This simulator models the foundational trade-offs of the modern internet by supporting two starkly contrasting transport models:

|   |   |   |   |
|---|---|---|---|
|**Protocol Mode**|**Reliability Mechanism**|**Congestion Control**|**Impact Under Heavy Network Congestion**|
|**TCP Reno**|**Reliable (Retransmissions):** Detects dropped packets, rolls back pointers, and resends until delivered safely.|**AIMD (Active):** Constantly shrinks/expands window size to avoid router collapse.|**Perfect File Recovery.** Takes longer to finish, but reassembles the destination file with 100.0% zero-loss accuracy.|
|**UDP**|**Unreliable:** Blasts data continuously at the physical rate of the WLAN bandwidth without acknowledging safety.|**None (Passive):** Completely ignores packet drops.|**Fast but Glitched.** Transmission finishes immediately, but dropped packets result in corrupted data arrays, visual gray streaks, and digital glitches.|

## 🎮 Multi-Node Demonstration Guide

This simulator is optimized to run over a **Local Area Network (LAN)** across up to **three separate computers** (or browser tabs) simultaneously.

### Step 1: Launch the Application

Start the Streamlit server on your host system:

```
streamlit run main.py
```

Observe the terminal output and note down your local network address:

- **Local Server URL:** `http://localhost:8501`
    
- **Local WLAN URL:** `http://192.168.x.x:8501`
    

### Step 2: Open the 3 Node Viewports

Provide these exact addresses to your testing systems:

1. **PC 1 (Admin/Router Dashboard):** `http://192.168.x.x:8501/?role=admin`
    
    - _This acts as the network monitor. You control the buffer size sliders, network loss sliders, choose the protocol (TCP vs UDP), and watch the charts stream in real-time._
        
2. **PC 2 (Sender Client):** `http://192.168.x.x:8501/?role=sender`
    
    - _Uploads files (text documents, images, PDFs) to stage inside the network buffer._
        
3. **PC 3 (Receiver Client):** `http://192.168.x.x:8501/?role=receiver`
    
    - _Reassembles the incoming byte streams and allows independent byte-for-byte verification using locally stored original source files._
        

## ⚡ Live Presentation Script for Professors

To ensure you get maximum credit during your presentation, demonstrate these two contrasting experiments side-by-side:

### Demo A: The Perfect TCP Recovery (Reliability Experiment)

1. Set the Admin Protocol to **TCP (Reliable / Retransmissions)**.
    
2. Turn up the **WLAN Wireless Loss** slider to a harsh **7.0%**.
    
3. Upload an image on the **Sender** screen and click transmit.
    
4. Click **Run Discrete-Event Simulation** on the **Admin** dashboard.
    
5. **Show the Professor:** The live-streaming line graph drawing the classic **TCP Reno Sawtooth**. Point out how the window shrinks when packets drop but linearly climbs back up.
    
6. Check the **Receiver** screen. Show that despite the severe 7% loss, the image rendered **perfectly without a single corrupted pixel**.
    
7. Run the **Independent Integrity Checker** by uploading the original image file. It will output `🟢 100% Bit-Perfect Match`.
    

### Demo B: The Glitched UDP Output (The Speed Trade-Off)

1. Change the Admin Protocol to **UDP**. Keep WLAN loss at **7.0%**.
    
2. Run the simulation again. Note how it finishes instantly because UDP does not retry.
    
3. Check the **Receiver** screen.
    
4. **Show the Professor:** The image will render immediately, but it will be **highly glitched**—filled with missing gray blocks, shifted pixel scan lines, and color digital distortions where data was dropped.
    
5. Run the **Independent Integrity Checker** on the Receiver. It will warn: `🔴 7.35% Byte Deficit Detected`!
    

## 💻 Prerequisites & Setup

Ensure you have Python 3.8+ installed. Install the two lightweight packages required:

```
pip install streamlit pandas
```

Clone or move all your project files into a folder and launch the UI:

```
cd "your-project-folder"
streamlit run main.py
```