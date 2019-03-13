FROM alpine

ENV TERM linux
RUN apk --update --no-cache add bash apache2-utils
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /tmp/wait-for-it.sh
RUN chmod +x /tmp/wait-for-it.sh
