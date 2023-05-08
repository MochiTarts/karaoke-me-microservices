import os, subprocess, logging
import json, uuid, os, shutil, tempfile, boto3

s3 = boto3.client('s3')
lambda_tmp_dir = '/tmp'
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
  """
  Handles receiving events from an AWS websocket API gateway.
  
  $connect: When a client connects to the websocket. Add the connectionId to the connections table in DynamoDB.
  $disconnect: When a client disconnects from the websocket. Remove the connectionId from the connections table in DynamoDB.
  split: When a client sends a message to the websocket. Split the audio file and send the s3 urls back to the client.
  """
  logger.info(f"Received event: {event}")
  logger.info(f"Received context: {context}")

  try:
    connection_id = event['requestContext']['connectionId']
    route_key = event['requestContext']['routeKey']
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    apig_management_api = boto3.client('apigatewaymanagementapi', endpoint_url=f'https://{domain}/{stage}')
  except KeyError as e:
    logger.exception(str(e))
    return {"statusCode": 500}
  
  table_name = os.environ.get('CONNECTIONS_TABLE_NAME')
  table = boto3.resource('dynamodb').Table(table_name)

  if route_key == '$connect':
    return handle_connect(connection_id, table)
  elif route_key == '$disconnect':
    return handle_disconnect(connection_id, table)
  elif route_key == 'split':
    try:
      # Get url from body (url of extracted youtube audio stored in s3)
      s3_yt_audio_url = json.loads(event['body'])['url']
    except KeyError as e:
      logger.exception(str(e))
      apig_management_api.post_to_connection(
        ConnectionId=connection_id, Data=json.dumps({"status": "error", "message": "No url provided"}).encode('utf-8'))
      return {"statusCode": 400}
    return handle_split(s3_yt_audio_url, connection_id, apig_management_api)

  apig_management_api.post_to_connection(
    ConnectionId=connection_id, Data=json.dumps({"status": "error", "message": "Invalid route key"}).encode('utf-8'))
  return {"statusCode": 500}

 
def handle_connect(connection_id, table):
  """
  Add the connection_id to the connections table in DynamoDB.
  """
  try:
    table.put_item(Item={'connection_id': connection_id})
  except Exception as e:
    logger.exception(str(e))
    return {"statusCode": 500}
  return {"statusCode": 200}


def handle_disconnect(connection_id, table):
  """
  Remove the connection_id from the connections table in DynamoDB.
  """
  try:
    table.delete_item(Key={'connection_id': connection_id})
  except Exception as e:
    logger.exception(str(e))
    return {"statusCode": 500}
  return {"statusCode": 200}
  

def handle_split(s3_yt_audio_url, connection_id, apig_management_api):
  """
  Split the audio file and send the s3 urls back to the client.
  """
  try:
    # Extract bucket name and object key from s3 url
    s3_bucket_name = s3_yt_audio_url.split('/')[2].split('.')[0]
    s3_object_key = s3_yt_audio_url.split('/', 3)[-1]
    yt_audio_file = f'yt_audio.{s3_object_key.split(".")[-1]}'
    # Send message to client that we are downloading the audio file
    apig_management_api.post_to_connection(
      ConnectionId=connection_id, Data=json.dumps({"status": "processing", "message": "Downloading audio file..."}).encode('utf-8'))
    # Download audio file from s3
    s3.download_file(s3_bucket_name, s3_object_key, f'{lambda_tmp_dir}/{yt_audio_file}')
  except Exception as e:
    logger.exception(str(e))
    apig_management_api.post_to_connection(
      ConnectionId=connection_id, Data=json.dumps({"status": "error", "message": "Error downloading audio file"}).encode('utf-8'))
    return {"statusCode": 500}
  
  try:
    s3_vocals_url, s3_accomp_url = split_audio_spleeter(f'{lambda_tmp_dir}/{yt_audio_file}', yt_audio_file, apig_management_api, connection_id)
    #s3_vocals_url, s3_accomp_url = split_audio_demucs(f'{lambda_tmp_dir}/{yt_audio_file}', yt_audio_file, apig_management_api, connection_id)
  except Exception as e:
    logger.exception(str(e))
    apig_management_api.post_to_connection(
      ConnectionId=connection_id, Data=json.dumps({"status": "error", "message": "Error splitting audio file"}).encode('utf-8'))
    return {"statusCode": 500}
  
  # Delete audio file from lambda tmp directory (non-blocking)
  try:
    os.remove(f'{lambda_tmp_dir}/{yt_audio_file}')
  except Exception as e:
    logger.exception(str(e))
  
  try:
    logger.info(f"Deleting audio file from s3: {s3_bucket_name}/{s3_object_key}")
    #s3.delete_object(Bucket=s3_bucket_name, Key=s3_object_key)
  except Exception as e:
    logger.exception(str(e))
    apig_management_api.post_to_connection(
      ConnectionId=connection_id,
      Data=json.dumps({"status": "error", "message": "Error deleting audio file from s3 during cleanup"}).encode('utf-8'))
    return {"statusCode": 500}

  # Send message to client with s3 urls
  apig_management_api.post_to_connection(
    ConnectionId=connection_id,
    Data=json.dumps({
      "status": "success",
      "message": "Finished splitting audio file",
      "data": {"vocals_url": s3_vocals_url, "accomp_url": s3_accomp_url}}).encode('utf-8'))
  return {"statusCode": 200}


