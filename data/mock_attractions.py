"""
Mock attraction data for development and testing purposes.
"""

MOCK_ATTRACTIONS = [
    {
        "id": "ATT001",
        "name": "台北101",
        "address": "台北市信義區信義路五段7號",
        "district": "信義區",
        "county": "台北市",
        "type": "地標",
        "rating": 4.7,
        "description": "台北101是台灣台北市信義區的一棟摩天大樓，樓高508米，曾為世界第一高樓。大樓內有觀景台、高級餐廳和精品商場。",
        "visiting_hours": "上午9點至晚上10點",
        "admission_fee": 600,
        "popular_activities": ["觀景", "購物", "美食"],
        "recommended_time": 3,  # hours
        "images": ["url_to_image1", "url_to_image2"],
        "location": {
            "latitude": 25.033976,
            "longitude": 121.5644722
        }
    },
    {
        "id": "ATT002",
        "name": "國立故宮博物院",
        "address": "台北市士林區至善路二段221號",
        "district": "士林區",
        "county": "台北市",
        "type": "博物館",
        "rating": 4.8,
        "description": "國立故宮博物院是台灣最著名的博物館，收藏了近70萬件中國藝術品和文物，是世界上規模最大、內容最豐富的中華藝術寶庫之一。",
        "visiting_hours": "上午8點30分至下午6點30分",
        "admission_fee": 350,
        "popular_activities": ["參觀文物", "導覽", "文化學習"],
        "recommended_time": 4,  # hours
        "images": ["url_to_image1", "url_to_image2"],
        "location": {
            "latitude": 25.1023899,
            "longitude": 121.5482504
        }
    },
    {
        "id": "ATT003",
        "name": "陽明山國家公園",
        "address": "台北市陽明山竹子湖路1-20號",
        "district": "北投區",
        "county": "台北市",
        "type": "自然景點",
        "rating": 4.6,
        "description": "陽明山國家公園位於台北市北部，是台灣三大國家公園之一，以溫泉、火山地形和豐富的生態系統聞名。公園內有多條登山步道和知名的花季活動。",
        "visiting_hours": "全天開放",
        "admission_fee": 0,
        "popular_activities": ["遠足", "賞花", "溫泉", "野餐"],
        "recommended_time": 6,  # hours
        "images": ["url_to_image1", "url_to_image2"],
        "location": {
            "latitude": 25.1559892,
            "longitude": 121.5608641
        }
    },
    {
        "id": "ATT004",
        "name": "饒河街觀光夜市",
        "address": "台北市松山區饒河街",
        "district": "松山區",
        "county": "台北市",
        "type": "夜市",
        "rating": 4.5,
        "description": "饒河街觀光夜市是台北市最著名的夜市之一，提供各式各樣的台灣小吃、遊戲攤位和商品。夜市位於松山區，沿著饒河街延伸約600公尺。",
        "visiting_hours": "下午4點至凌晨12點",
        "admission_fee": 0,
        "popular_activities": ["品嚐小吃", "購物", "遊戲"],
        "recommended_time": 2,  # hours
        "images": ["url_to_image1", "url_to_image2"],
        "location": {
            "latitude": 25.0505033,
            "longitude": 121.5772474
        }
    },
    {
        "id": "ATT005",
        "name": "貓空纜車",
        "address": "台北市文山區新光路二段8號",
        "district": "文山區",
        "county": "台北市",
        "type": "交通景點",
        "rating": 4.4,
        "description": "貓空纜車連接台北市文山區與貓空茶園區，沿途可欣賞茶園和山林風光。纜車終點站附近有多家知名茶館和餐廳，是品茗和欣賞台北市景的理想地點。",
        "visiting_hours": "上午9點至晚上9點",
        "admission_fee": 120,
        "popular_activities": ["搭乘纜車", "喝茶", "遠足"],
        "recommended_time": 3,  # hours
        "images": ["url_to_image1", "url_to_image2"],
        "location": {
            "latitude": 24.9680503,
            "longitude": 121.5798684
        }
    }
]


def get_all_attractions():
    """Return all mock attractions."""
    return MOCK_ATTRACTIONS


def get_attraction_by_id(attraction_id):
    """Find an attraction by its ID."""
    for attraction in MOCK_ATTRACTIONS:
        if attraction["id"] == attraction_id:
            return attraction
    return None


def search_attractions(district=None, attraction_type=None, free_admission=None, recommended_time=None):
    """Search attractions based on criteria."""
    results = MOCK_ATTRACTIONS.copy()
    
    if district:
        results = [a for a in results if a["district"] == district]
    
    if attraction_type:
        results = [a for a in results if a["type"] == attraction_type]
    
    if free_admission is not None:
        if free_admission:
            results = [a for a in results if a["admission_fee"] == 0]
        else:
            results = [a for a in results if a["admission_fee"] > 0]
    
    if recommended_time is not None:
        results = [a for a in results if a["recommended_time"] <= recommended_time]
    
    return results


def get_nearby_attractions(latitude, longitude, radius_km=5):
    """Find attractions near a given location (very simplified)."""
    # This is a simplified version that doesn't actually calculate distances
    # In a real implementation, you would calculate haversine distance
    
    # Just return some attractions for demonstration
    if latitude > 25.0 and longitude > 121.5:
        return [a for a in MOCK_ATTRACTIONS if a["district"] in ["信義區", "松山區"]]
    else:
        return [a for a in MOCK_ATTRACTIONS if a["district"] in ["文山區", "士林區", "北投區"]] 