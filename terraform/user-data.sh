#!/bin/bash

# We really should be using something better for this...like Chef.

apt-get update -y && apt-get dist-upgrade -y

apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    nginx \
    software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

apt-get install -y docker-ce docker-ce-cli containerd.io

export REGISTRY_HOST="${docker_registry_host}"

docker image pull "${docker_image_name}"

cat <<EOF >/etc/systemd/system/hedge.service
[Unit]
Description=Hedge Container
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=root
ExecStart=docker run --rm --name hedge_container -p 8080:8080 "${docker_image_name}"
ExecStop=docker container stop hedge_container

[Install]
WantedBy=multi-user.target
EOF

systemctl enable hedge.service
systemctl start hedge.service

# Proxy the docker container
cat <<EOF > /etc/nginx/sites-available/default

server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        location / {
            proxy_pass http://localhost:8080/;
            proxy_set_header Connection "";
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
        }
}
EOF

systemctl restart nginx
