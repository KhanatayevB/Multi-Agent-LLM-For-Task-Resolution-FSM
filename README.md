# Capstone_AutogenChatbot

## Project Overview
The Support Intelligence Assistant (SIA) is an AI-powered chatbot designed to help Flipkart marketplace sellers resolve common issues with their listings and brand approvals. This system aims to automate the support process by handling routine queries and following standard operating procedures (SOPs) without requiring human intervention.

### Key Features
- Automated listing status checks
- Brand approval request tracking
- Support ticket creation
- User account status verification
- Interactive chat interface (both CLI and web-based)
- Retry mechanism for API calls
- Session state management
- Real-time status updates

## System Architecture

### Core Components
1. **SIA (Support Intelligence Assistant)**
   - Primary agent handling user interactions
   - Manages conversation flow and decision-making
   - Implements business logic for different scenarios

2. **FunctionExecutor Agent**
   - Handles API calls and function execution
   - Manages retry logic for failed API calls
   - Processes function calls from SIA

3. **Coordinator Agent**
   - Manages conversation flow between agents
   - Handles speaker selection and turn-taking
   - Ensures proper message routing

4. **User/UserProxy Agent**
   - Represents the end user in the system
   - Handles user input processing
   - Manages user context

### Implementation Options
The system is available in two implementations:

1. **Command-Line Interface (main.py)**
   - Terminal-based interaction
   - Suitable for testing and development
   - Direct API interaction

2. **Web Interface (main_streamlit.py)**
   - User-friendly web interface
   - Real-time status updates
   - Interactive chat experience
   - Configuration sidebar
   - Debug information display

## Component Documentation

### main.py
The command-line implementation of SIA provides a terminal-based interface for interacting with the support system.

#### Features
- Direct API interaction
- Automated status checks
- Support ticket creation
- Brand approval tracking
- Retry mechanism for API calls
- Conversation flow management

#### Key Functions
- `get_user_status()`: Checks user account status
- `get_listing_status()`: Verifies listing status
- `can_reactivate_listing()`: Checks if a blocked listing can be reactivated
- `create_support_ticket()`: Creates support tickets
- `get_brand_approval_status()`: Tracks brand approval requests

### main_streamlit.py
The web-based implementation provides a user-friendly interface for interacting with SIA.

#### Features
- Interactive chat interface
- Real-time status updates
- Configuration management
- Session state tracking
- Debug information display
- Quick testing inputs

#### UI Components
- Chat history display
- Configuration sidebar
- Status indicators
- Testing buttons
- Debug information panel

## Setup and Installation

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)
- Azure OpenAI API access

### Installation Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Command-Line Interface (main.py)
1. Ensure your virtual environment is activated
2. Run the application:
```bash
python main.py
```
3. Follow the prompts in the terminal to interact with SIA

### Web Interface (main_streamlit.py)
1. Ensure your virtual environment is activated
2. Run the Streamlit application:
```bash
streamlit run main_streamlit.py
```
3. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

### Configuration
Before running either version, make sure to:
1. Set up your Azure OpenAI API credentials
2. Configure the API endpoint and version
3. Select the appropriate model (gpt-4o-mini, gpt-4o, or gpt-4)

## Usage Examples

### Listing Support
1. Start a conversation with "I need help with my listing"
2. Provide your user ID when prompted
3. Provide your listing ID when requested
4. Follow the automated process for status checks and ticket creation

### Brand Approval
1. Start a conversation with "I need help with brand approval"
2. Provide your brand request ID
3. Follow the automated process for status checks and ticket creation

## Error Handling
The system includes robust error handling:
- Automatic retry mechanism for API calls
- Graceful handling of invalid inputs
- Clear error messages and status updates
- Session state preservation
- Conversation termination on critical errors

## Development and Testing
The system includes features for development and testing:
- Debug information display
- Quick testing inputs
- Message chain visualization
- Status tracking
- Retry attempt monitoring

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
