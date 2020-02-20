FROM python:3.7-slim

RUN apt update && \
    apt install -y build-essential

# installing dependencies ONLY
COPY setup.py ./
COPY README.md ./
COPY neuromation neuromation
COPY requirements.txt ./
RUN pip install -r requirements.txt


CMD sleep 5 && neuro config show