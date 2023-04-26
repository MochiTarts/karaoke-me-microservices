FROM python:3.9.16-slim-buster

WORKDIR /app
COPY app.py requirements.txt ./

# Install ffmpeg and pip dependencies, then remove unnecessary packages
RUN apt update && apt install -y ffmpeg && rm -rf /var/lib/apt/lists/*
#RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install -U -r requirements.txt --no-cache-dir
# Remove unnecessary packages
RUN apt autoclean && apt autoremove

ENV PORT $PORT
ENV PROD $PROD
# Run the app
ENTRYPOINT [ "python", "app.py" ]