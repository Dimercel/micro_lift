FROM alpine:3.14

ARG workdir='/opt/micro_lift'

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en' \
    LC_ALL='en_US.UTF-8' \
    PYTHONUNBUFFERED=1

ENV APP_DIR="${workdir}" \
    APP_CODE="${workdir}/micro_lift" \
    APP_LOGS="${workdir}/logs" \
    APP_CONFIG="${workdir}/config"

RUN mkdir -p "$APP_CODE" "$APP_LOGS" "$APP_CONFIG"

RUN apk update && \
    apk add --no-cache \
        python3 \
        py3-pip && \
    rm -rf /var/cache/apk/* /var/tmp/* /tmp/*

COPY ./micro_lift $APP_CODE
COPY ./requirements.txt "$APP_DIR"

RUN apk add --no-cache \
        build-base \
        python3-dev && \
    pip3 install --no-cache-dir -r $APP_DIR/requirements.txt && \
    apk del build-base python3-dev && \
    rm -rf /var/cache/apk/* /var/tmp/* /tmp/*

WORKDIR ${workdir}

EXPOSE 8080

CMD ["python3", "micro_lift/main.py", "--config", "config/config.yaml"]