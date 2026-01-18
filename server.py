import socket
import threading
import shutil
import os
import time
import json
import logging
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# Load configuration
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "server": {"host": "0.0.0.0", "port": 5555},
    "client": {"auto_reconnect": True, "save_history": True}
}

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

config = load_config()
HOST = config["server"]["host"]
PORT = config["server"]["port"]

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename='logs/server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

active_agents = {}
public_keys = {}
offline_mailbox = {}
agent_last_seen = {}  # Track last activity time
agent_status = {}  # Track online/offline status

def print_centered(text, color=Fore.WHITE):
    try: 
        width = shutil.get_terminal_size().columns
    except: 
        width = 80
    padding = max(0, (width - len(text)) // 2)
    print(" " * padding + color + text)
    logging.info(text)

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def handle_client(client, agent_id):
    """Handle client connections and route messages/files"""
    agent_status[agent_id] = "ONLINE"
    agent_last_seen[agent_id] = get_timestamp()
    
    while True:
        try:
            data = client.recv(65536)
            if not data: 
                break
            
            agent_last_seen[agent_id] = get_timestamp()
            command_packet = data.decode('utf-8', errors='ignore')
            
            # Handle agent list requests
            if command_packet.startswith("[LIST_AGENTS]"):
                agent_list = []
                for aid in active_agents.keys():
                    status = agent_status.get(aid, "OFFLINE")
                    last_seen = agent_last_seen.get(aid, "Unknown")
                    agent_list.append(f"{aid}|{status}|{last_seen}")
                
                response = f"[AGENT_LIST]{'||'.join(agent_list)}"
                client.send(response.encode('utf-8'))
                print_centered(f"[LIST] Sent agent list to {agent_id}", Fore.CYAN)
            
            # Handle public key requests
            elif command_packet.startswith("[GET_KEY]"):
                target_request = command_packet.split("]")[1]
                if target_request in public_keys:
                    response = f"[KEY_FOUND]{public_keys[target_request]}"
                    client.send(response.encode('utf-8'))
                else:
                    client.send(b"[KEY_NOT_FOUND]")
            
            # Handle typing indicators
            elif command_packet.startswith("[TYPING]"):
                target_id = command_packet.split("]")[1]
                if target_id in active_agents:
                    try:
                        packet = f"[TYPING_INDICATOR]{agent_id}"
                        active_agents[target_id].send(packet.encode('utf-8'))
                    except:
                        pass
            
            # Handle read receipts
            elif command_packet.startswith("[READ_RECEIPT]"):
                _, content = command_packet.split("]", 1)
                target_id, msg_id = content.split("|", 1)
                if target_id in active_agents:
                    try:
                        packet = f"[RECEIPT]{agent_id}|{msg_id}"
                        active_agents[target_id].send(packet.encode('utf-8'))
                    except:
                        pass
            
            # Handle regular messages
            elif command_packet.startswith("[MSG]"):
                _, content = command_packet.split("]", 1)
                target_id, encrypted_blob = content.split("|", 1)
                
                # Support group messages (comma-separated IDs)
                targets = [t.strip() for t in target_id.split(",")]
                
                for tid in targets:
                    packet_to_send = f"[INCOMING]{agent_id}|{encrypted_blob}"
                    
                    if tid in active_agents:
                        try:
                            active_agents[tid].send(packet_to_send.encode('utf-8'))
                            print_centered(f"[MSG] {agent_id} → {tid}", Fore.CYAN)
                        except:
                            if tid not in offline_mailbox: 
                                offline_mailbox[tid] = []
                            offline_mailbox[tid].append(packet_to_send)
                            print_centered(f"[BUFFERED] {agent_id} → {tid}", Fore.YELLOW)
                    else:
                        if tid not in offline_mailbox: 
                            offline_mailbox[tid] = []
                        offline_mailbox[tid].append(packet_to_send)
                        print_centered(f"[BUFFERED] {agent_id} → {tid}", Fore.YELLOW)
            
            # Handle file transfers
            elif command_packet.startswith("[FILE]"):
                _, content = command_packet.split("]", 1)
                target_id, file_data = content.split("|", 1)
                
                targets = [t.strip() for t in target_id.split(",")]
                
                for tid in targets:
                    packet_to_send = f"[FILE_INCOMING]{agent_id}|{file_data}"
                    
                    if tid in active_agents:
                        try:
                            active_agents[tid].send(packet_to_send.encode('utf-8'))
                            print_centered(f"[FILE] {agent_id} → {tid}", Fore.MAGENTA)
                        except:
                            if tid not in offline_mailbox: 
                                offline_mailbox[tid] = []
                            offline_mailbox[tid].append(packet_to_send)
                            print_centered(f"[FILE BUFFERED] {agent_id} → {tid}", Fore.YELLOW)
                    else:
                        if tid not in offline_mailbox: 
                            offline_mailbox[tid] = []
                        offline_mailbox[tid].append(packet_to_send)
                        print_centered(f"[FILE BUFFERED] {agent_id} → {tid}", Fore.YELLOW)

        except Exception as e:
            logging.error(f"Error handling client {agent_id}: {e}")
            break
    
    # Cleanup on disconnect
    agent_status[agent_id] = "OFFLINE"
    agent_last_seen[agent_id] = get_timestamp()
    
    if agent_id in active_agents: 
        del active_agents[agent_id]
    client.close()
    print_centered(f"[-] AGENT DISCONNECTED: {agent_id}", Fore.RED)

def receive():
    """Main server loop to accept connections"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" * 2)
    print_centered("╔═══════════════════════════════════════════════╗", Fore.GREEN)
    print_centered("║   G.I.D SECURE TERMINAL SERVER v2.0 (E2EE)    ║", Fore.GREEN)
    print_centered("╚═══════════════════════════════════════════════╝", Fore.GREEN)
    print_centered("-" * 50, Fore.WHITE)
    print_centered(f"[*] LISTENING ON {HOST}:{PORT}", Fore.CYAN)
    print_centered("[*] WAITING FOR SECURE HANDSHAKES...", Fore.CYAN)
    print_centered("-" * 50, Fore.WHITE)
    print("\n")
    logging.info(f"Server started on {HOST}:{PORT}")
    
    while True:
        try:
            client, address = server.accept()
            try:
                initial_data = client.recv(8192).decode('utf-8')
                
                if initial_data.startswith("[REGISTER]"):
                    _, payload = initial_data.split("]", 1)
                    agent_id, pub_key_pem = payload.split("|", 1)
                    
                    active_agents[agent_id] = client
                    public_keys[agent_id] = pub_key_pem
                    agent_status[agent_id] = "ONLINE"
                    agent_last_seen[agent_id] = get_timestamp()
                    
                    print_centered(f"[+] REGISTERED: {agent_id} ({address[0]})", Fore.GREEN)
                    logging.info(f"Agent registered: {agent_id} from {address[0]}")
                    
                    # Deliver offline messages
                    if agent_id in offline_mailbox:
                        print_centered(f"[*] DELIVERING {len(offline_mailbox[agent_id])} OFFLINE MESSAGES TO {agent_id}", Fore.YELLOW)
                        for saved_msg in offline_mailbox[agent_id]:
                            client.send(saved_msg.encode('utf-8'))
                            time.sleep(0.2)
                        del offline_mailbox[agent_id]

                    thread = threading.Thread(target=handle_client, args=(client, agent_id))
                    thread.daemon = True
                    thread.start()
            except Exception as e:
                logging.error(f"Error during registration: {e}")
                client.close()
        except Exception as e:
            logging.error(f"Error accepting connection: {e}")

if __name__ == "__main__":
    try:
        receive()
    except KeyboardInterrupt:
        print_centered("\n[!] SERVER SHUTDOWN", Fore.RED)
        logging.info("Server shutdown by user")