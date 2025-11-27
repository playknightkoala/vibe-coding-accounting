FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build argument to determine environment (default: development)
ARG NODE_ENV=development

# Build for production if NODE_ENV=production
RUN if [ "$NODE_ENV" = "production" ]; then \
      npm run build; \
    fi

# Set as environment variable for runtime
ENV NODE_ENV=${NODE_ENV}

EXPOSE 5173

# Run dev server in development, serve built files in production
CMD sh -c 'if [ "$NODE_ENV" = "production" ]; then \
      npx vite preview --host 0.0.0.0 --port 5173; \
    else \
      npm run dev; \
    fi'
