FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y git && \
    yum clean all

COPY src/ ${LAMBDA_TASK_ROOT}/

CMD ["lambda_handler.lambda_backup_repository"]