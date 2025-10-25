# Automated Social Media Content Publishing Factory

This Python script replicates the functionality of the provided n8n workflow for automated social media content creation and publishing.

## Features

- Fetches system prompts and schemas from Google Docs
- Generates social media content using OpenAI GPT
- Creates images using pollinations.ai
- Uploads images to imgbb.com
- Sends approval emails via Gmail
- Publishes to X (Twitter), Instagram, Facebook, LinkedIn, etc.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set up Google API credentials for Docs and Gmail.
3. Add API keys to `.env` file based on `.env.example`.
4. Run `python main.py`

## Usage

Modify the `main()` function with your inputs (route, user_prompt).
The script will handle the rest, including approval (manual input for simplicity).

## Notes

- Approval is simulated with console input; in production, integrate with email/webhook.
- Social media posting requires valid API tokens and proper setup.
- Update Google Doc IDs in the code.
