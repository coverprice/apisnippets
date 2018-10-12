FROM fedora:28

RUN dnf update \
  && \
  dnf install -y \
    gnupg \
    python3 \
    python3-pip \
    python3-boto3 \
    python3-botocore \
    python3-gnupg \
    openldap-clients \
  && \
  pip-3 install --upgrade \
    google-oauth \
    google-api-python-client \
    google-auth-oauthlib \
    ldap3 \
    slackclient

COPY . /tools
WORKDIR "/tools"
ENTRYPOINT [ "/bin/bash" ]
