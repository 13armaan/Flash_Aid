import streamlit as st
import requests
import streamlit.components.v1 as components
import os
from loguru import logger

st.title("AI Health Navigator")
query = st.text_input("Your Question")
location = st.text_input("Your Location(Optional if gps allowed)")
language =st.selectbox("Language",["en","hi","bn"])

use_gps=st.checkbox("Use my GPS location")
lat,lon=None,None

if use_gps:
    st.markdown("open in browser with location access") #need to implement JS for this (later)
    gps_html="""
    <script>
    navigator.geolocation.getCurrentPosition(
        function(position){
            const lat=position.coords.latitude;
            const lon=position.coords.longitude;
            document.querySelector('body').innerHTML +=
            `<input type='hidden' id='lat' value='${lat}'>
            <input type='hidden' id='lon' value='${lon}'>`;
        },
        function(error){alert ('GPS access denied or not available');}
    );
    </script>
    """
    components.html(gps_html)

    js_lat=st.query_params.get("lat")
    js_lon=st.query_params.get("lon")
    if js_lat and js_lon:
        lat=float(js_lat[0])
        lon=float(js_lon[0])
    else:
        st.info("Please allow GPS access and reload if necessary.")

os.makedirs("logs", exist_ok=True)

logger.add(
    "logs/agent.log",
     rotation="1 MB",
      retention="10 days",
      level="INFO"
      )

def log_query(query,tool_used,latency):
    logger.info(f"tool={tool_used},latency={latency:.2f}s")

consent=st.checkbox("Allow anonymized logging")

blocklist=["suicide","self-harm"]

if st.button("Ask"):
    payload={
        "question":query,
        "location_text":location,
        "target_language":language,
        "lat":lat,"lon":lon
        }
    if any(word in query.lower() for word in blocklist):
        st.error("Cannot provide advice on this topic. Please seek professional help")
    resp=requests.post("http://localhost:8000/ask",json=payload)
    if resp==None:
        st.write("Connected with backend but no data recieved")
    else:
        data=resp.json()
        if data:
            if "answer" in data:
                st.write("Answer:", data["answer"])
        
            facilities=data.get("facilities")
            if facilities:
                for f in data["facilities"]:
                     st.write(f"{f['name']} - {f['distance_km']} km [MAP]({f['map_url']})")
            else:
                st.warning("No answer returned from backend.")
        else:
            st.warning("No answer returned from backend.")
    if consent:
        log_query(query,"search_docs",0.12)  

st.warning("THIS IS NOT A SUBSTITUTE FOR PROFESSIONAL MEDICAL ADVICE. SEEK PROFFESINAL CARE WHEN NEEDED.")
