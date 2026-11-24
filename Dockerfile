FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY listings.json /usr/share/nginx/html/listings.json
EXPOSE 80
