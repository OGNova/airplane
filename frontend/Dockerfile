FROM node:10.6.0-alpine

RUN mkdir /opt/frontend

ADD package.json /opt/frontend
ADD package-lock.json /opt/frontend
RUN cd /opt/frontend

ADD src /opt/frontend/src
WORKDIR /opt/frontend
