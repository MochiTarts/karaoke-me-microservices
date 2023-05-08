import os, boto3, json, logging

s3 = boto3.client('s3')
lambda_tmp_dir = '/tmp'
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
  """
  Retrieve REST API body from event and return a presigned url for the client to perform specific actions on the file.

  API body parameters:
  - bucket: The name of the s3 bucket.
  - key: The key of the s3 object.
  - action: The action to perform on the s3 object. Valid actions are: get, put, delete.
  """

  logger.info(f'Receiving event: {event}')

  body = json.loads(event.get('body'))
  try:
    bucket = body['bucket']
    key = body['key']
    action = body['action']
  except KeyError as e:
    return {
      "statusCode": 400,
      "headers": {
        "Content-Type": "application/json",
      },
      "body": json.dumps({"error": f"Missing required parameter: {e}"})
    }
  
  if action == 'get':
    url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key})
  elif action == 'put':
    url = s3.generate_presigned_url('put_object', Params={'Bucket': bucket, 'Key': key})
  elif action == 'delete':
    url = s3.generate_presigned_url('delete_object', Params={'Bucket': bucket, 'Key': key})
  else:
    return {
      "statusCode": 400,
      "headers": {
        "Content-Type": "application/json",
      },
      "body": json.dumps({"error": f"Invalid action: {action}"})
    }
  
  return {
    "statusCode": 200,
    "headers": {
      "Content-Type": "application/json",
    },
    "body": json.dumps({"presigned_url": url})
  }