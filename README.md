# Travel Assistant & Itinerary Planning Multi-Agent System

A Multi-Agent architecture-based travel assistant system, including "Hotel Recommendation Agent" and "Itinerary Planning Agent," providing users with an integrated solution for travel accommodation and surrounding exploration.

## System Features

- Responds to user queries within 5 seconds
- Provides complete recommendations within 30 seconds
- Coordinates multiple specialized agents to provide integrated services
- Delivers progressive responses, providing immediate feedback even when complete results are not yet ready
- Final output includes: recommended accommodation options, surrounding attractions, and transportation suggestions
- Provides a structured form for users to input detailed travel requirements

## Directory Structure

```
.
├── app.py                  # Streamlit application entry point
├── requirements.txt        # List of dependencies
├── .env.example            # Environment variables example
├── .env                    # Environment variables (not included in version control)
├── test_api.py             # API testing script
├── test_hotel_detail.py    # Hotel detail API testing script
└── src/                    # Source code directory
    ├── __init__.py
    ├── config.py           # System configuration
    ├── agents/             # Agent modules
    │   ├── __init__.py
    │   ├── base_agent.py   # Base Agent class
    │   ├── orchestrator_agent.py  # Orchestrator Agent
    │   ├── hotel_agent.py  # Hotel Recommendation Agent
    │   └── itinerary_agent.py  # Itinerary Planning Agent
    ├── api/                # API clients
    │   ├── __init__.py
    │   ├── api_client.py   # API client base class
    │   ├── hotel_api.py    # Hotel API client
    │   └── place_api.py    # Place API client
    └── utils/              # Utility modules
        ├── __init__.py
        └── logging_utils.py  # Logging utilities
```

## Installation and Setup

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file and fill in your OpenAI API key and travel API key.

## Running the Application

```bash
streamlit run app.py
```

The application will start at http://localhost:8501.

## Usage

The system provides two ways to interact with the travel assistant:

### Method 1: Using the Sidebar Form

1. Fill in the following information in the "Travel Information Form" section of the application sidebar:
   - Target travel county/city (select from the list of counties/cities obtained from the API)
   - Check-in and check-out dates
   - Number of adults and children
   - Preferred hotel types (select from the list of hotel types obtained from the API)
   - Nightly budget range
2. Click the "Submit" button
3. After confirming the information is correct, click "Start Planning Trip"
4. The system will automatically generate a query and provide travel recommendations

### Method 2: Direct Chat

1. Enter your travel requirements in the chat input box on the main interface
2. The assistant will provide an initial response within 5 seconds
3. Complete travel recommendations will be provided within 30 seconds

Example questions:
- I want to travel to Taipei, what are some good accommodation recommendations?
- Please help me plan a three-day, two-night itinerary for Hualien
- My family and I want to go to Kenting with a budget of NT$5,000, are there suitable accommodations?

## Architecture Design

The system is based on a Multi-Agent architecture and mainly includes the following components:

1. **Base Agent (BaseAgent)**:
   - The base class for all specialized agents
   - Provides basic functions such as tool management, memory management, and task execution

2. **Orchestrator Agent (OrchestratorAgent)**:
   - Responsible for conversing with users and understanding their needs
   - Coordinates other specialized agents to complete tasks
   - Provides progressive responses

3. **Specialized Agents**:
   - **Hotel Recommendation Agent (HotelAgent)**: Responsible for recommending suitable accommodation options
   - **Itinerary Planning Agent (ItineraryAgent)**: Responsible for planning surrounding attractions and activities

## API Usage

The system uses the following APIs:

1. **Hotel Basic Parameters API**: Obtains parameters such as counties/cities, townships/districts, hotel types, etc.
2. **Hotel Information API**: Obtains hotel lists, details, vacancy information, etc.
3. **Nearby Landmark Query API**: Searches for nearby attractions and landmarks

## Testing

The project includes several test scripts:

- `test_api.py`: Tests the basic API functionality
- `test_hotel_detail.py`: Tests the hotel detail retrieval functionality

## Environment Variables

The project uses the following environment variables:

- `OPENAI_API_KEY`: OpenAI API key, used for generating responses
- `API_KEY`: Travel API key, used for obtaining travel-related data

## Developer

- [Your Name]

## License

[License Information]