FROM node:12 as build-stage

COPY . /app

WORKDIR /app

RUN npm install && npm build

FROM nginx:1.19

COPY --from=build-stage /app/build/ /usr/share/nginx/html
# Copy the default nginx.conf provided by tiangolo/node-frontend
COPY --from=build-stage /app/nginx.conf /etc/nginx/conf.d/default.conf
