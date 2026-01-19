# G.I.D Secure Terminal v3.0

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![RSA](https://img.shields.io/badge/Encryption-RSA--2048-green?logo=lock&logoColor=white)
![AES](https://img.shields.io/badge/Encryption-AES--256-green?logo=lock&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-3.0-brightgreen)

**G.I.D Secure Terminal** is a production-ready End-to-End Encrypted (E2EE) chat application with professional features. Built with military-grade encryption for complete privacy in communications.

---

## Features

### Core Security

- **End-to-End Encryption**: Hybrid RSA-2048 + AES-256 encryption
- **Persistent Identity**: Password-protected keypair storage with consistent Agent IDs
- **Zero-Knowledge Server**: Server cannot decrypt any messages or files
- **Secure Password Input**: Hidden password entry using getpass (v3.0)

### Communication

- **Secure Messaging**: Real-time encrypted text communication
- **File Transfer**: Send encrypted files using `/sendfile <filepath>`
- **Voice Notes**: Record and send encrypted voice messages with `/record` (v3.0)
- **Group Chat**: Message multiple agents simultaneously
- **Offline Message Delivery**: Messages buffered for offline recipients
- **Message History**: Local encrypted chat logs
- **Typing Indicators**: Real-time typing notifications
- **Read Receipts**: Message delivery status tracking

### Network & Discovery

- **Agent Discovery**: `/agents` command to list online users
- **Online Status Tracking**: Real-time availability status
- **Auto-Reconnect**: Automatic connection recovery
- **Last Seen Timestamps**: Track agent activity

### Professional Features

- **Block System**: Block/unblock agents with `/block` and `/unblock`
- **Statistics Dashboard**: View session stats with `/stats`
- **Chat Export**: Export conversations to TXT or JSON
- **Docker Support**: One-command deployment with Docker Compose (v3.0)
- **Configuration System**: Customize via `config.json`
- **Comprehensive Logging**: Server and client logs

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ahmedfox1/Python-E2EE-Hacker-Chat.git
   cd Python-E2EE-Hacker-Chat
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   **Optional (for voice notes):**

   ```bash
   pip install sounddevice soundfile numpy
   ```

---

## Usage

### Starting the Server

**Option 1: Python (Development)**

```bash
python server.py
```

**Option 2: Docker (Production)**

```bash
docker-compose up -d
```

Server listens on `0.0.0.0:5555` by default (configurable in `config.json`).

### Connecting as a Client

1. **Run the client:**

   ```bash
   python client.py
   ```

2. **Identity Setup:**
   - First time: Create password to encrypt your identity (min 8 characters)
   - Returning users: Enter existing password (hidden input)
   - 3 attempts before lockout

3. **Security Verification:**
   - Enter access code (default: 'SECURE' or press Enter)

4. **Connect to Target:**
   - Use `/agents` to see who's online
   - Enter target Agent ID to communicate

### Available Commands

| Command                          | Description                              |
| -------------------------------- | ---------------------------------------- |
| `/agents`                        | List all online agents with status       |
| `/sendfile <filepath>`           | Send encrypted file                      |
| `/record [duration]`             | Record voice note (default 10s, max 60s) |
| `/history [agent-id]`            | View chat history                        |
| `/block <agent-id>`              | Block an agent                           |
| `/unblock <agent-id>`            | Unblock an agent                         |
| `/blocklist`                     | View blocked agents                      |
| `/stats`                         | View session statistics                  |
| `/export <agent-id> [txt\|json]` | Export chat history                      |
| `/clear`                         | Clear terminal screen                    |
| `/exit` or `/quit`               | Disconnect                               |
| `/help`                          | Display available commands               |

---

## Docker Deployment

### Quick Start

```bash
docker-compose up -d
```

### Cloud Deployment

**AWS EC2:**

```bash
git clone https://github.com/ahmedfox1/Python-E2EE-Hacker-Chat.git
cd Python-E2EE-Hacker-Chat
docker-compose up -d
```

**DigitalOcean:**

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
git clone https://github.com/ahmedfox1/Python-E2EE-Hacker-Chat.git
cd Python-E2EE-Hacker-Chat
docker-compose up -d
```

See [DOCKER.md](DOCKER.md) for detailed deployment guide.

---

## Security Architecture

### Encryption Flow

1. **Key Generation**: 2048-bit RSA keypair per client
2. **Persistent Identity**: Private key encrypted with user password (PKCS8)
3. **Agent ID**: Derived from SHA-256 hash of public key
4. **Message Encryption**: Hybrid RSA + AES-256 (Fernet)
5. **File/Voice Encryption**: Same hybrid approach

### Server Role

The server is a **key exchange and routing hub** only:

- Stores public keys (not private keys)
- Routes encrypted messages between clients
- Buffers offline messages
- Tracks agent status
- **Cannot decrypt any messages, files, or voice notes**

---

## Configuration

Edit `config.json` to customize settings:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 5555
  },
  "client": {
    "auto_reconnect": true,
    "reconnect_delay": 5,
    "max_reconnect_attempts": 10,
    "save_history": true,
    "typing_indicators": true,
    "read_receipts": true
  }
}
```

---

## Project Structure

```
Python-E2EE-Hacker-Chat/
├── server.py              # Central key server and message router
├── client.py              # Client application with E2EE
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker orchestration
├── DOCKER.md             # Docker deployment guide
├── .gitignore            # Git ignore rules
├── .dockerignore         # Docker ignore rules
├── identity.pem          # Encrypted private key (auto-generated)
├── blocklist.json        # Blocked agents list (auto-generated)
├── chat_history/         # Message history logs (auto-created)
├── downloads/            # Received files (auto-created)
├── exports/              # Exported chats (auto-created)
├── voice_notes/          # Voice recordings (auto-created)
├── logs/                 # Server and client logs (auto-created)
└── README.md             # This file
```

---

## Troubleshooting

### "SERVER UNREACHABLE"

- Ensure the server is running
- Check firewall settings
- Verify `host` and `port` in `config.json`

### "INCORRECT PASSWORD"

- You have 3 attempts before lockout
- Password is case-sensitive
- Delete `identity.pem` to create new identity (new Agent ID)

### "TARGET AGENT NOT REGISTERED"

- Target agent must connect to server at least once
- Verify Agent ID using `/agents` command

### Voice Recording Not Available

```bash
pip install sounddevice soundfile numpy
```

### Docker Issues

```bash
docker-compose logs -f
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

This project is licensed under the MIT License.

---

## Credits

**Original Concept & Development:** [AhmedFox1](https://github.com/ahmedfox1)  
**v2.0 & v3.0 Enhancements:** [F9-o](https://github.com/F9-o)

### Version History

**v3.0 (Production-Ready):**

- Secure password input with getpass
- Docker containerization
- Voice notes support
- Enhanced security and UX

**v2.0:**

- Persistent Identity System
- Encrypted File Transfer
- Agent Discovery & Status
- Message History
- Typing Indicators & Read Receipts
- Group Chat Support
- Auto-Reconnect
- Block/Unblock System
- Statistics Dashboard
- Chat Export

**v1.0:**

- End-to-End Encryption (RSA + AES)
- Basic messaging
- Key exchange server

---

## Disclaimer

This tool is for educational and legitimate privacy purposes only. The developers are not responsible for any misuse of this software.

---

## Repository

**Original:** [https://github.com/ahmedfox1/Python-E2EE-Hacker-Chat](https://github.com/ahmedfox1/Python-E2EE-Hacker-Chat)  
**Enhanced Fork:** [https://github.com/F9-o/Python-E2EE-Hacker-Chat](https://github.com/F9-o/Python-E2EE-Hacker-Chat)
