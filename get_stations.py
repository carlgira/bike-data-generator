import osmnx as ox
import warnings
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


def test_plots(places):
    result = []
    for place in places:
        try:
            G = ox.graph_from_place(place, network_type='drive', simplify=False)
            key = list(G.nodes.keys())[0]
            # get lat-long coordinates for one of the points
            #node = G.nodes.get(key)
            result.append({"name": place, "key": key})
        except:
            print("Error in ", place)
    return result

    
results = test_plots(places=dubai_stations)
print(results)
