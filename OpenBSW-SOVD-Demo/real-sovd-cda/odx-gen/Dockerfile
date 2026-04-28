FROM python:3.12-slim-trixie
RUN pip install --no-cache-dir odxtools==11.0.0
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/python", "generate_openbsw.py"]
