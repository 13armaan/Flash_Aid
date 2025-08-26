import streamlit as st
import requests
import streamlit.components.v1 as components

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
            