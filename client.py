import socket
import threading
import random
import time
import os
import sys
import shutil
import hashlib
import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, init
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.fernet import Fernet

init(autoreset=True)

# Load configuration
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "server": {"host": "127.0.0.1", "port": 5555},
    "client": {
        "auto_reconnect": True,
        "reconnect_delay": 5,
        "max_reconnect_attempts": 10,
        "save_history": True,
        "typing_indicators": True,
        "read_receipts": True
    }
}

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

config = load_config()
SERVER_IP = config["server"]["host"]
SERVER_PORT = config["server"]["port"]
IDENTITY_FILE = "identity.pem"
DOWNLOADS_DIR = "downloads"
HISTORY_DIR = "chat_history"
BLOCKLIST_FILE = "blocklist.json"

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename='logs/client.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

client = None
private_key = None
public_key = None
pem_public = None
my_agent_id = None
target_public_key_cache = None
blocked_agents = set()
session_stats = {
    "messages_sent": 0,
    "messages_received": 0,
    "files_sent": 0,
    "files_received": 0,
    "bytes_sent": 0,
    "bytes_received": 0,
    "start_time": None
}
typing_timer = None
last_typing_time = 0
is_connected = False

# ==================== UTILITY FUNCTIONS ====================

def get_width():
    try: 
        return shutil.get_terminal_size().columns
    except: 
        return 80

def clear_screen(): 
    os.system('cls' if os.name == 'nt' else 'clear')

def play_sound(): 
    sys.stdout.write('\a')
    sys.stdout.flush()

