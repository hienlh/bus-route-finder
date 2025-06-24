# Bus Route Finder

Ứng dụng tìm đường xe buýt tối ưu sử dụng thuật toán A* để tìm đường đi ngắn nhất giữa các trạm xe buýt.

## Tính năng

- Tìm đường đi tối ưu giữa hai trạm xe buýt
- Hỗ trợ chuyển tuyến
- Giao diện web thân thiện
- API RESTful
- Tính toán thời gian di chuyển dựa trên khoảng cách thực tế

## Cấu trúc dự án

```
thuat-toan/
├── bus_route_api.py      # Flask API server
├── bus_route_finder.py   # Thuật toán A* và xử lý dữ liệu
├── bus_route_ui.html     # Giao diện web
├── requirements.txt      # Dependencies Python
├── README.md            # Hướng dẫn sử dụng
└── routes/              # Dữ liệu tuyến xe buýt
    ├── route_1.json
    ├── route_3.json
    ├── route_4.json
    ├── route_5.json
    ├── route_6.json
    ├── route_7.json
    ├── route_8.json
    ├── route_9.json
    └── route_10.json
```

## Yêu cầu hệ thống

- Python 3.7+
- pip (Python package manager)

## Cài đặt

### 1. Clone hoặc tải dự án

```bash
git clone <repository-url>
cd thuat-toan
```

### 2. Tạo môi trường ảo (khuyến nghị)

```bash
# Trên macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Trên Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## Cách sử dụng

### 1. Khởi động API server

```bash
python bus_route_api.py
```

Server sẽ chạy tại `http://localhost:8000`

### 2. Mở giao diện web

Mở file `bus_route_ui.html` trong trình duyệt web hoặc truy cập trực tiếp file này.

### 3. Sử dụng ứng dụng

1. Chọn trạm bắt đầu từ dropdown
2. Chọn trạm đích từ dropdown
3. Nhấn "Tìm đường" để xem kết quả

## API Endpoints

### GET /stations
Lấy danh sách tất cả các trạm xe buýt

**Response:**
```json
[
  {
    "id": "station_id",
    "name": "Tên trạm",
    "route": "Tuyến số",
    "lat": 10.123456,
    "lng": 106.123456
  }
]
```

### POST /route
Tìm đường đi giữa hai trạm

**Request:**
```json
{
  "start_id": "station_id_1",
  "end_id": "station_id_2"
}
```

**Response:**
```json
{
  "steps": [
    {
      "type": "start",
      "station": "Tên trạm",
      "route": "Tuyến số",
      "details": "Mô tả"
    }
  ],
  "totalTime": 25.5
}
```

## Thuật toán

Ứng dụng sử dụng thuật toán A* để tìm đường đi tối ưu:

1. **Heuristic function**: Sử dụng khoảng cách Haversine để ước tính thời gian
2. **Graph construction**: Xây dựng đồ thị từ dữ liệu tuyến xe buýt
3. **Transfer detection**: Tự động phát hiện các trạm chuyển tuyến
4. **Route optimization**: Tìm đường đi ngắn nhất về thời gian

## Dữ liệu

Dữ liệu tuyến xe buýt được lưu trong thư mục `routes/` với định dạng JSON:

```json
{
  "routeNo": "1",
  "stations": [
    {
      "stationId": "station_1",
      "stationName": "Tên trạm",
      "lat": 10.123456,
      "lng": 106.123456,
      "stationOrder": 1,
      "stationDirection": 0
    }
  ]
}
```

## Troubleshooting

### Lỗi thường gặp

1. **Port 8000 đã được sử dụng**
   ```bash
   # Thay đổi port trong bus_route_api.py
   app.run(debug=True, port=8001)
   ```

2. **Lỗi import modules**
   ```bash
   # Đảm bảo đã cài đặt dependencies
   pip install -r requirements.txt
   ```

3. **CORS errors**
   - Đảm bảo Flask-CORS đã được cài đặt
   - Kiểm tra cấu hình CORS trong `bus_route_api.py`

## Đóng góp

1. Fork dự án
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## License

Dự án này được phát hành dưới MIT License.

## Liên hệ

Nếu có câu hỏi hoặc góp ý, vui lòng tạo issue trên repository.
