# G.I.D Secure Terminal v2.0

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![RSA](https://img.shields.io/badge/Encryption-RSA--2048-green?logo=lock&logoColor=white)
![AES](https://img.shields.io/badge/Encryption-AES--256-green?logo=lock&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-2.0-brightgreen)

**G.I.D Secure Terminal** is an advanced End-to-End Encrypted (E2EE) chat application with a professional terminal interface. Built with military-grade encryption for complete privacy in communications.

---

## Features

### Core Security

- **End-to-End Encryption**: Hybrid encryption using RSA-2048 and AES-256
- **Persistent Identity**: Password-protected keypair storage with consistent Agent IDs
- **Zero-Knowledge Server**: Server cannot decrypt any messages or files
- **Quick Access Verification**: Simple authentication system

### Communication

- **Secure Messaging**: Real-time encrypted text communication
- **File Transfer**: Send encrypted files using `/sendfile <filepath>`
- **Group Chat**: Message multiple agents simultaneously
- **Offline Message Delivery**: Messages buffered and delivered when recipients come online
- **Message History**: Local encrypted chat logs with `/history` command
- **Typing Indicators**: Real-time typing notifications
- **Read Receipts**: Message delivery status tracking
- **Message Timestamps**: Precise timestamps on all communications

### Network & Discovery

- **Agent Discovery**: `/agents` command to list all online users
- **Online Status Tracking**: Real-time availability status
- **Auto-Reconnect**: Automatic connection recovery
- **Last Seen Timestamps**: Track when agents were last active

### Professional Features (v2.0)

- **Block System**: Block/unblock agents with `/block` and `/unblock`
- **Statistics Dashboard**: View session stats with `/stats` command
- **Chat Export**: Export conversations to TXT or JSON with `/export`
- **Configuration System**: Customize settings via `config.json`
- **Comprehensive Logging**: Server and client logs for monitoring

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/F9-o/Python-E2EE-Hacker-Chat.git
   ```

2. **Navigate to the directory:**

   ```bash
   cd Python-E2EE-Hacker-Chat
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Starting the Server

```bash
python server.py
```

Server listens on `0.0.0.0:5555` by default (configurable in `config.json`).

### Connecting as a Client

1. **Run the client:**

   ```bash
   python client.py
   ```

2. **Identity Setup:**
   - First time: Create password to encrypt your identity keypair
   - Returning users: Enter existing password to load identity

3. **Security Verification:**
   - Enter access code (default: 'SECURE' or press Enter)

4. **Connect to Target:**
   - Use `/agents` to see who's online
   - Enter target Agent ID to communicate

### Available Commands

| Command                          | Description                        |
| -------------------------------- | ---------------------------------- |
| `/agents`                        | List all online agents with status |
| `/sendfile <filepath>`           | Send encrypted file                |
| `/history [agent-id]`            | View chat history                  |
| `/block <agent-id>`              | Block an agent                     |
| `/unblock <agent-id>`            | Unblock an agent                   |
| `/blocklist`                     | View blocked agents                |
| `/stats`                         | View session statistics            |
| `/export <agent-id> [txt\|json]` | Export chat history                |
| `/clear`                         | Clear terminal screen              |
| `/exit` or `/quit`               | Disconnect                         |
| `/help`                          | Display available commands         |

---

## Example Session

```
╔═══════════════════════════════════════════════╗
║      G.I.D SECURE TERMINAL v2.0 (E2EE)        ║
╚═══════════════════════════════════════════════╝

INITIALIZING RSA-2048 CRYPTO ENGINE...

[*] EXISTING IDENTITY DETECTED
ENTER IDENTITY PASSWORD: ********
[+] IDENTITY LOADED FROM identity.pem

[!] SECURITY VERIFICATION PROTOCOL
--------------------------------------------------
ENTER ACCESS CODE (default: 'SECURE'):
VERIFYING ACCESS...

[*] CONNECTING TO 127.0.0.1:5555...

IDENTITY VERIFIED: AGENT-A3F7B2C8D1E9
PUBLIC KEY FINGERPRINT: MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...
--------------------------------------------------

ENTER TARGET AGENT ID (or /agents to list): /agents

=== ONLINE AGENTS ===
AGENT-A3F7B2C8D1E9 [ONLINE] - Last seen: 2026-01-18 15:10:15
AGENT-B4E8C3D2F1A0 [ONLINE] - Last seen: 2026-01-18 15:10:20

ENTER TARGET AGENT ID: AGENT-B4E8C3D2F1A0
[*] FETCHING KEY FOR AGENT-B4E8C3D2F1A0...
[+] SECURE CHANNEL ESTABLISHED.

[COMMANDS] /agents | /block | /stats | /export | /help

[SECURE INPUT] >> Hello, secure communication!
[SENT] 2048-BIT ENCRYPTED PACKET.

[MSG] FROM AGENT-B4E8C3D2F1A0 (E2EE)
>> Message received!
[2026-01-18 15:10:23]

[SECURE INPUT] >> /stats

=== SESSION STATISTICS ===
Messages Sent: 5
Messages Received: 3
Files Sent: 1
Files Received: 0
Data Sent: 2,048 bytes
Data Received: 1,536 bytes
Session Uptime: 00:15:42

[SECURE INPUT] >> /export AGENT-B4E8C3D2F1A0 txt
[+] CHAT EXPORTED: exports/AGENT-B4E8C3D2F1A0_20260118_151025.txt

[SECURE INPUT] >> /exit
[*] DISCONNECTING...
```

---

## Security Architecture

### Encryption Flow

1. **Key Generation**: 2048-bit RSA keypair per client
2. **Persistent Identity**: Private key encrypted with user password (PKCS8)
3. **Agent ID**: Derived from SHA-256 hash of public key
4. **Message Encryption**: Hybrid RSA + AES-256 (Fernet)
5. **File Encryption**: Same hybrid approach for file transfers

### Server Role

The server is a **key exchange and routing hub** only:

- Stores public keys (not private keys)
- Routes encrypted messages between clients
- Buffers offline messages
- Tracks agent status
- **Cannot decrypt any messages or files**

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
├── .gitignore            # Git ignore rules
├── identity.pem          # Encrypted private key (auto-generated)
├── blocklist.json        # Blocked agents list (auto-generated)
├── chat_history/         # Message history logs (auto-created)
├── downloads/            # Received files directory (auto-created)
├── exports/              # Exported chats directory (auto-created)
├── logs/                 # Server and client logs (auto-created)
└── README.md             # This file
```

---

## Troubleshooting

### "SERVER UNREACHABLE"

- Ensure the server is running
- Check firewall settings
- Verify `host` and `port` in `config.json`

### "INVALID PASSWORD OR CORRUPTED IDENTITY"

- Wrong password entered
- Delete `identity.pem` to create new identity (new Agent ID)

### "TARGET AGENT NOT REGISTERED"

- Target agent must connect to server at least once
- Verify Agent ID using `/agents` command

### Connection Drops

- Auto-reconnect enabled by default
- Check logs in `logs/` directory

---

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

---

## License

This project is licensed under the MIT License.

---

## Credits

**Original Concept:** [AhmedFox1](https://github.com/ahmedfox1)  
**Enhanced & Developed by:** [F9-o](https://github.com/F9-o)

### v2.0 Enhancements:

- Persistent Identity System with Password Encryption
- Encrypted File Transfer Support
- Agent Discovery & Online Status Tracking
- Message History with Local Storage
- Typing Indicators & Read Receipts
- Group Chat Support
- Auto-Reconnect Mechanism
- Block/Unblock System
- Session Statistics Dashboard
- Chat Export (TXT/JSON)
- Configuration System
- Comprehensive Logging

---

## Disclaimer

This tool is for educational and legitimate privacy purposes only. The developers are not responsible for any misuse of this software.
