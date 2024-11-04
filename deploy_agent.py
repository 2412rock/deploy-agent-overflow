
from flask import Flask, request, jsonify
import os
import subprocess
import shutil
import glob
import socket
import time
import sys

desktop_dir = '/home/albuadrian2412/'
documents_dir = '/home/albuadrian2412/documents/overflow/'
host = sys.argv[1]

app = Flask(__name__)

@app.route('/api/deploy', methods=['POST'])
def post_data():
    # Get the JSON data from the request
    data = request.get_json()
    f = open(f'{documents_dir}password.txt', 'r')
    password = f.readline()
    f.close()
    if password == data["password"]:
        deploy_be = data["deploy_backend"]
        should_deploy_sql = data["deploy_sql"]
        deploy_migrations = data["deploy_migrations"]
        should_deploy_bot = data["deploy_bot"]
        #should_deploy_minio = data["deploy_minio"]
        
        if deploy_be:
            deploy_backend()
        if should_deploy_sql:
            deploy_sql_server(deploy_migrations)
        if should_deploy_bot:
            deploy_bot()
        # if should_deploy_minio:
        #     deploy_minio_server()
        if deploy_migrations:
            deploy_sql_migrations()
        # Return a JSON response
        return jsonify("ok"), 200
    return jsonify("Bad password"), 400

def getSqlPassword():
    f = open(f'{documents_dir}sql_password.txt', 'r')
    password = f.readline()
    f.close()
    return password

def readLineFromFile(file):
    f = open(file)
    result = f.readline()
    f.close()
    return result


def deploy_bot():
    os.chdir(f"{desktop_dir}")
    os.system("rm -rf overflow-bot")
    os.system("git clone https://github.com/2412rock/overflow-bot")
    os.chdir(f"{desktop_dir}overflow-bot")
    os.system("docker stop bot")
    os.system("docker rm bot")
    os.system("docker build -t bot .")
    local_ip = get_local_ip()
    password = readLineFromFile(f"{documents_dir}bot_password.txt")
    subprocess.Popen([
    "docker", "run", "-d", "-e", f"LOCAL_IP={local_ip}", "-e", f"PASSWORD={password}", "--name", "bot", "bot"])

def deploy_sql_migrations():
    os.chdir(f"{desktop_dir}")
    os.system("rm -rf sql-overflow")
    os.system("git clone https://github.com/2412rock/sql-overflow")
    os.chdir(f"{desktop_dir}sql-overflow")

    os.system("docker cp init.sql sql-server:/usr/src")
    os.system("docker cp populate.sql sql-server:/usr/src")
    #docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P MyP@ssword1! -d master -i /usr/src/init.sql
    os.system(f'docker exec -it sql-server /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/init.sql')
    os.system(f'docker exec -it sql-server /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/populate.sql')


def deploy_sql_server(deploy_migrations):
    os.chdir(f"{desktop_dir}")
    os.system("rm -rf sql-overflow ")
    os.system("git clone https://github.com/2412rock/sql-overflow")
    os.chdir(f"{desktop_dir}sql-overflow")
    os.system("docker stop sql-server")
    os.system("docker rm sql-server")
    os.system("docker build -t sql-server .")
    #docker run -e SA_PASSWORD=MyP@ssword1! -d -p 1433:1433 --name sql-overflow sql-overflow
    print(f'SA_PASSWORD={getSqlPassword()}')
    subprocess.Popen([
    "docker", "run", "-d", "-e", f'SA_PASSWORD={getSqlPassword()}',
     "-p", "1433:1433", "--name", "sql-server", "sql-server"
])
    if deploy_migrations:
        print('Waiting for server to start')
        time.sleep(10)
        os.system("docker cp init.sql sql-overflow:/usr/src")
        os.system("docker cp pupulate_with_data.sql sql-server:/usr/src")
        os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/init.sql")
        os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/pupulate_with_data.sql")

def get_local_ip():
    # Create a dummy connection to determine the LAN IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("192.168.1.1", 80))  # Using a common LAN IP as a dummy destination
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip


def deploy_backend():
    os.chdir(f"{desktop_dir}")
    os.system("rm -rf overflow-backend")
    os.system("git clone https://github.com/2412rock/overflow-backend")
    os.chdir(f"{desktop_dir}overflow-backend")
    os.system("docker stop backend")
    os.system("docker rm backend")
    os.system("docker build -t backend .")

    pfx_pass_file = open(f'{documents_dir}pfx_pass.txt', 'r')
    pfx_pass = pfx_pass_file.readline()
    pfx_pass_file.close()
    local_ip = get_local_ip()

    jwt_secret = readLineFromFile(f"{documents_dir}JWT_SECRET.txt")
    minio_password = readLineFromFile(f"{documents_dir}minio_password.txt")
    email_password = readLineFromFile(f"{documents_dir}emailpasswd.txt")
    subprocess.Popen(["docker", "run", "-d",
                      "-v",  f"{documents_dir}docker-logs:/app/logs",
                      "-e", f'SA_PASSWORD={getSqlPassword()}',
                      "-e", f'LOCAL_IP={local_ip}',
                       "-e", f'PFX_PASS={pfx_pass}',
                       "-e", f"JWT_SECRET={jwt_secret}",
                       "-e", f"MINIO_PASS={minio_password}",
                       "-e", f"EMAIL_PASSWD={email_password}",
                         "--name" ,"backend", "-p" ,"4200:4200" ,"backend"])
    
if __name__ == '__main__':
    app.run(host=host, port="8080",debug=True)
