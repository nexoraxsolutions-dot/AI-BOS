# ------------- Build stage -------------
FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --only=production && \
    cp -R node_modules /prod_node_modules && \
    npm install

# Copy source code and build
COPY . .
RUN npm run build

# ------------- Runtime stage -------------
FROM node:20-alpine AS runner

# Create non-root user
RUN addgroup --system --gid 1001 nextjs && \
    adduser --system --uid 1001 --gid 1001 nextjs

WORKDIR /app

# Set to production
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Copy production node_modules and built output
COPY --from=builder /prod_node_modules ./node_modules
COPY --from=builder /build/.next ./.next
COPY --from=builder /build/public ./public
COPY --from=builder /build/package.json ./package.json
COPY --from=builder /build/next.config.mjs ./next.config.mjs

# Set ownership to non-root user
RUN chown -R nextjs:nextjs /app

# Switch to non-root user
USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

EXPOSE 3000

CMD ["node_modules/.bin/next", "start", "-p", "3000"]