"""
Mock hotel data for development and testing purposes.
"""

MOCK_HOTELS = [
    {
        "id": "TPE001",
        "name": "台北豪華大飯店",
        "address": "台北市信義區忠孝東路五段10號",
        "district": "信義區",
        "county": "台北市",
        "type": "五星級酒店",
        "price_range": {"min": 3500, "max": 8000},
        "rating": 4.8,
        "facilities": ["游泳池", "健身房", "SPA", "商務中心", "餐廳", "會議室"],
        "room_types": [
            {
                "name": "豪華雙人房",
                "capacity": 2,
                "price": 4500,
                "bed_type": "King",
                "facilities": ["mini吧", "浴缸", "免費Wi-Fi", "電視"],
                "available": True
            },
            {
                "name": "行政套房",
                "capacity": 2,
                "price": 7500,
                "bed_type": "King",
                "facilities": ["mini吧", "浴缸", "免費Wi-Fi", "電視", "客廳", "行政酒廊"],
                "available": True
            }
        ],
        "description": "台北豪華大飯店位於台北市信義區的核心地帶，距離台北101和信義商圈僅幾分鐘步行路程。飯店提供豪華住宿、精緻餐飲和一流設施，是商務和休閒旅客的理想之選。",
        "images": ["url_to_image1", "url_to_image2"],
        "location": {
            "latitude": 25.0339639,
            "longitude": 121.5644722
        }
    },
    {
        "id": "TPE002",
        "name": "台北舒適商旅",
        "address": "台北市大安區復興南路一段20號",
        "district": "大安區",
        "county": "台北市",
        "type": "精品商旅",
        "price_range": {"min": 2200, "max": 4500},
        "rating": 4.5,
        "facilities": ["免費早餐", "健身房", "商務中心", "洗衣服務"],
        "room_types": [
            {
                "name": "標準雙人房",
                "capacity": 2,
                "price": 2500,
                "bed_type": "Queen",
                "facilities": ["免費Wi-Fi", "電視", "冰箱"],
                "available": True
            },
            {
                "name": "商務單人房",
                "capacity": 1,
                "price": 2200,
                "bed_type": "Single",
                "facilities": ["免費Wi-Fi", "電視", "書桌", "咖啡機"],
                "available": True
            }
        ],
        "description": "台北舒適商旅位於台北市大安區，提供現代化客房和實用設施，適合商務旅客。飯店鄰近捷運站，交通便利，可輕鬆抵達台北各大景點。",
        "images": ["url_to_image1", "url_to_image2"],
        "location": {
            "latitude": 25.0329694,
            "longitude": 121.5438033
        }
    },
    {
        "id": "TPE003",
        "name": "台北家庭旅店",
        "address": "台北市文山區木柵路一段100號",
        "district": "文山區",
        "county": "台北市",
        "type": "經濟型旅館",
        "price_range": {"min": 1500, "max": 3000},
        "rating": 4.2,
        "facilities": ["免費停車", "免費Wi-Fi", "共用廚房"],
        "room_types": [
            {
                "name": "家庭四人房",
                "capacity": 4,
                "price": 2800,
                "bed_type": "Two Double",
                "facilities": ["免費Wi-Fi", "電視", "冰箱", "微波爐"],
                "available": True
            },
            {
                "name": "經濟雙人房",
                "capacity": 2,
                "price": 1800,
                "bed_type": "Double",
                "facilities": ["免費Wi-Fi", "電視"],
                "available": True
            }
        ],
        "description": "台北家庭旅店是一家溫馨的住宿選擇，尤其適合家庭旅遊。位於台北市文山區，環境寧靜，鄰近貓空纜車站，方便遊客探索台北的自然風光。",
        "images": ["url_to_image1", "url_to_image2"],
        "location": {
            "latitude": 24.9880223,
            "longitude": 121.5661233
        }
    }
]


def get_all_hotels():
    """Return all mock hotels."""
    return MOCK_HOTELS


def get_hotel_by_id(hotel_id):
    """Find a hotel by its ID."""
    for hotel in MOCK_HOTELS:
        if hotel["id"] == hotel_id:
            return hotel
    return None


def search_hotels(district=None, hotel_type=None, min_price=None, max_price=None, facilities=None):
    """Search hotels based on criteria."""
    results = MOCK_HOTELS.copy()
    
    if district:
        results = [h for h in results if h["district"] == district]
    
    if hotel_type:
        results = [h for h in results if h["type"] == hotel_type]
    
    if min_price is not None:
        results = [h for h in results if h["price_range"]["min"] >= min_price]
    
    if max_price is not None:
        results = [h for h in results if h["price_range"]["max"] <= max_price]
    
    if facilities and isinstance(facilities, list):
        results = [h for h in results if all(f in h["facilities"] for f in facilities)]
    
    return results 