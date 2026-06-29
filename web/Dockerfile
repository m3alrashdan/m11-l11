# Vendored M10 frontend Dockerfile (unchanged for M11 Lab; web is NOT graded this module).
# The web service is included in docker-compose.yml so the M10 stack can be
# brought up end-to-end if the learner wants to verify behavior through the UI.

FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps || npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
