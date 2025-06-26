# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from bus_route_finder import load_routes, build_graph, a_star, BusStop
import os
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load data
folder_path = 'routes'
route_files = []
for filename in os.listdir(folder_path):
    with open(os.path.join(folder_path, filename), 'r') as f:
        route_files.append(f.read())

stops, routes = load_routes(route_files)
graph, stop_dict = build_graph(stops, routes)

def get_unique_stations(stops):
    seen = set()
    unique = []
    for stop in stops:
        if stop.station_id not in seen:
            unique.append(stop)
            seen.add(stop.station_id)
    return unique

@app.route('/stations', methods=['GET'])
def stations():
    unique_stops = get_unique_stations(stops)
    result = [
        {
            'id': stop.station_id,
            'name': stop.name,
            'route': stop.route_no,
            'lat': stop.lat,
            'lng': stop.lng,
            'address': stop.address
        }
        for stop in unique_stops
    ]
    return jsonify(result)

@app.route('/route', methods=['POST'])
def route():
    data = request.get_json()
    start_id = data.get('start_id')
    end_id = data.get('end_id')
    if not start_id or not end_id:
        return jsonify({'error': 'Missing start_id or end_id'}), 400
    if start_id not in stop_dict or end_id not in stop_dict:
        return jsonify({'error': 'Invalid station id'}), 400
    path, route_path, total_time = a_star(start_id, end_id, graph, stop_dict)
    if not path:
        return jsonify({'error': 'No route found'}), 404
    steps = []
    current_route = None
    for i, (stop_id, route_info) in enumerate(zip(path, route_path)):
        stop = stop_dict[stop_id]
        if 'Chuyển tuyến' in str(route_info):
            steps.append({
                'type': 'transfer',
                'station': stop.name,
                'route': stop.route_no,
                'address': stop.address,
                'details': route_info
            })
        elif route_info != current_route:
            steps.append({
                'type': 'start' if i == 0 else 'continue',
                'station': stop.name,
                'route': route_info,
                'address': stop.address,
                'details': 'Lên xe tuyến {} tại {}'.format(route_info, stop.name)
            })
            current_route = route_info
        else:
            steps.append({
                'type': 'pass',
                'station': stop.name,
                'route': route_info,
                'address': stop.address,
                'details': 'Đi qua {}'.format(stop.name)
            })
    # Add end step
    steps.append({
        'type': 'end',
        'station': stop_dict[path[-1]].name,
        'route': route_path[-1],
        'address': stop_dict[path[-1]].address,
        'details': 'Đến điểm đích'
    })
    return jsonify({
        'steps': steps,
        'totalTime': round(total_time, 2)
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000) 