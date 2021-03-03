FROM python:3.9.2-buster
LABEL maintainer="rkc7h@virginia.edu"
ARG BUILD_ENV
ARG ES_ENV_HOST
ENV APP_LOC /ithriv_service
RUN mkdir -p /root/.aws
RUN mkdir -p /home/.aws
RUN mkdir -p /etc/private/ithriv
RUN mkdir -p $APP_LOC
WORKDIR $APP_LOC
ADD ./requirements.txt .
RUN pip3 install -r requirements.txt
EXPOSE 5000
RUN apt-get update
RUN apt-get install -y libmagic-dev
RUN apt-get install -y nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN apt-get install -y supervisor
ENV FLASK_APP app/__init__.py
ENV FLASK_DEBUG 0
ADD ./nginx_app.conf /etc/nginx/sites-available/default
ADD ./supervisor_app.conf /etc/supervisor/conf.d/supervisor_app.conf
ADD ./supervisor_app.conf /etc/supervisor/supervisord.conf
ADD ./. .
RUN cd instance && ln -sf ../config/$BUILD_ENV.py settings.py && cd ../
CMD ["./wait-for-it.sh", "$ES_ENV_HOST:9200", "--", "supervisord"]
