FROM tensorflow/tensorflow

LABEL maintainer="Shuhei Iitsuka <tushuhei@google.com>"

RUN apt-get update && \
    apt-get install -y git \
        python3 \
        python3-pip \
        apt-utils && \
    apt-get clean

RUN pip3 install -U pip

RUN pip3 --no-cache-dir install tensorflowjs==0.3.1

WORKDIR /


CMD python3 -m tensorflowjs.converters.converter \
        --input_format=tf_saved_model \
        --output_node_names='final_result' \
        --saved_model_tags=serve \
        /data/saved_model/ \
        /data/saved_model_web/