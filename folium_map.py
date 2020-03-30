from utility import *
from collections import namedtuple
import numpy as np
import folium


# Folium Arrow Functions (src: https://medium.com/@bobhaffner/folium-lines-with-arrows-25a0fe88e4e)
def get_arrows(locations, color, size, n_arrows):
    '''
    Get a list of correctly placed and rotated
    arrows/markers to be plotted

    Parameters
    locations : list of lists of lat lons that represent the
                start and end of the line.
                eg [[41.1132, -96.1993],[41.3810, -95.8021]]
    arrow_color : default is 'blue'
    size : default is 6
    n_arrows : number of arrows to create.  default is 3
    Return
    list of arrows/markers
    '''

    Point = namedtuple('Point', field_names=['lat', 'lon'])

    # creating point from our Point named tuple
    p1 = Point(locations[0][0], locations[0][1])
    p2 = Point(locations[1][0], locations[1][1])

    # getting the rotation needed for our marker.
    # Subtracting 90 to account for the marker's orientation
    # of due East(get_bearing returns North)
    rotation = get_bearing(p1, p2) - 90

    # get an evenly space list of lats and lons for our arrows
    # note that I'm discarding the first and last for aesthetics
    # as I'm using markers to denote the start and end
    arrow_lats = np.linspace(p1.lat, p2.lat, n_arrows + 2)[1:n_arrows + 1]
    arrow_lons = np.linspace(p1.lon, p2.lon, n_arrows + 2)[1:n_arrows + 1]

    arrows = []

    # creating each "arrow" and appending them to our arrows list
    for points in zip(arrow_lats, arrow_lons):
        arrows.append(folium.RegularPolygonMarker(location=points,
                                                  fill_color=color, number_of_sides=3,
                                                  radius=size, rotation=rotation))
    return arrows


def get_bearing(p1, p2):
    '''
    Returns compass bearing from p1 to p2

    Parameters
    p1 : namedtuple with lat lon
    p2 : namedtuple with lat lon

    Return
    compass bearing of type float

    Notes
    Based on https://gist.github.com/jeromer/2005586
    '''

    long_diff = np.radians(p2.lon - p1.lon)

    lat1 = np.radians(p1.lat)
    lat2 = np.radians(p2.lat)

    x = np.sin(long_diff) * np.cos(lat2)
    y = (np.cos(lat1) * np.sin(lat2)
         - (np.sin(lat1) * np.cos(lat2)
            * np.cos(long_diff)))
    bearing = np.degrees(np.arctan2(x, y))

    # adjusting for compass bearing
    if bearing < 0:
        return bearing + 360
    return bearing


def getMap(base):

    # Station Marker
    for i in range(len(settings.stations_pd)):
        location = [settings.stations_pd.iloc[i]["latitude"], settings.stations_pd.iloc[i]["longitude"]]
        folium.Marker(location, popup=settings.stations_pd.iloc[i]["Description"]).add_to(base)

    # House Marker
    for i in range(len(settings.houses_pd)):
        location = [settings.houses_pd.iloc[i]["latitude"], settings.houses_pd.iloc[i]["longitude"]]
        folium.CircleMarker(location, popup=settings.houses_pd.iloc[i]["address"], color="#FF0000", radius=2, fill=True,
                            fill_opacity=1).add_to(base)

    # Bus Stop Marker
    for i in range(len(settings.stops_pd)):
        location = [settings.stops_pd.iloc[i]["latitude"], settings.stops_pd.iloc[i]["longitude"]]
        folium.CircleMarker(location, color="#0000FF", radius=2, fill=True,
                            fill_opacity=1).add_to(base)

    return base


