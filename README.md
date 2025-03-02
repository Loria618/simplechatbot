# Simple Chatbot

This is a chatbot that supports both local and cloud deployment, using local models (Ollama or llama-cpp) or the HuggingFace Inference API.

## Features

- Simple and intuitive user interface
- Support for both local and cloud deployment
- Support for multiple models:
  - Local: Meta Llama 3.2 1B (via Ollama)
  - Local: Any compatible model (via llama-cpp-python)
  - Cloud: HuggingFace Inference API
- Support for conversation history
- Knowledge base management functionality
- Web API and WebSocket interface

## Installing Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Setup

1. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

2. Edit the `.env` file:
   - For local development: Set `ENVIRONMENT=local`
   - For cloud deployment: Set `ENVIRONMENT=production` and add your HuggingFace API key

### Model Configuration

Edit the `config.json` file to configure the model settings:

- For local Ollama usage:
  - Set `use_ollama` to `true`
  - Set `name` to the name of your Ollama model (e.g., "llama3.2:1b")

- For HuggingFace API:
  - In the `huggingface` section, set `model_name` to the model you want to use

## Local Usage

### Prerequisites for Local Mode

- [Ollama](https://ollama.ai/) installed and running (if using Ollama)
- Or a local model file (if using llama-cpp-python)

### Desktop Application

1. Make sure you have installed the dependencies
2. Run the desktop application:

```bash
python main.py
```

### Web Server

1. Make sure you have installed the dependencies
2. Run the web server:

```bash
python api_server.py
```

3. Access http://localhost:8000 in your browser

## Deploying to Render

1. Create a new Web Service on Render
2. Connect to your GitHub repository
3. Set the following environment variables:
   - `HUGGINGFACE_API_KEY`: Your HuggingFace API key
   - `ENVIRONMENT`: Set to `production`
4. Set the build command to: `pip install -r requirements.txt`
5. Set the start command to: `python api_server.py`

## How It Works

### Environment Detection

The application automatically detects whether it's running locally or in production:

- In local mode, it uses the model specified in `config.json` (Ollama or local model)
- In production mode, it automatically switches to using the HuggingFace API

### API Integration

The HuggingFace API integration is handled by:

1. The `huggingface_handler.py` module for dedicated HuggingFace operations
2. The `llm_handler.py` module, which can switch between local and cloud models

## Troubleshooting

- If you see Chinese text in the UI after translation, try clearing your browser cache or doing a hard refresh (Ctrl+F5 or Cmd+Shift+R)
- If you encounter errors with the HuggingFace API, check that your API key is correct and the model you're trying to use is accessible
- For local development issues, ensure Ollama is running if you're using it

## License

This project is licensed under the MIT License - see the LICENSE file for details.
