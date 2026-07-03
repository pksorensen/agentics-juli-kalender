# agentics.dk juli-kalender — statisk site bag nginx.
# nginx serverer statiske filer med HTTP Range-support (206) som standard,
# hvilket er PÅKRÆVET for scroll-scrub-videoen på dag 2.
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -q --spider http://127.0.0.1/calendar.html || exit 1
