# syntax=docker/dockerfile:1.5
FROM node:20

WORKDIR /workspace

COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/contracts/package.json packages/contracts/package.json

RUN --mount=type=cache,target=/root/.npm npm ci

CMD ["npm", "run", "dev", "-w", "apps/web", "--", "--host", "0.0.0.0", "--port", "5173"]
