# Node 22 LTS
FROM node:22-alpine

WORKDIR /app

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

# Copy workspace config first (for caching)
COPY pnpm-workspace.yaml ./
COPY package.json ./

# Copy package.json files for all workspaces
COPY frontend/package.json ./frontend/
COPY themes/ ./themes/

# Install dependencies
RUN pnpm install

# Copy entire monorepo
COPY . .

# Build frontend with themes transpilation
WORKDIR /app/frontend
RUN pnpm build

# Copy standalone assets
RUN cp -r public .next/standalone/public && \
    mkdir -p .next/standalone/.next && \
    cp -r .next/static .next/standalone/.next/static

# Expose the port
EXPOSE 3000

# Set working directory to standalone
WORKDIR /app/frontend/.next/standalone

# Run standalone server
CMD ["node", "server.js"]
