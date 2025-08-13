# syntax=docker/dockerfile:1.7-labs

FROM node:16 AS frontend

ARG REACT_APP_BASE_URL="http://127.0.0.1:5000"
ENV REACT_APP_BASE_URL=$REACT_APP_BASE_URL
 
# Set the working directory inside the container
WORKDIR /app
 
# Copy package.json and package-lock.json
COPY frontend/package*.json ./
 
RUN npm install
 
COPY frontend/ .

RUN yarn build


FROM python:3.10

WORKDIR /app

COPY --from=frontend /app/build frontend/build

COPY requirements.txt /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY --exclude=frontend . /app

ENTRYPOINT ["python3"]
CMD ["main.py"]
