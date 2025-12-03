FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Expose stdio for MCP
CMD ["node", "build/index.js"]
