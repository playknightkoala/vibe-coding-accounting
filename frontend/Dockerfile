# Development Dockerfile - Uses Vite dev server with HMR
FROM node:20-alpine

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies with clean cache
RUN npm ci --prefer-offline --no-audit

# Copy source code last (changes most frequently)
COPY . .

EXPOSE 5173

# Always run dev server in development
CMD ["npm", "run", "dev"]
