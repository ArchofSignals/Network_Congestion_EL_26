import streamlit as st
import time
import io
from network_engine import Router, NetworkLink, Packet, transmit_tick
from cc_algorithms import TCPReno, UDPGenerator
from metrics_manager import MetricsManager

# --- STREAMLIT PAGE LAYOUT ---
st.set_page_config(page_title="Multi-Node Congestion Dashboard", layout="wide")

# --- SHARED CROSS-PC REAL-TIME STATE ---
# This dictionary acts as our local simulated server memory.
# It synchronizes data between the Sender PC, Admin PC, and Receiver PC.
@st.cache_resource
def get_shared_network_db():
    return {
        "sender_raw_bytes": None,
        "shared_file_name": None,
        "shared_file_type": None,
        "received_bytes": None,
        "simulation_triggered": False,
        "sim_completed": False,
        "active_protocol": "TCP (Reliable / Retransmissions)",
        "last_run_protocol": "TCP (Reliable / Retransmissions)",
        "admin_buffer": 30,
        "admin_service_rate": 4,
        "admin_loss": 1.0,
        "total_drops": 0,
        "peak_cwnd": 0
    }

db = get_shared_network_db()
PROTOCOL_OPTIONS = [
    "TCP (Reliable / Retransmissions)",
    "UDP (Unreliable / Drops Glitch Image)"
]

# --- ROLE DETECTION VIA URL QUERY ---
# Access via:
# Admin:    http://localhost:8501/?role=admin
# Sender:   http://localhost:8501/?role=sender
# Receiver: http://localhost:8501/?role=receiver
query_params = st.query_params
user_role = query_params.get("role", "sender") # Defaults to sender

# --- SIDEBAR CONTROL UNIT ---
st.sidebar.header("⚙️ Global Network Conditions")

if user_role == "admin":
    st.sidebar.success("👑 Admin Terminal Activated")

    if "admin_protocol" not in st.session_state or st.session_state.admin_protocol not in PROTOCOL_OPTIONS:
        st.session_state.admin_protocol = db.get("active_protocol", PROTOCOL_OPTIONS[0])
    
    # Live sliders to tweak network performance
    db["admin_buffer"] = st.sidebar.slider("Router Buffer Capacity (Packets)", 5, 100, db["admin_buffer"])
    db["admin_service_rate"] = st.sidebar.slider("WLAN Available Bandwidth (Pkts/Tick)", 1, 10, db["admin_service_rate"])
    db["admin_loss"] = st.sidebar.slider("Background Wireless Interference/Loss (%)", 0.0, 10.0, db["admin_loss"], step=0.5)
    
    # Protocol Choice (TCP vs UDP)
    db["active_protocol"] = st.sidebar.radio(
        "Select Transport Layer Protocol",
        PROTOCOL_OPTIONS,
        index=PROTOCOL_OPTIONS.index(st.session_state.admin_protocol),
        key="admin_protocol"
    )
else:
    st.sidebar.warning("🔒 Controlled by Network Administrator")
    st.sidebar.metric("WLAN Available Bandwidth", f"{db['admin_service_rate']} Pkts/Tick")
    st.sidebar.metric("Router Buffer Capacity", f"{db['admin_buffer']} Packets")
    st.sidebar.metric("Wireless Link Loss Rate", f"{db['admin_loss']}%")
    st.sidebar.metric("Active Protocol Enforced", "TCP" if "TCP" in db["active_protocol"] else "UDP")

# --- VIEWPORT ROUTER LOGIC ---

# ================= SENDER TERMINAL (PC 2) =================
if user_role == "sender":
    st.title("📤 Universal Client Node: Sender Terminal")
    st.markdown("Upload any file type to transmit across the simulated network topology.")
    
    uploaded_file = st.file_uploader("Select File to Send", type=["txt", "png", "jpg", "jpeg", "pdf"])
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        file_type = uploaded_file.type
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📁 Staged File: **{file_name}**")
        with col2:
            st.info(f"📊 Payload Size: **{len(file_bytes)} bytes**")
            
        if st.button("🚀 Push Payload to Server Queue", type="primary"):
            db["sender_raw_bytes"] = file_bytes
            db["shared_file_name"] = file_name
            db["shared_file_type"] = file_type
            db["simulation_triggered"] = True
            db["sim_completed"] = False
            db["received_bytes"] = None  # Clear out old receiver history
            st.success("File pushed! Notify the Admin to run and analyze the transmission telemetry.")

