# Step 1: Build React App
FROM node:18-alpine AS build

WORKDIR /app

# Copy dependencies
COPY package.json ./
RUN npm install

# Copy full source
COPY . .

COPY ../.env .env 

# Build the React project
RUN npm run build

# Step 2: Serve build via Nginx
FROM nginx:alpine

# Copy CRA build output (./build) to nginx html
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]