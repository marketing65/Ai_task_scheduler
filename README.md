# AI-Powered Task Management System

An end-to-end AI system that converts voice or text instructions (in **Hindi**, **Hinglish**, or **English**) into structured task entries using OpenAI GPT and Whisper.

## 🏗️ Architecture

```
Input (Text/Audio)
        │
        ▼
┌───────────────────┐
│   FastAPI Server   │
├───────────────────┤
│  /process-text    │ ──→ GPT Task Extraction ──→ JSON
│  /process-audio   │ ──→ Whisper STT ──→ GPT ──→ JSON
│  /health          │ ──→ System Status
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Post-Processing  │
│  • Date Validation│
│  • Name Cleanup   │
│  • Dept Normalize │
└───────────────────┘
        │
        ▼
   Structured JSON
```

## 📋 Features

- **Multilingual**: Hindi, Hinglish, English — all supported
- **Voice Input**: Upload mp3/wav/m4a/webm audio files
- **Smart Extraction**: Requester, doer, department, due date, task description, attachment
- **Date Intelligence**: Handles "kal", "parso", "next Monday", "25 April"
- **Name Normalization**: Strips "sir", "mam", "ji", "bhai" and other honorifics
- **Multi-Task**: Detects multiple tasks in a single input
- **Confidence Scoring**: Reports AI confidence in extraction accuracy
- **Error Handling**: Graceful fallbacks for missing or unclear fields

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example .env file
copy .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Run the Server

```bash
python run.py
```

The server starts at **http://localhost:8000**

### 4. Open API Docs

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

## 📡 API Endpoints

### `POST /process-text`

Extract tasks from text input.

**Request:**
```json
{
  "text": "Mukesh sir ne bola Rahul ko HR department mein documents submit karne hain aur last date 25 April hai"
}
```

**Response:**
```json
{
  "input_text": "Mukesh sir ne bola Rahul ko HR department mein documents submit karne hain aur last date 25 April hai",
  "tasks": [
    {
      "requester_name": "Mukesh",
      "doer_department": "HR",
      "doer_name": "Rahul",
      "due_date": "2026-04-25",
      "task_description": "Submit the required documents to the HR department.",
      "attachment": null
    }
  ],
  "confidence": 0.95,
  "processing_time_ms": 1234.56
}
```

### `POST /process-audio`

Extract tasks from an audio file.

**Request:** `multipart/form-data`
- `audio`: Audio file (mp3, wav, m4a, webm, ogg, flac)
- `language` (optional): Language hint — `"hi"` for Hindi, `"en"` for English

**Response:** Same structure as `/process-text`

### `GET /health`

Check system health and configuration status.

## 🧪 Testing

### Run Unit Tests (no API key needed)

```bash
pytest tests/test_date_handler.py tests/test_normalizer.py -v
```

### Run Integration Tests (requires API key)

```bash
pytest tests/ -v
```

## 📂 Project Structure

```
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # Environment configuration
│   ├── models.py             # Pydantic data models
│   ├── routers/
│   │   ├── text.py           # /process-text endpoint
│   │   └── audio.py          # /process-audio endpoint
│   ├── services/
│   │   ├── speech_to_text.py # Whisper API integration
│   │   ├── task_extractor.py # GPT extraction pipeline
│   │   ├── date_handler.py   # Date normalization
│   │   └── normalizer.py     # Name & department cleanup
│   ├── prompts/
│   │   └── extraction.py     # GPT prompt templates
│   └── utils/
│       └── logger.py         # Structured logging
├── tests/                    # Unit & integration tests
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── run.py                    # Server entry point
└── README.md                 # This file
```

## 📝 Example Inputs & Outputs

### Hindi Input
**Input:** `"Mukesh sir ne bola Rahul ko HR department mein documents submit karne hain aur last date 25 April hai"`

| Field | Value |
|---|---|
| requester_name | Mukesh |
| doer_name | Rahul |
| doer_department | HR |
| due_date | 2026-04-25 |
| task_description | Submit the required documents to the HR department. |
| attachment | null |

### Hinglish Input
**Input:** `"Simran ko bolo kal tak production report ready kare"`

| Field | Value |
|---|---|
| requester_name | null |
| doer_name | Simran |
| doer_department | Production |
| due_date | *(tomorrow's date)* |
| task_description | Prepare the production report. |
| attachment | null |

### English with Attachment
**Input:** `"John asked Sarah from Finance to prepare the quarterly budget report by next Monday. The Excel file is attached."`

| Field | Value |
|---|---|
| requester_name | John |
| doer_name | Sarah |
| doer_department | Finance |
| due_date | *(next Monday's date)* |
| task_description | Prepare the quarterly budget report. |
| attachment | Excel file attached |

### Multi-Task Input
**Input:** `"Rahul ko HR mein documents submit karne hain 25 April tak. Aur Simran ko production report kal tak ready kare."`

Returns **2 task objects** in the `tasks` array.

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | GPT model for extraction |
| `WHISPER_MODEL` | `whisper-1` | Whisper model for STT |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_AUDIO_SIZE_MB` | `25` | Max audio upload size |
