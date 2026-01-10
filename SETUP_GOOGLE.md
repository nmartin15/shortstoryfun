# Google Gemini API Setup — Quick Start

> **See [README.md](README.md) for general setup instructions.**

Simple setup—just need an API key!

## Quick Setup (2 steps)

### 1. Get Your API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

### 2. Set Environment Variable

**Option 1: Create a `.env` file (Recommended)**

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Then edit `.env` and add your API key:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

The app will automatically load this file when it starts.

**Option 2: Set environment variable directly**

**macOS/Linux:**
```bash
export GOOGLE_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:GOOGLE_API_KEY="your_api_key_here"
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

That's it! The app will automatically use Google Gemini API.

## Verify Setup

Run the app:
```bash
python app.py
```

You should see:
```
✅ Using Google Gemini API
   Story generation will use AI-powered prose generation
```

## Model Options

Default model is `gemini-2.5-flash`. To use a different model:

```bash
export LLM_MODEL=gemini-1.5-pro  # or other Gemini models
```

Available models (text-only, no image support):
- `gemini-2.5-flash` (default) - Fast and efficient for text generation
- `gemini-2.0-flash-exp` - Experimental flash model
- `gemini-1.5-pro` - Higher quality, slower
- `gemini-1.5-flash` - Balanced performance
- `gemini-1.0-pro` - Legacy model

Note: This application is text-only. Image/vision models are not supported.

## Why Google Gemini API?

- **Simple setup** - Just an API key, no installation needed
- **High quality** - State-of-the-art language models
- **Fast** - Cloud-based, no local processing required
- **Reliable** - Managed service with good uptime

## Troubleshooting

### "API key required"
- Make sure `GOOGLE_API_KEY` is set
- Check spelling: `GOOGLE_API_KEY` (not `GOOGLE_AI_KEY` or similar)

### "Invalid API key"
- Verify your key at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Make sure the key hasn't been revoked
- Check for extra spaces when copying

### Rate Limits
- Free tier has rate limits
- If you hit limits, consider:
  - Upgrading to paid tier
  - Adding retry logic (can be added to code)
  - Using the template-based fallback (works without API)

