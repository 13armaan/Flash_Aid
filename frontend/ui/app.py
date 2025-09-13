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

stream=True
BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "logo.png")
st.set_page_config(layout="wide")

col2,empty=st.columns([5,1])


st.sidebar.image(logo_path)
st.sidebar.markdown("Your health, in a ⚡.")
with col2:
    st.title("Flash Aid")
    st.write( "From symptoms to solutions - instantly with FlashAid.")
    query = st.text_input("Your Question")
    location = st.text_input("Your Location(Optional if gps allowed)")
    language =st.selectbox("Language",["en","hi","bn"])
    if language!="en":
        stream=False
        st.write("Streaming option not available for translation")
    use_gps=st.checkbox("Use my GPS location")
lat,lon=None,None



if use_gps:
    coords=streamlit_js_eval(js_expressions="""
    new Promise((resolve,reject)=>{
        navigator.geolocation.getCurrentPosition(
            (pos)=>resolve(`${pos.coords.latitude},${pos.coords.longitude}`),
            (err)=>reject(err)
        );   
    
    })""",key="get_coords")
    with col2:
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
    metadata_shown=False
    with requests.post("https://flashaid-production.up.railway.app/ask?stream=true",json=payload,timeout=None,stream=True)as r:
      
        for line in r.iter_lines():
            if line:
                decoded =line.decode("utf-8")
                if decoded.startswith("data: "):
                    chunk= decoded.replace("data: ","")
                    if chunk =="[DONE]":
                        break
                    try:
                        message=json.loads(chunk)
                    except json.JSONDecodeError as e:
                        print("JSON decode error:", e, "chunk=", chunk)
                        continue
                    if message["type"]=="token":
                        text+=message["content"]
                        formatted_ans=format_ans(text)
                        
                        placeholder.markdown(f"## 🤖 AI Response ##\n\n{formatted_ans}")
                    elif message["type"]=="metadata" and not metadata_shown:
                        data=message["content"]
                        facilities=data.get("facilities",[])
                        citations=data.get("citations",[])

                        if facilities:
                            st.markdown("## 🏥 Nearby Facilities ##")
                            for f in facilities:
                                st.markdown(
                                    f"""
                                  <div style="padding:15px; border-radius:15px; border-radius:12px solid #e0e0e0;box-shadow: 0 2px 6px rgba(0,0,0,0.1); margin-bottom:10px; background-color:#130E33;color:#f9f9f9;">
                                 <b>🏥 {f['name']} ({f['distance_km']}) km </b><br>
                                 📍<a href="{f['map_url']}" >View on Map</a><br>
                                 </div>
                                 """,
                                 unsafe_allow_html=True
                                )
                        if citations:     
                            st.markdown("## 📚 References ##")
                            with st.expander("show references"):
                                         for c in citations:
                                            st.markdown(f"{c['title']} - {c['url']} ")
                        
                        metadata_shown=True

with col2:
    consent=st.checkbox("Allow anonymized logging")

blocklist=["suicide","self-harm"]
with col2:
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
            t0=time.perf_counter()
            resp=requests.post("https://flashaid-production.up.railway.app/ask",json=payload)
            if resp==None:
                st.write("Connected with backend  but no data recieved")
            else:
                
                data=resp.json()
                if data:
                    if "answer" in data:
                        st.markdown("## 🤖 AI Response ##")
                        st.markdown(data["answer"])

                    facilities=data.get("facilities")
                    st.markdown("## 🏥 Nearby Facilities ##")
                    if facilities:
                        for f in data["facilities"]:
                             st.markdown(f"""
                              <div style="padding:15px; border-radius:15px; border-radius:12px solid #e0e0e0;box-shadow: 0 2px 6px rgba(0,0,0,0.1); margin-bottom:10px; background-color:#130E33;color:#f9f9f9;">
                             <b>🏥 {f['name']} ({f['distance_km']}) km </b><br>
                             📍<a href="{f['map_url']}" >View on Map</a><br>
                             """,
                             unsafe_allow_html=True
                             )
                    else:
                        st.warning("No answer returned from  Backend.")
                    st.markdown("## 📚 References ##")
                    with st.expander("show references"):
                        if "citations" in data:
                             for f in data["citations"]:
                                 st.write(f"{f['title']} - {f['url']} ")
                    #st.write("latency")
                    #if "latency" in data:
                    #    for f in data["latency"]:
                    #         st.write(f"{f['title']} - {f['time']} ")
                    # for debugging
                    t1=time.perf_counter()
                    st.write(t1-t0)

                else:
                    st.warning("No Answer returned from backend.")
        if consent:
            log_query(query,"search_docs",0.12)  
    import streamlit as st

    st.markdown(
    """
    <div style="background-color: #b58900; padding: 12px; border-radius: 6px; 
                text-align: center; font-weight: bold; color: black;">
        ⚠️ THIS IS NOT A SUBSTITUTE FOR PROFESSIONAL MEDICAL ADVICE. 
        SEEK PROFESSIONAL CARE WHEN NEEDED.
    </div>
    """,
    unsafe_allow_html=True
)


    