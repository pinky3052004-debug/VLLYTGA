import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def create_or_update_broadcast():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    next_id = os.environ.get("NEXT_ID")
    
    with open("work/main.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    video_item = None
    for item in data:
        if str(item.get("id")) == str(next_id):
            video_item = item
            break
            
    if not video_item:
        print(f"Error: ID {next_id} not found in main.json")
        exit(1)
        
    title = video_item.get("title")
    description = video_item.get("description")
    tags = video_item.get("video_tags", [])

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token"
    )
    
    youtube = build("youtube", "v3", credentials=creds)
    
    # 1. YouTube Live Broadcast အသစ်ဖန်တီးခြင်း (Insert)
    print("Creating new YouTube Live Broadcast...")
    broadcast_request = youtube.liveBroadcasts().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": "2026-09-22T00:00:00Z" # လိုအပ်ပါက သတ်မှတ်နိုင်သည် (သို့မဟုတ် လက်ရှိအချိန်)
            },
            "status": {
                "privacyStatus": "public", # public, unlisted သို့မဟုတ် private
                "selfDeclaredMadeForKids": False
            }
        }
    )
    broadcast_response = broadcast_request.execute()
    broadcast_id = broadcast_response["id"]
    print(f"Successfully created Broadcast ID: {broadcast_id}")
    
    # 2. Stream Key ကို Broadcast နဲ့ ချိတ်ဆက်ပေးခြင်း (Bind)
    # မှတ်ချက် - သင့်အကောင့်တွင် bound လုပ်ရန် Stream တစ်ခုရှိရပါမည်။ 
    # အကယ်၍ Stream Key တစ်ခုတည်းကို အမြဲသုံးချင်ပါက Bind လုပ်စရာမလိုဘဲ Video ID ကိုသာ သုံးနိုင်ပါသည်။
    
    # 3. Tags များကို Update လုပ်ခြင်း
    try:
        youtube.videos().update(
            part="snippet",
            body={
                "id": broadcast_id,
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": "24",
                    "tags": tags
                }
            }
        ).execute()
        print("Video tags updated.")
    except Exception as e:
        print(f"Warning: Tags update failed: {e}")

    # 4. Thumbnail တင်ခြင်း
    padded_id = f"{int(next_id):05d}"
    thumb_path = f"work/{padded_id}.jpg"
    
    if os.path.exists(thumb_path):
        print(f"Uploading thumbnail for broadcast {broadcast_id}...")
        youtube.thumbnails().set(
            videoId=broadcast_id,
            media_body=MediaFileUpload(thumb_path)
        ).execute()
        print("Thumbnail uploaded successfully.")

if __name__ == "__main__":
    create_or_update_broadcast()
