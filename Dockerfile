FROM fedora:28

RUN dnf update \
  && \
  dnf install -y \
    python3 \
    python3-pip \
    python3-boto3 \
    python3-botocore \
    python3-gnupg \
    gnupg \
    openldap-clients \
  && \
  pip-3 install --upgrade \
    google-oauth \
    google-api-python-client \
    google-auth-oauthlib \
    ldap3

COPY . /tools
WORKDIR "/tools"
ENTRYPOINT [ "/bin/bash" ]
