"""
Itinerary planning agent for recommending activities and attractions.
"""
import asyncio
import sys
import os
import time
import random

# Add parent directory to path to allow module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import mock_attractions, mock_hotels
from utils.async_helper import with_timeout, timed_execution

from autogen_agentchat.agents import AssistantAgent

class ItineraryPlanningAgent(AssistantAgent):
    """
    An agent specialized in planning itineraries based on user preferences and hotel location.
    This agent suggests attractions, activities, and transportation options.
    """
    
    def __init__(self, name="Itinerary Planning Agent", model_client=None, **kwargs):
        super().__init__(name=name, model_client=model_client, **kwargs)
    
    async def generate_itinerary(self, message):
        """Process the message and generate an itinerary plan."""
        # Extract user preferences and hotel info from message
        user_preferences, hotel_info = self._extract_info(message)
        
        # Get itinerary suggestions based on preferences and hotel
        try:
            itinerary = await self._plan_itinerary(user_preferences, hotel_info)
            return itinerary
        except Exception as e:
            return f"Error generating itinerary plan: {str(e)}"
    
    def _extract_info(self, message):
        """Extract user preferences and hotel information from the message."""
        # Default preferences
        preferences = {
            "destination": "台北市",  # Default to Taipei
            "date_range": None,
            "num_people": 2,
            "interests": [],
            "other_requirements": None
        }
        
        hotel_info = None
        
        # Try to extract structured data if available
        if isinstance(message, dict):
            if "preferences" in message:
                user_prefs = message["preferences"]
                
                # Update preferences with user data if available
                if "destination" in user_prefs and user_prefs["destination"]:
                    preferences["destination"] = user_prefs["destination"]
                
                if "date_range" in user_prefs and user_prefs["date_range"]:
                    preferences["date_range"] = user_prefs["date_range"]
                
                if "num_people" in user_prefs and user_prefs["num_people"]:
                    preferences["num_people"] = user_prefs["num_people"]
                
                if "interests" in user_prefs and user_prefs["interests"]:
                    preferences["interests"] = user_prefs["interests"]
                
                if "other_requirements" in user_prefs and user_prefs["other_requirements"]:
                    preferences["other_requirements"] = user_prefs["other_requirements"]
            
            if "hotel" in message:
                hotel_info = message["hotel"]
        
        return preferences, hotel_info
    
    @with_timeout(3)  # Set a 3-second timeout for initial response
    @timed_execution
    async def _plan_itinerary(self, preferences, hotel_info=None):
        """Plan an itinerary based on user preferences and hotel location."""
        # Simulate some processing time
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # For testing partial response, you could uncomment this to simulate a longer process
        # await asyncio.sleep(5)
        
        # If we have hotel info, find nearby attractions
        nearby_attractions = []
        if hotel_info and isinstance(hotel_info, dict) and "location" in hotel_info:
            location = hotel_info["location"]
            nearby_attractions = mock_attractions.get_nearby_attractions(
                location["latitude"], 
                location["longitude"]
            )
        else:
            # If no hotel info, get all attractions
            nearby_attractions = mock_attractions.get_all_attractions()
        
        # Filter attractions based on user interests if available
        if preferences.get("interests"):
            # This is a simplified matching - in reality, you'd use more sophisticated matching
            interest_keywords = {
                "美食": ["夜市", "餐廳"],
                "購物": ["購物", "夜市", "商場"],
                "歷史": ["博物館", "古蹟"],
                "文化": ["博物館", "廟宇"],
                "自然": ["自然", "公園", "山", "海灘"],
                "藝術": ["博物館", "藝術", "展覽"]
            }
            
            # Create a set of all applicable keywords from the user's interests
            relevant_keywords = set()
            for interest in preferences["interests"]:
                if interest in interest_keywords:
                    relevant_keywords.update(interest_keywords[interest])
            
            # Filter attractions that match any of the relevant keywords
            if relevant_keywords:
                filtered_attractions = []
                for attraction in nearby_attractions:
                    # Check if any keyword is in the description or type
                    desc_lower = attraction["description"].lower()
                    type_lower = attraction["type"].lower()
                    if any(keyword in desc_lower or keyword in type_lower 
                           for keyword in relevant_keywords):
                        filtered_attractions.append(attraction)
                
                # If we found matches, use them; otherwise keep all attractions
                if filtered_attractions:
                    nearby_attractions = filtered_attractions
        
        # Sort by rating (best first)
        nearby_attractions.sort(key=lambda x: x["rating"], reverse=True)
        
        # Generate transportation suggestions
        transportation_suggestions = []
        if hotel_info and nearby_attractions:
            hotel_name = hotel_info.get("name", "酒店")
            for attraction in nearby_attractions[:3]:  # Top 3 attractions
                attraction_name = attraction["name"]
                
                # In a real system, you'd calculate actual routes and times
                # Here we're generating mock suggestions
                transportation_methods = ["公共交通", "計程車", "步行"]
                chosen_method = random.choice(transportation_methods)
                
                suggestion = {
                    "from": hotel_name,
                    "to": attraction_name,
                    "method": chosen_method,
                    "description": self._generate_transport_description(
                        hotel_name, attraction_name, chosen_method
                    )
                }
                transportation_suggestions.append(suggestion)
        
        # Form the response
        response = {
            "status": "success",
            "attractions": nearby_attractions,
            "transportation": transportation_suggestions,
            "preferences_used": preferences
        }
        
        return response
    
    def _generate_transport_description(self, from_place, to_place, method):
        """Generate a description of the transportation method."""
        if method == "公共交通":
            return f"從{from_place}搭乘捷運/公車前往{to_place}，約需30-45分鐘。"
        elif method == "計程車":
            return f"從{from_place}搭乘計程車前往{to_place}，約需15-20分鐘，費用約NT$250。"
        elif method == "步行":
            return f"從{from_place}步行前往{to_place}，距離約1.5公里，約需20分鐘。"
        else:
            return f"從{from_place}前往{to_place}，可選擇多種交通方式。"
    
    # Define a fallback function for timeout situations
    async def timeout_fallback(self, preferences, hotel_info=None):
        """Return partial results when a timeout occurs."""
        # Get a limited set of attractions as fallback
        all_attractions = mock_attractions.get_all_attractions()
        
        # Sort by rating and take top 2
        all_attractions.sort(key=lambda x: x["rating"], reverse=True)
        partial_results = all_attractions[:2]
        
        return {
            "status": "partial",
            "message": "Due to time constraints, here are some initial attraction suggestions. Complete results will follow.",
            "attractions": partial_results,
            "transportation": [],  # No transportation suggestions in partial results
            "preferences_used": preferences
        }
    
    # Attach the fallback to the main function
    _plan_itinerary.timeout_fallback = timeout_fallback


def create_itinerary_agent(model_client=None):
    """Factory function to create and configure an itinerary planning agent."""
    return ItineraryPlanningAgent(
        name="itinerary_agent",
        model_client=model_client,
        system_message="""You are an itinerary planning agent specializing in creating personalized
        travel plans. You recommend attractions, activities, and transportation options based
        on user preferences and hotel location.
        
        When planning itineraries, consider factors such as distance between locations,
        opening hours, typical visit duration, and the user's interests to create efficient
        and enjoyable travel plans.
        """
    ) 