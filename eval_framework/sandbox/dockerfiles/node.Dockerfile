# eval_framework/sandbox/dockerfiles/node.Dockerfile
FROM node:20-slim

RUN npm install -g jest

WORKDIR /eval

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
