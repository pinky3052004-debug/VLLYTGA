import os
import json
import datetime
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
    
    # လက်ရှိအချိန်ကို ယူ၍ Broadcast စတင်မည့်အချိန်ကို အလိုအလျောက် သတ်မှတ်ခြင်း (UTC)
    scheduled_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # YouTube Live Broadcast အသစ် ဖန်တီးခြင်း
    print("YouTube Live Broadcast အသစ် ဖန်တီးနေပါသည်...")
    broadcast_request = youtube.liveBroadcasts().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": scheduled_time
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }
    )
    broadcast_response = broadcast_request.execute()
    broadcast_id = broadcast_response["id"]
    
    # Broadcast ID ကို text ဖိုင်ထဲသို့ သိမ်းဆည်းပေးခြင်း (FFmpeg အတွက် သုံးရန်)
    with open("broadcast_id.txt", "w") as b_file:
        b_file.write(broadcast_id)

    print("--------------------------------------------------")
    print(f"🎉 YouTube Live Broadcast အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ!")
    print(f"📌 ထွက်ရှိလာသော Broadcast ID မှာ: {broadcast_id} ဖြစ်ပါသည်။")
    print("--------------------------------------------------")
    
    # Tags များကို Update လုပ်ခြင်း
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
        print("✅ ဗီဒီယို Tags များကို အောင်မြင်စွာ Update လုပ်ပြီးပါပြီ။")
    except Exception as e:
        print(f"⚠️ သတိပေးချက် - Tags Update လုပ်၍မရပါ: {e}")

    # Thumbnail တင်ခြင်း
    padded_id = f"{int(next_id):05d}"
    thumb_path = f"work/{padded_id}.jpg"
    
    if os.path.exists(thumb_path):
        print(f"🖼️ Broadcast ID ({broadcast_id}) အတွက် Thumbnail တင်နေပါသည်...")
        youtube.thumbnails().set(
            videoId=broadcast_id,
            media_body=MediaFileUpload(thumb_path)
        ).execute()
        print("✅ Thumbnail တင်ခြင်း အောင်မြင်ပါသည်။")

if __name__ == "__main__":
    create_or_update_broadcast()
