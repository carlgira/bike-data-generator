# Bike data generator

## Model

user
- id
- name
- age
- profession
- gender

bike
- id
- model
- manufacturer


rental
`- id
- bike_id
- user_id
- insurance_type (standard | advance)`

route
- id
- rental_id
- timestamp_origin
- latitute_origin
- longitud_origin
- latiture_destiation
- longitud_destiation
- timestamp_destination
- distance
- avg_speed

gps_locations
- id
- route_id
- order
- longitud
- latidtud

## Requirements

```
pip install osmnx networkx scikit-learn Faker pandas
```

## Configuration
You can change inside the main.py files the number of samples you want to create for the dataset.

```
number_of_users = 10
number_of_bikes = 10
number_of_rentals = 10
```

You can also change the location of the routes to generate and the locale.
```
file_name = "dubai.graphml"
graph_area = "Dubai, United Arab Emirates"
locales = ['ar']
```

## Run
First time it will download the graphml file, it will take several minutes. 
```
python main.py
```

## Outputs

- A **graphml** file with the selected map
- **data/users.csv**: Simple profile of users
- **data/bikes.csv**: List of bike for rental
- **data/rentals.csv**: List of rentals of bikes
- **data/routes.csv**: The Origin and destination information of one rental from an user.
- **data/gps_locations**: GPS locations during the route of every rental.
