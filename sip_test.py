import socket
import time
import hashlib
import re
import sys

def create_register_request(username, domain, nonce=None, auth_response=None):
    """Create a SIP REGISTER request with or without authentication"""
    branch = f"z9hG4bK-{int(time.time())}"
    call_id = f"test-{int(time.time())}"
    
    request = [
        f"REGISTER sip:{domain} SIP/2.0",
        f"Via: SIP/2.0/UDP client.local;branch={branch}",
        "Max-Forwards: 70",
        f"From: <sip:{username}@{domain}>;tag=test",
        f"To: <sip:{username}@{domain}>",
        f"Call-ID: {call_id}",
        "CSeq: 1 REGISTER",
        f"Contact: <sip:{username}@client.local>",
        "Expires: 3600",
    ]
    
    if nonce and auth_response:
        auth_header = (
            f'Authorization: Digest username="{username}", '
            f'realm="asterisk", '
            f'nonce="{nonce}", '
            f'uri="sip:{domain}", '
            'algorithm=MD5, '
            f'response="{auth_response}"'
        )
        request.append(auth_header)
    
    request.extend(["Content-Length: 0", "", ""])
    return "\r\n".join(request)

def calculate_auth_response(username, password, realm, nonce, method, uri):
    """Calculate the authentication response"""
    ha1 = hashlib.md5(f"{username}:{realm}:{password}".encode()).hexdigest()
    ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
    response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
    return response

def test_sip_registration(server_ip, username, password):
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    
    try:
        print(f"\nTesting SIP registration for {username}@{server_ip}")
        print("=" * 50)
        
        # First REGISTER request (without auth)
        request = create_register_request(username, server_ip)
        print("\nSending initial REGISTER request...")
        print("-" * 30)
        print(request)
        
        sock.sendto(request.encode(), (server_ip, 5060))
        
        # Get first response (expecting 401 Unauthorized)
        data, addr = sock.recvfrom(4096)
        response = data.decode()
        print("\nReceived response:")
        print("-" * 30)
        print(response)
        
        # Extract nonce from WWW-Authenticate header
        nonce_match = re.search(r'nonce="([^"]+)"', response)
        realm_match = re.search(r'realm="([^"]+)"', response)
        
        if nonce_match and realm_match:
            nonce = nonce_match.group(1)
            realm = realm_match.group(1)
            print(f"\nExtracted nonce: {nonce}")
            print(f"Extracted realm: {realm}")
            
            # Calculate authentication response
            uri = f"sip:{server_ip}"
            auth_response = calculate_auth_response(username, password, realm, nonce, "REGISTER", uri)
            
            # Send authenticated REGISTER request
            auth_request = create_register_request(username, server_ip, nonce, auth_response)
            print("\nSending authenticated REGISTER request...")
            print("-" * 30)
            print(auth_request)
            
            sock.sendto(auth_request.encode(), (server_ip, 5060))
            
            # Get final response
            data, addr = sock.recvfrom(4096)
            response = data.decode()
            print("\nReceived final response:")
            print("-" * 30)
            print(response)
            
            # Check if registration was successful
            if "200 OK" in response:
                print("\n✓ Registration successful!")
            else:
                print("\n✗ Registration failed!")
        else:
            print("\nError: Could not extract authentication challenge from response")
            
    except socket.timeout:
        print("\nError: Timeout waiting for response from server")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        sock.close()

if __name__ == "__main__":
    # Configuration
    SERVER_IP = "127.0.0.1"  # Local testing
    
    # Test both the custom user and default user
    print("\nTesting custom user configuration:")
    test_sip_registration(SERVER_IP, "uno", "password123")
    
    print("\n" + "=" * 70 + "\n")
    
    print("Testing default user configuration:")
    test_sip_registration(SERVER_IP, "uno", "uno1234")
