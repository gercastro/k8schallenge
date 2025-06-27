FROM webdevops/php-nginx:alpine

# Copiamos el index.php
COPY src/html/ /app

# Puerto por defecto
EXPOSE 80
