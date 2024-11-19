import streamlit as st
import pandas as pd
import socket
import threading
import time
import os


dracula_css = """
<style>
body {
    background-color: #282a36;
    color: #f8f8f2;
}
.stApp {
    background-color: #282a36;
}
header {
    background-color: #44475a;
}
.css-1q8dd3e {  /* Sidebar background color */
    background-color: #44475a;
}
.css-1v0mbdj {  /* Primary buttons */
    background-color: #bd93f9;
    color: #282a36;
}
.css-1pahdxg {  /* Secondary buttons */
    background-color: #6272a4;
    color: #f8f8f2;
}
</style>
"""

st.markdown(dracula_css, unsafe_allow_html=True)


class TCPStreamer:
    def __init__(self):
        self.server_socket = None
        self.is_streaming = False

    def start_stream(self, data, ip, port, interval=1):
        """Starts streaming the CSV data to the specified IP and port."""
        self.is_streaming = True

        def stream_data():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                self.server_socket = server_socket
                server_socket.bind((ip, port))
                server_socket.listen(1)
                st.write(f"Server started. Listening on {ip}:{port}...")

                conn, addr = server_socket.accept()
                with conn:
                    st.write(f"Connection established with {addr}.")
                    for _, row in data.iterrows():
                        if not self.is_streaming:
                            break
                        # Convert row to a comma-separated string and send it
                        message = ','.join(map(str, row)) + "\n"
                        conn.sendall(message.encode('utf-8'))
                        time.sleep(interval)
                    st.write("Streaming stopped.")

        thread = threading.Thread(target=stream_data)
        thread.start()

    def stop_stream(self):
        """Stops the streaming."""
        self.is_streaming = False
        if self.server_socket:
            self.server_socket.close()

streamer = TCPStreamer()

st.logo('https://libertyenergy.com/wp-content/uploads/2023/05/Liberty-Energy-Horizontal-Logo.png', size='large', link='https://libertyenergy.com/')

st.title("STREAMER SCREAMER")

# fqdn = socket.getfqdn()[:3]
# if fqdn == "LOS":

# File upload section
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Preview of uploaded CSV file:")
    st.dataframe(df)

# IP and port input section
c1, c2 = st.columns(2)
with c1:
    ip = st.text_input("Enter the IP address", value="127.0.0.1")
with c2:
    port = st.number_input("Enter the port", value=8080, min_value=1, max_value=65535)

# Interval input section
interval = st.slider("Set the interval between rows (seconds)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)

# Streaming controls
if st.button("Start Streaming"):
    if uploaded_file and ip and port:
        st.write(f"Starting to stream data to {ip}:{port}...")
        streamer.start_stream(df, ip, int(port), interval)
    else:
        st.error("Please upload a CSV file and specify IP and port.")

if st.button("Stop Streaming"):
    streamer.stop_stream()
    st.write("Streaming stopped.")

# Display current status
if streamer.is_streaming:
    st.success(f"Streaming data to {ip}:{port}...")
else:
    st.info("Streaming is not active.")

