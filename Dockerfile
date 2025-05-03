FROM python:3.11-slim

WORKDIR /app

RUN apt-get update --allow-insecure-repositories
RUN apt-get install debian-archive-keyring --allow-unauthenticated
RUN apt-get install -y ffmpeg --allow-unauthenticated
COPY requirements.txt /app/
RUN pip install -r requirements.txt

RUN pip install uv

COPY . .
# docker 启动时，默认使用 SSE 协议
ENV BILISCRIBE_SERVER_SSE=true

CMD ["uv", "run", "src/mcp_server_biliscribe"]