# ================= ADMIN DASHBOARD (PC 1 / SERVER) =================
elif user_role == "admin":
    st.title("👑 Network Router & Monitoring Dashboard")
    st.markdown("Run network simulations, inspect traffic packet flows, and view real-time bottleneck statistics.")
    
    if db["simulation_triggered"] and db["sender_raw_bytes"] is not None:
        st.info(f"📢 Ready to transmit queued payload: **{db['shared_file_name']}** ({len(db['sender_raw_bytes'])} bytes)")
        
        if st.button("📊 Run Discrete-Event Simulation", type="primary"):
            # 1. Convert payload to byte chunks
            file_bytes = db["sender_raw_bytes"]
            chunk_size = 512  # Packets of 512 bytes
            byte_chunks = [file_bytes[i:i+chunk_size] for i in range(0, len(file_bytes), chunk_size)]
            total_packets = len(byte_chunks)
            
            # 2. Instantiate simulator components
            router = Router(buffer_size=db["admin_buffer"])
            link = NetworkLink(loss_rate=db["admin_loss"] / 100.0)
            algo = TCPReno(init_cwnd=2.0, init_ssthresh=db["admin_buffer"] * 0.8)
            udp = UDPGenerator(packets_per_tick=db["admin_service_rate"])
            metrics = MetricsManager()
            metrics.clear()
            
            transmitted_successfully = {}
            in_flight = {}
            tick = 0
            next_seq_to_send = 0
            run_protocol = db["active_protocol"]
            is_tcp = "TCP" in run_protocol
            
            # --- LIVE ANIMATION PLACEHOLDERS ---
            st.markdown("### ⚡ Live Network Telemetry Streaming...")
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            chart_placeholder1 = st.empty()
            chart_placeholder2 = st.empty()
            
            # --- RUN SIMULATION PIPELINE ---
            while len(transmitted_successfully) < total_packets:
                tick += 1
                outgoing_packets = []
                
                # Sender: Window Allocation
                window_limit = max(1, int(algo.cwnd)) if is_tcp else udp.window_limit()
                
                while (len(in_flight) + len(outgoing_packets)) < window_limit and next_seq_to_send < total_packets:
                    pkt = Packet(next_seq_to_send, byte_chunks[next_seq_to_send], tick)
                    outgoing_packets.append(pkt)
                    if is_tcp:
                        in_flight[pkt.sequence_number] = pkt
                    next_seq_to_send += 1
                
                # Router and link: queue, service, wireless drop, and delivery
                delivered, dropped = transmit_tick(
                    router=router,
                    link=link,
                    outgoing_packets=outgoing_packets,
                    service_rate=db["admin_service_rate"]
                )
                tick_drops = len(dropped)
                tick_successes = len(delivered)
                
                for pkt in delivered:
                    transmitted_successfully[pkt.sequence_number] = pkt.data
                    in_flight.pop(pkt.sequence_number, None)

                for pkt in dropped:
                    in_flight.pop(pkt.sequence_number, None)
                    if is_tcp:
                        next_seq_to_send = min(next_seq_to_send, pkt.sequence_number)
                    else:
                        transmitted_successfully[pkt.sequence_number] = b'\x00' * len(pkt.data)
                
                # Congestion Window Math adjustments
                if is_tcp:
                    if tick_drops > 0:
                        algo.on_loss()
                    else:
                        for _ in range(tick_successes):
                            algo.on_ack()
                
                # Register time log
                metrics.log_tick(
                    tick=tick, 
                    cwnd=algo.cwnd if is_tcp else 0.0, 
                    ssthresh=algo.ssthresh if is_tcp else 0.0, 
                    queue_length=len(router.queue), 
                    drops=tick_drops, 
                    throughput=tick_successes, 
                    state=algo.state if is_tcp else udp.state
                )
                
                # --- UPDATE DASHBOARD REFRESH STREAM (EVERY TICK) ---
                current_df = metrics.get_dataframe()
                completion = len(transmitted_successfully) / max(total_packets, 1)
                progress_bar.progress(min(completion, 1.0))
                status_text.write(f"🔄 Processing Tick **#{tick}** | Total Packets Dropped: **{current_df['Packet Drops'].sum()}**")
                
                # Render/Refresh the charts live on the UI
                if is_tcp:
                    chart_placeholder1.line_chart(current_df, x="Tick", y=["CWND (Window Size)", "SSThresh"], color=["#FF4B4B", "#000000"])
                chart_placeholder2.bar_chart(current_df, x="Tick", y=["Throughput (Pkts/Tick)", "Packet Drops"], color=["#00F4B4", "#FF004B"])
                
                # A micro-sleep delay controls the animation speed for visual style
                time.sleep(0.05) 
                
                if tick > 5000:
                    break
            
            # --- FILE REASSEMBLY ---
            reassembled_chunks = []
            for idx in range(total_packets):
                if idx in transmitted_successfully:
                    reassembled_chunks.append(transmitted_successfully[idx])
                else:
                    reassembled_chunks.append(b'\x00' * len(byte_chunks[idx]))
                    
            db["received_bytes"] = b"".join(reassembled_chunks)
            db["last_run_protocol"] = run_protocol
            db["simulation_triggered"] = False
            db["sim_completed"] = True
            db["total_drops"] = int(metrics.get_dataframe()["Packet Drops"].sum())
            db["peak_cwnd"] = float(metrics.get_dataframe()["CWND (Window Size)"].max()) if is_tcp else 0
            
            # Save the final data set back to memory so it stays on screen after loop completion
            db["final_dataframe"] = metrics.get_dataframe()
            st.rerun()
            
    # Draw static snapshot metrics if simulation finished and stays passive
    if db["sim_completed"]:
        result_protocol = db.get("last_run_protocol", db["active_protocol"])
        result_is_tcp = "TCP" in result_protocol
        st.success("🎉 Simulation run complete! Telemetry captured below:")
        col1, col2, col3 = st.columns(3)
        col1.metric("Selected Layer Mode", "TCP (Reliable)" if result_is_tcp else "UDP (Lossy)")
        col2.metric("Total Drops", f"{db['total_drops']} packets")
        if result_is_tcp:
            col3.metric("Peak Congestion Window", f"{db['peak_cwnd']:.1f} packets")
        else:
            col3.metric("UDP Delivery Speed", "Maximum Link Rate")
            
        st.subheader("📈 Multi-Node Transmission Telemetry")
        
        # Display the final static charts using stored memory dataframe
        if "final_dataframe" in db:
            df = db["final_dataframe"]
            if result_is_tcp:
                st.markdown("#### Congestion Window ($CWND$) Evolution vs SSThresh")
                st.line_chart(df, x="Tick", y=["CWND (Window Size)", "SSThresh"], color=["#FF4B4B", "#000000"])
            
            st.markdown("#### Throughput Rates vs Packet Failures")
            st.bar_chart(df, x="Tick", y=["Throughput (Pkts/Tick)", "Packet Drops"], color=["#00F4B4", "#FF004B"])
    else:
        st.warning("Idle State: Waiting for the Client Sender to upload and queue a file.")

        
