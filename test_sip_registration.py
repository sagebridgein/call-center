import sys
import pjsua2 as pj
import time

# Subclass to receive events from Account
class MyAccount(pj.Account):
    def onRegState(self, prm):
        print("Registration state changed:")
        print("Code =", prm.code)
        print("Status text =", prm.reason)
        print("Expiration =", prm.expiration)

# Subclass to receive events from Endpoint
class MyEndpoint(pj.Endpoint):
    def onNatDetectionComplete(self, prm):
        print("NAT detection completed:")
        print("Status =", prm.status)
        print("Nat type =", prm.natTypeName)

def main():
    # Create and initialize the library
    ep = MyEndpoint()
    ep.libCreate()

    # Initialize endpoint
    epConfig = pj.EpConfig()
    ep.libInit(epConfig)

    # Create SIP transport
    sipTpConfig = pj.TransportConfig()
    sipTpConfig.port = 0  # Let the system choose the port
    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig)

    # Start the library
    ep.libStart()

    # Account configuration
    acc_cfg = pj.AccountConfig()
    acc_cfg.idUri = "sip:uno@134.185.85.234"
    acc_cfg.regConfig.registrarUri = "sip:134.185.85.234"
    
    # Auth credentials
    cred = pj.AuthCredInfo("digest", "asterisk", "uno", 0, "password123")
    acc_cfg.sipConfig.authCreds.append(cred)

    # Create and register the account
    account = MyAccount()
    account.create(acc_cfg)

    print("Starting registration test...")
    print("Please wait for registration status...")

    # Wait for 10 seconds
    time.sleep(10)

    # Cleanup
    account.delete()
    ep.libDestroy()

if __name__ == "__main__":
    try:
        main()
    except pj.Error as e:
        print("Exception: " + str(e))
        sys.exit(1)
