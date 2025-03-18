# TravelingAssistant

A smart multi-agent system for travel planning and hotel recommendations based on Autogen framework.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

TravelingAssistant is an AI-powered travel planning solution that helps users find suitable accommodations and plan itineraries based on their preferences. The system employs multiple specialized agents working in parallel to provide quick and comprehensive travel recommendations.

### Key Features

- **Rapid Response**: Initial response within 5 seconds, complete recommendations within 30 seconds
- **Multi-Agent Collaboration**: Hotel recommendation and itinerary planning agents coordinated by a central agent
- **Progressive Feedback**: Delivers incremental responses as information becomes available
- **Comprehensive Planning**: Provides hotel recommendations, nearby attractions, and transportation suggestions
- **Error Handling**: Manages inconsistent response times between agents to ensure system stability

## Architecture

```
TravelingAssistant/
├── agents/            # Agent definitions
│   ├── user_proxy.py      # User proxy agent
│   ├── hotel_agent.py     # Hotel recommendation agent
│   ├── itinerary_agent.py # Itinerary planning agent
│   └── coordinator_agent.py # Coordination agent
├── config/            # Configuration files
├── data/              # Mock data
│   ├── mock_hotels.py     # Hotel data
│   └── mock_attractions.py # Attraction data
├── src/               # Source code
│   └── api/           # API client implementations
├── utils/             # Utility functions
│   ├── async_helper.py    # Asynchronous processing utilities
│   └── logger_setup.py    # Logging configuration
├── logs/              # Log files (git-ignored)
├── app.py             # Main Streamlit application
├── requirements.txt   # Project dependencies
└── .env.example       # Example environment variables
```

### Agent Responsibilities

- **User Proxy Agent**: Handles user input, displays system responses, and manages the user experience
- **Hotel Recommendation Agent**: Recommends suitable accommodations based on user preferences
- **Itinerary Planning Agent**: Suggests attractions and activities based on user interests and hotel location
- **Coordinator Agent**: Orchestrates specialized agents, ensures timely responses, and formats results

## Communication Flow

The system uses the Autogen framework to facilitate communication between agents:

1. User inputs travel requirements
2. Coordinator agent extracts requirement information and distributes to specialized agents
3. Specialized agents process requests in parallel while the coordinator manages timeouts and priorities
4. Coordinator collects preliminary results and quickly responds to the user
5. Specialized agents continue processing complete results
6. Coordinator integrates all results and provides comprehensive recommendations

## Resource Management

- **Task Prioritization**: Critical tasks execute first to ensure key information is presented promptly
- **Timeout Handling**: Operations have timeouts, returning partial results rather than failing
- **Progressive Presentation**: Delivers preliminary information first, followed by complete details
- **Asynchronous Processing**: Uses Python's asyncio for non-blocking operations

## Installation

### Prerequisites

- Python 3.8 or higher
- Streamlit
- Autogen framework

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/TravelingAssistant.git
cd TravelingAssistant
```

2. Set up a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key
API_KEY=your_api_key
```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

Enter your travel requirements in the interface, for example:
```
I want to take my family to Taipei for 2 days starting tomorrow. My budget is $5000, and we enjoy history and food.
```

The system will provide quick initial feedback followed by comprehensive travel recommendations.

## Future Development

- Integration with real hotel and attraction APIs
- Additional specialized agents for restaurant recommendations, weather forecasts, etc.
- Enhanced natural language processing for more precise extraction of user requirements
- User feedback loop for continuous improvement based on recommendation ratings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue to discuss your ideas and suggestions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 