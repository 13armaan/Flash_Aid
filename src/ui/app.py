import streamlit as st
import requests

st.title("AI Health Navigator")
query = st.text_input("Your Question")
location = st.text_input("Your Location(Optional if gps allowed)")
language =st.selectbox("Language",["en","hi","bn"])

use_gps=st.checkbox("Use my GPS location")
lat,lon=None,None

if use_gps:
    st.markdown("open in browser with location access") #need to implement JS for this (later)

if st.button("Ask"):
    payload={
        "question":query,
        "location_text":location,
        "target_language":language,
        "lat":lat,"lon":lon
        }
    resp=requests.post("http://localhost:8000/agent",json=payload)
    data=resp.json()
    st.write("Answer:",data["answer"])
    if data["facilities"]:
        for f in data["facilities"]:
            st.write(f"{f['name']} - {f['distance_km']} km [MAP]({f['map_url']})")
            