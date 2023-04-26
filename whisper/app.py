import uvicorn, asyncio, os, json, whisper, ssl, uuid, replicate, openai, shutil
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated
from urllib import request, parse
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_silence, detect_nonsilent

ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()

app = FastAPI()
origins = ['*']
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

abs_cwd = os.path.dirname(os.path.abspath(__file__))
openai.api_key = os.environ.get("OPENAI_API_KEY")

#TEST_AUDIO = os.path.join(abs_cwd, "shrek_2.wav")
#with open(os.path.join(abs_cwd, "whisper_result.json"), "r") as f:
#  TEST_RESULT = json.load(f)
#  f.close()


@app.put("/")
async def openai_api(audio_file: Annotated[UploadFile, File(...)] = None,
                 audio_uri: Annotated[str, Form(...)] = None):
  if audio_file is None and audio_uri is None:
    return JSONResponse(status_code=400, content={"error": "Please provide either an audio file or an audio URI."})
  if audio_file is not None and audio_uri is not None:
    return JSONResponse(status_code=400, content={"error": "Please provide either an audio file or an audio URI, not both."})
  
  if audio_file is not None:
    # Write audio file to disk. Save location in audio_input_path.
    print("Received audio file!")
    file_ext = audio_file.filename.split(".")[-1]
    audio_input_path = os.path.join(abs_cwd, uuid.uuid1().hex + "." + file_ext)
    try:
      print("Writing audio file to disk...")
      with open(audio_input_path, "wb") as f:
        f.write(audio_file.file.read())
        f.close()
    except Exception as e:
      return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while saving your audio file. Please try again later."})
  else:
    # Download audio file from URI. Save location in audio_input_path.
    print("Received audio uri!")
    audio_uri = parse.unquote(audio_uri)
    file_ext = audio_uri.split(".")[-1]
    audio_input_path = os.path.join(abs_cwd, uuid.uuid1().hex + "." + file_ext)
    try:
      print("Downloading audio file from URI...")
      with request.urlopen(audio_uri) as response, open(audio_input_path, "wb") as f:
        f.write(response.read())
        f.close()
    except Exception as e:
      return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while downloading your audio file. Please try again later."})

  audio_file= open(audio_input_path, "rb")
  try:
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
  except Exception as e:
    print(e)
    return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while transcribing your audio file. Please try again later."})
  
  os.remove(audio_input_path)
  
  return JSONResponse(status_code=200, content=transcript)


@app.put("/replicate")
async def replicate_model(audio_file: Annotated[UploadFile, File(...)] = None,
                      audio_uri: Annotated[str, Form(...)] = None):
  if audio_file is None and audio_uri is None:
    return JSONResponse(status_code=400, content={"error": "Please provide either an audio file or an audio URI."})
  if audio_file is not None and audio_uri is not None:
    return JSONResponse(status_code=400, content={"error": "Please provide either an audio file or an audio URI, not both."})
  
  if audio_file is not None:
    # Write audio file to disk. Save location in audio_input_path.
    print("Received audio file!")
    file_ext = audio_file.filename.split(".")[-1]
    audio_input_path = os.path.join(abs_cwd, uuid.uuid1().hex + "." + file_ext)
    try:
      print("Writing audio file to disk...")
      with open(audio_input_path, "wb") as f:
        f.write(audio_file.file.read())
        f.close()
    except Exception as e:
      return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while saving your audio file. Please try again later."})
  else:
    # Download audio file from URI. Save location in audio_input_path.
    print("Received audio uri!")
    audio_uri = parse.unquote(audio_uri)
    file_ext = audio_uri.split(".")[-1]
    audio_input_path = os.path.join(abs_cwd, uuid.uuid1().hex + "." + file_ext)
    try:
      print("Downloading audio file from URI...")
      with request.urlopen(audio_uri) as response, open(audio_input_path, "wb") as f:
        f.write(response.read())
        f.close()
    except Exception as e:
      return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while downloading your audio file. Please try again later."})
    
  try:
    output = replicate.run(
      "m1guelpf/whisper-subtitles:7f686e243a96c7f6f0f481bcef24d688a1369ed3983cea348d1f43b879615766",
      input={
        "audio_path": open(audio_input_path, "rb"),
        "model_name": "large"
      }
    )
  except Exception as e:
    return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while running Whisper. Please try again later."})
  
  os.remove(audio_input_path)
  
  return JSONResponse(status_code=200, content=output)


@app.put("/whisper")
async def whisper_model(audio_file: Annotated[UploadFile, File(...)] = None,
                        audio_uri: Annotated[str, Form(...)] = None):
  if audio_file is None and audio_uri is None:
    return JSONResponse(status_code=400, content={"error": "Please provide either an audio file or an audio URI."})
  if audio_file is not None and audio_uri is not None:
    return JSONResponse(status_code=400, content={"error": "Please provide either an audio file or an audio URI, not both."})
  
  if audio_file is not None:
    # Write audio file to disk. Save location in audio_input_path.
    print("Received audio file!")
    file_ext = audio_file.filename.split(".")[-1]
    audio_input_path = os.path.join(abs_cwd, uuid.uuid1().hex + "." + file_ext)
    try:
      print("Writing audio file to disk...")
      with open(audio_input_path, "wb") as f:
        f.write(audio_file.file.read())
        f.close()
    except Exception as e:
      return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while saving your audio file. Please try again later."})
  else:
    # Download audio file from URI. Save location in audio_input_path.
    print("Received audio uri!")
    audio_uri = parse.unquote(audio_uri)
    file_ext = audio_uri.split(".")[-1]
    audio_input_path = os.path.join(abs_cwd, uuid.uuid1().hex + "." + file_ext)
    try:
      print("Downloading audio file from URI...")
      with request.urlopen(audio_uri) as response, open(audio_input_path, "wb") as f:
        f.write(response.read())
        f.close()
    except Exception as e:
      return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while downloading your audio file. Please try again later."})

  try:
    model = whisper.load_model("medium", download_root=abs_cwd)
    result = whisper.transcribe(model, audio_input_path)
  except Exception as e:
    return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while running Whisper. Please try again later."})
  #result = TEST_RESULT
  try:
    cleaned_segments = list(map(lambda x: segment_cleaner(x), result["segments"]))
  except Exception as e:
    return JSONResponse(status_code=500, content={"error": "Sorry, an error occurred while cleaning your results. Please try again later."})

  # Delete audio file from disk.
  os.remove(audio_input_path)

  return cleaned_segments


def segment_cleaner(segment):
  # Remove all keys from segment except for the following: "start", "end", "text"
  cleaned_segment = {}
  keys_to_keep = ["start", "end", "text"]
  for key in keys_to_keep:
    cleaned_segment[key] = segment[key]
  return cleaned_segment


if __name__ == "__main__":
  if os.environ.get('PROD'):
    uvicorn.run("app:app", host="0.0.0.0", port=os.environ.get('PORT', 8080), reload=False)
  else:
    print("Running in dev mode...")
    uvicorn.run("app:app", host="0.0.0.0", port=os.environ.get('PORT', 8080), reload=True)