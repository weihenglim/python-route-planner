from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import webbrowser
import os
import pathlib
from werkzeug.utils import redirect
from folium_map import *
from utility import *

# Initialize Flask
app = Flask(__name__)
bootstrap = Bootstrap(app)

# Initialise the needed resources
settings.init()
Initialize()


@app.route('/')
def index():
    return render_template("App.html", data=settings.drop_station, data1=settings.drop_house, options=settings.list_options)


# Generate Function
@app.route("/", methods=['POST', 'GET'])
def generate():
    start = request.form.get('start')
    end = request.form.get('end')
    decision = request.form.get('option')

    if decision == "Shortest Route":
        settings.transfer_cost = 3.0
        settings.bus_stop_cost = 7.0
        settings.train_stop_cost = 5.0

    elif decision == "Least Transfers":
        settings.transfer_cost = 99.0
        settings.bus_stop_cost = 7.0
        settings.train_stop_cost = 5.0

    elif decision == "Prefer Bus":
        settings.transfer_cost = 0.0
        settings.bus_stop_cost = 0.0
        settings.train_stop_cost = 99.0

    elif decision == "Prefer Train":
        settings.transfer_cost = 0.0
        settings.bus_stop_cost = 99.0
        settings.train_stop_cost = 0.0

    # Create Map Object
    base = folium.Map(location=[1.407201, 103.908402], zoom_start=15, min_zoom=14)

    # Get all the HDB and bus stops points down on the map
    base = getMap(base)

    if os.path.exists('data/output.txt'):
        os.remove('data/output.txt')

    # Get the route with the path
    base = routePlanner(base, start, end)

    # check if exisiting file exist
    if os.path.exists('templates/route.html'):
        os.remove('templates/route.html')

    # Generate Map
    base.save("templates/route.html")

    # Open file
    current_directory = pathlib.Path(__file__).parent.absolute()
    output_url = str(current_directory) + "/data/output.txt"
    webbrowser.get("windows-default").open(output_url, new=2)  # open in new tab

    return redirect(request.referrer)


@app.route('/map')
def map():
    if os.path.exists('templates/route.html'):
        return render_template('route.html')
    else:
        return render_template('base_Map.html')


# To start the app
if __name__ == '__main__':
    app.run(debug=True)
