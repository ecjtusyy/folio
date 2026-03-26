FROM node:20-bookworm-slim AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json /app/package.json
COPY scripts /app/scripts
RUN npm install --no-audit --no-fund
COPY . /app
# ensure pdfjs assets exist in public/ after source overlay
RUN node scripts/copy-pdfjs.mjs
RUN npm run build

FROM node:20-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/.next/standalone /app
COPY --from=builder /app/.next/static /app/.next/static
COPY --from=builder /app/public /app/public
EXPOSE 3000
CMD ["node","server.js"]
