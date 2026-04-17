FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

# Fallback to deployed backend URL if build arg is not provided
ARG VITE_API_URL=https://inventory-agent-api-wtfuivteea-el.a.run.app
ENV VITE_API_URL=$VITE_API_URL

RUN node ./node_modules/vite/bin/vite.js build

# Serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]