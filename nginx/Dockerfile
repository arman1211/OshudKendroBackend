FROM nginx

RUN apt-get update -y && apt-get install -y wait-for-it

CMD ["nginx", "-g", "--timeout 180", "daemon off;"]