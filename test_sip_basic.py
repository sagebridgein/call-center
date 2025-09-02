import socket
import time
import sys

def create_register_request(username, domain, password):
    """Create a SIP REGISTER request"""
    request = [
        f"REGISTER sip:{domain} SIP/2.0",
        f"Via: SIP/2.0/UDP client.local:5060;branch=z9hG4bK-test",
        f"Max-Forwards: 70",
        f"From: <sip:{username}@{domain}>;tag=test",
        f"To: <sip:{username}@{domain}>",
        f"Call-ID: test-call-id",
        f"CSeq: 1 REGISTER",
        f"Contact: <sip:{username}@client.local:5060>",
        f"Expires: 3600",
        f"Content-Length: 0",
        "",
        ""
    ]
    return "\r\n".join(request)

def test_sip_registration(server_ip, username, password):
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Set timeout
        sock.settimeout(5)
        
        # Create and send REGISTER request
        request = create_register_request(username, server_ip, password)
        print("\nSending REGISTER request:")
        print("------------------------")
        print(request)
        
        # Send the request
        sock.sendto(request.encode(), (server_ip, 5060))
        
        # Receive response
        print("\nWaiting for response...")
        data, addr = sock.recvfrom(4096)
        response = data.decode()
        
        print("\nReceived response:")
        print("------------------")
        print(response)
        
    except socket.timeout:
        print("Error: Timeout waiting for response")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        sock.close()

if __name__ == "__main__":
    SERVER_IP = "134.185.85.234"  # Your SIP server IP
    USERNAME = "uno"              # Your SIP username
    PASSWORD = "password123"      # Your SIP password
    
    print(f"Testing SIP registration for {USERNAME}@{SERVER_IP}")
    test_sip_registration(SERVER_IP, USERNAME, PASSWORD)
