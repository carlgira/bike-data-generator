from faker import Faker
import pandas as pd
import osmnx as ox
import networkx as nx
import numpy as np
from datetime import date
import os
import datetime
import random
import json
import sys
import time

# check that args has been passed
config_file = sys.argv[1]

with open(config_file) as json_file:
    config = json.load(json_file)


number_of_users = config['numberOfUsers']
number_of_bikes = config['numberOfBikes']

stations = config['stations']
stations_keys = [s["key"] for s in stations]

file_name = config['fileName']
graph_area = config['placeName']
locales = config['locales']

rain_scale = 0.25
windy_scale = 0.1

Faker.seed(42)
fake = Faker(locales)

G = None
nodes = None
number_of_nodes = 0


def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def download_map():
    global G, nodes, number_of_nodes
    if not os.path.exists(file_name):
        G = ox.graph_from_place(graph_area, network_type='drive')
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        ox.save_graphml(G, file_name)
    else:
        G = ox.load_graphml(file_name)
        nodes = list(G.nodes.keys())
        number_of_nodes = len(nodes)




def generate_users():
    users = []
    for i in range(number_of_users):
        profile = fake.simple_profile()
        age = calculate_age(profile['birthdate'])
        while age < 18 or age > 72:
            profile = fake.simple_profile()
            age = calculate_age(profile['birthdate'])
        users.append(profile)
    
    users_df = pd.DataFrame(users)
    users_df.index.name = 'id'
    users_df.to_csv('data/users.csv')


def generate_bikes():
    bikes = []
    manufacturers = ['Rad Power Bikes', 'Ride1Up', 'Ariel Rider', 'Juiced Bikes']
    models = ['mountain', 'electric', ]
    for i in range(number_of_bikes):
        bikes.append({'model': random.choice(models), 'manufacturer': random.choice(manufacturers)})
    
    bikes_df = pd.DataFrame(bikes)
    bikes_df.index.name = 'id'
    bikes_df.to_csv('data/bikes.csv')


def generate_rentals(init_date, end_date):
    count_date = init_date
    while count_date <= end_date:
        
        month = [m for m in config["weather"] if m["month"] == count_date.month][0]
        
        while month == count_date.month:
            day_of_week = count_date.weekday()
            week = [w for w in config["renting"] if day_of_week in w["days"]][0]
            for hod in range(1, 24):
                hour = [h for h in week["hours"] if hod > week['fromHour'] and hod <= week['toHour'] ][0]
                generate_routes(month, count_date.strftime("%d"), hour, hod, init_date, end_date)
            count_date += datetime.timedelta(days=1)

def generate_routes(month, dayOfMonth, hour, hod ,init_date, end_date):
    routes = []
    rentals = []
    insurance_type = ['standard', 'advanced']
    
    rain = month['rain']
    windy = month['windy']
    scaleRenting = month['scaleRenting']
    
    # get the number of rentals using a normal distribution
    
    number_of_rentals = int(np.random.normal(hour['mean'], hour['std'])*scaleRenting)
        
    is_windy = random.random() < windy
    is_raining = random.random() < rain
    
    if is_raining:
        number_of_rentals = int(number_of_rentals * rain_scale)
    
    if is_windy:
        number_of_rentals = int(number_of_rentals * windy_scale)

    for i in range(number_of_rentals):
        user_id = int(random.random() * number_of_users)
        bike_id = int(random.random() * number_of_bikes)
        rental = {'user_id': user_id, 'bike_id': bike_id, 'insurance_type': random.choice(insurance_type)}
        rentals.append(rental)

    rentals_df = pd.DataFrame(rentals)
    rentals_df.index.name = 'id'
    rentals_df.to_csv('data/rentals.csv')
    
    node_origin = random.choice(stations_keys)
    node_destination = random.choice(stations_keys)
    while node_origin == node_destination:
        node_origin = random.choice(stations_keys)
        node_destination = random.choice(stations_keys)

    origin_node = G.nodes.get(node_origin)
    destination_node = G.nodes.get(node_destination)
    distance_in_meters = nx.shortest_path_length(G, nodes[node_origin], nodes[node_destination], weight='length')
    
    avg_speed_meters = int(np.random.normal(9000, 2000))
    start_date = datetime.datetime(year=init_date.year, month=month['month'], day=dayOfMonth, hour=hod, minute=random.randint(0, 59))
    start_time = time.time(hour=hod, minute=random.randint(0, 59))
    duration_minutes = (distance_in_meters / avg_speed_meters) * 60
    
    routes.append({'origin_node': nodes[node_origin], 'destination_node':  nodes[node_destination],
                    'distance': distance_in_meters, 'avg_speed_meters': avg_speed_meters, 'start_date': start_date,
                    'start_time': start_time, 'duration_minutes': duration_minutes,
                    'latitude_origin': origin_node['x'], 'longitude_origin': origin_node['y'],
                    'latitude_destination': destination_node['x'], 'longitude_destination': destination_node['y']})

    routes_df = pd.DataFrame(routes)
    routes_df.index.name = 'id'
    routes_df.to_csv('data/routes.csv')


def generator_gps_locations():
    gps_locations = []
    routes_df = pd.read_csv('data/routes.csv', index_col='id')
    for route_id, route in routes_df.iterrows():
        shortest_route_by_distance = ox.shortest_path(G, route['origin_node'], route['destination_node'], weight='length')
        for node_id_index, node_id in enumerate(shortest_route_by_distance):
            node = G.nodes.get(node_id)
            gps_location = {'route_id': route_id, 'order': node_id_index,
                            'latitude': node['x'], 'longitude': node['y']}
            gps_locations.append(gps_location)

    gps_locations_df = pd.DataFrame(gps_locations)
    gps_locations_df.index.name = 'id'
    gps_locations_df.to_csv('data/gps_locations.csv')


download_map()
generate_users()
generate_bikes()
date_init = datetime.datetime(year=2019, month=1, day=1)
# add one hour to date_init
end_date = date_init + datetime.timedelta(hours=1)
generate_rentals(date_init, end_date)

# get latitudes and longitudes from name of place using osmnx
def get_lat_long(place):
    G = ox.graph_from_place(place, network_type='drive')
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    nodes = list(G.nodes.keys())
    number_of_nodes = len(nodes)
    node = G.nodes.get(nodes[int(random.random() * number_of_nodes)])
    return node['x'], node['y']
