name: Run YouTube Shorts Bot

on:
  schedule:
    - cron: '0 10 * * *'
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install System Video and Font Tools
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg imagemagick
          sudo sed -i 's/policy domain="path" rights="none" pattern="@\*"/policy domain="path" rights="read|write" pattern="@\*"/g' /etc/ImageMagick-6/policy.xml

      - name: Install dependencies
        run: |
          pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 google-genai edge-tts moviepy requests

      - name: Inject Secrets & Run Bot
        env:
          CLIENT_SECRETS_DATA: ${{ secrets.CLIENT_SECRETS }}
          TOKEN_JSON_DATA: ${{ secrets.TOKEN_JSON }}
        run: |
          echo "$CLIENT_SECRETS_DATA" > client_secrets.json
          echo "$TOKEN_JSON_DATA" > token.json
          python main.py
