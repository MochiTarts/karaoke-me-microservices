FROM amazon/aws-lambda-python:3.9

RUN yum install -y tar xz

# Install ffmpeg
ADD https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz /tmp/ffmpeg.tar.xz
RUN cd /tmp && \
    tar Jxvf ffmpeg.tar.xz && \
    cp ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ffmpeg && \
    cp ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ffprobe

# Install python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir --target "${LAMBDA_TASK_ROOT}"
RUN find /var/lang/lib/python3.9/site-packages -name "*.dist-info" -exec rm -rf {} \; | true && \
    find /var/lang/lib/python3.9/site-packages -name "*.egg-info" -exec rm -rf {} \; | true && \
    find /var/lang/lib/python3.9/site-packages -name "*.pth" -exec rm -rf {} \; | true && \
    find /var/lang/lib/python3.9/site-packages -name "__pycache__" -exec rm -rf {} \; | true && \
    rm -rf requirements.txt

ENV BUCKET_NAME=${BUCKET_NAME}

COPY youtube_dl.py "${LAMBDA_TASK_ROOT}"

# Change permissions of all files in current directory
RUN chmod -R o+rwx "${LAMBDA_TASK_ROOT}"
CMD [ "youtube_dl.handler" ]