FROM ubuntu:latest

RUN apt update && \
    apt install -y build-essential

# installing dependencies ONLY
COPY setup.py ./
COPY README.md ./
COPY neuromation neuromation
COPY requirements.txt ./
RUN pip install -r requirements.txt

CMD ["neuro", "config", "show"]