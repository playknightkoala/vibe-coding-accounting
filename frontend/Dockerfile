# Development Dockerfile - Uses Vite dev server with HMR
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

EXPOSE 5173

# Always run dev server in development
CMD ["npm", "run", "dev"]
