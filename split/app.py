import os, subprocess

def root():
  print(" -- pip install --upgrade demucs")
  path_to_audio_file = os.path.join(os.getcwd(), "viva_la_vida.mp3")
  cmd = ["python3", "-m", "demucs.separate", "--two-stems=vocals", path_to_audio_file]
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
  # Write process to stdout
  for stdout_line in iter(p.stdout.readline, ""):
    print(stdout_line, end="")
  p.stdout.close()
  p.wait()
  if p.returncode != 0:
    print("Error: ", p.stderr.read())

if __name__ == "__main__":
  root()