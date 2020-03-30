import settings
import pandas as pd
from math import radians, sin, cos, asin, sqrt
import json
import heapq


def Initialize():
    # Load services, stops, routes
    settings.stops = json.loads(open("data/stops.json").read())
    settings.bus_routes = json.loads(open("data/bus_routes.json").read())
    settings.train_routes = json.loads(open("data/train_routes.json").read())

    # Load house and bus_stops nodes
    settings.houses_pd = pd.read_excel("data/coordinates.xlsx")
    settings.stops_pd = pd.read_excel("data/stops.xlsx")
    settings.stations_pd = pd.read_csv("data/stations.csv")

    # Initialize BusStopCode, Description
    settings.stops_code_map = {stop['BusStopCode']: stop for stop in settings.stops}
    settings.stops_desc_map = {stop["Description"]: stop for stop in settings.stops}

    # Initialize the route_map dictionary
    # route_map = { (service, direction, type) : [route] }
    for route in settings.bus_routes:
        key = (route["ServiceNo"], route["Direction"], "Bus")
        if key not in settings.routes_map:
            settings.routes_map[key] = []
        settings.routes_map[key] += [route]

    for route in settings.train_routes:
        key = (route["ServiceName"], route["Direction"], "Train")
        if key not in settings.routes_map:
            settings.routes_map[key] = []
        settings.routes_map[key] += [route]

    # Initialize the graph
    # graph = { node : { (adj_node, (service, direction, type)) : distance } }
    for service, route in settings.routes_map.items():
        if service[-1] == "Bus":
            key_name = "BusStopCode"
        else:
            key_name = "StationName"
        for route_index in range(len(route) - 1):
            key = route[route_index][key_name]
            if key not in settings.graph:
                settings.graph[key] = {}
            if None in {route[route_index]["Distance"], route[route_index + 1]["Distance"]}:
                distance = 0
            else:
                distance = route[route_index + 1]["Distance"] - route[route_index]["Distance"]
            settings.graph[key][(route[route_index + 1][key_name], service)] = distance

    for index, station in settings.stations_pd.iterrows():
        nearest_nodes = nodes_within_dist(station, settings.max_walking_dist)
        for node in nearest_nodes:
            nearest, dist, key_name = node
            settings.graph[station["Description"]][(str(nearest[key_name]), ("", 0, "Walk"))] = dist

    # For the dropdown list
    settings.drop_station = settings.stations_pd["Description"].to_numpy().tolist()
    settings.drop_house = settings.houses_pd["blk_no"].to_numpy().tolist()
    settings.list_options = ["Shortest Route", "Least Transfers", "Prefer Bus", "Prefer Train"]


def distNodes(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1 = radians(lon1)
    lat1 = radians(lat1)
    lon2 = radians(lon2)
    lat2 = radians(lat2)
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km


def nodes_within_dist(loc, radius):
    """
       Return all nodes that are in the radius of given location
    """
    lat = float(loc['latitude'])
    lon = float(loc['longitude'])
    nodes = []
    for index, stop in settings.stops_pd.iterrows():
        lat2 = float(stop['latitude'])
        lon2 = float(stop['longitude'])
        dist = distNodes(lon, lat, lon2, lat2)
        if radius > dist > 0:
            nodes.append((stop, dist, "BusStopCode"))
    for index, station in settings.stations_pd.iterrows():
        lat2 = float(station['latitude'])
        lon2 = float(station['longitude'])
        dist = distNodes(lon, lat, lon2, lat2)
        if radius > dist > 0:
            nodes.append((station, dist, "Description"))
    return nodes


def dijkstra(graph, start, end):
    """
        Calculates the shortest path between two points
    """
    # priority queue to store the paths
    heap = []
    # seen set to prevent checking the same node twice
    seen = set()
    # push the first item into the priority queue. item is a tuple: (cost, distance, path)
    heapq.heappush(heap, (0, 0, [(start, None, 0)]))
    while heap:
        # get the item with the least cost from the queue
        curr_cost, curr_dist, path = heapq.heappop(heap)
        # get the last node of the path
        node, curr_service, _ = path[-1]
        # if path is found, return the path
        if node == end:
            return curr_dist, path
        # if node has been already checked, skip
        if (node, curr_service) in seen:
            continue
        # add node to the seen set
        seen.add((node, curr_service))

        # iterate through all adjacent nodes
        for (adjacent, service), dist in graph.get(node, {}).items():
            # construct a new path with the adjacent node
            new_path = list(path)
            new_path.append((adjacent, service, dist))

            # calculate the cost of going to the adjacent node
            new_cost = curr_cost
            if curr_service and curr_service[-1] != 'Walk' and curr_service != service:
                new_cost += settings.transfer_cost
            if service[-1] == "Bus":
                new_cost += settings.bus_stop_cost + (dist * 10)
            elif service[-1] == "Train":
                new_cost += settings.train_stop_cost + (dist * 10)
            else:
                new_cost += (settings.walking_cost + 1) * (dist * 10)

            # push the new path into the queue
            heapq.heappush(heap, (new_cost, dist + curr_dist, new_path))