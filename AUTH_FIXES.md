# Authentication Issues and Fixes

## Issues Identified

1. **Missing SSL Certificates**: The nginx configuration expected SSL certificates at `/certs/server.crt` and `/certs/server.key`, but these files were missing.

2. **UI Container Port Configuration**: The UI container had an incorrect port mapping (`"8443:9296"`) which conflicted with nginx's port handling.

3. **Missing Environment Variables**: The `variables.env` file was missing critical environment variables needed for proper service communication.

4. **Syntax Error in Auth Configuration**: There was a trailing comma in the `wazo-auth.yml` file causing a YAML syntax error.

5. **External Dependencies**: The configuration was trying to mount external git repositories that may not exist.

## Fixes Applied

### 1. Generated SSL Certificates
```bash
cd certs/
openssl req -x509 -sha256 -nodes -days 825 -newkey rsa:2048 -config openssl.cfg -keyout server.key -out server.crt
```

### 2. Fixed UI Container Port Configuration
Changed from:
```yaml
expose:
  - "8443:9296"
```
To:
```yaml
expose:
  - "9296"
```

### 3. Added Missing Environment Variables
Added to `variables.env`:
- Database configuration
- RabbitMQ configuration  
- Auth service configuration
- UI configuration
- Service discovery settings
- Debug mode

### 4. Fixed Auth Configuration Syntax
Removed trailing comma from `bootstrap_user_on_startup: True,` in `wazo-auth.yml`.

### 5. Simplified Volume Mounts
- Removed external git repository dependencies
- Added proper volume mounts for auth keys
- Added service dependencies

### 6. Created Restart Script
Created `restart-services.sh` to properly start services in the correct order.

## How to Apply Fixes

1. **Run the restart script**:
   ```bash
   ./restart-services.sh
   ```

2. **Or manually restart**:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

3. **Access the UI**:
   - URL: https://localhost:8443
   - Default credentials: admin / secret

## Expected Behavior After Fixes

- No more redirect loops
- Proper authentication flow
- All services should start correctly
- UI should be accessible without authentication errors

## Troubleshooting

If you still experience issues:

1. Check service logs:
   ```bash
   docker-compose logs auth
   docker-compose logs ui
   docker-compose logs nginx
   ```

2. Verify SSL certificates:
   ```bash
   ls -la certs/
   ```

3. Check if all services are running:
   ```bash
   docker-compose ps
   ```

4. Verify environment variables are loaded:
   ```bash
   docker-compose exec auth env | grep WAZO
   ```
