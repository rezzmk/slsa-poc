FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install mail server packages and Python
RUN apt-get update && apt-get install -y \
    postfix \
    dovecot-imapd \
    dovecot-pop3d \
    spamassassin \
    spamc \
    supervisor \
    mailutils \
    python3 \
    python3-pip \
    swaks \
    rsyslog \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install prometheus_client

# Configure SpamAssassin
RUN sed -i 's/ENABLED=0/ENABLED=1/' /etc/default/spamassassin && \
    sed -i 's/CRON=0/CRON=1/' /etc/default/spamassassin

# Create necessary users and groups
RUN groupadd -g 5000 vmail && \
    useradd -g vmail -u 5000 vmail -d /var/mail -M && \
    useradd -m testuser && echo "testuser:password" | chpasswd

# Create necessary directories and files
RUN mkdir -p /var/run/dovecot && \
    mkdir -p /var/mail && \
    mkdir -p /var/log && \
    mkdir -p /var/spool/postfix && \
    touch /var/log/mail.log && \
    chmod 777 /var/mail && \
    chmod 644 /var/log/mail.log

# Setup Maildir structure for testuser
RUN mkdir -p /var/mail/testuser/Maildir/new && \
    mkdir -p /var/mail/testuser/Maildir/cur && \
    mkdir -p /var/mail/testuser/Maildir/tmp && \
    chown -R testuser:testuser /var/mail/testuser && \
    chmod -R 700 /var/mail/testuser && \
    touch /var/mail/testuser/Maildir/subscriptions && \
    echo 'INBOX' > /var/mail/testuser/Maildir/subscriptions && \
    chown -R testuser:testuser /var/mail/testuser/Maildir/subscriptions && \
    chmod 600 /var/mail/testuser/Maildir/subscriptions

# Set final mail directory permissions
RUN chown -R vmail:vmail /var/mail && \
    chmod -R 2700 /var/mail && \
    chmod -R g+s /var/mail

# Copy configurations
COPY config/postfix/main.cf /etc/postfix/main.cf
COPY config/postfix/master.cf /etc/postfix/master.cf
COPY config/dovecot/dovecot.conf /etc/dovecot/dovecot.conf
COPY config/spamassassin/local.cf /etc/spamassassin/local.cf
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY config/rsyslog.conf /etc/rsyslog.conf

# Create log files and set permissions
RUN touch /var/log/mail.log && \
    chmod 644 /var/log/mail.log && \
    chown syslog:adm /var/log/mail.log

# Copy metrics exporter
COPY spam_metrics.py /usr/local/bin/
RUN chmod +x /usr/local/bin/spam_metrics.py

# Add mail.local to hosts
# RUN echo "127.0.0.1 mail.local mail localhost" >> /etc/hosts

EXPOSE 25 143 587 5000

# Start supervisord directly
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# Configure SpamAssassin
RUN mkdir -p /var/spamassassin && \
    mkdir -p /var/log/spamassassin && \
    chown debian-spamd:debian-spamd /var/spamassassin && \
    chown debian-spamd:debian-spamd /var/log/spamassassin && \
    sa-update
