# eval_framework/sandbox/dockerfiles/python.Dockerfile
FROM python:3.12-slim

RUN pip install --no-cache-dir pytest pytest-cov

WORKDIR /eval

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