def routePlanner(base, start_station, end_block):
    # Get the path
    start_loc_pd = settings.stations_pd.loc[settings.stations_pd['Description'] == start_station].iloc[0]
    end_loc_pd = settings.houses_pd.loc[settings.houses_pd['blk_no'] == end_block].iloc[0]

    end_loc_nodes = nodes_within_dist(end_loc_pd, settings.max_walking_dist)

    smallest = float("inf")
    for node in end_loc_nodes:
        end_loc, end_dist, end_type = node
        total_dist, path = dijkstra(settings.graph, str(start_loc_pd['Description']), str(end_loc[end_type]))

        dist_factor = end_dist * 3 + total_dist
        if dist_factor < smallest:
            smallest = dist_factor
            final_path = path
            final_total_dist = total_dist
            final_end_dist = end_dist
            final_loc = end_loc

    # Draw the path
    for index in range(len(final_path) - 1):
        type = final_path[index + 1][1][2]
        curr_code = final_path[index][0]
        next_code = final_path[index + 1][0]

        if curr_code.isdigit():
            start = [settings.stops_code_map[curr_code]["Latitude"], settings.stops_code_map[curr_code]["Longitude"]]
        else:
            lat = settings.stations_pd.loc[settings.stations_pd['Description'] == curr_code]["latitude"].iloc[0]
            lon = settings.stations_pd.loc[settings.stations_pd['Description'] == curr_code]["longitude"].iloc[0]
            start = [lat, lon]

        if next_code.isdigit():
            end = [settings.stops_code_map[next_code]["Latitude"], settings.stops_code_map[next_code]["Longitude"]]
        else:
            lat = settings.stations_pd.loc[settings.stations_pd['Description'] == next_code]["latitude"].iloc[0]
            lon = settings.stations_pd.loc[settings.stations_pd['Description'] == next_code]["longitude"].iloc[0]
            end = [lat, lon]

        if type == "Bus":
            color = "blue"
        elif type == "Train":
            color = "black"
        else:
            color = "orange"

        folium.PolyLine(locations=[start, end], color=color).add_to(base)

        arrows = get_arrows(locations=[start, end], color=color, size=10, n_arrows=1)

        for arrow in arrows:
            arrow.add_to(base)

    start_end_lat = final_loc["latitude"]
    start_end_lon = final_loc["longitude"]
    start = [start_end_lat, start_end_lon]

    final_end_lat = end_loc_pd["latitude"]
    final_end_lon = end_loc_pd["longitude"]
    end = [final_end_lat, final_end_lon]

    folium.PolyLine(locations=[start, end], color='orange').add_to(base)

    arrows = get_arrows(locations=[start, end], color="red", size=10, n_arrows=1)

    for arrow in arrows:
        arrow.add_to(base)

    write_to_File(final_path, final_total_dist, final_end_dist, final_loc, end_loc_pd)

    return base


def write_to_File(final_path, final_total_dist, final_end_dist, final_loc, end_loc_pd):
    f = open("data/output.txt", "w")
    for index in range(len(final_path) - 1):
        type = final_path[index + 1][1][2]
        service = final_path[index + 1][1][0]
        curr_code = final_path[index][0]
        next_code = final_path[index + 1][0]
        dist_to_next = final_path[index + 1][2]

        if curr_code.isdigit():
            curr_loc = settings.stops_code_map[curr_code]["Description"].upper()
        else:
            curr_loc = curr_code.upper()

        if next_code.isdigit():
            next_loc = settings.stops_code_map[next_code]["Description"].upper()
        else:
            next_loc = next_code.upper()

        if service:
            f.write(type + " (" + service + ") from " + curr_loc + " to " + next_loc+"\n")
        else:
            f.write("Walk %.1fm from %s to %s" % (dist_to_next * 1000, curr_loc, next_loc)+"\n")

    f.write("Walk %.1fm from %s to BLK %s" % (
        final_end_dist * 1000, final_loc["Description"].upper(), end_loc_pd["blk_no"])+"\n")

    f.write("Stops:" + str(len(final_path))+"\n")
    sum_dist = final_total_dist + final_end_dist
    f.write("Distance: %.2fkm" % sum_dist+"\n")

    f.close()

