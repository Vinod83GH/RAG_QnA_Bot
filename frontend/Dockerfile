# Stage 1: Build the Angular app
FROM node:18 AS build

RUN mkdir -p /app

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN rm -rf node_modules && npm install

# Copy the Angular application source code
COPY . .

# Build the Angular app for production
RUN npm run build

# Stage 2: Serve the Angular app using NGINX
FROM nginx:stable-alpine

# Copy built Angular app to NGINX's default html folder
COPY --from=build /app/dist/your-angular-app-name /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start NGINX server
CMD ["nginx", "-g", "daemon off;"]
