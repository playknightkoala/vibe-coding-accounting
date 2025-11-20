# SSL Certificates Directory

This directory stores SSL/TLS certificates for HTTPS.

## ⚠️ Security Warning

**NEVER commit SSL certificates to version control!**

This directory is excluded in `.gitignore`.

## Required Files for HTTPS

Place your SSL certificate files here:

```
ssl/
├── fullchain.pem    # Full certificate chain
├── privkey.pem      # Private key (keep secure!)
└── chain.pem        # Intermediate certificates
```

## File Permissions

Set correct permissions for security:

```bash
chmod 644 fullchain.pem
chmod 644 chain.pem
chmod 600 privkey.pem  # Private key should be readable only by owner
```

## Obtaining Certificates

### Option 1: Let's Encrypt (Recommended - Free)

Use the provided setup script:

```bash
sudo ./setup-ssl.sh yourdomain.com www.yourdomain.com your@email.com
```

### Option 2: Manual Let's Encrypt

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your@email.com \
  --agree-tos

# Copy to this directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./
sudo cp /etc/letsencrypt/live/yourdomain.com/chain.pem ./

# Set permissions
chmod 644 fullchain.pem chain.pem
chmod 600 privkey.pem
```

### Option 3: Commercial Certificate

If you purchased a certificate from a CA:

1. Copy `fullchain.pem` (your certificate + intermediate certificates)
2. Copy `privkey.pem` (your private key)
3. Copy `chain.pem` (intermediate certificates only)
4. Set proper permissions as shown above

## Certificate Validation

After placing certificates, verify them:

```bash
# Check certificate details
openssl x509 -in fullchain.pem -text -noout

# Verify certificate chain
openssl verify -CAfile chain.pem fullchain.pem

# Check expiration date
openssl x509 -in fullchain.pem -noout -dates
```

## Certificate Renewal

Let's Encrypt certificates expire after 90 days.

### Automatic Renewal

The setup script configures automatic renewal. Certificates are checked daily and renewed when they have 30 days or less remaining.

### Manual Renewal

```bash
# Renew all certificates
sudo certbot renew

# Force renewal (for testing)
sudo certbot renew --force-renewal

# After renewal, copy new certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/* ./
chmod 644 fullchain.pem chain.pem
chmod 600 privkey.pem

# Restart nginx
docker restart accounting_nginx_prod
```

## Testing HTTPS

After setting up certificates:

```bash
# Test HTTPS connection
curl -I https://yourdomain.com

# Test SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Online SSL test
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

## Troubleshooting

### Certificate Not Found

```bash
# Check files exist
ls -la

# Check nginx can read files
docker exec accounting_nginx_prod ls -la /etc/nginx/ssl/
```

### Permission Denied

```bash
# Fix permissions
chmod 644 fullchain.pem chain.pem
chmod 600 privkey.pem

# Restart nginx
docker restart accounting_nginx_prod
```

### Certificate Expired

```bash
# Check expiration
openssl x509 -in fullchain.pem -noout -dates

# Renew
sudo certbot renew
```

## For Development

If you need HTTPS for development, you can use self-signed certificates:

```bash
# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Copy fullchain to chain
cp fullchain.pem chain.pem
```

**Note**: Self-signed certificates will show security warnings in browsers.

## Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)

---

**Remember**: Keep your private key (`privkey.pem`) secure and never share it!