def print_centered(text, color=Fore.WHITE, style=Style.NORMAL):
    width = get_width()
    padding = max(0, (width - len(text)) // 2)
    print(" " * padding + color + style + text)

def input_centered(prompt_text, color=Fore.YELLOW):
    width = get_width()
    padding = max(0, (width - len(prompt_text) - 10) // 2) 
    sys.stdout.write(" " * padding + color + prompt_text)
    sys.stdout.flush()
    return input(Fore.WHITE)

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ==================== MESSAGE HISTORY ====================

def save_message_to_history(agent_id, message, direction="sent"):
    """Save encrypted message to local history"""
    if not config["client"]["save_history"]:
        return
    
    try:
        os.makedirs(HISTORY_DIR, exist_ok=True)
        history_file = os.path.join(HISTORY_DIR, f"{agent_id}.log")
        
        timestamp = get_timestamp()
        entry = f"[{timestamp}] [{direction.upper()}] {message}\n"
        
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception as e:
        logging.error(f"Error saving history: {e}")

def load_message_history(agent_id, limit=50):
    """Load message history for an agent"""
    try:
        history_file = os.path.join(HISTORY_DIR, f"{agent_id}.log")
        if not os.path.exists(history_file):
            return []
        
        with open(history_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        return lines[-limit:] if len(lines) > limit else lines
    except Exception as e:
        logging.error(f"Error loading history: {e}")
        return []

# ==================== BLOCK SYSTEM ====================

def load_blocklist():
    """Load blocked agents from file"""
    global blocked_agents
    try:
        if os.path.exists(BLOCKLIST_FILE):
            with open(BLOCKLIST_FILE, 'r') as f:
                blocked_agents = set(json.load(f))
    except Exception as e:
        logging.error(f"Error loading blocklist: {e}")
        blocked_agents = set()

def save_blocklist():
    """Save blocked agents to file"""
    try:
        with open(BLOCKLIST_FILE, 'w') as f:
            json.dump(list(blocked_agents), f, indent=2)
    except Exception as e:
        logging.error(f"Error saving blocklist: {e}")

def block_agent(agent_id):
    """Block an agent"""
    blocked_agents.add(agent_id)
    save_blocklist()
    print_centered(f"[+] BLOCKED: {agent_id}", Fore.RED)

def unblock_agent(agent_id):
    """Unblock an agent"""
    if agent_id in blocked_agents:
        blocked_agents.remove(agent_id)
        save_blocklist()
        print_centered(f"[+] UNBLOCKED: {agent_id}", Fore.GREEN)
    else:
        print_centered(f"[!] {agent_id} IS NOT BLOCKED", Fore.YELLOW)

def is_blocked(agent_id):
    """Check if an agent is blocked"""
    return agent_id in blocked_agents

# ==================== STATISTICS ====================

def update_stats(stat_type, value=1):
    """Update session statistics"""
    if stat_type in session_stats:
        session_stats[stat_type] += value

def get_uptime():
    """Get session uptime"""
    if session_stats["start_time"]:
        elapsed = time.time() - session_stats["start_time"]
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return "00:00:00"

def show_statistics():
    """Display session statistics"""
    print("\n")
    print_centered("=== SESSION STATISTICS ===", Fore.CYAN, Style.BRIGHT)
    print_centered(f"Messages Sent: {session_stats['messages_sent']}", Fore.WHITE)
    print_centered(f"Messages Received: {session_stats['messages_received']}", Fore.WHITE)
    print_centered(f"Files Sent: {session_stats['files_sent']}", Fore.WHITE)
    print_centered(f"Files Received: {session_stats['files_received']}", Fore.WHITE)
    print_centered(f"Data Sent: {session_stats['bytes_sent']:,} bytes", Fore.WHITE)
    print_centered(f"Data Received: {session_stats['bytes_received']:,} bytes", Fore.WHITE)
    print_centered(f"Session Uptime: {get_uptime()}", Fore.WHITE)
    print("\n")

# ==================== EXPORT SYSTEM ====================

def export_chat(agent_id, format_type="txt"):
    """Export chat history to file"""
    try:
        history = load_message_history(agent_id, limit=None)
        
        if not history:
            print_centered(f"[!] NO HISTORY FOUND FOR {agent_id}", Fore.YELLOW)
            return
        
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type.lower() == "txt":
            filename = os.path.join(export_dir, f"{agent_id}_{timestamp}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Chat Export: {my_agent_id} <-> {agent_id}\n")
                f.write(f"Exported: {get_timestamp()}\n")
                f.write("=" * 60 + "\n\n")
                f.writelines(history)
            
            print_centered(f"[+] CHAT EXPORTED: {filename}", Fore.GREEN)
        
        elif format_type.lower() == "json":
            filename = os.path.join(export_dir, f"{agent_id}_{timestamp}.json")
            export_data = {
                "export_info": {
                    "my_agent_id": my_agent_id,
                    "target_agent_id": agent_id,
                    "export_time": get_timestamp(),
                    "message_count": len(history)
                },
                "messages": [line.strip() for line in history]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print_centered(f"[+] CHAT EXPORTED: {filename}", Fore.GREEN)
        
        else:
            print_centered(f"[!] UNSUPPORTED FORMAT: {format_type}", Fore.RED)
    
    except Exception as e:
        print_centered(f"[!] EXPORT ERROR: {e}", Fore.RED)
        logging.error(f"Export error: {e}")

# ==================== PERSISTENT IDENTITY ====================

def derive_agent_id_from_key(pub_key):
    """Generate consistent Agent ID from public key hash"""
    key_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    hash_digest = hashlib.sha256(key_bytes).hexdigest()
    return f"AGENT-{hash_digest[:12].upper()}"

def save_identity(priv_key, password):
    """Encrypt and save private key to file"""
    try:
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode('utf-8'))
        pem_private = priv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )
        
        with open(IDENTITY_FILE, 'wb') as f:
            f.write(pem_private)
        
        print_centered(f"[+] IDENTITY SAVED TO {IDENTITY_FILE}", Fore.GREEN)
        return True
    except Exception as e:
        print_centered(f"[!] ERROR SAVING IDENTITY: {e}", Fore.RED)
        logging.error(f"Identity save error: {e}")
        return False

def load_identity(password):
    """Load and decrypt private key from file"""
    try:
        with open(IDENTITY_FILE, 'rb') as f:
            pem_private = f.read()
        
        priv_key = serialization.load_pem_private_key(
            pem_private,
            password=password.encode('utf-8')
        )
        
        print_centered(f"[+] IDENTITY LOADED FROM {IDENTITY_FILE}", Fore.GREEN)
        return priv_key
    except FileNotFoundError:
        return None
    except Exception as e:
        print_centered(f"[!] ERROR LOADING IDENTITY: {e}", Fore.RED)
        logging.error(f"Identity load error: {e}")
        return None

def setup_identity():
    """Setup or load persistent identity"""
    global private_key, public_key, pem_public, my_agent_id
    
    if os.path.exists(IDENTITY_FILE):
        print_centered("[*] EXISTING IDENTITY DETECTED", Fore.CYAN)
        password = input_centered("ENTER IDENTITY PASSWORD: ", Fore.YELLOW)
        
        private_key = load_identity(password)
        if private_key is None:
            print_centered("[!] INVALID PASSWORD OR CORRUPTED IDENTITY", Fore.RED)
            time.sleep(2)
            return False
    else:
        print_centered("[*] NO IDENTITY FOUND - GENERATING NEW KEYPAIR", Fore.CYAN)
        time.sleep(1)
        
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        
        password = input_centered("CREATE IDENTITY PASSWORD: ", Fore.YELLOW)
        confirm = input_centered("CONFIRM PASSWORD: ", Fore.YELLOW)
        
        if password != confirm:
            print_centered("[!] PASSWORDS DO NOT MATCH", Fore.RED)
            return False
        
        if not save_identity(private_key, password):
            return False
    
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    my_agent_id = derive_agent_id_from_key(public_key)
    
    return True

# ==================== SECURITY CHALLENGE ====================

def binary_matrix_hack():
    """Simple security verification - Access Code"""
    print("\n")
    print_centered("[!] SECURITY VERIFICATION PROTOCOL", Fore.RED, Style.BRIGHT)
    print_centered("-" * 50, Fore.RED)
    time.sleep(0.5)
    
    # Simple access code (can be customized)
    access_code = input_centered("ENTER ACCESS CODE (default: 'SECURE'): ", Fore.YELLOW)
    
    if not access_code.strip():
        access_code = "SECURE"
    
    print_centered("VERIFYING ACCESS...", Fore.BLUE)
    time.sleep(1)
    
    # Always grant access (or you can add custom logic here)
    return True


# ==================== ENCRYPTION ====================

def encrypt_message(message, target_pub_pem):
    """Encrypt message using hybrid encryption (RSA + AES)"""
    session_key = Fernet.generate_key()
    cipher_suite = Fernet(session_key)
    encrypted_text = cipher_suite.encrypt(message.encode('utf-8'))
    
    target_pub = serialization.load_pem_public_key(target_pub_pem.encode('utf-8'))
    encrypted_session_key = target_pub.encrypt(
        session_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    blob = encrypted_session_key.hex() + "||" + encrypted_text.decode('utf-8')
    return blob

def decrypt_message(blob):
    """Decrypt message using hybrid decryption"""
    try:
        enc_sess_key_hex, enc_text_str = blob.split("||")
        enc_sess_key = bytes.fromhex(enc_sess_key_hex)
        session_key = private_key.decrypt(
            enc_sess_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        cipher_suite = Fernet(session_key)
        return cipher_suite.decrypt(enc_text_str.encode('utf-8')).decode('utf-8')
    except:
        return "[ENCRYPTED DATA - CANNOT DECRYPT]"

# ==================== FILE TRANSFER ====================

def encrypt_file(filepath, target_pub_pem):
    """Encrypt file for transfer"""
    try:
        with open(filepath, 'rb') as f:
            file_data = f.read()
        
        filename = os.path.basename(filepath)
        file_size = len(file_data)
        
        session_key = Fernet.generate_key()
        cipher_suite = Fernet(session_key)
        encrypted_data = cipher_suite.encrypt(file_data)
        
        target_pub = serialization.load_pem_public_key(target_pub_pem.encode('utf-8'))
        encrypted_session_key = target_pub.encrypt(
            session_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        
        blob = f"{filename}||{file_size}||{encrypted_session_key.hex()}||{base64.b64encode(encrypted_data).decode('utf-8')}"
        return blob
    except Exception as e:
        print_centered(f"[!] FILE ENCRYPTION ERROR: {e}", Fore.RED)
        logging.error(f"File encryption error: {e}")
        return None

def decrypt_file(blob, sender_id):
    """Decrypt and save received file"""
    try:
        parts = blob.split("||")
        filename = parts[0]
        file_size = int(parts[1])
        enc_sess_key_hex = parts[2]
        encrypted_data_b64 = parts[3]
        
        enc_sess_key = bytes.fromhex(enc_sess_key_hex)
        session_key = private_key.decrypt(
            enc_sess_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        
        cipher_suite = Fernet(session_key)
        encrypted_data = base64.b64decode(encrypted_data_b64)
        file_data = cipher_suite.decrypt(encrypted_data)
        
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        save_path = os.path.join(DOWNLOADS_DIR, f"{sender_id}_{filename}")
        
        with open(save_path, 'wb') as f:
            f.write(file_data)
        
        return save_path, file_size
    except Exception as e:
        print_centered(f"[!] FILE DECRYPTION ERROR: {e}", Fore.RED)
        logging.error(f"File decryption error: {e}")
        return None, 0

# ==================== MESSAGING ====================

def receive_messages():
    """Background thread to receive messages and files"""
    global target_public_key_cache, is_connected
    
    while is_connected:
        try:
            data = client.recv(65536)
            if not data: 
                break
            packet = data.decode('utf-8', errors='ignore')
            
            # Handle agent list response
            if packet.startswith("[AGENT_LIST]"):
                agent_data = packet.split("]")[1]
                if agent_data:
                    agents = agent_data.split("||")
                    print("\n")
                    print_centered("=== ONLINE AGENTS ===", Fore.CYAN, Style.BRIGHT)
                    for agent in agents:
                        parts = agent.split("|")
                        if len(parts) == 3:
                            aid, status, last_seen = parts
                            color = Fore.GREEN if status == "ONLINE" else Fore.YELLOW
                            print_centered(f"{aid} [{status}] - Last seen: {last_seen}", color)
                    print("\n")
                else:
                    print_centered("[*] NO AGENTS ONLINE", Fore.YELLOW)
                continue
            
            # Handle key lookup responses
            if packet.startswith("[KEY_FOUND]"):
                target_public_key_cache = packet.split("]")[1]
                continue
            
            if packet.startswith("[KEY_NOT_FOUND]"):
                target_public_key_cache = "ERROR"
                continue
            
            # Handle typing indicators
            if packet.startswith("[TYPING_INDICATOR]"):
                sender = packet.split("]")[1]
                print(f"\r{' ' * get_width()}\r", end='')
                print_centered(f"[TYPING] {sender} is typing...", Fore.CYAN)
                time.sleep(2)
                prompt = "[SECURE INPUT] >> "
                padding = max(0, (get_width() - len(prompt) - 10) // 2)
                sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
                sys.stdout.flush()
                continue

            # Handle incoming messages
            if packet.startswith("[INCOMING]"):
                _, content = packet.split("]", 1)
                sender, blob = content.split("|", 1)
                
                # Check if sender is blocked
                if is_blocked(sender):
                    logging.info(f"Blocked message from {sender}")
                    continue
                
                play_sound()
                msg_text = decrypt_message(blob)
                
                # Update statistics
                update_stats("messages_received")
                update_stats("bytes_received", len(blob))
                
                # Save to history
                save_message_to_history(sender, msg_text, "received")
                
                print("\n")
                print_centered(f"[MSG] FROM {sender} (E2EE)", Fore.CYAN)
                print_centered(f">> {msg_text}", Fore.GREEN, Style.BRIGHT)
                print_centered(f"[{get_timestamp()}]", Fore.BLUE)
                print("\n")
                
                # Send read receipt
                if config["client"]["read_receipts"]:
                    try:
                        client.send(f"[READ_RECEIPT]{sender}|{get_timestamp()}".encode('utf-8'))
                    except:
                        pass
                
                prompt = "[SECURE INPUT] >> "
                padding = max(0, (get_width() - len(prompt) - 10) // 2)
                sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
                sys.stdout.flush()
            
            # Handle incoming files
            if packet.startswith("[FILE_INCOMING]"):
                _, content = packet.split("]", 1)
                sender, file_blob = content.split("|", 1)
                
                # Check if sender is blocked
                if is_blocked(sender):
                    logging.info(f"Blocked file from {sender}")
                    continue
                
                play_sound()
                print("\n")
                print_centered(f"[FILE] RECEIVING FROM {sender}...", Fore.MAGENTA)
                
                save_path, file_size = decrypt_file(file_blob, sender)
                
                if save_path:
                    # Update statistics
                    update_stats("files_received")
                    update_stats("bytes_received", file_size)
                    
                    print_centered(f"[+] FILE SAVED: {save_path} ({file_size} bytes)", Fore.GREEN)
                    save_message_to_history(sender, f"[FILE RECEIVED: {os.path.basename(save_path)}]", "received")
                else:
                    print_centered("[!] FILE RECEIVE FAILED", Fore.RED)
                
                print("\n")
                prompt = "[SECURE INPUT] >> "
                padding = max(0, (get_width() - len(prompt) - 10) // 2)
                sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
                sys.stdout.flush()

        except Exception as e:
            logging.error(f"Receive error: {e}")
            if config["client"]["auto_reconnect"]:
                print_centered("[!] CONNECTION LOST - ATTEMPTING RECONNECT...", Fore.YELLOW)
                time.sleep(config["client"]["reconnect_delay"])
            break

def send_typing_indicator(target_code):
    """Send typing indicator to target"""
    if not config["client"]["typing_indicators"]:
        return
    
    global last_typing_time
    current_time = time.time()
    
    if current_time - last_typing_time > 3:  # Send every 3 seconds max
        try:
            client.send(f"[TYPING]{target_code}".encode('utf-8'))
            last_typing_time = current_time
        except:
            pass

def send_messages(target_code):
    """Main message sending loop with command support"""
    global target_public_key_cache
    
    print_centered("\n[COMMANDS] /agents | /block | /stats | /export | /help\n", Fore.CYAN)
    
    while is_connected:
        prompt = "[SECURE INPUT] >> "
        padding = max(0, (get_width() - len(prompt) - 10) // 2)
        sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
        sys.stdout.flush()
        
        msg = input("")
        
        # Handle commands
        if msg.lower() in ['/exit', '/quit']:
            print_centered("[*] DISCONNECTING...", Fore.YELLOW)
            break
        
        if msg.lower() == '/clear':
            clear_screen()
            print_centered(f"[*] SECURE CHANNEL: {my_agent_id} → {target_code}", Fore.GREEN)
            continue
        
        if msg.lower() == '/agents':
            try:
                client.send(b"[LIST_AGENTS]")
                time.sleep(0.5)
            except:
                print_centered("[!] ERROR FETCHING AGENT LIST", Fore.RED)
            continue
        
        if msg.lower().startswith('/history'):
            parts = msg.split()
            agent_id = parts[1] if len(parts) > 1 else target_code
            history = load_message_history(agent_id)
            
            if history:
                print("\n")
                print_centered(f"=== CHAT HISTORY WITH {agent_id} ===", Fore.CYAN, Style.BRIGHT)
                for line in history:
                    print(line.strip())
                print("\n")
            else:
                print_centered(f"[*] NO HISTORY FOUND FOR {agent_id}", Fore.YELLOW)
            continue
        
        if msg.lower() == '/help':
            print("\n")
            print_centered("=== AVAILABLE COMMANDS ===", Fore.CYAN, Style.BRIGHT)
            print_centered("/agents - List online agents", Fore.WHITE)
            print_centered("/sendfile <filepath> - Send encrypted file", Fore.WHITE)
            print_centered("/history [agent-id] - View chat history", Fore.WHITE)
            print_centered("/block <agent-id> - Block an agent", Fore.WHITE)
            print_centered("/unblock <agent-id> - Unblock an agent", Fore.WHITE)
            print_centered("/blocklist - View blocked agents", Fore.WHITE)
            print_centered("/stats - View session statistics", Fore.WHITE)
            print_centered("/export <agent-id> [txt|json] - Export chat", Fore.WHITE)
            print_centered("/clear - Clear screen", Fore.WHITE)
            print_centered("/exit or /quit - Disconnect", Fore.WHITE)
            print_centered("/help - Show this help", Fore.WHITE)
            print("\n")
            continue
        
        # Block system commands
        if msg.lower().startswith('/block '):
            agent_id = msg[7:].strip()
            if agent_id:
                block_agent(agent_id)
            else:
                print_centered("[!] USAGE: /block <agent-id>", Fore.YELLOW)
            continue
        
        if msg.lower().startswith('/unblock '):
            agent_id = msg[9:].strip()
            if agent_id:
                unblock_agent(agent_id)
            else:
                print_centered("[!] USAGE: /unblock <agent-id>", Fore.YELLOW)
            continue
        
        if msg.lower() == '/blocklist':
            if blocked_agents:
                print("\n")
                print_centered("=== BLOCKED AGENTS ===", Fore.RED, Style.BRIGHT)
                for agent in blocked_agents:
                    print_centered(f"[BLOCKED] {agent}", Fore.RED)
                print("\n")
            else:
                print_centered("[*] NO BLOCKED AGENTS", Fore.YELLOW)
            continue
        
        # Statistics command
        if msg.lower() == '/stats':
            show_statistics()
            continue
        
        # Export command
        if msg.lower().startswith('/export '):
            parts = msg.split()
            if len(parts) >= 2:
                agent_id = parts[1]
                format_type = parts[2] if len(parts) > 2 else "txt"
                export_chat(agent_id, format_type)
            else:
                print_centered("[!] USAGE: /export <agent-id> [txt|json]", Fore.YELLOW)
            continue
        
        if msg.lower().startswith('/sendfile '):
            filepath = msg[10:].strip()
            
            if not os.path.exists(filepath):
                print_centered(f"[!] FILE NOT FOUND: {filepath}", Fore.RED)
                continue
            
            print_centered(f"[*] ENCRYPTING FILE: {filepath}...", Fore.YELLOW)
            
            target_public_key_cache = None
            client.send(f"[GET_KEY]{target_code}".encode('utf-8'))
            
            wait_timer = 0
            while target_public_key_cache is None and wait_timer < 20:
                time.sleep(0.1)
                wait_timer += 1
            
            if target_public_key_cache == "ERROR" or target_public_key_cache is None:
                print_centered("[!] ERROR: TARGET AGENT NOT AVAILABLE", Fore.RED)
                continue
            
            encrypted_file_blob = encrypt_file(filepath, target_public_key_cache)
            
            if encrypted_file_blob:
                packet = f"[FILE]{target_code}|{encrypted_file_blob}"
                client.send(packet.encode('utf-8'))
                print_centered(f"[+] FILE SENT: {os.path.basename(filepath)}", Fore.GREEN)
                save_message_to_history(target_code, f"[FILE SENT: {os.path.basename(filepath)}]", "sent")
            else:
                print_centered("[!] FILE SEND FAILED", Fore.RED)
            
            continue
        
        # Regular message sending
        if not msg.strip():
            continue
        
        # Send typing indicator
        send_typing_indicator(target_code)
        
        # Get target's public key
        target_public_key_cache = None
        client.send(f"[GET_KEY]{target_code}".encode('utf-8'))
        
        wait_timer = 0
        while target_public_key_cache is None and wait_timer < 20:
            time.sleep(0.1)
            wait_timer += 1
            
        if target_public_key_cache == "ERROR" or target_public_key_cache is None:
            print_centered("[!] ERROR: TARGET AGENT NOT AVAILABLE OR KEY INVALID.", Fore.RED)
            continue

        try:
            encrypted_blob = encrypt_message(msg, target_public_key_cache)
            packet = f"[MSG]{target_code}|{encrypted_blob}"
            client.send(packet.encode('utf-8'))
            
            # Update statistics
            update_stats("messages_sent")
            update_stats("bytes_sent", len(encrypted_blob))
            
            # Save to history
            save_message_to_history(target_code, msg, "sent")
            
            print_centered("[SENT] 2048-BIT ENCRYPTED PACKET.", Fore.GREEN)
        except Exception as e:
            print_centered(f"[ERROR] SEND FAILED: {e}", Fore.RED)
            logging.error(f"Send error: {e}")

# ==================== MAIN SYSTEM ====================

def start_system():
    """Main application entry point"""
    global target_public_key_cache, client, is_connected
    
    clear_screen()
    print("\n" * 2)
    
    # ASCII Banner
    print_centered("╔═══════════════════════════════════════════════╗", Fore.GREEN, Style.BRIGHT)
    print_centered("║      G.I.D SECURE TERMINAL v2.0 (E2EE)        ║", Fore.GREEN, Style.BRIGHT)
    print_centered("╚═══════════════════════════════════════════════╝", Fore.GREEN, Style.BRIGHT)
    print("\n")
    
    print_centered("INITIALIZING RSA-2048 CRYPTO ENGINE...", Fore.CYAN)
    time.sleep(1)
    
    # Initialize session stats and load blocklist
    session_stats["start_time"] = time.time()
    load_blocklist()
    
    # Setup persistent identity
    if not setup_identity():
        print_centered("[!] IDENTITY SETUP FAILED", Fore.RED)
        return
    
    # Security challenge
    if not binary_matrix_hack():
        print_centered("ACCESS DENIED.", Fore.RED)
        return

    # Connect to server
    try:
        print_centered(f"\n[*] CONNECTING TO {SERVER_IP}:{SERVER_PORT}...", Fore.CYAN)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, SERVER_PORT))
        client.send(f"[REGISTER]{my_agent_id}|{pem_public}".encode('utf-8'))
        is_connected = True
        logging.info(f"Connected to server as {my_agent_id}")
    except Exception as e:
        print_centered(f"[!] SERVER UNREACHABLE: {e}", Fore.RED)
        logging.error(f"Connection error: {e}")
        return

    clear_screen()
    print("\n" * 2)
    print_centered(f"IDENTITY VERIFIED: {my_agent_id}", Fore.GREEN, Style.BRIGHT)
    print_centered(f"PUBLIC KEY FINGERPRINT: {pem_public[50:80]}...", Fore.BLUE)
    print_centered("-" * 50)
    
    # Start message receiver thread
    threading.Thread(target=receive_messages, daemon=True).start()

    # Get target agent
    while True:
        target_agent_code = input_centered("\nENTER TARGET AGENT ID (or /agents to list): ", Fore.MAGENTA)
        
        if target_agent_code.lower() == '/agents':
            try:
                client.send(b"[LIST_AGENTS]")
                time.sleep(1)
                continue
            except:
                print_centered("[!] ERROR FETCHING AGENT LIST", Fore.RED)
                continue
        
        print_centered(f"[*] FETCHING KEY FOR {target_agent_code}...", Fore.YELLOW)
        target_public_key_cache = None
        client.send(f"[GET_KEY]{target_agent_code}".encode('utf-8'))
        
        waits = 0
        while target_public_key_cache is None and waits < 15:
            time.sleep(0.2)
            waits += 1
            
        if target_public_key_cache == "ERROR":
            print("\n")
            print_centered(f"[!] AGENT '{target_agent_code}' NOT REGISTERED.", Fore.RED)
            print_centered("    TARGET MUST LOGIN AT LEAST ONCE TO GENERATE KEYS.", Fore.RED)
            print_centered("-" * 30, Fore.RED)
        elif target_public_key_cache:
            print_centered("[+] SECURE CHANNEL ESTABLISHED.", Fore.GREEN)
            break 
        else:
            print_centered("[!] SERVER TIMEOUT.", Fore.RED)

    # Start messaging
    send_messages(target_agent_code)
    is_connected = False

if __name__ == "__main__":
    try:
        start_system()
    except KeyboardInterrupt:
        print_centered("\n\n[!] SESSION TERMINATED", Fore.RED)
        logging.info("Session terminated by user")
    except Exception as e:
        print_centered(f"\n\n[!] CRITICAL ERROR: {e}", Fore.RED)
        logging.error(f"Critical error: {e}")