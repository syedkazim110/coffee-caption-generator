#!/bin/bash

# Script to setup Ollama model in Docker container
# This script pulls the phi3:mini model after Ollama starts

echo "🤖 Setting up Ollama model..."
echo "Waiting for Ollama service to be ready..."

# Wait for Ollama to be ready
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker compose exec ollama ollama list >/dev/null 2>&1; then
        echo "✅ Ollama service is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "⏳ Waiting for Ollama... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Ollama service failed to start"
    exit 1
fi

# Pull the phi3:mini model
echo "📥 Pulling phi3:mini model (this may take a few minutes on first run)..."
docker compose exec ollama ollama pull phi3:mini

if [ $? -eq 0 ]; then
    echo "✅ Model phi3:mini successfully pulled!"
    echo "🎉 Ollama setup complete!"
    echo ""
    echo "You can now use LLM caption generation in your application."
    echo "The model is cached and will be available on future runs."
else
    echo "❌ Failed to pull model"
    exit 1
fi
