FROM pretix/standalone:stable

USER root

# Copy SSH keys
COPY id_pretix_enterprise /root/.ssh/id_rsa
COPY id_pretix_enterprise.pub /root/.ssh/id_rsa.pub

# Set up SSH and install plugin
RUN chmod -R 0600 /root/.ssh && \
    mkdir -p /etc/ssh && \
    ssh-keyscan -t rsa -p 10022 code.rami.io >> /root/.ssh/known_hosts && \
    echo StrictHostKeyChecking=no >> /root/.ssh/config && \
    DJANGO_SETTINGS_MODULE= pip3 install -U "git+ssh://git@code.rami.io:10022/pretix/pretix-rollno-validator.git@stable#egg=pretix-rollno-validator" && \
    cd /pretix/src && \
    sudo -u pretixuser make production

USER pretixuser 