# ================= RECEIVER TERMINAL (PC 3) =================
elif user_role == "receiver":
    st.title("📥 Client Node: Receiver Terminal & Verification Panel")
    
    if db["sim_completed"] and db["received_bytes"] is not None:
        net_bytes = db["received_bytes"]
        file_name = db["shared_file_name"]
        file_type = db["shared_file_type"]
        
        st.success(f"📩 Data stream successfully intercepted at destination! File: **{file_name}**")
        
        # Display the file (glitched or perfect depending on protocol selection)
        st.markdown("### 🖼️ Reassembled Output View")
        
        if "image" in file_type:
            st.image(net_bytes, caption=f"Reassembled Image Output ({db.get('last_run_protocol', db['active_protocol'])})", use_container_width=True)
        elif "text" in file_type:
            try:
                st.text_area("Reassembled Text", value=net_bytes.decode("utf-8", errors="replace"), height=250)
            except Exception as e:
                st.error("Could not safely decode text characters.")
        else:
            st.download_button(
                label=f"💾 Download Reassembled {file_name}",
                data=net_bytes,
                file_name=f"received_{file_name}"
            )
            
        # --- INDEPENDENT DATA VERIFIER ---
        st.markdown("---")
        st.subheader("🔍 Independent End-to-End Integrity Checker")
        st.markdown("Upload your copy of the original source file to run independent binary comparisons.")
        
        verify_uploader = st.file_uploader("Upload True Reference File", type=["txt", "png", "jpg", "jpeg", "pdf"], key="rec_verify")
        
        if verify_uploader is not None:
            ref_bytes = verify_uploader.read()
            
            # Exact bit comparison logic
            min_len = min(len(ref_bytes), len(net_bytes))
            match_count = sum(1 for idx in range(min_len) if ref_bytes[idx] == net_bytes[idx])
            
            accuracy_rate = (match_count / max(len(ref_bytes), 1)) * 100
            corruption_rate = 100.0 - accuracy_rate
            
            col1, col2 = st.columns(2)
            col1.metric("Data Accuracy Rate", f"{accuracy_rate:.3f}%")
            col2.metric("Byte Mismatch / Loss Rate", f"{corruption_rate:.3f}%")
            
            if corruption_rate == 0.0:
                st.success("🟢 Security Verification Passed! Byte-for-byte matching is identical. Network layer successfully resolved all drops.")
            else:
                st.error(f"🔴 Integrity Alert! Checked file contains corruption. Bytes mismatched: {len(ref_bytes) - match_count} bytes.")
                
    else:
        st.warning("Idle State: Waiting for data stream to arrive from the network loop...")
