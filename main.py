from faker import Faker
import pandas as pd
import osmnx as ox
import networkx as nx
import numpy as np
from datetime import date
import os
import datetime
import random

number_of_users = 10
number_of_bikes = 10
number_of_rentals = 10

file_name = "dubai.graphml"
graph_area = "Dubai, United Arab Emirates"
locales = ['ar']

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


def generate_rentals():
    rentals = []
    insurance_type = ['standard', 'advanced']
    for i in range(number_of_rentals):
        user_id = int(random.random() * number_of_users)
        bike_id = int(random.random() * number_of_bikes)
        rental = {'user_id': user_id, 'bike_id': bike_id, 'insurance_type': random.choice(insurance_type)}
        rentals.append(rental)

    rentals_df = pd.DataFrame(rentals)
    rentals_df.index.name = 'id'
    rentals_df.to_csv('data/rentals.csv')


def generate_routes():
    routes = []
    for i in range(number_of_rentals):
        distance_in_meters = 0
        while distance_in_meters < 200 or distance_in_meters > 24000:
            node_origin = int(random.random() * number_of_nodes)
            node_destination = int(random.random() * number_of_nodes)
            origin_node = G.nodes.get(nodes[node_origin])
            destination_node = G.nodes.get(nodes[node_destination])
            try:
                distance_in_meters = nx.shortest_path_length(G, nodes[node_origin], nodes[node_destination], weight='length')
            except Exception as e:
                print(e)

        avg_speed_meters = int(np.random.normal(9000, 2000))
        start_date = fake.date_between_dates(datetime.datetime(2022, 9, 1), datetime.datetime(2022, 9, 7))
        start_time = fake.time()
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
generate_rentals()
generate_routes()
generator_gps_locations()

