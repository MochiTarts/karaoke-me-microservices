import json, uuid, os, shutil, yt_dlp, boto3, io

lambda_tmp_dir = '/tmp'
allowed_origins = ['http://localhost:3000']

def handler(event, context):
  try:
    # Get url from body
    youtube_url = json.loads(event['body'])['url']
  except KeyError as e:
    return {
      "statusCode": 400,
      "headers": {
        "Content-Type": "application/json",
      },
      "body": json.dumps({"error": f"Missing required parameter: {e}"})
    }
  
  try:
    s3_url = get_youtube(youtube_url)
  except Exception as e:
    return {
      "statusCode": 500,
      "headers": {
        "Content-Type": "application/json",
      },
      "body": json.dumps({"error": str(e)})
    }

  return {
    "statusCode": 200,
    "headers": {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": allowed_origins, # Required for CORS support to work
    },
    "body": json.dumps({"url": s3_url})
  }


def get_youtube(url):
  # Use youtube_dl to download the audio file from the given YouTube URL.
  filename = f'{uuid.uuid1().hex}'
  ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': f'{lambda_tmp_dir}/yt-dlp/{filename}',
    'nocheckcertificate': True,
    'postprocessors': [{
      'key': 'FFmpegExtractAudio',
      'preferredcodec': 'flac',
      'preferredquality': '192',
    }],
  }
  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
  
  # Return the audio stream. And remove the file after the request is done.
  path = f'{lambda_tmp_dir}/yt-dlp/{filename}.flac'

  s3 = boto3.client('s3')
  s3_key = f'{filename}.flac'
  s3.upload_file(path, os.environ.get('BUCKET_NAME'), s3_key)

  shutil.rmtree(f'{lambda_tmp_dir}/yt-dlp', ignore_errors=True)

  return f'https://{os.environ.get("BUCKET_NAME")}.s3.{os.environ.get("REGION")}.amazonaws.com/{s3_key}'