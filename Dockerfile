FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y git && \
    yum clean all

COPY src/ ${LAMBDA_TASK_ROOT}/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

CMD ["lambda_handler.lambda_backup_repository"]