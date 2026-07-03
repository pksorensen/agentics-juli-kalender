# agentics.dk juli-kalender — Node-service der både serverer de statiske sider
# og stemme-API'et (/api/votes, /api/vote, /api/health).
# express.static leverer HTTP Range (206) via send — PÅKRÆVET for dag-2 scroll-scrub.
FROM node:22-alpine

ENV NODE_ENV=production
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY . .

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -q -O /dev/null http://127.0.0.1/api/health || exit 1

CMD ["node", "server.js"]
