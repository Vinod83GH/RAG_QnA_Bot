FROM python:3.11-slim

# ENV TERM linux
ENV APPUSER_HOME /home/appuser
ENV APP_HOME /application

ENV APP_SRC /application/django_rag_service
ENV PYTHONPATH "${PYTHONPATH}:/application/django_rag_service"

WORKDIR $APP_HOME

RUN apt-get update && apt-get upgrade -y
# copy all items in current local directory (source) to current container directory (destination)
COPY . .
RUN set -ex \
    && buildDeps=' \
    libpq-dev \
    python3-dev' \
    && apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
    $buildDeps \
    build-essential \
    jq \
    procps \
    awscli \
    openssh-client \
    git \
    curl

RUN useradd -m -u 10010 appuser

WORKDIR $APP_HOME
#COPY entrypoint.sh entrypoint.sh

# Copy code into Image
ADD . $APP_HOME

# Add python package folder
RUN mkdir -p $APPUSER_HOME/.local
RUN chmod 600 $APPUSER_HOME/.local && chmod 700 $APPUSER_HOME/.local

# Copy keys
RUN mkdir -p $APPUSER_HOME/.ssh

RUN chown -R appuser $APP_HOME
RUN chown -R appuser $APP_HOME $APPUSER_HOME/.local
RUN chown -R appuser $APP_HOME $APPUSER_HOME/.ssh


COPY ./entrypoint.sh /entrypoint.sh

RUN sed -i 's/\r//' /entrypoint.sh
RUN chmod +x /entrypoint.sh


RUN pip install --upgrade pip

USER appuser

# Make entrypoint.sh executable
RUN chmod +x entrypoint.sh

# Install pip packages
RUN pip install --user -r requirements.txt


ENV PATH="/home/appuser/.local/bin:${PATH}"

# Clean up Build Files
RUN rm -rf $APP_HOME/.Build-Dir*

EXPOSE 8000
EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
