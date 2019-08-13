from django.shortcuts import render
from django.utils import timezone
from .models import Post
from django.shortcuts import render, redirect, render_to_response
from django.http import HttpResponse
from django.template.loader import get_template
from django.template.context import RequestContext
import folium
from IPython.display import HTML, display
import numpy as np
import osmnx as ox
import networkx as nx
from sklearn.neighbors import KDTree
import folium
import folium.plugins
import pandas as pd
from folium import plugins
import requests
import googlemaps
import numbers
import math
from geopy.geocoders import Nominatim

def show_map(request):
    G = ox.graph_from_place('종로구')

    a = ox.elevation.add_node_elevations(G, 'AIzaSyBQYn4uBzdjr1ULXYqfn_z7lUWoIXYQB1Q', max_locations_per_batch=350, pause_duration=0.02)
    b =ox.elevation.add_edge_grades(G, add_absolute=True)

    nodes,edge = ox.graph_to_gdfs(b)
    edge.head()

    gmaps_key = "AIzaSyBQYn4uBzdjr1ULXYqfn_z7lUWoIXYQB1Q"
    gmaps = googlemaps.Client(key=gmaps_key)

    geolocator = Nominatim()

    class GeoUtil:
        """
        Geographical Utils
        """
        @staticmethod
        def degree2radius(degree):
            return degree * (math.pi/180)

        @staticmethod
        def get_harversion_distance(x1, y1, x2, y2, round_decimal_digits=5):

            if x1 is None or y1 is None or x2 is None or y2 is None:
                return None
            assert isinstance(x1, numbers.Number) and -180 <= x1 and x1 <= 180
            assert isinstance(y1, numbers.Number) and  -90 <= y1 and y1 <=  90
            assert isinstance(x2, numbers.Number) and -180 <= x2 and x2 <= 180
            assert isinstance(y2, numbers.Number) and  -90 <= y2 and y2 <=  90

            R = 6371 # 지구의 반경(단위: km)
            dLon = GeoUtil.degree2radius(x2-x1)
            dLat = GeoUtil.degree2radius(y2-y1)

            a = math.sin(dLat/2) * math.sin(dLat/2) \
                + (math.cos(GeoUtil.degree2radius(y1)) \
                *math.cos(GeoUtil.degree2radius(y2)) \
                *math.sin(dLon/2) * math.sin(dLon/2))
            b = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return round(R * b, round_decimal_digits)

    def seeshortestway(x1,x2):
        #loc1 = ox.geocode(x1)
        #loc2 = ox.geocode(x2)

        place1=gmaps.geocode(x1)
        lat1=place1[0]['geometry']['location']['lat']
        lng1=place1[0]['geometry']['location']['lng']

        place2=gmaps.geocode(x2)
        lat2=place2[0]['geometry']['location']['lat']
        lng2=place2[0]['geometry']['location']['lng']

        loc1=(lat1,lng1)
        loc2=(lat2,lng2)

        #KD트리를 이용하면 최단거리를 쉽고 효율적으로 찾아준다.
        tree = KDTree(nodes[['y', 'x']], metric='euclidean')
        loc1_idx = tree.query([loc1], k=1, return_distance=False)[0]
        loc2_idx = tree.query([loc2], k=1, return_distance=False)[0]
        closest_node_to_loc1 = nodes.iloc[loc1_idx].index.values[0]
        closest_node_to_loc2 = nodes.iloc[loc2_idx].index.values[0]

        route = nx.shortest_path(G, closest_node_to_loc1,closest_node_to_loc2, weight='length')
        onlygodoroute = nx.shortest_path(G, closest_node_to_loc1,closest_node_to_loc2, weight='grade_abs')
        impedanceroute = nx.shortest_path(G, closest_node_to_loc1,closest_node_to_loc2, weight='impedance')
        #distance=nx.shortest_path_length(G, closest_node_to_loc1,closest_node_to_loc2)


        graderoute = []
        impedance = []

        for i in range(len(onlygodoroute)):
            lng = G.node[onlygodoroute[i]]['x']
            lat = G.node[onlygodoroute[i]]['y']
            b = [lat,lng]

            graderoute.append(b)

        for i in range(len(impedanceroute)):
            lng = G.node[impedanceroute[i]]['x']
            lat = G.node[impedanceroute[i]]['y']
            b = [lat,lng]

            impedance.append(b)

        m = ox.plot_route_folium(G, route, route_color='navy',tiles='stamen toner')

        antpath = plugins.AntPath(locations=graderoute,color='purple')
        antpath.add_to(m)
        antpath = plugins.AntPath(locations=impedance,color='red')
        antpath.add_to(m)
            #folium.PolyLine(graderoute, color="purple", weight=4).add_to(m)
            #folium.PolyLine(impedance, color="red", weight=4).add_to(m)

        kw = {
        'prefix': 'fa',
        'color': 'green',
        'icon': 'arrow-up'
        }
        ka = {
        'prefix': 'fa',
        'color': 'blue',
        'icon': 'arrow-up'
        }


        icon1 = folium.Icon(angle=45, **kw)
        folium.Marker(location=loc1, icon=icon1,popup=x1, tooltip='출발').add_to(m)


        icon2 = folium.Icon(angle=180, **ka)
        folium.Marker(location=loc2, icon=icon2, popup=x2,tooltip='도착').add_to(m)

                #lium.Marker(location=loc1,
                # icon=folium.Icon(color='red'), popup=x1, tooltip='출발').add_to(m)
                #folium.Marker(location=loc2,
                #icon=folium.Icon(color='blue'),popup=x2, tooltip='도착').add_to(m)


        dobo=4
        add = []

        for i in range(len(route)-1):
            lng1 = G.node[route[i]]['x']
            lat1 = G.node[route[i]]['y']
            lng2 = G.node[route[i+1]]['x']
            lat2 = G.node[route[i+1]]['y']

            result =GeoUtil.get_harversion_distance(lng1,lat1,lng2,lat2)

            add.append(result)

            noroundkm = sum(add)
            km = round(noroundkm,1)

            noroundminute = (km/dobo)*60
            minute = round(noroundminute,1)


        print('거리는',km,'KM 이며, ','시간은', minute,'분 걸립니다.')
        return m
    m=seeshortestway('안국역 3호선', '북촌생활사박물관')






    a = m.save("blog/templates/blog/map.html")
    context = {'my_map': m}
    return render(request, 'blog/map.html', context)
