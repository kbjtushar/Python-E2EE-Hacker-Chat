# Docker Deployment Guide

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and start the server:**

   ```bash
   docker-compose up -d
   ```

2. **View logs:**

   ```bash
   docker-compose logs -f
   ```

3. **Stop the server:**
   ```bash
   docker-compose down
   ```

### Using Docker Directly

1. **Build the image:**

   ```bash
   docker build -t gid-server .
   ```

2. **Run the container:**

   ```bash
   docker run -d \
     --name gid-secure-terminal \
     -p 5555:5555 \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/config.json:/app/config.json:ro \
     --restart unless-stopped \
     gid-server
   ```

3. **View logs:**

   ```bash
   docker logs -f gid-secure-terminal
   ```

4. **Stop the container:**
   ```bash
   docker stop gid-secure-terminal
   docker rm gid-secure-terminal
   ```

## Configuration

Edit `config.json` before deployment:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5555
  }
}
```

## Cloud Deployment

### AWS EC2

```bash
# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start

# Clone repository
git clone https://github.com/F9-o/Python-E2EE-Hacker-Chat.git
cd Python-E2EE-Hacker-Chat

# Deploy
docker-compose up -d
```

### DigitalOcean Droplet

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone and deploy
git clone https://github.com/F9-o/Python-E2EE-Hacker-Chat.git
cd Python-E2EE-Hacker-Chat
docker-compose up -d
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/gid-server

# Deploy
gcloud run deploy gid-server \
  --image gcr.io/PROJECT_ID/gid-server \
  --platform managed \
  --port 5555 \
  --allow-unauthenticated
```

## Security Notes

- The container runs as non-root user (UID 1000)
- Logs are persisted via volume mount
- Configuration is read-only mounted
- Health checks ensure service availability
- Automatic restart on failure

## Troubleshooting

### Container won't start

```bash
docker logs gid-secure-terminal
```

### Port already in use

```bash
# Change port in docker-compose.yml
ports:
  - "5556:5555"  # External:Internal
```

### Permission issues

```bash
# Fix log directory permissions
chmod 777 logs/
```
