# Use a lightweight Python base image
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libchromaprint-dev \
    ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt --no-cache-dir 

# Copy the Python script(s) into the container and make the py executable
COPY config.json /usr/bin/
COPY app.py /usr/bin/update_metadata.py
RUN chmod +x /usr/bin/update_metadata.py


# Set working directory Change this to /media/music coordinate with config.json
RUN mkdir -p /media/music
WORKDIR /media/music

# Install dependencies and ttyd
COPY requirements.txt .
RUN apt update && apt install -y git curl && rm -rf /var/lib/apt/lists/* && \
    curl -L -o /usr/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.aarch64 && \
    chmod +x /usr/bin/ttyd

RUN apt update && apt install -y --no-install-recommends tini && rm -rf /var/lib/apt/lists/*

# Expose ports for Streamlit and ttyd
EXPOSE 8501 7681

# Create instructions as MOTD
RUN cat <<EOF > /etc/motd

Welcome to the system!
Today is: $(date)

You should be in music/
To scan oll audio media files and apply tags to missing metadata,
feel free to navigate to MAIN and run:

update_metadata.py

EOF
RUN echo -n "cat /etc/motd" >> /root/.bashrc


ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/bin/ttyd", "-W", "bash"]
