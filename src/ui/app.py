import streamlit as st
import requests
import streamlit.components.v1 as components
import os
from loguru import logger
from streamlit_js_eval import streamlit_js_eval
import time
import asyncio
import httpx
import threading

st.title("AI Health Navigator")
query = st.text_input("Your Question")
location = st.text_input("Your Location(Optional if gps allowed)")
language =st.selectbox("Language",["en","hi","bn"])

use_gps=st.checkbox("Use my GPS location")
lat,lon=None,None

stream=True

if use_gps:
    coords=streamlit_js_eval(js_expressions="""
    new Promise((resolve,reject)=>{
        navigator.geolocation.getCurrentPosition(
            (pos)=>resolve(`${pos.coords.latitude},${pos.coords.longitude}`),
            (err)=>reject(err)
        );   
    
    })""",key="get_coords")

    if coords:
        lat,lon=coords.split(",")
        st.write("Latitude:", lat)
        st.write("Longitude:", lon)
           
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

def fetch_stream(payload,placeholder):
    text=""
    with httpx.stream("POST","http://localhost:8000/ask",json=payload,timeout=None)as r:
        for line in r.iter_lines():
            if line:
                chunk =line
                text+=chunk
                placeholder.text(text)
consent=st.checkbox("Allow anonymized logging")

blocklist=["suicide","self-harm"]

if st.button("Ask"):
    payload={
        "question":query,
        "location_text":location,
        "target_lang":language,
        "lat":lat,"lon":lon
        }
    print(payload)
    if any(word in query.lower() for word in blocklist):
        st.error("Cannot provide advice on this topic. Please seek professional help")
    if stream==True:
        t0=time.perf_counter()
        placeholder=st.empty()
        threading.Thread(target=fetch_stream,args=(payload,placeholder))
        t1=time.perf_counter()
        st.write(t1-t0)
    else:
        resp=requests.post("http://localhost:8000/ask",json=payload)
        if resp==None:
            st.write("Connected with backend but no data recieved")
        else:
            data=resp.json()
            if data:
                if "answer" in data:
                    st.write("Answer:", data["answer"])

                facilities=data.get("facilities")
                st.write("Nearby Facilities")
                if facilities:
                    for f in data["facilities"]:
                         st.write(f"{f['name']} - {f['distance_km']} km [MAP]({f['map_url']})")
                else:
                    st.warning("No answer returned from Backend.")
                st.write("Citations:")
                if "citations" in data:
                     for f in data["citations"]:
                         st.write(f"{f['title']} - {f['url']} ")
                st.write("latency")
                if "latency" in data:
                    for f in data["latency"]:
                         st.write(f"{f['title']} - {f['time']} ")



            else:
                st.warning("No Answer returned from backend.")
    if consent:
        log_query(query,"search_docs",0.12)  

st.warning("THIS IS NOT A SUBSTITUTE FOR PROFESSIONAL MEDICAL ADVICE. SEEK PROFFESINAL CARE WHEN NEEDED.")
