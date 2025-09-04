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
import re
import json

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

def format_ans(text:str)->str:

    text=re.sub(r"\s*•\s*",r"\n\n•",text)
    text=re.sub(r"\s*–\s*",r"\n–",text)
    text=re.sub(r"(\d+)\.\s*",r"\n\1.",text)
    text=re.sub(r"\s*:\s*",r":\n\n",text)
    text=re.sub(r"\s*>\s*",r"\n\n>",text)
    
    text=text.strip()
    return text

def fetch_stream(payload,placeholder):
    text=""
    
    with requests.post("http://localhost:8000/ask?stream=true",json=payload,timeout=None,stream=True)as r:
      
        for line in r.iter_lines():
            if line:
                decoded =line.decode("utf-8")
                if decoded.startswith("data: "):
                    chunk= decoded.replace("data: ","")
                    if chunk =="[DONE]":
                        break
                    try:
                        message=json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    if message["type"]=="token":
                        text+=chunk
                        formatted_ans=format_ans(text)
                        placeholder.markdown(f"\n{formatted_ans}")
                    elif message["type"]=="metadata" and not metadata_shown:
                         st.markdown(message["content"])


consent=st.checkbox("Allow anonymized logging")

blocklist=["suicide","self-harm"]

if st.button("Ask"):
    payload={
        "question":query,
        "location_text":location,
        "target_lang":language,
        "lat":lat,"lon":lon
        }
    placeholder=st.empty()
    print(payload)
    if any(word in query.lower() for word in blocklist):
        st.error("Cannot provide advice on this topic. Please seek professional help")
    if stream==True:
        t0=time.perf_counter()
        
        fetch_stream(payload,placeholder)
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
