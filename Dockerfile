FROM registry.gocurb.internal:80/ansible

RUN apt-get update && \
		apt-get -y upgrade && \
		apt-get install -y build-essential
RUN mkdir -p /opt/curbformation
WORKDIR /opt/curbformation
RUN pip install -e .
ENTRYPOINT ["make", "test"]
