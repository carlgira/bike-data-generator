import osmnx as ox
import warnings
import os
warnings.filterwarnings("ignore")


dubai_stations = ["Expo 2020 Dubai, dubai",
          "Dubai Marina, dubai",
          "Barsha Heights (TECOM), dubai",
          "The Greens, dubai",
          "Dubai Internet City, dubai",
          "Dubai Media City, dubai",
          "Palm Jumeirah, dubai",
          "Deira, dubai",
          "Downtown Dubai, dubai",
          "Dubai Canal, dubai",
          "Karama, dubai",
          "Mankhool, dubai",
          "Umm Suqeim, dubai",
          ]


def get_graph(graph_area):
    go = ox.graph_from_place(graph_area, network_type='drive')
    go = ox.add_edge_speeds(go)
    go = ox.add_edge_travel_times(go)
    return go

def test_plots(area, places):
    result = []
    g_area = get_graph(area)
    for place in places:
        try:
            g_place = get_graph(place)
            key = list(g_place.nodes.keys())[0]
            # get lat-long coordinates for one of the points
            node = g_area.nodes.get(key)
            if node is not None:
                node['key'] = key
                node['place'] = place
                result.append(node)
        except:
            print("Error in ", place)
    return result

    
results = test_plots('Dubai, United Arab Emirates', places=dubai_stations)
print(results)
