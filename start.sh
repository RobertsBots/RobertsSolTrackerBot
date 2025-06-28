#!/bin/bash

echo "🔧 Setze Webhook..."
python3 set_webhook.py

echo "🚀 Starte Bot..."
python3 main.py
