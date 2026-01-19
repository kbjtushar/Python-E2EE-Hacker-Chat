# Dockerfile for G.I.D Secure Terminal Server

FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server files
COPY server.py .
COPY config.json .

# Create necessary directories
RUN mkdir -p logs

# Expose port
EXPOSE 5555

# Run as non-root user
RUN adduser -D -u 1000 gid-server
USER gid-server

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 5555)); s.close()" || exit 1

# Run server
CMD ["python", "-u", "server.py"]
