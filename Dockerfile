FROM odoo:18

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3-venv python3-pip \
 && rm -rf /var/lib/apt/lists/*

# Create virtualenv and install OpenAI SDK inside it
RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install -U pip setuptools wheel \
 && /opt/venv/bin/pip install openai

# Ensure Odoo uses venv python/pip packages first
ENV PATH="/opt/venv/bin:${PATH}"

USER odoo

