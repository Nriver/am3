[Unit]
Description=Application Manager for Python 3
Documentation=https://github.com/Nriver/am3
After=network.target

[Service]
Type=forking
User={user}
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
Environment=PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
Environment=AM3_HOME={am3_data_path}
# PIDFile={am3_data_path}/am3.pid
Restart=on-failure

ExecStart={am3_executable_path} load
ExecReload={am3_executable_path} restart all
ExecStop={am3_executable_path} stop all

[Install]
WantedBy=multi-user.target
