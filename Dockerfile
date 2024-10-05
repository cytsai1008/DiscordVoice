FROM python:slim
COPY . /app
WORKDIR /app

# RUN --mount=type=secret,id=_env,dst=/etc/secrets/.env cat /etc/secrets/.env
# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common gnupg && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 871920D1991BC93C && \
    add-apt-repository 'deb [trusted=yes arch=amd64] http://security.ubuntu.com/ubuntu bionic-security main' -y && \
    add-apt-repository 'deb [trusted=yes arch=amd64] http://archive.ubuntu.com/ubuntu jammy main universe' -y && \
    add-apt-repository 'deb [trusted=yes arch=amd64] http://archive.ubuntu.com/ubuntu jammy main main' -y && \
    add-apt-repository 'deb [trusted=yes arch=amd64] http://http.us.debian.org/debian bullseye main' -y && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    libssl-dev libssl1.1 wget ffmpeg opus-tools libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app
COPY . /app

# Set up Python environment
RUN python3 -m venv /app/venv && \
    . /app/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt


# Setup Environments
# RUN --mount=type=secret,id=_env,dst=./.env cat ./.env
# ENV DISCORD_DV_TOKEN $DISCORD_DV_TOKEN
# ENV DISCORD_DV_PREFIX $DISCORD_DV_PREFIX
# ENV DISCORD_WFNM_TOKEN $DISCORD_WFNM_TOKEN
# ENV DISCORD_WFNM_PREFIX $DISCORD_WFNM_PREFIX
# ENV DISCORD_OWNER $DISCORD_OWNER
# ENV REDIS_DV_URL $REDIS_DV_URL
# ENV REDIS_USER $REDIS_USER
# ENV REDIS_DV_PASSWD $REDIS_DV_PASSWD
# ENV REDIS_WFNM_URL $REDIS_WFNM_URL
# ENV REDIS_WFNM_PASSWD $REDIS_WFNM_PASSWD
# ENV GCP_TOKEN $GCP_TOKEN
# ENV GOOGLE_APPLICATION_CREDENTIALS gcp-token.json
# ENV AZURE_TTS_KEY $AZURE_TTS_KEY
# ENV DATABASE_URL $DATABASE_URL
# ENV PORT $PORT
ENV PYTHONPATH .:$PYTHONPATH

# Run the bot
RUN chmod +x ./main.sh

CMD ./main.sh
