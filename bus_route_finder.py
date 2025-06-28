import heapq
import json
from math import radians, sin, cos, sqrt, atan2
import os

# Hàm tính khoảng cách Haversine (km)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Bán kính Trái Đất (km)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Lớp đại diện cho trạm xe buýt
class BusStop:
    def __init__(self, station_id, name, lat, lng, route_no, address=""):
        self.station_id = station_id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.route_no = route_no  # Tuyến đi qua trạm
        self.address = address  # Địa chỉ trạm

# Hàm đọc dữ liệu từ nhiều file JSON
def load_routes(route_files):
    stops = []
    routes = {}
    for route_file in route_files:
        data = json.loads(route_file)
        route_no = data['routeNo']
        routes[route_no] = []
        
        # Tạo danh sách trạm cho tuyến
        for station in sorted(data['stations'], key=lambda x: x['stationOrder']):
            if station['stationDirection'] == 0:  # Chỉ lấy chiều đi
                stop = BusStop(
                    station['stationId'],
                    station['stationName'],
                    station['lat'],
                    station['lng'],
                    route_no,
                    station.get('stationAddress', '')  # Lấy địa chỉ, mặc định là chuỗi rỗng nếu không có
                )
                stops.append(stop)
                routes[route_no].append(station['stationId'])
    
    return stops, routes

# Hàm xây dựng đồ thị
def build_graph(stops, routes):
    graph = {}
    stop_dict = {stop.station_id: stop for stop in stops}
    
    # Kết nối các trạm liên tiếp trong mỗi tuyến
    for route_no, stop_sequence in routes.items():
        for i in range(len(stop_sequence) - 1):
            stop1_id = stop_sequence[i]
            stop2_id = stop_sequence[i + 1]
            if stop1_id in stop_dict and stop2_id in stop_dict:
                stop1 = stop_dict[stop1_id]
                stop2 = stop_dict[stop2_id]
                distance = haversine(stop1.lat, stop1.lng, stop2.lat, stop2.lng)
                time = distance * 2  # Giả định tốc độ 30 km/h (phút)
                
                if stop1_id not in graph:
                    graph[stop1_id] = []
                graph[stop1_id].append((stop2_id, time, route_no))
                
                if stop2_id not in graph:
                    graph[stop2_id] = []
                graph[stop2_id].append((stop1_id, time, route_no))
    
    # Kết nối các trạm chung tuyến (chuyển tuyến)
    for stop1 in stops:
        for stop2 in stops:
            if stop1.station_id != stop2.station_id and stop1.route_no != stop2.route_no:
                distance = haversine(stop1.lat, stop1.lng, stop2.lat, stop2.lng)
                if distance < 0.5:  # Giả định trạm chuyển tuyến cách nhau < 500m
                    time = distance * 2 + 5  # Thêm 5 phút chờ chuyển tuyến
                    if stop1.station_id not in graph:
                        graph[stop1.station_id] = []
                    graph[stop1.station_id].append((stop2.station_id, time, f"Chuyển tuyến từ {stop1.route_no} sang {stop2.route_no}"))

    return graph, stop_dict

# Hàm heuristic
def heuristic(stop_id, goal_id, stop_dict):
    stop1 = stop_dict[stop_id]
    stop2 = stop_dict[goal_id]
    distance = haversine(stop1.lat, stop1.lng, stop2.lat, stop2.lng)
    return distance * 2  # Thời gian ước lượng (phút)

# Thuật toán A*
def a_star(start_id, goal_id, graph, stop_dict):
    queue = [(0, 0, start_id, [], [])]  # (f, g, node, path, routes)
    visited = set()
    
    while queue:
        f, g, node, path, route_path = heapq.heappop(queue)
        state = (node, tuple(route_path[-1:]))
        if state in visited:
            continue
        visited.add(state)
        
        path = path + [node]
        
        if node == goal_id:
            return path, route_path, g
        
        for neighbor, cost, route_info in graph.get(node, []):
            if (neighbor, route_info) not in visited:
                new_g = g + cost
                h = heuristic(neighbor, goal_id, stop_dict)
                f = new_g + h
                new_route_path = route_path + [route_info]
                heapq.heappush(queue, (f, new_g, neighbor, path, new_route_path))
    
    return None, None, float('inf')

