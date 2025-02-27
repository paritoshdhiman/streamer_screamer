import streamlit as st
import pandas as pd
import socket
import threading
import time
import asyncio
import os
import warnings

warnings.filterwarnings("ignore", message="missing ScriptRunContext!")

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

# Footer section
footer = """
<style>
footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #44475a;
    color: #f8f8f2;
    text-align: center;
    padding: 10px;
    font-size: 14px;
    box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.2);
}
a {
    color: #bd93f9;
    text-decoration: none;
}
</style>
<footer>
    Made with ❤️ | Liberty Energy 
</footer>
"""


st.markdown(dracula_css, unsafe_allow_html=True)
st.markdown(footer, unsafe_allow_html=True)


class TCPStreamer:
    def __init__(self):
        self.server = None
        self.is_streaming = False
        self.clients = set()  # Use a set to store active client connections

    async def handle_client(self, reader, writer, data, interval):
        """Handles streaming data to a single client."""
        addr = writer.get_extra_info('peername')
        print(f"Connection established with {addr}.")
        st.toast(f"Connection established with {addr}.")
        self.clients.add(writer)
        try:
            for _, row in data.iterrows():
                if not self.is_streaming:
                    break
                message = ','.join(map(str, row)) + "\n"
                writer.write(message.encode('utf-8'))
                await writer.drain()
                await asyncio.sleep(interval)
        except Exception as e:
            st.toast(f"Error with client {addr}: {e}")
        finally:
            print(f"Closing connection with {addr}.")
            st.toast(f"Closing connection with {addr}.")
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()

    async def start_server(self, data, ip, port, interval):
        """Starts the asyncio server."""
        self.is_streaming = True
        self.server = await asyncio.start_server(
            lambda r, w: self.handle_client(r, w, data, interval),
            ip,
            port,
        )
        print(f"Server started. Listening on {ip}:{port}.")
        st.toast(f"Server started. Listening on {ip}:{port}.")
        async with self.server:
            await self.server.serve_forever()

    async def stop_stream(self):
        """Stops the server and closes all connections."""
        self.is_streaming = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for writer in list(self.clients):
            writer.close()
            await writer.wait_closed()
        self.clients.clear()
        print("Streaming stopped.")

streamer = TCPStreamer()

st.logo('https://libertyenergy.com/wp-content/uploads/2023/05/Liberty-Energy-Horizontal-Logo.png', size='large', link='https://libertyenergy.com/')

st.title("STREAMER SCREAMER")

fqdn = socket.getfqdn()[:3]
if fqdn == "LOS":

    # Selection between Maven and FracPro
    dataacq_type = st.selectbox("DataAcq Type", options=("Maven", "FracPro"))

    # File upload section
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        # Check if "Date Time" column exists
        if dataacq_type != "FracPro":
            if "Date Time" not in df.columns:
                # print('"Date Time" column is missing. Adding it as the first column...')

                # Add the "Date Time" column as the first column
                df.insert(0, "Date Time", pd.Timestamp.now())

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

    m1, m2 = st.columns([1,2])
    with m1:
        start_stream = st.button("Start Streaming")
    with m2:
        stop_stream = st.button("Stop Streaming")

    # Streaming controls
    if start_stream:
        if uploaded_file and ip and port:
            st.success(f"Starting to stream data to {ip}:{port}...")


            def start_streaming():
                asyncio.run(streamer.start_server(df, ip, int(port), interval))


            threading.Thread(target=start_streaming).start()
        else:
            st.error("Please upload a CSV file and specify IP and port.")

    # Stop streaming
    if stop_stream:
        def stop_streaming():
            asyncio.run(streamer.stop_stream())


        threading.Thread(target=stop_streaming).start()
        st.error("Streaming stopped.")

