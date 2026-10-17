# The frontend image. Caddy serves the static site from /srv/www on port 8080.
FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY www /srv/www

EXPOSE 8080
