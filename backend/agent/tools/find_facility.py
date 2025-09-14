from geopy.geocoders import Nominatim
from haversine import haversine
import overpy
from core.models import facility

_geocoder=Nominatim(user_agent="AIHealthNavigator/0.2")
overpass=overpy.Overpass()

async def lookup(location_text:str=None,lat:float=None,lon:float=None):
    if location_text:
        loc=_geocoder.geocode(location_text)
        if not loc:
            return[]
        lat,lon=loc.latitude,loc.longitude
    elif lat is None or lon is None:
        return []
    
    query=f"""
    [out:json];
    node["amenity"~"clinic|hospital"](around:5000,{lat},{lon});
    out center;
"""
    try:
        res=overpass.query(query)
    except Exception as e:
        return[]
    out=[]
    for node in res.nodes:
        d=haversine((lat,lon),(node.lat,node.lon))
        out.append(facility(
            name=node.tags.get("name","Unnamed"),
            distance_km=round(d,2),
            phone=node.tags.get("phone"),
            opening_hours=node.tags.get("opening hours"),
            map_url=f"https://www.openstreetmap.org/?mlat={node.lat}&mlon={node.lon}#map=17/{node.lat}/{node.lon}"
        ))
    
    return sorted(out,key=lambda x:x.distance_km)[:5]