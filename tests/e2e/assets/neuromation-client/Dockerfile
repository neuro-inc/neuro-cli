FROM python:3.6-slim

RUN apt update && \
    apt install -y build-essential

# installing dependencies ONLY
COPY setup.py ./
COPY README.md ./
COPY neuromation neuromation
RUN pip install -e .

CMD ["neuro", "config", "show"]