# Thuật toán Dijkstra
def dijkstra(start_id, goal_id, graph, stop_dict):
    queue = [(0, start_id, [], [])]  # (g, node, path, routes)
    visited = set()
    
    while queue:
        g, node, path, route_path = heapq.heappop(queue)
        state = (node, tuple(route_path[-1:]))
        if state in visited:
            continue
        visited.add(state)
        
        path = path + [node]
        
        if node == goal_id:
            return path, route_path, g
        
        for neighbor, cost, route_info in graph.get(node, []):
            if (neighbor, route_info) not in visited:
                new_g = g + cost
                new_route_path = route_path + [route_info]
                heapq.heappush(queue, (new_g, neighbor, path, new_route_path))
    
    return None, None, float('inf')

folder_path = 'routes'
route_files = []
for filename in os.listdir(folder_path):
    with open(os.path.join(folder_path, filename), 'r') as f:
        route_files.append(f.read())

# Tải dữ liệu
stops, routes = load_routes(route_files)

# Xây dựng đồ thị
graph, stop_dict = build_graph(stops, routes)

# Tìm trạm gần Chợ Bến Thành và ĐH Quốc gia nhất
# def find_nearest_stop(target_lat, target_lng, stops):
#     min_distance = float('inf')
#     nearest_stop = None
#     for stop in stops:
#         distance = haversine(stop.lat, stop.lng, target_lat, target_lng)
#         if distance < min_distance:
#             min_distance = distance
#             nearest_stop = stop
#     return nearest_stop

# # Tọa độ Chợ Bến Thành và ĐH Quốc gia
# ben_thanh = (10.77255, 106.6983)
# dhqg = (10.87362, 106.803042)

# start_stop = find_nearest_stop(ben_thanh[0], ben_thanh[1], stops)
# goal_stop = find_nearest_stop(dhqg[0], dhqg[1], stops)

# --- New code for user selection ---

def get_unique_stations(stops):
    seen = set()
    unique = []
    for stop in stops:
        if stop.station_id not in seen:
            unique.append(stop)
            seen.add(stop.station_id)
    return unique

unique_stops = get_unique_stations(stops)

# print("Danh sách các trạm xe buýt:")
# for idx, stop in enumerate(unique_stops):
#     print(f"{idx+1}. {stop.name} (ID: {stop.station_id}, Tuyến: {stop.route_no})")

# while True:
#     try:
#         start_idx = int(input("\nNhập số thứ tự trạm bắt đầu: ")) - 1
#         end_idx = int(input("Nhập số thứ tự trạm kết thúc: ")) - 1
#         if 0 <= start_idx < len(unique_stops) and 0 <= end_idx < len(unique_stops):
#             break
#         else:
#             print("Số thứ tự không hợp lệ. Vui lòng thử lại.")
#     except ValueError:
#         print("Vui lòng nhập số hợp lệ.")

# start_stop = unique_stops[start_idx]
# goal_stop = unique_stops[end_idx]
# --- End user selection ---

# Tìm đường đi
# path, route_path, total_time = a_star(start_stop.station_id, goal_stop.station_id, graph, stop_dict)
# path, route_path, total_time = dijkstra(start_stop.station_id, goal_stop.station_id, graph, stop_dict)

# # In kết quả
# if path:
#     print("Đường đi tối ưu:")
#     current_route = None
#     for i, (stop_id, route) in enumerate(zip(path, route_path)):
#         stop_name = stop_dict[stop_id].name
#         if "Transfer" in route:
#             print(f"Chuyển tuyến tại {stop_name}: {route}")
#         elif route != current_route:
#             print(f"Lên xe tuyến {route} tại {stop_name}")
#             current_route = route
#         else:
#             print(f"Đi qua {stop_name}")
#     print(f"Thời gian ước tính: {total_time:.2f} phút")
# else:
#     print("Không tìm thấy đường đi.")