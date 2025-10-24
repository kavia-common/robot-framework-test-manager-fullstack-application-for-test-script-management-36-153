# syntax=docker/dockerfile:1.6
FROM node:18-alpine

WORKDIR /usr/src/app

# Copy package manifests first for better caching; if not present, continue gracefully
# Assuming a standard React app layout exists in this FrontendUI workspace.
COPY package*.json ./
RUN if [ -f package.json ]; then npm ci --no-audit --no-fund; fi

# Copy rest of the source
COPY . .

# Build if scripts exist; otherwise run dev server
RUN if [ -f package.json ]; then \
      if npm run | grep -q "build"; then npm run build; fi; \
    fi

ENV PORT=3000 \
    HOST=0.0.0.0

EXPOSE 3000

# Prefer start script if available, fallback to serve build with a simple server
CMD ["/bin/sh", "-c", "if npm run | grep -q 'start'; then npm run start; else npx serve -s build -l ${PORT}; fi"]
