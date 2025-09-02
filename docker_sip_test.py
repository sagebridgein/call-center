import socket
import time
import sys

def test_docker_sip():
    """Test SIP connectivity through Docker network"""
    message = (
        "OPTIONS sip:asterisk SIP/2.0\r\n"
        "Via: SIP/2.0/UDP test:5060;branch=z9hG4bK123\r\n"
        "Max-Forwards: 70\r\n"
        "From: <sip:test@test>;tag=123\r\n"
        "To: <sip:asterisk>\r\n"
        "Call-ID: test123\r\n"
        "CSeq: 1 OPTIONS\r\n"
        "Contact: <sip:test@test:5060>\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )

    # List of addresses to try
    addresses = [
        ('127.0.0.1', 5060),
        ('0.0.0.0', 5060),
        ('172.17.0.1', 5060),  # Common Docker bridge network
        ('134.185.85.234', 5060)
    ]

    for addr, port in addresses:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        try:
            print(f"\nTesting {addr}:{port}")
            print("-" * 40)
            
            # Try to bind to a random port
            sock.bind(('0.0.0.0', 0))
            local_addr = sock.getsockname()
            print(f"Bound to local address: {local_addr}")
            
            # Send OPTIONS request
            print(f"Sending OPTIONS request to {addr}:{port}")
            sock.sendto(message.encode(), (addr, port))
            
            # Wait for response
            try:
                data, server = sock.recvfrom(4096)
                print(f"Received response from {server}:")
                print(data.decode())
            except socket.timeout:
                print(f"No response from {addr}:{port} (timeout)")
                
        except Exception as e:
            print(f"Error testing {addr}:{port}: {e}")
        finally:
            sock.close()
            print()

if __name__ == "__main__":
    print("\nStarting SIP connectivity tests through Docker network...")
    print("=" * 60)
    test_docker_sip()
