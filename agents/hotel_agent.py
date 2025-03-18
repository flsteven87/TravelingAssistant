"""
Hotel recommendation agent for suggesting accommodations.
"""
import asyncio
import sys
import os
import time
import random

# Add parent directory to path to allow module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import mock_hotels
from utils.async_helper import with_timeout, timed_execution

from autogen_agentchat.agents import AssistantAgent

class HotelRecommendationAgent(AssistantAgent):
    """
    An agent specialized in hotel recommendations based on user preferences.
    This agent analyzes user requirements and suggests the most suitable accommodations.
    """
    
    def __init__(self, name="Hotel Recommendation Agent", model_client=None, **kwargs):
        super().__init__(name=name, model_client=model_client, **kwargs)
    
    async def generate_hotel_recommendations(self, message):
        """Process the message and generate hotel recommendations."""
        # Extract user preferences from message
        user_preferences = self._extract_preferences(message)
        
        # Get hotel recommendations based on preferences
        try:
            recommendations = await self._get_recommendations(user_preferences)
            return recommendations
        except Exception as e:
            return f"Error generating hotel recommendations: {str(e)}"
    
    def _extract_preferences(self, message):
        """Extract hotel preferences from the user message."""
        # In a real system, this would use NLP to extract preferences
        # For simplicity, we'll assume the message contains a structured preferences object
        
        # Default preferences
        preferences = {
            "destination": "台北市",  # Default to Taipei
            "date_range": None,
            "num_people": 2,
            "budget": 5000,
            "hotel_type": None,
            "facilities": [],
            "district": None
        }
        
        # Try to extract structured data if available (simplified)
        if isinstance(message, dict) and "preferences" in message:
            user_prefs = message["preferences"]
            
            # Update preferences with user data if available
            if "destination" in user_prefs and user_prefs["destination"]:
                preferences["destination"] = user_prefs["destination"]
            
            if "date_range" in user_prefs and user_prefs["date_range"]:
                preferences["date_range"] = user_prefs["date_range"]
            
            if "num_people" in user_prefs and user_prefs["num_people"]:
                preferences["num_people"] = user_prefs["num_people"]
            
            if "budget" in user_prefs and user_prefs["budget"]:
                preferences["budget"] = user_prefs["budget"]
            
            if "hotel_preferences" in user_prefs and user_prefs["hotel_preferences"]:
                hotel_prefs = user_prefs["hotel_preferences"]
                
                if "type" in hotel_prefs:
                    preferences["hotel_type"] = hotel_prefs["type"]
                
                if "facilities" in hotel_prefs:
                    preferences["facilities"] = hotel_prefs["facilities"]
                
                if "district" in hotel_prefs:
                    preferences["district"] = hotel_prefs["district"]
        
        return preferences
    
    @with_timeout(3)  # Set a 3-second timeout for initial response
    @timed_execution
    async def _get_recommendations(self, preferences):
        """Get hotel recommendations based on user preferences."""
        # Simulate some processing time
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # For testing partial response, you could uncomment this to simulate a longer process
        # await asyncio.sleep(5)
        
        # Use mock data for hotel search
        results = mock_hotels.search_hotels(
            district=preferences.get("district"),
            hotel_type=preferences.get("hotel_type"),
            min_price=None,
            max_price=preferences.get("budget"),
            facilities=preferences.get("facilities")
        )
        
        # Sort by rating (best first)
        results.sort(key=lambda x: x["rating"], reverse=True)
        
        # Filter by number of people if needed
        if preferences.get("num_people"):
            num_people = preferences["num_people"]
            results = [h for h in results if any(
                room["capacity"] >= num_people for room in h["room_types"]
            )]
        
        # Form the response
        response = {
            "status": "success",
            "recommendations": results,
            "preferences_used": preferences
        }
        
        return response

    # Define a fallback function for timeout situations
    async def timeout_fallback(self, preferences):
        """Return partial results when a timeout occurs."""
        # Get all hotels as a fallback
        all_hotels = mock_hotels.get_all_hotels()
        
        # Sort by rating (best first) and take top 2
        all_hotels.sort(key=lambda x: x["rating"], reverse=True)
        partial_results = all_hotels[:2]
        
        return {
            "status": "partial",
            "message": "Due to time constraints, here are some initial recommendations. Complete results will follow.",
            "recommendations": partial_results,
            "preferences_used": preferences
        }
    
    # Attach the fallback to the main function
    _get_recommendations.timeout_fallback = timeout_fallback


def create_hotel_agent(model_client=None):
    """Factory function to create and configure a hotel recommendation agent."""
    return HotelRecommendationAgent(
        name="hotel_agent",
        model_client=model_client,
        system_message="""You are a hotel recommendation agent specializing in finding the best accommodations
        based on user preferences. You analyze factors such as location, price range, amenities,
        and ratings to suggest the most suitable hotels for travelers.
        
        When responding to requests, use your detailed knowledge of hotels to provide personalized
        recommendations with clear explanations of why each option matches the user's needs.
        """
    ) 