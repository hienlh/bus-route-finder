# -*- coding: utf-8 -*-
import heapq
import json
import math
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass

@dataclass
class Station:
    """Thông tin trạm xe buýt"""
    id: int
    name: str
    address: str
    lat: float
    lng: float

@dataclass
class RouteInfo:
    """Thông tin tuyến xe buýt"""
    route_id: int
    route_no: str
    route_name: str
    distance: int
    normal_ticket: int
    time_of_trip: int

@dataclass
class Edge:
    """Cạnh trong đồ thị (kết nối giữa 2 trạm)"""
    neighbor: int
    weight: float
    route_id: int
    route_no: str

@dataclass
class PathStep:
    """Một bước trong đường đi"""
    station_id: int
    station_name: str
    station_address: str
    route_info: Optional[Dict] = None

@dataclass
class PathResult:
    """Kết quả tìm đường"""
    found: bool
    path: List[PathStep] = None
    routes: List[Dict] = None
    total_weight: float = 0.0
    total_stations: int = 0
    total_routes: int = 0
    summary: str = ""
    message: str = ""

class BusRouteGraph:
    """Đồ thị hệ thống xe buýt sử dụng thuật toán Dijkstra"""
    
    def __init__(self):
        self.stations: Dict[int, Station] = {}
        self.graph: Dict[int, List[Edge]] = {}
        self.routes: Dict[int, RouteInfo] = {}
    
    def add_route(self, route_data: Dict):
        """Thêm tuyến xe buýt vào đồ thị"""
        route_id = route_data['routeId']
        
        # Xử lý timeOfTrip - có thể là string hoặc number
        time_of_trip = route_data.get('timeOfTrip', '30')
        if isinstance(time_of_trip, str):
            # Nếu là string, thử parse số đầu tiên (trước dấu - hoặc khoảng trắng)
            try:
                time_of_trip = int(time_of_trip.split('-')[0].split()[0])
            except (ValueError, IndexError):
                time_of_trip = 30  # Giá trị mặc định
        
        # Thêm thông tin tuyến
        self.routes[route_id] = RouteInfo(
            route_id=route_id,
            route_no=route_data['routeNo'],
            route_name=route_data['routeName'],
            distance=route_data['distance'],
            normal_ticket=route_data.get('normalTicketNum', 5000),
            time_of_trip=time_of_trip
        )
        
        # Thêm các trạm vào danh sách stations
        for station in route_data['stations']:
            station_id = station['stationId']
            self.stations[station_id] = Station(
                id=station_id,
                name=station['stationName'],
                address=station['stationAddress'],
                lat=station['lat'],
                lng=station['lng']
            )
            
            # Khởi tạo danh sách kề nếu chưa có
            if station_id not in self.graph:
                self.graph[station_id] = []
        
        # Tạo các cạnh trong đồ thị
        # Chia stations theo hướng (direction)
        forward_stations = [s for s in route_data['stations'] if s['stationDirection'] == 0]
        backward_stations = [s for s in route_data['stations'] if s['stationDirection'] == 1]
        
        # Sắp xếp theo thứ tự trạm
        forward_stations.sort(key=lambda x: x['stationOrder'])
        backward_stations.sort(key=lambda x: x['stationOrder'])
        
        # Thêm cạnh cho cả hai hướng
        self._add_edges_for_direction(forward_stations, route_id)
        self._add_edges_for_direction(backward_stations, route_id)
    
    def _add_edges_for_direction(self, stations: List[Dict], route_id: int):
        """Thêm cạnh cho một hướng cụ thể"""
        for i in range(len(stations) - 1):
            current_station = stations[i]
            next_station = stations[i + 1]
            
            # Tính trọng số dựa trên khoảng cách giữa 2 trạm liên tiếp
            weight = self._calculate_weight(
                current_station['lat'], current_station['lng'],
                next_station['lat'], next_station['lng'],
                route_id
            )
            
            # Thêm cạnh từ trạm hiện tại đến trạm tiếp theo
            edge = Edge(
                neighbor=next_station['stationId'],
                weight=weight,
                route_id=route_id,
                route_no=self.routes[route_id].route_no
            )
            
            self.graph[current_station['stationId']].append(edge)
    
    def _calculate_weight(self, lat1: float, lng1: float, lat2: float, lng2: float, route_id: int) -> float:
        """Tính trọng số giữa 2 trạm (khoảng cách + thời gian + chi phí)"""
        # Tính khoảng cách Haversine (km)
        distance = self._haversine_distance(lat1, lng1, lat2, lng2)
        
        route = self.routes[route_id]
        ticket_price = route.normal_ticket / 1000  # Chuyển về nghìn đồng
        time_per_km = route.time_of_trip / (route.distance / 1000)  # phút/km
        
        # Trọng số tổng hợp: khoảng cách (km) + thời gian (phút) * 0.1 + giá vé * 0.01
        return distance + (time_per_km * distance * 0.1) + (ticket_price * 0.01)
    
    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Tính khoảng cách Haversine giữa 2 điểm"""
        R = 6371  # Bán kính Trái Đất (km)
        
        # Chuyển đổi sang radian
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Tính hiệu số
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        # Công thức Haversine
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def dijkstra(self, start_station_id: int, end_station_id: int) -> PathResult:
        """Thuật toán Dijkstra tìm đường đi ngắn nhất"""
        
        # Kiểm tra tính hợp lệ của đầu vào
        if start_station_id not in self.stations or end_station_id not in self.stations:
            return PathResult(
                found=False,
                message='Trạm không tồn tại trong hệ thống'
            )
        
        # Khởi tạo
        distances = {station_id: float('inf') for station_id in self.stations}
        distances[start_station_id] = 0
        
        previous = {station_id: None for station_id in self.stations}
        visited = set()
        
        # Priority queue: (distance, station_id)
        pq = [(0, start_station_id)]
        
        while pq:
            current_distance, current_station = heapq.heappop(pq)
            
            if current_station in visited:
                continue
                
            visited.add(current_station)
            
            # Nếu đã đến đích, dừng lại
            if current_station == end_station_id:
                break
            
            # Kiểm tra các trạm kề
            for edge in self.graph.get(current_station, []):
                neighbor_id = edge.neighbor
                weight = edge.weight
                
                if neighbor_id in visited:
                    continue
                
                new_distance = current_distance + weight
                
                if new_distance < distances[neighbor_id]:
                    distances[neighbor_id] = new_distance
                    previous[neighbor_id] = {
                        'station_id': current_station,
                        'route_id': edge.route_id,
                        'route_no': edge.route_no
                    }
                    heapq.heappush(pq, (new_distance, neighbor_id))
        
        # Xây dựng đường đi
        return self._build_path(start_station_id, end_station_id, distances, previous)
    
    def _build_path(self, start_station_id: int, end_station_id: int, 
                   distances: Dict[int, float], previous: Dict[int, Optional[Dict]]) -> PathResult:
        """Xây dựng đường đi từ kết quả Dijkstra"""
        
        total_distance = distances[end_station_id]
        
        if total_distance == float('inf'):
            return PathResult(
                found=False,
                message='Không tìm thấy đường đi giữa hai trạm này'
            )
        
        # Truy vết đường đi
        path = []
        routes = []
        current_station = end_station_id
        
        while current_station is not None:
            station_info = self.stations[current_station]
            prev_info = previous[current_station]
            
            path_step = PathStep(
                station_id=current_station,
                station_name=station_info.name,
                station_address=station_info.address,
                route_info={
                    'route_id': prev_info['route_id'],
                    'route_no': prev_info['route_no']
                } if prev_info else None
            )
            
            path.insert(0, path_step)
            
            # Thu thập thông tin tuyến
            if prev_info and prev_info['route_id']:
                route_exists = any(r['route_id'] == prev_info['route_id'] for r in routes)
                if not route_exists:
                    route_info = self.routes[prev_info['route_id']]
                    routes.append({
                        'route_id': prev_info['route_id'],
                        'route_no': prev_info['route_no'],
                        'route_name': route_info.route_name
                    })
            
            current_station = prev_info['station_id'] if prev_info else None
        
        # Đảo ngược danh sách routes để có thứ tự đúng
        routes.reverse()
        
        return PathResult(
            found=True,
            path=path,
            routes=routes,
            total_weight=round(total_distance, 3),
            total_stations=len(path),
            total_routes=len(routes),
            summary=self._generate_summary(path, routes)
        )
    
    def _generate_summary(self, path: List[PathStep], routes: List[Dict]) -> str:
        """Tạo tóm tắt hành trình"""
        if len(path) < 2:
            return 'Không có hành trình hợp lệ'
        
        summary = f"Hành trình từ {path[0].station_name} đến {path[-1].station_name}:\n"
        summary += f"- Số trạm: {len(path)}\n"
        summary += f"- Số tuyến cần chuyển: {len(routes)}\n"
        
        if routes:
            summary += "\nCác tuyến xe cần đi:\n"
            for i, route in enumerate(routes):
                summary += f"{i + 1}. Tuyến {route['route_no']}: {route['route_name']}\n"
        
        return summary
    
    def search_stations(self, keyword: str) -> List[Dict]:
        """Tìm tất cả trạm có tên chứa từ khóa"""
        results = []
        search_term = keyword.lower()
        
        for station_id, station in self.stations.items():
            if (search_term in station.name.lower() or 
                search_term in station.address.lower()):
                results.append({
                    'id': station_id,
                    'name': station.name,
                    'address': station.address
                })
        
        return results
    
    def get_station_info(self, station_id: int) -> Optional[Dict]:
        """Lấy thông tin chi tiết một trạm"""
        if station_id not in self.stations:
            return None
        
        station = self.stations[station_id]
        connected_routes = set()
        
        for edge in self.graph.get(station_id, []):
            connected_routes.add(edge.route_id)
        
        route_info = []
        for route_id in connected_routes:
            route = self.routes[route_id]
            route_info.append({
                'route_id': route_id,
                'route_no': route.route_no,
                'route_name': route.route_name
            })
        
        return {
            'id': station.id,
            'name': station.name,
            'address': station.address,
            'lat': station.lat,
            'lng': station.lng,
            'connected_routes': route_info
        }
    
    def load_route_from_file(self, file_path: str):
        """Load tuyến xe từ file JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                route_data = json.load(f)
                self.add_route(route_data)
                print(f"✅ Đã load tuyến {route_data['routeNo']}: {route_data['routeName']}")
        except Exception as e:
            print(f"❌ Lỗi khi load file {file_path}: {e}")
    
    def load_multiple_routes(self, file_paths: List[str]):
        """Load nhiều tuyến xe từ danh sách file"""
        for file_path in file_paths:
            self.load_route_from_file(file_path)
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê hệ thống"""
        total_edges = sum(len(edges) for edges in self.graph.values())
        
        return {
            'total_stations': len(self.stations),
            'total_routes': len(self.routes),
            'total_connections': total_edges,
            'average_connections_per_station': round(total_edges / len(self.stations), 2) if self.stations else 0
        }
    
    def load_all_routes_from_folder(self, folder_path: str = "routes"):
        """Load tất cả tuyến xe từ thư mục routes"""
        try:
            # Tìm tất cả file JSON trong thư mục routes
            json_files = glob.glob(os.path.join(folder_path, "*.json"))
            
            if not json_files:
                print(f"❌ Không tìm thấy file JSON nào trong thư mục {folder_path}")
                return
            
            print(f"📁 Tìm thấy {len(json_files)} file tuyến xe:")
            
            loaded_count = 0
            for file_path in sorted(json_files):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        route_data = json.load(f)
                    
                    # Thêm tuyến vào hệ thống
                    self.add_route(route_data)
                    loaded_count += 1
                    
                    print(f"✅ Đã load tuyến {route_data['routeNo']}: {route_data['routeName']}")
                    
                except Exception as e:
                    print(f"❌ Lỗi khi load file {file_path}: {e}")
            
            print(f"\n🎉 Hoàn thành! Đã load {loaded_count}/{len(json_files)} tuyến xe thành công.")
            
        except Exception as e:
            print(f"❌ Lỗi khi load thư mục {folder_path}: {e}")

    def draw_route_graph(self, path_result: PathResult = None, show_all_stations: bool = True):
        """Vẽ đồ thị tuyến xe buýt và đường đi tìm được"""
        try:
            # Tạo figure và axis
            fig, ax = plt.subplots(figsize=(15, 12))
            
            # Lấy tọa độ của tất cả trạm
            all_lats = [station.lat for station in self.stations.values()]
            all_lngs = [station.lng for station in self.stations.values()]
            
            # Vẽ tất cả các trạm
            if show_all_stations:
                ax.scatter(all_lngs, all_lats, c='lightgray', s=20, alpha=0.6, label='Tất cả trạm')
            
            # Vẽ các tuyến xe
            route_colors = {}
            color_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                           '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
            
            for route_id, route_info in self.routes.items():
                if route_id not in route_colors:
                    route_colors[route_id] = color_palette[len(route_colors) % len(color_palette)]
                
                # Tìm các trạm thuộc tuyến này
                route_stations = []
                for station_id, edges in self.graph.items():
                    for edge in edges:
                        if edge.route_id == route_id:
                            station = self.stations[station_id]
                            route_stations.append((station.lng, station.lat))
                            break
                
                if route_stations:
                    route_lngs, route_lats = zip(*route_stations)
                    ax.scatter(route_lngs, route_lats, c=route_colors[route_id], 
                             s=30, alpha=0.8, label=f'Tuyến {route_info.route_no}')
            
            # Vẽ đường đi nếu có
            if path_result and path_result.found:
                path_lngs = []
                path_lats = []
                path_colors = []
                
                for i, step in enumerate(path_result.path):
                    station = self.stations[step.station_id]
                    path_lngs.append(station.lng)
                    path_lats.append(station.lat)
                    
                    # Màu sắc dựa trên tuyến
                    if step.route_info:
                        route_id = step.route_info['route_id']
                        path_colors.append(route_colors.get(route_id, '#FF0000'))
                    else:
                        path_colors.append('#FF0000')
                
                # Vẽ đường đi
                for i in range(len(path_lngs) - 1):
                    ax.plot([path_lngs[i], path_lngs[i+1]], [path_lats[i], path_lats[i+1]], 
                           color=path_colors[i], linewidth=3, alpha=0.8)
                
                # Vẽ các trạm trên đường đi
                ax.scatter(path_lngs, path_lats, c=path_colors, s=100, 
                          edgecolors='black', linewidth=2, zorder=5, label='Đường đi')
                
                # Đánh dấu trạm bắt đầu và kết thúc
                ax.scatter(path_lngs[0], path_lats[0], c='green', s=200, 
                          marker='s', edgecolors='black', linewidth=2, zorder=6, label='Điểm xuất phát')
                ax.scatter(path_lngs[-1], path_lats[-1], c='red', s=200, 
                          marker='s', edgecolors='black', linewidth=2, zorder=6, label='Điểm đích')
                
                # Thêm nhãn cho các trạm quan trọng
                for i, step in enumerate(path_result.path):
                    if i == 0 or i == len(path_result.path) - 1 or step.route_info:
                        station = self.stations[step.station_id]
                        ax.annotate(step.station_name, (station.lng, station.lat), 
                                  xytext=(5, 5), textcoords='offset points', 
                                  fontsize=8, bbox=dict(boxstyle='round,pad=0.3', 
                                  facecolor='white', alpha=0.8))
            
            # Cấu hình đồ thị
            ax.set_xlabel('Kinh độ (Longitude)')
            ax.set_ylabel('Vĩ độ (Latitude)')
            ax.set_title('Bản đồ tuyến xe buýt TP.HCM\n' + 
                        (f'Đường đi từ {path_result.path[0].station_name} đến {path_result.path[-1].station_name}' 
                         if path_result and path_result.found else ''))
            
            # Thêm legend
            if show_all_stations:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Căn chỉnh layout
            plt.tight_layout()
            
            # Hiển thị đồ thị
            plt.show()
            
        except ImportError:
            print("❌ Cần cài đặt matplotlib để vẽ đồ thị:")
            print("pip install matplotlib")
        except Exception as e:
            print(f"❌ Lỗi khi vẽ đồ thị: {e}")

def demonstrate_bus_system():
    """Demo hệ thống xe buýt với nhập liệu từ người dùng"""
    
    # Tạo hệ thống
    bus_system = BusRouteGraph()
    
    print('=' * 60)
    print('HỆ THỐNG XE BUÝT TP.HCM - THUẬT TOÁN DIJKSTRA')
    print('=' * 60)
    
    # Load tất cả tuyến từ thư mục routes
    print("\n📂 LOADING DỮ LIỆU TỪ THƯ MỤC ROUTES...")
    bus_system.load_all_routes_from_folder()
    
    # Hiển thị thống kê hệ thống
    stats = bus_system.get_statistics()
    print(f"\n📊 THỐNG KÊ HỆ THỐNG:")
    print(f"- Tổng số trạm: {stats['total_stations']}")
    print(f"- Tổng số tuyến: {stats['total_routes']}")
    print(f"- Tổng số kết nối: {stats['total_connections']}")
    print(f"- Trung bình kết nối/trạm: {stats['average_connections_per_station']}")
    
    # --- Nhập liệu từ người dùng ---
    def select_station(prompt):
        while True:
            user_input = input(prompt)
            # Thử parse ID
            try:
                station_id = int(user_input)
                if station_id in bus_system.stations:
                    return station_id
                else:
                    print("❌ Không tìm thấy trạm với ID này. Hãy thử lại.")
                    continue
            except ValueError:
                # Tìm theo tên
                matches = bus_system.search_stations(user_input)
                if not matches:
                    print("❌ Không tìm thấy trạm nào phù hợp với từ khóa này. Hãy thử lại.")
                    continue
                elif len(matches) == 1:
                    print(f"✅ Đã chọn: {matches[0]['name']} (ID: {matches[0]['id']})")
                    return matches[0]['id']
                else:
                    print("🔎 Có nhiều trạm phù hợp:")
                    for idx, st in enumerate(matches):
                        print(f"{idx+1}. {st['name']} (ID: {st['id']}) - {st['address']}")
                    while True:
                        sel = input(f"Chọn số thứ tự trạm (1-{len(matches)}): ")
                        try:
                            sel_idx = int(sel) - 1
                            if 0 <= sel_idx < len(matches):
                                return matches[sel_idx]['id']
                            else:
                                print("Số thứ tự không hợp lệ. Hãy thử lại.")
                        except ValueError:
                            print("Vui lòng nhập số hợp lệ.")
    
    print("\n💡 Bạn có thể nhập tên hoặc ID trạm. Nếu nhập tên, hệ thống sẽ gợi ý các trạm phù hợp.")
    start_id = select_station("Nhập tên hoặc ID trạm xuất phát: ")
    end_id = select_station("Nhập tên hoặc ID trạm đích: ")
    
    print(f"\n🔍 TÌM ĐƯỜNG ĐI TỪ {bus_system.stations[start_id].name} ĐẾN {bus_system.stations[end_id].name}:")
    result = bus_system.dijkstra(start_id, end_id)
    if result.found:
        print('✅ Tìm thấy đường đi!\n')
        print('📍 THÔNG TIN HÀNH TRÌNH:')
        print(f"- Từ: {result.path[0].station_name}")
        print(f"- Đến: {result.path[-1].station_name}")
        print(f"- Tổng trọng số: {result.total_weight}")
        print(f"- Số trạm: {result.total_stations}")
        print(f"- Số tuyến: {result.total_routes}\n")
        print('🚌 CHI TIẾT ĐƯỜNG ĐI:')
        for i, step in enumerate(result.path):
            route_info = f" [Tuyến {step.route_info['route_no']}]" if step.route_info else ''
            print(f"{i + 1:2d}. {step.station_name}{route_info}")
            print(f"     📍 {step.station_address}")
        print(f"\n📋 TÓM TẮT:")
        print(result.summary)
        
        # Vẽ đồ thị
        print(f"\n🎨 VẼ BẢN ĐỒ TUYẾN XE...")
        bus_system.draw_route_graph(result)
        
    else:
        print(f'❌ {result.message}')
    return bus_system

# Hàm tiện ích để sử dụng
def find_shortest_path(bus_system: BusRouteGraph, start_id: int, end_id: int):
    """Tìm đường đi ngắn nhất và in kết quả"""
    result = bus_system.dijkstra(start_id, end_id)
    
    if result.found:
        print(f"✅ Đường đi từ trạm {start_id} đến trạm {end_id}:")
        print(f"Trọng số: {result.total_weight}, Số trạm: {result.total_stations}")
        
        for i, step in enumerate(result.path):
            route_info = f" [Tuyến {step.route_info['route_no']}]" if step.route_info else ''
            print(f"{i + 1}. {step.station_name}{route_info}")
    else:
        print(f"❌ {result.message}")

if __name__ == "__main__":
    # Chạy demo
    bus_system = demonstrate_bus_system()