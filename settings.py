def init():
    # Initialize all global variables (to be called only once)
    global stops, bus_routes, train_routes, houses_pd, stops_pd, stations_pd, graph, routes_map, stops_code_map, \
        stops_desc_map, max_walking_dist, transfer_cost, bus_stop_cost, train_stop_cost, walking_cost, drop_station, \
        drop_house, list_options

    graph = {}
    routes_map = {}
    stops_code_map = {}
    stops_desc_map = {}

    # Variables to be adjusted for different routes
    max_walking_dist = 0.35
    transfer_cost = 3.0
    bus_stop_cost = 7.0
    train_stop_cost = 5.0
    walking_cost = 40.0