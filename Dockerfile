FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OPENAI_API_KEY=""
ENV SLACK_WEBHOOK_URL=""
ENV GITHUB_TOKEN=""
ENV CONFIDENCE_THRESHOLD="0.75"
ENV AUTO_MERGE_HIGH_CONFIDENCE="false"

ENTRYPOINT ["python", "main.py"]
