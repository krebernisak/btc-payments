FROM nginx:1.17.7
LABEL maintainer="Kristijan Rebernisak<kristijan.rebernisak@gmail.com>"

# copy nginx configuration file
RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/

# copy nginx project configuration file
RUN rm /etc/nginx/conf.d/default.conf
COPY project.conf /etc/nginx/conf.d/

# copy static files
COPY ./static ./static
