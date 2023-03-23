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

# check that args has been passed
config_file = 'dubai-config.json'

with open(config_file) as json_file:
    config = json.load(json_file)

number_of_users = config['numberOfUsers']
number_of_bikes = config['numberOfBikes']
routes_cached = {}
distance_cached = {}

stations = config['stations']
stations_nodes = {}
for s in stations:
    stations_nodes[s['key']] = {'y': s['y'], 'x': s['x'], "street_count": s['street_count']}

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
    all_rentals = []
    all_routes = []
    while count_date <= end_date:
        
        month = [m for m in config["weather"] if int(m["month"]) == int(count_date.month)][0]
        print(month)
        
        while int(month['month']) == int(count_date.month) and count_date <= end_date:

            day_of_week = count_date.weekday()
            week = [w for w in config["renting"] if day_of_week in w["days"]][0]['hours']
            for hod in range(1, 24):
                hour = [h for h in week if hod > h['fromHour'] and hod <= h['toHour'] ][0]
                routes, rentals = generate_routes(month, count_date.strftime("%d"), hour, hod, init_date, end_date)
                all_rentals.extend(rentals)
                all_routes.extend(routes)

            count_date += datetime.timedelta(days=1)

    rentals_df = pd.DataFrame(all_rentals)
    rentals_df.index.name = 'id'
    rentals_df.to_csv('data/rentals.csv')

    routes_df = pd.DataFrame(all_routes)
    routes_df.index.name = 'id'
    routes_df['rental_id'] = rentals_df.index
    routes_df.to_csv('data/routes.csv')





def generate_routes(month, dayOfMonth, hour, hod, init_date, end_date):
    routes = []
    rentals = []
    insurance_type = ['standard', 'advanced']
    
    rain = float(month['rain'])
    windy = float(month['windy'])
    scaleRenting = float(month['scaleRenting'])
    
    # get the number of rentals using a normal distribution
    
    number_of_rentals = int(np.random.normal(hour['mean'], hour['std'])*scaleRenting)

    is_windy = random.random() < windy
    is_raining = random.random() < rain
    
    if is_raining:
        number_of_rentals = int(number_of_rentals * rain_scale)
    
    if is_windy:
        number_of_rentals = int(number_of_rentals * windy_scale)


    # calculate the temperature using a minimal temperature reached at 5 hours and a maximum temperature reached at 17 hours
    # the temperature is calculated using a linear function
    temperature = 0

    temperature = np.round(np.roll(np.append(np.linspace(month['temperature']['min'], month['temperature']['max'], 12), np.linspace(month['temperature']['min'], month['temperature']['min'], 12)), 6))[hod]

    for i in range(number_of_rentals):
        user_id = int(random.random() * number_of_users)
        bike_id = int(random.random() * number_of_bikes)
        rental = {'user_id': user_id, 'bike_id': bike_id, 'insurance_type': random.choice(insurance_type)}
        rentals.append(rental)

        origin_node = None
        destination_node = None
        node_origin = None
        node_destination = None

        while origin_node is None or destination_node is None:
            node_origin = random.choice(stations)
            node_destination = random.choice(stations)

            while node_origin['key'] == node_destination['key']:
                node_origin = random.choice(stations)
                node_destination = random.choice(stations)

            origin_node = G.nodes.get(node_origin['key'])
            destination_node = G.nodes.get(node_destination['key'])

        route_key = str(node_origin['key']) + "-" + str(node_destination['key'])

        distance_in_meters = 0
        if route_key in distance_cached:
            distance_in_meters = distance_cached[route_key]
        else:
            distance_in_meters = nx.shortest_path_length(G, node_origin['key'], node_destination['key'], weight='length')

        avg_speed_meters = int(np.random.normal(9000, 2000))
        start_date = datetime.datetime(year=init_date.year, month=int(month['month']), day=int(dayOfMonth), hour=int(hod), minute=random.randint(0, 59))
        start_time = datetime.time(hod, random.randint(0, 59))
        duration_minutes = (distance_in_meters / avg_speed_meters) * 60

        routes.append({'origin_node': node_origin['key'], 'destination_node':  node_destination['key'],
                        'distance': distance_in_meters, 'avg_speed_meters': avg_speed_meters, 'start_date': start_date,
                        'start_time': start_time, 'duration_minutes': duration_minutes,
                        'latitude_origin': origin_node['x'], 'longitude_origin': origin_node['y'],
                        'latitude_destination': destination_node['x'], 'longitude_destination': destination_node['y'],
                       'is_raining': is_raining, 'is_windy': is_windy, 'temperature': temperature})

    return routes, rentals

def generator_gps_locations():
    gps_locations = []
    routes_df = pd.read_csv('data/routes.csv', index_col='id')
    for route_id, route in routes_df.iterrows():
        shortest_route_by_distance = []
        route_key = str(route['origin_node']) + "-" + str(route['destination_node'])
        if route_key in routes_cached:
            shortest_route_by_distance = routes_cached[route_key]
        else:
            shortest_route_by_distance = ox.shortest_path(G, route['origin_node'], route['destination_node'], weight='length')
            routes_cached[route_key] = shortest_route_by_distance

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
date_init = datetime.datetime(year=2022, month=1, day=1)
end_date = date_init + datetime.timedelta(days=365)
generate_rentals(date_init, end_date)
generator_gps_locations()

# get latitudes and longitudes from name of place using osmnx
def get_lat_long(place):
    G = ox.graph_from_place(place, network_type='drive')
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    nodes = list(G.nodes.keys())
    number_of_nodes = len(nodes)
    node = G.nodes.get(nodes[int(random.random() * number_of_nodes)])
    return node['x'], node['y']
