import os
import re
import json
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import smtplib
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/gmail.send']
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # Assuming for notifications

# Social media API keys (add as needed)
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
LINKEDIN_ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN')
# Add more as needed

def authenticate_google():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_google_doc_content(doc_id):
    creds = authenticate_google()
    service = build('docs', 'v1', credentials=creds)
    document = service.documents().get(documentId=doc_id).execute()
    content = ''
    for element in document.get('body').get('content'):
        if 'paragraph' in element:
            for text_run in element['paragraph']['elements']:
                if 'textRun' in text_run:
                    content += text_run['textRun']['content']
    return content

def parse_xml_tags(xml_string, tag_name):
    pattern = f'<{tag_name}>(.*?)</{tag_name}>'
    match = re.search(pattern, xml_string, re.DOTALL)
    return match.group(1).strip() if match else None

def parse_all_xml_tags(xml_string):
    pattern = r'<([^>\\/]+)>([\\s\\S]*?)</\\1>'
    matches = re.findall(pattern, xml_string)
    result = {}
    for tag, content in matches:
        result[tag.strip()] = content.strip()
    return result

def generate_social_content(route, user_prompt, system_config, schema):
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"Social Media Platform: {route}\nUser Prompt: {user_prompt}\n"
    system_message = system_config.get('system', '') + "\n\n<tools>\nYou have been provided with an internet search tool. Use this tool to find relevant information about the users request before responding. Today's date is: {datetime.now()}\n</tools>\n\n<rules>\n" + system_config.get('rules', '') + "\n- Output must conform to provided JSON schema\n</rules>\n\nFollow this Output JSON Schema:\n{\n  root_schema: " + json.dumps(schema.get('root_schema', {})) + ",\n  common_schema: " + json.dumps(schema.get('common_schema', {})) + ",\n  schema: " + json.dumps(schema.get('schema', {})) + "\n}"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def generate_image(image_suggestion):
    url = f"https://image.pollinations.ai/prompt/{image_suggestion.replace(' ', '-').replace(',', '').replace('.', '').slice(0, 100)}"
    response = requests.get(url)
    return response.content

def upload_to_imgbb(image_data):
    url = "https://api.imgbb.com/1/upload"
    files = {'image': image_data}
    data = {'key': IMGBB_API_KEY, 'expiration': '0'}
    response = requests.post(url, files=files, data=data)
    return response.json()['data']['url']

def send_approval_email(content, title):
    creds = authenticate_google()
    service = build('gmail', 'v1', credentials=creds)
    
    message = MIMEMultipart()
    message['to'] = TELEGRAM_CHAT_ID  # Assuming this is email
    message['subject'] = f"🔥FOR APPROVAL🔥 {title}"
    message.attach(MIMEText(content, 'html'))
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()

def post_to_twitter(text):
    headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}
    data = {'text': text}
    response = requests.post('https://api.twitter.com/2/tweets', headers=headers, json=data)
    return response.json()

def post_to_instagram(image_url, caption):
    # Simplified, actual implementation requires more steps
    # Use Facebook Graph API for Instagram
    pass  # Implement based on workflow

def post_to_facebook(text, image_url):
    data = {'message': text, 'link': image_url, 'access_token': FACEBOOK_ACCESS_TOKEN}
    response = requests.post(f'https://graph.facebook.com/me/feed', data=data)
    return response.json()

def post_to_linkedin(text, image_url):
    headers = {'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}'}
    data = {'content': {'contentEntities': [{'entityLocation': image_url, 'thumbnails': [{'resolvedUrl': image_url}]}]}, 'owner': 'urn:li:person:YOUR_PERSON_URN', 'text': {'text': text}}
    response = requests.post('https://api.linkedin.com/v2/ugcPosts', headers=headers, json=data)
    return response.json()

def main():
    # Inputs (from workflow trigger)
    route = 'instagram'  # Example
    user_prompt = "i need an instagram post about using n8n to transform business automation with reference to a related historical fact and example"
    
    # Fetch docs
    schema_doc_id = '12345'  # Replace with actual
    system_prompt_doc_id = '12345'  # Replace with actual
    schema_content = get_google_doc_content(schema_doc_id)
    system_prompt_content = get_google_doc_content(system_prompt_doc_id)
    
    # Parse
    platform = route.lower()
    extracted_schema = parse_xml_tags(schema_content, platform)
    root_schema = parse_xml_tags(schema_content, 'root')
    common_schema = parse_xml_tags(schema_content, 'common')
    schema = {
        'schema': json.loads(extracted_schema) if extracted_schema else {},
        'root_schema': json.loads(root_schema) if root_schema else {},
        'common_schema': json.loads(common_schema) if common_schema else {}
    }
    
    system_config = parse_all_xml_tags(system_prompt_content)
    
    # Generate content
    content = generate_social_content(route, user_prompt, system_config, schema)
    
    # Generate image
    image_data = generate_image(content['common_schema']['image_suggestion'])
    image_url = upload_to_imgbb(image_data)
    
    # Prepare email content
    email_html = f"<table><tr><td><img src='{image_url}'></td></tr><tr><td>{content['output']['caption']}</td></tr></table>"  # Simplified
    
    # Send approval
    send_approval_email(email_html, content['root_schema']['name'])
    
    # Assuming approved (in real, check response)
    approved = input("Approve? (y/n): ").lower() == 'y'
    if approved:
        if route == 'xtwitter':
            post_to_twitter(content['data']['social_content']['schema']['post'])
        elif route == 'instagram':
            post_to_instagram(image_url, content['output']['caption'])
        elif route == 'facebook':
            post_to_facebook(content['output']['post'], image_url)
        elif route == 'linkedin':
            post_to_linkedin(content['data']['social_content']['schema']['post'], image_url)
        # Add others

if __name__ == "__main__":
    main()
