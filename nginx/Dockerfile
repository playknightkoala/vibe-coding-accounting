FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy default configuration (will be overridden in production with SSL)
COPY default.conf /etc/nginx/conf.d/default.conf

# Create directories for SSL certificates and certbot
RUN mkdir -p /etc/nginx/ssl /var/www/certbot

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
