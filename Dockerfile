FROM node:22-alpine AS client

WORKDIR /web
COPY weather-app/package.json weather-app/package-lock.json ./
RUN npm ci
COPY weather-app/ .
RUN npm run build

FROM python:3.11-slim

WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ .
COPY --from=client /web/dist ./static
ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000
CMD ["python", "server.py"]
