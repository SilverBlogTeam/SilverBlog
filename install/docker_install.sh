#!/usr/bin/env bash
set -o errexit
if test $(ps h -o comm -p $$) = "sh"; then
    echo "Please use bash to execute this script."
    exit 1
fi
if [[ $UID -eq 0 ]]; then
    read -p "Running this script as root can damage your system. Continue to execute? (y/N) :" yn
    if [[ "$yn" != "Y" ]] || [[ "$yn" != "y" ]]; then
        exit 0
    fi
fi
china_install=false
install_name="silverblog"

while getopts "n:c" arg; do
    case ${arg} in
         n)
            install_name=$OPTARG
            ;;
         c)
            china_install=true
            ;;
         ?)
            echo "Unknown argument"
            echo "use ./docker_install.sh [-n <project name>] [-c]"
            exit 1
            ;;
    esac
done

docker_image="silverblog/silverblog"
repo_url=https://github.com/SilverBlogTeam/SilverBlog.git

if [[ ${china_install} = true ]];then
    docker_image="registry.cn-hangzhou.aliyuncs.com/silverblog/silverblog"
    repo_url=https://code.aliyun.com/silverblogteam/silverblog.git
fi

if [[ ! -f "initialization.sh" ]]; then
    if [[ ! -d ${install_name} ]]; then
        echo "Cloning silverblog..."
        git clone ${repo_url} --depth=1 ${install_name}
    fi
    cd ${install_name}
    echo "Change directory to $(pwd)"
    git fetch
    cd install
    echo "Change directory to $(pwd)"
fi

echo "{\"install\":\"docker\"}" > install.lock


if [[ ! -f "./nginx_config" ]]; then
python nginx_gen.py --tcp
fi

cd ..
echo "Change directory to $(pwd)"

bash install/initialization.sh

embedded_nginx=false
read -p "Use embedded nginx? (Y/N) :" yn
if [[ "$yn" == "Y" ]] || [[ "$yn" == "y" ]]; then
embedded_nginx=true
fi

sed -i '''s@./config/unix_socks/main.sock@0.0.0.0:5000@g' uwsgi.json
sed -i '''s@./config/unix_socks/control.sock@0.0.0.0:5001@g' uwsgi.json

if [[ ${embedded_nginx} == false ]];then
if [[ ! -f "./docker-compose.yml" ]]; then
cat << EOF > docker-compose.yml
version: '3'
services:
  ${install_name}:
    user: user_docker
    image: "${docker_image}"
    container_name: "${install_name}"
    restart: on-failure:10
    command: python3 watch.py
    volumes:
     - /etc/localtime:/etc/localtime:ro
     - $(pwd):/home/silverblog/
    ports:
     - "127.0.0.1:5000:5000"
  ${install_name}_control:
    image: "${docker_image}"
    container_name: "${install_name}_control"
    restart: on-failure:10
    command: python3 watch.py --control
    volumes:
     - /etc/localtime:/etc/localtime:ro
     - $(pwd):/home/silverblog/
    ports:
     - "127.0.0.1:5001:5001"
EOF
fi
fi

if [[ ${embedded_nginx} == true ]];then
sed -i ''"s/127.0.0.1:5000/${install_name}:5000/g" nginx_config
sed -i ''"s/127.0.0.1:5001/${install_name}_control:5001/g" nginx_config
sed -i ''"s@$(pwd)@/home/silverblog@g" nginx_config
if [[ ! -f "./docker-compose.yml" ]]; then
cat << EOF > docker-compose.yml
version: '3'
services:
  ${install_name}:
    image: "${docker_image}"
    container_name: "${install_name}"
    restart: on-failure:10
    command: python3 watch.py
    networks:
     - ${install_name}_net
    volumes:
     - /etc/localtime:/etc/localtime:ro
     - $(pwd):/home/silverblog/
  ${install_name}_control:
    image: "${docker_image}"
    container_name: "${install_name}_control"
    restart: on-failure:10
    command: python3 watch.py --control
    networks:
     - ${install_name}_net
    volumes:
     - /etc/localtime:/etc/localtime:ro
     - $(pwd):/home/silverblog/
  ${install_name}_nginx:
    image: "nginx:alpine"
    container_name: "${install_name}_nginx"
    restart: on-failure:10
    command: sh -c "cp \"/home/silverblog/nginx_config\" /etc/nginx/conf.d/default.conf && nginx -g \"daemon off;\""
    networks:
      - ${install_name}_net
    depends_on:
      - ${install_name}
      - ${install_name}_control
    ports:
      - 80:80
    volumes:
      - $(pwd):/home/silverblog
networks:
  ${install_name}_net:
EOF
fi
fi

if test $(ps h -o comm -p $$) = "bash"; then
shell_config_file="$HOME/.bashrc"
if [[ -f "$HOME/.bash_profile" ]]; then
shell_config_file="~/.bash_profile"
fi
fi

if test $(ps h -o comm -p $$) = "zsh"; then
if [[ -f "$HOME/.zshrc" ]]; then
shell_config_file="$HOME/.zshrc"
fi
fi

echo -e "\nYou need to perform [./manage.py] to initialize your silverblog environment."
echo -e "\nYou can add the following code to [${shell_config_file}] to quickly launch SilverBlog."
echo -e "\necho \"${install_name}() {(cd \"$(pwd)\"&&./manage.py \\\$@)}\" >> ${shell_config_file}"
echo -e "\nYou can generate an nginx configuration file using ./install/gen_nginx.py."