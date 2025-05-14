FROM node:20

# Set workdir
WORKDIR /app

# Install deps
COPY package*.json ./
RUN npm install

# Copy and build
COPY . .
RUN npm run build

# Use Vite preview to serve
EXPOSE 3000
CMD ["npm", "run", "preview", "--", "--host"]