def split_audio_spleeter(audio_path, audio_file, apig_management_api, connection_id):
  """
  Split the audio file into vocals and accompaniment using spleeter.
  """
  from spleeter.separator import Separator

  logger.info("Running spleeter...")
  apig_management_api.post_to_connection(
    ConnectionId=connection_id, Data=json.dumps({"status": "processing", "message": "Running spleeter..."}).encode('utf-8'))
  separator = Separator("spleeter:2stems", multiprocess=False)
  audio_codec = "mp3"
  audio_filename = audio_file.split(".")[0] # yt_audio
  output_destination = f'{lambda_tmp_dir}/{audio_filename}' # /tmp/yt_audio
  separator.separate_to_file(audio_path, lambda_tmp_dir, codec=audio_codec, synchronous=True)

  logger.info("Finished spleeter")

  # Upload vocals and accompaniment to s3
  s3_vocal_key = f'vocals/{uuid.uuid4()}.{audio_codec}'
  s3_accomp_key = f'accompaniment/{uuid.uuid4()}.{audio_codec}'

  logger.info("Uploading to s3...")
  apig_management_api.post_to_connection(
    ConnectionId=connection_id, Data=json.dumps({"status": "processing", "message": "Uploading to s3..."}).encode('utf-8'))
  
  s3.upload_file(f'{output_destination}/vocals.{audio_codec}', os.environ.get('BUCKET_NAME'), s3_vocal_key)
  s3.upload_file(f'{output_destination}/accompaniment.{audio_codec}', os.environ.get('BUCKET_NAME'), s3_accomp_key)

  logger.info("Finished uploading to s3")

  # Delete output directory (non-blocking)
  shutil.rmtree(output_destination, ignore_errors=True)

  return (f'https://{os.environ.get("BUCKET_NAME")}.s3.{os.environ.get("REGION")}.amazonaws.com/{s3_vocal_key}',
          f'https://{os.environ.get("BUCKET_NAME")}.s3.{os.environ.get("REGION")}.amazonaws.com/{s3_accomp_key}')


def split_audio_demucs(audio_path, audio_file, apig_management_api, connection_id):
  # Use demucs to split the audio file into vocals and accompaniment
  logger.info("Running demucs...")
  apig_management_api.post_to_connection(
    ConnectionId=connection_id, Data=json.dumps({"status": "processing", "message": "Running demucs..."}).encode('utf-8'))

  cmd = ["python3", "-m", "demucs.separate", "--mp3", "--two-stems", "vocals", "-n", "htdemucs", "-o", f'{lambda_tmp_dir}', audio_path]
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
  for stdout_line in iter(p.stdout.readline, ""):
    print(stdout_line, end="")
  p.stdout.close()
  p.wait()
  if p.returncode != 0:
    raise Exception(p.stderr.read())
  
  logger.info("Finished running demucs")

  # Then upload the split audio files to s3
  logger.info("Uploading split audio files to s3...")
  apig_management_api.post_to_connection(
    ConnectionId=connection_id, Data=json.dumps({"status": "processing", "message": "Uploading split audio files to s3..."}))
  audio_filename = audio_file.split(".")[0] # yt_audio
  # ie. /tmp/htdemucs/yt_audio
  separated_tracks_path = f'{lambda_tmp_dir}/htdemucs/{audio_filename}'
  
  s3_vocal_key = f'vocals/{uuid.uuid4()}.mp3'
  s3_accomp_key = f'accompaniment/{uuid.uuid4()}.mp3'

  s3.upload_file(f'{separated_tracks_path}/vocals.mp3', os.environ.get("BUCKET_NAME"), s3_vocal_key)
  s3.upload_file(f'{separated_tracks_path}/no_vocals.mp3', os.environ.get("BUCKET_NAME"), s3_accomp_key)
  
  logger.info("Finished uploading split audio files to s3")

  return (f'https://{os.environ.get("BUCKET_NAME")}.s3.{os.environ.get("REGION")}.amazonaws.com/{s3_vocal_key}',
          f'https://{os.environ.get("BUCKET_NAME")}.s3.{os.environ.get("REGION")}.amazonaws.com/{s3_accomp_key}')


# Just some local testing
def demucs_test():
  print("Running demucs on viva_la_vida.mp3")
  path_to_audio_file = os.path.join(os.getcwd(), "viva_la_vida.mp3")
  cmd = ["python3", "-m", "demucs.separate", "--mp3", "--two-stems", "vocals", "-n", "htdemucs", path_to_audio_file]
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
  for stdout_line in iter(p.stdout.readline, ""):
    print(stdout_line, end="")
  p.stdout.close()
  p.wait()
  if p.returncode != 0:
    print("Error: ", p.stderr.read())


def spleeter_test():
  from spleeter.separator import Separator
  print("Running spleeter on viva_la_vida.mp3")
  separator = Separator("spleeter:2stems", multiprocess=False)
  separator.separate_to_file("viva_la_vida.mp3", "./", codec="flac", synchronous=True)

if __name__ == "__main__":
  #demucs_test()
  spleeter_test()