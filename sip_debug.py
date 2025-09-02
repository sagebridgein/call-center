import socket
import time
import hashlib
import re
import sys

def test_sip_ports():
    """Test different ports to find where Asterisk is listening"""
    test_ports = [5060, 5061, 5080]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    
    for port in test_ports:
        try:
            # Try to bind to the port
            sock.bind(('0.0.0.0', port))
            print(f"Port {port} is available (not in use)")
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
        except socket.error:
            print(f"Port {port} is in use")
            
            # Try sending a simple OPTIONS request
            try:
                options_request = (
                    "OPTIONS sip:127.0.0.1 SIP/2.0\r\n"
                    f"Via: SIP/2.0/UDP localhost;branch=z9hG4bK-{int(time.time())}\r\n"
                    "Max-Forwards: 70\r\n"
                    "From: <sip:test@localhost>;tag=test\r\n"
                    "To: <sip:test@localhost>\r\n"
                    f"Call-ID: test-{int(time.time())}\r\n"
                    "CSeq: 1 OPTIONS\r\n"
                    "Contact: <sip:test@localhost>\r\n"
                    "Content-Length: 0\r\n\r\n"
                )
                sock.sendto(options_request.encode(), ('127.0.0.1', port))
                try:
                    data, addr = sock.recvfrom(4096)
                    print(f"Response from port {port}:")
                    print(data.decode())
                except socket.timeout:
                    print(f"No response from port {port}")
            except Exception as e:
                print(f"Error testing port {port}: {str(e)}")
    
    sock.close()

def test_network_connectivity(host, port):
    """Test basic network connectivity"""
    try:
        print(f"\nTesting network connectivity to {host}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        # Try to connect and send a simple message
        message = b"test"
        print(f"Sending test message to {host}:{port}")
        sock.sendto(message, (host, port))
        
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received response from {addr}: {data}")
        except socket.timeout:
            print("No response received (timeout)")
            
    except Exception as e:
        print(f"Network error: {str(e)}")
    finally:
        sock.close()

def main():
    print("\nStarting SIP connectivity tests...")
    print("=" * 50)
    
    # Test available ports
    print("\n1. Testing SIP ports...")
    test_sip_ports()
    
    # Test network connectivity to both localhost and external IP
    print("\n2. Testing network connectivity...")
    test_network_connectivity('127.0.0.1', 5060)
    test_network_connectivity('134.185.85.234', 5060)

if __name__ == "__main__":
    main()
