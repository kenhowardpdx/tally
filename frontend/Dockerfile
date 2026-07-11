# Dev-only image: runs the Vite dev server with HMR against a bind-mounted
# source tree (see the frontend service in docker-compose.yml). Not used for
# the production build - that's a static export via adapter-static, deployed
# to S3/CloudFront (see infra/modules/frontend_s3).
FROM node:22-alpine

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .

EXPOSE 5173

# --host 0.0.0.0: Vite's dev server binds to localhost by default, which
# isn't reachable from outside the container.
CMD ["yarn", "dev", "--host", "0.0.0.0"]
