import requests,urllib.parse
import httpx

async def nearest_clinic(location_query:str):
    q=urllib.parse.quote(location_query)
    async with httpx.AsyncClient(timeout=30) as client:
        geo=await client.get(f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1",headers={"User-Agent":"ai_health_navigator/0.1"})
        geo = geo.json()

    if not geo: return None
    lat,lon =geo[0]["lat"],geo[0]["lon"]

    overpass=f"""
    [out:json][timeout:25];
    (
    node["amenity"="cilnic"](around:3000,{lat},{lon});
    node["healthcare"="clinic"](around:3000,{lat},{lon});
    node["amenity"="hospital"](around:5000,{lat},{lon});
    );
    out center 5;
"""
    async with httpx.AsyncClient(timeout=30) as client:
       r=await client.post("https://overpass-api.de/api/interpreter",data=overpass.encode("utf-8"))
    data=r.json().get("elements",[])
    if not data :return None
    best=data[0]
    name=best.get("tags",{}).get("name","(unnamed)")
    return {"name":name,"lat":best.get("lat"),"lon":best.get("lon")}
if __name__=="__main__":
    print(nearest_clinic("Hauz khas,New Delhi"))

