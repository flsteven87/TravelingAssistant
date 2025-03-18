"""
Coordinator agent for managing the multi-agent system.
"""
import asyncio
import sys
import os
import time
import logging
import json
from datetime import datetime

# Add parent directory to path to allow module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from utils.async_helper import run_tasks_with_priority, ProgressTracker
from autogen_agentchat.agents import AssistantAgent

# Configure logger
logger = logging.getLogger('traveling_assistant.coordinator')

class CoordinatorAgent(AssistantAgent):
    """
    Coordinator agent responsible for managing the multi-agent workflow.
    This agent coordinates between the hotel and itinerary agents, ensuring timely responses.
    """
    
    def __init__(self, name="Coordinator Agent", model_client=None, **kwargs):
        super().__init__(name=name, model_client=model_client, **kwargs)
        self.hotel_agent = None
        self.itinerary_agent = None
        self.user_proxy = None
        self.last_user_query = None
        self.logger = logging.getLogger('traveling_assistant.coordinator')
    
    def set_agents(self, hotel_agent, itinerary_agent, user_proxy):
        """Set the agents to coordinate."""
        self.hotel_agent = hotel_agent
        self.itinerary_agent = itinerary_agent
        self.user_proxy = user_proxy
        self.logger.info(f"Coordinator linked with: {hotel_agent.name}, {itinerary_agent.name}, {user_proxy.name}")
    
    async def on_messages(self, messages, cancellation_token=None):
        """
        Override the default on_messages method to provide custom coordination logic.
        This method is called when a message is received by the coordinator agent.
        """
        if not messages:
            return None
        
        # Get the last message
        last_message = messages[-1]
        message_content = last_message.get("content") if isinstance(last_message, dict) else (
            last_message.content if hasattr(last_message, "content") else str(last_message)
        )
        
        # 確定發送方
        sender = last_message.get("source") if isinstance(last_message, dict) else (
            last_message.source if hasattr(last_message, "source") else "unknown"
        )
        
        self.logger.info(f"Coordinator received message from {sender}")
        
        # 嘗試直接從消息中提取用戶偏好
        user_preferences = None
        if isinstance(last_message, dict) and "preferences" in last_message:
            user_preferences = last_message["preferences"]
            self.logger.info(f"Extracted preferences directly from message: {user_preferences.get('destination')}")
        # 作為備用，嘗試從用戶代理獲取偏好
        elif sender == self.user_proxy.name:
            self.logger.info("Trying to extract preferences from user proxy")
            user_preferences = self.user_proxy.process_user_query(message_content)
            self.logger.info(f"Extracted preferences from user proxy: {user_preferences.get('destination')}")
        
        self.last_user_query = message_content
        
        if not user_preferences or not user_preferences.get('destination'):
            self.logger.warning("No valid destination found in user preferences")
            return "請提供目的地信息，例如您打算去哪個城市或國家旅遊？"
        
        # 記錄完整的用戶偏好
        self.logger.info(f"Working with preferences: {json.dumps(user_preferences, ensure_ascii=False)}")
        
        # Coordinate the agents to generate a response
        try:
            result = await self._coordinate_workflow(user_preferences)
            return result
        except Exception as e:
            self.logger.error(f"Coordination error: {str(e)}", exc_info=True)
            return self._format_error_response(f"協調代理遇到問題: {str(e)}")
    
    async def _coordinate_workflow(self, user_preferences):
        """
        Coordinate the workflow between agents.
        This method handles the main coordination logic.
        """
        self.logger.info(f"Starting coordination workflow for destination: {user_preferences.get('destination')}")
        self.logger.info(f"User preferences: {json.dumps(user_preferences, ensure_ascii=False, indent=2)}")
        
        # Generate an initial response
        initial_response = self._format_initial_response()
        
        # Track response generation progress
        hotel_results = None
        attraction_results = None
        transportation_suggestions = None
        
        try:
            # Send initial response to user proxy
            self.logger.info("Sending initial response to user proxy...")
            # 調用用戶代理的 receive_response 方法
            try:
                # 首先嘗試同步調用
                self.user_proxy.receive_response(initial_response, is_initial=True)
            except Exception as e:
                # 如果同步調用失敗，嘗試異步調用
                self.logger.warning(f"同步調用 receive_response 失敗，嘗試異步調用: {str(e)}")
                await self.user_proxy.receive_response_async(initial_response, is_initial=True)
            self.logger.info("Sent initial response to user proxy")
            
            # Create progress tracker
            self.logger.info("Creating progress tracker")
            progress = ProgressTracker(
                total_steps=4,  # Get hotels, get attractions, get transportation, format response
                callback=self._progress_callback
            )
            
            # Define tasks with priorities (lower number = higher priority)
            self.logger.info("Defining initial tasks")
            tasks = {
                "hotel_recommendations": (
                    1,  # Priority 1 (highest)
                    self._get_hotel_recommendations(user_preferences)
                ),
                "initial_attractions": (
                    2,  # Priority 2
                    self._get_initial_attractions(user_preferences)
                )
            }
            
            # Run initial tasks with timeout for quick response
            self.logger.info(f"Running initial tasks with timeout: {config.INITIAL_RESPONSE_TIME}s")
            initial_results = await run_tasks_with_priority(
                tasks,
                timeout=config.INITIAL_RESPONSE_TIME
            )
            self.logger.info(f"Completed initial tasks. Results: {list(initial_results.keys())}")
            
            # Update progress
            if "hotel_recommendations" in initial_results:
                hotel_result = initial_results["hotel_recommendations"]
                if hotel_result and "recommendations" in hotel_result:
                    hotel_results = hotel_result["recommendations"]
                    self.logger.info(f"Got {len(hotel_results)} hotel recommendations")
                    self.logger.debug(f"Hotel recommendations: {json.dumps(hotel_results[:2], ensure_ascii=False, indent=2)}")
                    progress.update("hotel_recommendations", hotel_results)
                else:
                    self.logger.warning("Hotel recommendations missing or invalid format")
                    self.logger.debug(f"Raw hotel result: {json.dumps(hotel_result, ensure_ascii=False)}")
            else:
                self.logger.warning("No hotel recommendations in initial results")
            
            attraction_results = None
            if "initial_attractions" in initial_results:
                attraction_result = initial_results["initial_attractions"]
                if attraction_result and "attractions" in attraction_result:
                    attraction_results = attraction_result["attractions"]
                    self.logger.info(f"Got {len(attraction_results)} initial attractions")
                    self.logger.debug(f"Attraction recommendations: {json.dumps(attraction_results[:2], ensure_ascii=False, indent=2)}")
                    progress.update("initial_attractions", attraction_results)
                else:
                    self.logger.warning("Initial attractions missing or invalid format")
                    self.logger.debug(f"Raw attraction result: {json.dumps(attraction_result, ensure_ascii=False)}")
            else:
                self.logger.warning("No initial attractions in results")
            
            # Generate partial response
            self.logger.info("Generating partial response")
            partial_response = self._format_partial_response(
                hotel_results=hotel_results,
                attraction_results=attraction_results
            )
            
            # Send partial response
            self.logger.info("Sending partial response to user proxy")
            self.logger.debug(f"Partial response text: {partial_response[:200]}...")
            try:
                # 首先嘗試同步調用
                self.user_proxy.receive_response(partial_response)
            except Exception as e:
                # 如果同步調用失敗，嘗試異步調用
                self.logger.warning(f"同步調用 receive_response 失敗，嘗試異步調用: {str(e)}")
                await self.user_proxy.receive_response_async(partial_response)
            
            # Continue with complete processing
            # If we have hotel recommendations, use them to find better attractions
            selected_hotel = None
            if hotel_results and len(hotel_results) > 0:
                selected_hotel = hotel_results[0]  # Select the top-rated hotel
                self.logger.info(f"Selected top hotel: {selected_hotel.get('name')}")
            
            # Define the next tasks
            self.logger.info("Defining next tasks")
            next_tasks = {}
            
            # If we didn't get hotel results yet, add the task
            if not hotel_results:
                self.logger.info("Adding hotel task to next batch")
                next_tasks["hotel_recommendations"] = (
                    1,
                    self._get_hotel_recommendations(user_preferences)
                )
            
            # Always get detailed attractions, either based on hotel or general
            self.logger.info("Adding detailed attractions task")
            next_tasks["detailed_attractions"] = (
                2,
                self._get_detailed_attractions(user_preferences, selected_hotel)
            )
            
            # Add transportation task if we have both hotel and attractions
            if hotel_results and attraction_results:
                self.logger.info("Adding transportation task")
                next_tasks["transportation"] = (
                    3,
                    self._get_transportation_suggestions(selected_hotel, attraction_results[:3])
                )
            
            # Run the remaining tasks with a longer timeout
            remaining_time = config.COMPLETE_RESPONSE_TIME - config.INITIAL_RESPONSE_TIME
            self.logger.info(f"Running next tasks with timeout: {remaining_time}s")
            complete_results = await run_tasks_with_priority(
                next_tasks,
                timeout=remaining_time
            )
            self.logger.info(f"Completed next tasks. Results: {list(complete_results.keys())}")
            
            # Update progress with complete results
            if "hotel_recommendations" in complete_results and not hotel_results:
                hotel_result = complete_results["hotel_recommendations"]
                if hotel_result and "recommendations" in hotel_result:
                    hotel_results = hotel_result["recommendations"]
                    self.logger.info(f"Got {len(hotel_results)} hotel recommendations in second phase")
                    self.logger.debug(f"Hotel recommendations (phase 2): {json.dumps(hotel_results[:2], ensure_ascii=False, indent=2)}")
                    progress.update("hotel_recommendations", hotel_results)
            
            if "detailed_attractions" in complete_results:
                attraction_result = complete_results["detailed_attractions"]
                if attraction_result and "attractions" in attraction_result:
                    attraction_results = attraction_result["attractions"]
                    self.logger.info(f"Got {len(attraction_results)} detailed attractions")
                    self.logger.debug(f"Detailed attractions: {json.dumps(attraction_results[:2], ensure_ascii=False, indent=2)}")
                    progress.update("detailed_attractions", attraction_results)
            
            # Get transportation suggestions
            transportation_suggestions = "暫無交通建議。"
            if "transportation" in complete_results:
                transport_result = complete_results["transportation"]
                if isinstance(transport_result, list) and len(transport_result) > 0:
                    # Format transportation suggestions into text
                    transportation_text = ""
                    for i, suggestion in enumerate(transport_result, 1):
                        transportation_text += f"{i}. {suggestion['description']}\n"
                    transportation_suggestions = transportation_text
                    self.logger.info(f"Got {len(transport_result)} transportation suggestions")
                    self.logger.debug(f"Transportation suggestions: {json.dumps(transport_result[:2], ensure_ascii=False, indent=2)}")
                progress.update("transportation", transport_result)
            
            # Format the complete response
            self.logger.info("Formatting complete response")
            complete_response = self._format_complete_response(
                hotel_results=hotel_results or [],
                attraction_results=attraction_results or [],
                transportation_suggestions=transportation_suggestions
            )
            
            # Mark the final formatting step as complete
            progress.update("format_response", complete_response)
            
            # Send the complete response to the user proxy
            self.logger.info("Sending complete response to user proxy")
            self.logger.debug(f"Complete response text: {complete_response[:200]}...")
            try:
                # 首先嘗試同步調用
                self.user_proxy.receive_response(complete_response, is_complete=True)
            except Exception as e:
                # 如果同步調用失敗，嘗試異步調用
                self.logger.warning(f"同步調用 receive_response 失敗，嘗試異步調用: {str(e)}")
                await self.user_proxy.receive_response_async(complete_response, is_complete=True)
            
            return complete_response
        except Exception as e:
            self.logger.error(f"Error in coordinate workflow: {str(e)}", exc_info=True)
            error_response = self._format_error_response(f"處理您的請求時發生錯誤: {str(e)}")
            try:
                # 首先嘗試同步調用
                self.user_proxy.receive_response(error_response, is_complete=True)
            except Exception as e2:
                # 如果同步調用失敗，嘗試異步調用
                self.logger.warning(f"同步調用 receive_response 失敗，嘗試異步調用: {str(e2)}")
                await self.user_proxy.receive_response_async(error_response, is_complete=True)
            return error_response
    
    def _progress_callback(self, completed, total, step_name, result):
        """Callback function for progress updates."""
        self.logger.info(f"Progress: {completed}/{total} steps completed. Just finished: {step_name}")
    
    async def _get_hotel_recommendations(self, user_preferences):
        """Get hotel recommendations from the hotel agent."""
        # Prepare the message for the hotel agent
        message = {"preferences": user_preferences}
        
        # Get recommendations from the hotel agent
        try:
            response = await self.hotel_agent.generate_hotel_recommendations(message)
            return response
        except Exception as e:
            self.logger.error(f"Error getting hotel recommendations: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _get_initial_attractions(self, user_preferences):
        """Get initial attraction recommendations."""
        # Prepare the message for the itinerary agent
        message = {"preferences": user_preferences}
        
        # Get recommendations from the itinerary agent
        try:
            response = await self.itinerary_agent.generate_itinerary(message)
            return response
        except Exception as e:
            self.logger.error(f"Error getting initial attractions: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _get_detailed_attractions(self, user_preferences, hotel_info=None):
        """Get detailed attraction recommendations based on hotel location."""
        # Prepare the message for the itinerary agent
        message = {
            "preferences": user_preferences,
            "hotel": hotel_info
        }
        
        # Get recommendations from the itinerary agent
        try:
            response = await self.itinerary_agent.generate_itinerary(message)
            return response
        except Exception as e:
            self.logger.error(f"Error getting detailed attractions: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _get_transportation_suggestions(self, hotel_info, attractions):
        """Get transportation suggestions between hotel and attractions."""
        # In a real implementation, you'd call an API or use a specialized agent
        # Here we'll generate mock suggestions
        
        if not hotel_info or not attractions:
            return []
        
        hotel_name = hotel_info.get("name", "酒店")
        
        suggestions = []
        for attraction in attractions:
            attraction_name = attraction["name"]
            
            # Generate suggestions for all transport methods
            methods = ["公共交通", "計程車", "步行"]
            for method in methods:
                suggestion = {
                    "from": hotel_name,
                    "to": attraction_name,
                    "method": method,
                    "description": self._format_transportation(
                        hotel_name, attraction_name, method
                    )
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    # 內部格式化函數
    def _format_initial_response(self):
        """Format the initial response to the user."""
        return config.TEMPLATES["initial_response"]
    
    def _format_partial_response(self, hotel_results=None, attraction_results=None):
        """Format a partial response with available info."""
        response_parts = []
        
        # 確保我們有內容可顯示
        if not hotel_results and not attraction_results:
            self.logger.warning("No hotel or attraction results for partial response")
            return "我們正在為您查詢旅遊資訊，請稍候..."
        
        response_parts.append("# 初步旅遊建議\n\n")
        
        # 添加酒店建議
        if hotel_results and len(hotel_results) > 0:
            response_parts.append("## 住宿建議\n")
            
            for i, hotel in enumerate(hotel_results[:3], 1):  # Just show top 3
                response_parts.append(f"### {i}. {hotel.get('name', '未知酒店')}\n")
                response_parts.append(f"* **等級**: {hotel.get('rating', '無評分')} 星\n")
                response_parts.append(f"* **價格**: {hotel.get('price_range', '價格未知')}\n")
                response_parts.append(f"* **地點**: {hotel.get('location', '地點未知')}\n")
                if hotel.get('description'):
                    response_parts.append(f"* **簡介**: {hotel.get('description')[:150]}...\n")
                response_parts.append("\n")
        
        # 添加景點建議
        if attraction_results and len(attraction_results) > 0:
            response_parts.append("## 景點預覽\n")
            
            for i, attraction in enumerate(attraction_results[:5], 1):  # Just show top 5
                response_parts.append(f"### {i}. {attraction.get('name', '未知景點')}\n")
                response_parts.append(f"* **類型**: {attraction.get('type', '類型未知')}\n")
                if attraction.get('description'):
                    response_parts.append(f"* **簡介**: {attraction.get('description')[:150]}...\n")
                response_parts.append("\n")
        
        response_parts.append("_我們正在為您準備更詳細的資訊，請稍候..._")
        
        return "".join(response_parts)

    def _format_complete_response(self, hotel_results=None, attraction_results=None, transportation_suggestions=None):
        """Format the complete response with all information."""
        if not hotel_results and not attraction_results:
            self.logger.warning("No results for complete response")
            return "抱歉，我們無法找到符合您需求的旅遊資訊。請提供更多細節，例如目的地、預算或旅遊偏好等。"
        
        response_parts = []
        response_parts.append("# 您的旅遊計畫\n\n")
        
        # 添加酒店建議
        if hotel_results and len(hotel_results) > 0:
            response_parts.append("## 推薦住宿\n")
            
            for i, hotel in enumerate(hotel_results[:3], 1):
                response_parts.append(f"### {i}. {hotel.get('name', '未知酒店')}\n")
                response_parts.append(f"* **等級**: {hotel.get('rating', '無評分')} 星\n")
                response_parts.append(f"* **價格**: {hotel.get('price_range', '價格未知')}\n")
                response_parts.append(f"* **地點**: {hotel.get('location', '地點未知')}\n")
                if hotel.get('amenities'):
                    amenities = hotel.get('amenities')
                    if isinstance(amenities, list):
                        amenities_str = ", ".join(amenities[:5])
                    else:
                        amenities_str = str(amenities)
                    response_parts.append(f"* **設施**: {amenities_str}\n")
                if hotel.get('description'):
                    response_parts.append(f"* **簡介**: {hotel.get('description')}\n")
                response_parts.append("\n")
        else:
            response_parts.append("## 推薦住宿\n")
            response_parts.append("抱歉，我們目前無法提供符合您需求的住宿建議。\n\n")
        
        # 添加景點建議
        if attraction_results and len(attraction_results) > 0:
            response_parts.append("## 推薦景點與活動\n")
            
            for i, attraction in enumerate(attraction_results[:5], 1):
                response_parts.append(f"### {i}. {attraction.get('name', '未知景點')}\n")
                response_parts.append(f"* **類型**: {attraction.get('type', '類型未知')}\n")
                if attraction.get('location'):
                    response_parts.append(f"* **地點**: {attraction.get('location')}\n")
                if attraction.get('description'):
                    response_parts.append(f"* **簡介**: {attraction.get('description')}\n")
                if attraction.get('best_time'):
                    response_parts.append(f"* **最佳參訪時間**: {attraction.get('best_time')}\n")
                if attraction.get('tips'):
                    response_parts.append(f"* **小貼士**: {attraction.get('tips')}\n")
                response_parts.append("\n")
        else:
            response_parts.append("## 推薦景點與活動\n")
            response_parts.append("抱歉，我們目前無法提供符合您需求的景點建議。\n\n")
        
        # 添加交通建議
        response_parts.append("## 交通建議\n")
        if transportation_suggestions and transportation_suggestions != "暫無交通建議。":
            response_parts.append(transportation_suggestions)
        else:
            response_parts.append("### 一般交通建議\n")
            response_parts.append("* 從機場到市區可以搭乘計程車、機場巴士或捷運。\n")
            response_parts.append("* 市區內可以使用公共交通工具，如捷運、公車或租用自行車。\n")
            response_parts.append("* 前往郊區景點考慮租車或參加一日遊行程。\n")
        
        # 添加旅遊提示
        response_parts.append("\n## 旅遊小貼士\n")
        response_parts.append("* 出發前請檢查天氣預報，攜帶適當衣物。\n")
        response_parts.append("* 建議提前預訂熱門景點門票以節省排隊時間。\n")
        response_parts.append("* 尊重當地文化習俗，部分宗教場所可能有著裝要求。\n")
        response_parts.append("* 隨身攜帶充足的水和防曬用品。\n")
        
        return "".join(response_parts)

    def _format_error_response(self, error_message):
        """格式化錯誤回應"""
        return f"""
## 很抱歉，處理您的請求時出現問題

{error_message}

請嘗試重新提供您的旅遊需求，或提供更多資訊讓我們能更好地服務您。
"""

    def _format_transportation(self, from_place, to_place, method="公共交通"):
        """格式化交通建議為可讀字串"""
        # 簡化的模擬函數
        transport_options = {
            "公共交通": f"從{from_place}搭乘捷運/公車前往{to_place}，約需30-45分鐘。",
            "計程車": f"從{from_place}搭乘計程車前往{to_place}，約需15-20分鐘，費用約NT$250。",
            "步行": f"從{from_place}步行前往{to_place}，距離約1.5公里，約需20分鐘。",
        }
        
        return transport_options.get(method, transport_options["公共交通"])


def create_coordinator_agent(model_client=None):
    """Factory function to create and configure a coordinator agent."""
    return CoordinatorAgent(
        name="coordinator_agent",
        model_client=model_client,
        system_message="""You are a coordinator agent responsible for managing the workflow between
        specialized agents in a travel recommendation system. Your primary role is to ensure
        efficient communication between agents, timely responses to users, and a coherent
        final recommendation.
        
        When providing recommendations, always include:
        1. Clear section headings (hotels, attractions, transportation)
        2. For hotels: name, rating, price range, address, and key amenities
        3. For attractions: name, admission fee, location, type, and visiting hours
        4. For transportation: clear options between locations with time and cost estimates
        
        You should prioritize providing quick initial responses followed by more detailed
        information as it becomes available, ensuring users receive the best possible
        experience even when facing time constraints.
        """
    ) 