
# SIP Configuration Guide

This guide explains how to configure and manage SIP users in the call center system.

## Current Configuration

The system uses PJSIP for SIP endpoint management. Configuration files are located in `/etc/pjsip.d/`.

### Base Configuration Structure

```ini
[transport-udp-local]
type=transport
protocol=udp
bind=0.0.0.0:5060
allow_reload=yes

[username]
type=endpoint
context=from-internal
disallow=all
allow=ulaw,alaw
auth=username-auth
aors=username
direct_media=no
rtp_symmetric=yes
force_rport=yes
rewrite_contact=yes
transport=transport-udp-local
dtmf_mode=rfc4733
allow_transfer=yes
trust_id_inbo
d=yes
trust_id_outbound=yes
send_rpid=yes
timers_sess_expires=3600
from_user=username
from_domain=your_server_ip

[username-auth]
type=auth
auth_type=userpass
password=yourpassword
username=username
realm=asterisk
nonce_lifetime=300

[username]
type=aor
max_contacts=5
remove_existing=yes
qualify_frequency=60
```

## Adding New Users

### Method 1: Manual Configuration (Development/Testing)

1. Create a new configuration file in `/home/ubuntu/call-center/etc/pjsip.d/`:
   ```bash
   touch /home/ubuntu/call-center/etc/pjsip.d/new-user.conf
   ```

2. Add the configuration using the template above, replacing:
   - `username` with the desired username
   - `yourpassword` with the desired password
   - `your_server_ip` with your server's IP address

3. Apply the configuration:
   ```bash
   # Copy to container
   sudo docker cp etc/pjsip.d/new-user.conf call-center_asterisk_1:/etc/asterisk/pjsip.d/
   
   # Set permissions
   sudo docker exec call-center_asterisk_1 chown asterisk:asterisk /etc/asterisk/pjsip.d/new-user.conf
   
   # Reload PJSIP
   sudo docker exec call-center_asterisk_1 asterisk -rx 'module reload res_pjsip.so'
   
   # Verify
   sudo docker exec call-center_asterisk_1 asterisk -rx 'pjsip show endpoints'
   ```

### Method 2: Wazo Platform UI (Recommended for Production)

1. Access the Wazo Platform UI at `https://your_server_ip:8443`
2. Login with your administrator credentials
3. Navigate to Users → Add
4. Fill in the required information:
   - First Name
   - Last Name
   - Email
   - Password
   - SIP username
   - SIP secret (password)
5. Save the user

## Testing SIP Registration

### Softphone Configuration
Configure your SIP softphone with:
- Username: [configured username]
- Password: [configured password]
- Server/Domain: [your server IP]
- Port: 5060
- Transport: UDP
- Auth Username: [same as username]
- Realm: asterisk

### Verify Registration
```bash
# Check endpoint status
sudo docker exec call-center_asterisk_1 asterisk -rx 'pjsip show endpoints'

# Check registration status
sudo docker exec call-center_asterisk_1 asterisk -rx 'pjsip show contacts'

# Watch live registration attempts
sudo docker exec call-center_asterisk_1 asterisk -rx 'pjsip set logger on'
sudo docker exec call-center_asterisk_1 tail -f /var/log/asterisk/messages
```

## Troubleshooting

### Common Issues

1. 401 Unauthorized
   - Verify username and password
   - Check realm setting
   - Ensure authentication configuration is correct

2. Registration Timeout
   - Check network connectivity
   - Verify transport settings
   - Check firewall rules for port 5060

3. Audio Issues
   - Verify codec configuration
   - Check NAT settings
   - Verify RTP port range (19980-20000)

### Debug Commands
```bash
# Check PJSIP configuration
sudo docker exec call-center_asterisk_1 asterisk -rx 'pjsip show config'

# Show active channels
sudo docker exec call-center_asterisk_1 asterisk -rx 'core show channels'

# Enable SIP debug
sudo docker exec call-center_asterisk_1 asterisk -rx 'pjsip set logger on'
```
