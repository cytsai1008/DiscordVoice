FROM ubuntu:latest
COPY . /app
WORKDIR /app

# RUN --mount=type=secret,id=_env,dst=/etc/secrets/.env cat /etc/secrets/.env

# Install dependencies
RUN apt-get update && apt install software-properties-common -y
RUN add-apt-repository 'deb [trusted=yes arch=amd64] http://security.ubuntu.com/ubuntu bionic-security main' -y
RUN add-apt-repository ppa:savoury1/ffmpeg4 -y
RUN add-apt-repository ppa:savoury1/ffmpeg5 -y
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python3-pip build-essential libssl-dev libasound2 wget libssl1.1 ffmpeg opus-tools libpq-dev htop nano
RUN apt autoremove -y
RUN pip3 install -r requirements.txt
# RUN pip install python-dotenv

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