FROM alpine:3.9
ENV DOWNSPEED_PATH /downspeed/
ADD /downspeed/curl.txt $DOWNSPEED_PATH/curl.txt
ADD downspeed-exporter-host.py /run.py
ADD downspeed-exporter-list.py /run_list.py
RUN apk --no-cache add python3 curl py3-yaml \
    && pip3 install prometheus_client

ENTRYPOINT [ "/run.py" ]
