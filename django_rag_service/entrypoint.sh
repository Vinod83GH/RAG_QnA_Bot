#!/bin/bash
set -e
cmd="$@"

if [ -z "$AWS_REGION_SSM" ]; then
  export AWS_REGION_SSM=us-west-2
fi

# Local testing - Uncomment/Set while testing on local
#export AWS_PROFILE=
#export AWS_REGION=

if [ "$FETCH_AND_CONCAT_ENV" == True ]; then
  if [ -z $SSM_PARAM_ENV_NAME ]; then
    echo >&2 "SSM Parameter name not specified even after enabling it's usage. Exiting the container without starting it"
    sleep 5
    exit 1
  fi
  if [ -z $S3_ENV_FILE_NAME ]; then
    echo >&2 "S3 env file name not specified even after enabling it's usage. Exiting the container without starting it"
    sleep 5
    exit 1
  fi
  echo >&2 "Fetching env file fron s3"
  echo >&2 "Fetching the SSM Parameter from AWS:"
  echo 'aws s3 cp ${S3_ENV_FILE_NAME} /tmp/env_s3 --region ${AWS_REGION_SSM}' >/tmp/ssm_fetch_environ_file.sh
  echo 'aws ssm get-parameter --with-decryption --name ${SSM_PARAM_ENV_NAME} --region ${AWS_REGION_SSM} | jq -r '.Parameter.Value' >> /tmp/.env' >>/tmp/ssm_fetch_environ_file.sh
  echo 'cat /tmp/env_s3 >> /tmp/.env' >>/tmp/ssm_fetch_environ_file.sh
  bash /tmp/ssm_fetch_environ_file.sh
  aws_ssm_parameter_fetch_status=$?
  if [ $aws_ssm_parameter_fetch_status -eq 0 ]; then
    rm /tmp/ssm_fetch_environ_file.sh
    rm /tmp/env_s3
    export $(grep -v '^#' /tmp/.env | xargs -d '\n')
  else
    echo >&2 "Unable to access SSM Parameter name specified in the env. Exiting the container without starting it."
    sleep 5
    exit 1
  fi
fi

if [ "$FETCH_SSM_PARAM_ENV" == True ]; then
  if [ -z $SSM_PARAM_ENV_NAME ]; then
    echo >&2 "SSM Parameter name not specified even after enabling it's usage. Exiting the container without starting it"
    sleep 5
    exit 1
  else
    echo >&2 "Fetching the SSM Parameter from AWS:"
    echo 'aws ssm get-parameter --with-decryption --name ${SSM_PARAM_ENV_NAME} --region ${AWS_REGION_SSM} | jq -r '.Parameter.Value' > /tmp/.env' >/tmp/ssm_fetch_environ_file.sh
    bash /tmp/ssm_fetch_environ_file.sh
    aws_ssm_parameter_fetch_status=$?
    if [ $aws_ssm_parameter_fetch_status -eq 0 ]; then
      rm /tmp/ssm_fetch_environ_file.sh
      export $(grep -v '^#' /tmp/.env | xargs -d '\n')
    else
      echo >&2 "Unable to access SSM Parameter name specified in the env. Exiting the container without starting it."
      sleep 5
      exit 1
    fi
  fi
fi

GWC="${GUNICORN_WORKER_COUNT:=4}"
GGTC="${GUNICORN_GTHREAD_COUNT:=6}"
GGTO="${GUNICORN_GRACEFUL_TIMEOUT:=45}"
GWMXR="${GUNICORN_WORKER_MAX_REQUESTS:=250}"


if [ -z "$cmd" ]; then
  if [ "$DEBUG" == False ]; then
        echo >&2 "Running migrate command:"
        python $APP_HOME/django_rag_service/manage.py migrate --noinput
        python $APP_HOME/django_rag_service/manage.py collectstatic --noinput
        echo >&2 "DEBUG is set to False."
        gunicorn config.asgi:application --timeout 120 --keep-alive 120 --max-requests $GWMXR --graceful-timeout $GGTO -w $GWC --threads $GGTC -b 0.0.0.0:8000 --access-logfile=- -k uvicorn.workers.UvicornWorker --log-file -
  else
        echo >&2 "Running migrate command:"
        python $APP_HOME/django_rag_service/manage.py migrate --noinput
        python $APP_HOME/django_rag_service/manage.py collectstatic --noinput
        echo >&2 "DEBUG NOT set as False. DO NOT RUN with this setting on Production."
        gunicorn config.asgi:application --timeout 120 --keep-alive 120 -w 4 -b 0.0.0.0:8000 --access-logfile=- -k uvicorn.workers.UvicornWorker --log-file -
  fi
else 
    echo >&2 "Executing command passed using docker-compose"
    exec $cmd
fi
sleep infinity
