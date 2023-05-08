FROM amazon/aws-lambda-python:3.9
ENV PYTHONUNBUFFERED=1

ENV NUMBA_CACHE_DIR=/tmp/NUMBA_CACHE_DIR/
RUN mkdir -m 777 /tmp/NUMBA_CACHE_DIR/

RUN yum install -y tar xz

# Install ffmpeg
ADD https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz /tmp/ffmpeg.tar.xz
RUN cd /tmp && \
    tar Jxvf ffmpeg.tar.xz && \
    cp ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ffmpeg && \
    cp ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ffprobe

# Download pretrained models (2stems only)
RUN cd ${LAMBDA_TASK_ROOT} && \
    mkdir -p ./pretrained_models/2stems && \
    yum -y install tar wget gzip && \
    wget -O 2stems.tar.gz https://github.com/deezer/spleeter/releases/download/v1.4.0/2stems.tar.gz && \
    tar -xf 2stems.tar.gz -C ./pretrained_models/2stems && \
    rm -r 2stems.tar.gz

WORKDIR ${LAMBDA_TASK_ROOT}

# Install python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir --default-timeout=1000 --target "${LAMBDA_TASK_ROOT}"
RUN find /var/lang/lib/python3.9/site-packages -name "*.dist-info" -exec rm -rf {} \; | true && \
    find /var/lang/lib/python3.9/site-packages -name "*.egg-info" -exec rm -rf {} \; | true && \
    find /var/lang/lib/python3.9/site-packages -name "*.pth" -exec rm -rf {} \; | true && \
    find /var/lang/lib/python3.9/site-packages -name "__pycache__" -exec rm -rf {} \; | true && \
    rm -rf requirements.txt

ARG BUCKET_NAME
ARG CONNECTIONS_TABLE_NAME
ARG REGION
ENV BUCKET_NAME=${BUCKET_NAME}
ENV CONNECTIONS_TABLE_NAME=${CONNECTIONS_TABLE_NAME}
ENV REGION=${REGION}
ENV MODEL_PATH="${LAMBDA_TASK_ROOT}/pretrained_models"

COPY app.py "${LAMBDA_TASK_ROOT}"

RUN chmod -R o+rwx app.py
CMD [ "app.handler" ]