# Background Job Support

> **See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment instructions.**

This application now supports background job processing using RQ (Redis Queue) for heavy operations like story generation, revisions, and batch exports.

## Features

- **Asynchronous Story Generation**: Generate stories in the background without blocking the web server
- **Background Revisions**: Revise stories asynchronously
- **Batch Exports**: Export multiple stories in the background
- **Job Status Tracking**: Check job status and retrieve results via API

## Setup

### 1. Install Dependencies

Install RQ and its dependencies:

```bash
pip install rq rq-dashboard
```

### 2. Configure Redis

Ensure Redis is running and accessible. Update your `.env` file:

```bash
REDIS_URL=redis://localhost:6379/0
USE_BACKGROUND_JOBS=true
```

### 3. Start the Worker

Start a worker process to process background jobs:

```bash
python worker.py
```

Or with specific queues:

```bash
python worker.py --queue default,high,low
```

For production, use the Procfile which includes a worker process:

```bash
# Procfile includes:
web: gunicorn -c gunicorn_config.py app:app
worker: python worker.py
```

## Usage

### Story Generation

To generate a story in the background, include `"background": true` in your request:

```json
POST /api/generate
{
  "idea": "A story about...",
  "character": {...},
  "theme": "...",
  "genre": "General Fiction",
  "background": true
}
```

Response (202 Accepted):
```json
{
  "status": "queued",
  "job_id": "abc123...",
  "message": "Story generation started in background. Use /api/job/<job_id> to check status."
}
```

### Story Revision

To revise a story in the background:

```json
POST /api/story/<story_id>/revise
{
  "background": true,
  "use_llm": true
}
```

### Story Export

To export a story in the background:

```
GET /api/story/<story_id>/export/<format>?background=true
```

### Checking Job Status

Check the status of a background job:

```
GET /api/job/<job_id>
```

Response:
```json
{
  "job_id": "abc123...",
  "status": "finished",
  "created_at": "2025-01-01T12:00:00",
  "started_at": "2025-01-01T12:00:01",
  "ended_at": "2025-01-01T12:02:30",
  "result": {
    "status": "completed",
    "story_id": "story_abc123",
    "word_count": 5234
  }
}
```

### Getting Job Result

Get the result of a completed job:

```
GET /api/job/<job_id>/result
```

## Job Status Values

- `queued`: Job is waiting to be processed
- `started`: Job is currently being processed
- `finished`: Job completed successfully
- `failed`: Job failed with an error

## Benefits

1. **Non-blocking**: Web server remains responsive during long-running operations
2. **Scalability**: Can process multiple jobs concurrently with multiple workers
3. **Reliability**: Failed jobs can be retried
4. **Monitoring**: Track job progress and status
5. **Future-proof**: Ready for long stories, multi-step generation, and batch operations

## Monitoring

### RQ Dashboard (Optional)

Install and run RQ Dashboard for a web-based job monitoring interface:

```bash
pip install rq-dashboard
rq-dashboard
```

Then visit `http://localhost:9181` to view job queues and status.

### Logs

Monitor worker logs to see job processing:

```bash
python worker.py
```

## Production Considerations

1. **Multiple Workers**: Run multiple worker processes for better throughput
2. **Queue Priorities**: Use different queues (high, default, low) for priority-based processing
3. **Job Timeouts**: Jobs have timeouts (10m for generation, 5m for revision, 2m for export)
4. **Redis Persistence**: Ensure Redis is configured for persistence in production
5. **Error Handling**: Failed jobs are logged and can be retried

## Fallback Behavior

If background jobs are disabled or RQ is not available, all operations fall back to synchronous processing (original behavior). The API remains fully functional.

