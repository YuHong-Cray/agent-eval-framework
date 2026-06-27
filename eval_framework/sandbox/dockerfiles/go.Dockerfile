# eval_framework/sandbox/dockerfiles/go.Dockerfile
FROM golang:1.22-alpine

RUN go install github.com/stretchr/testify/assert@latest

WORKDIR /eval

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
