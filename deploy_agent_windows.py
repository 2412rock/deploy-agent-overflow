
from flask import Flask, request, jsonify
import os
import subprocess
import shutil
import glob
import socket
import time
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

@app.route('/api/deploy', methods=['POST'])
def post_data():
    # Get the JSON data from the request
    data = request.get_json()
    f = open('C:/Users/Server/Documents/overflow/password.txt', 'r')
    password = f.readline()
    f.close()
    if password == data["password"]:
        deploy_be = data["deploy_backend"]
        should_deploy_sql = data["deploy_sql"]
        should_deploy_bot = data["deploy_bot"]
        #should_deploy_minio = data["deploy_minio"]
        
        if deploy_be:
            deploy_backend()
        if should_deploy_sql:
            deploy_sql_server()
        if should_deploy_bot:
            deploy_bot()
        # if should_deploy_minio:
        #     deploy_minio_server()
        deploy_sql_migrations()
        # Return a JSON response
        return jsonify("ok"), 200
    return jsonify("Bad password"), 400

def getSqlPassword():
    f = open('C:/Users/Server/Documents/overflow/sql_password.txt', 'r')
    password = f.readline()
    f.close()
    return password

def readLineFromFile(file):
    f = open(file)
    result = f.readline()
    f.close()
    return result


def deploy_bot():
    os.chdir("C:/Users/Server/Desktop")
    os.system("rmdir /S /Q overflow-bot")
    os.system("git clone https://github.com/2412rock/overflow-bot")
    os.chdir("C:/Users/Server/Desktop/overflow-bot")
    os.system("docker stop bot")
    os.system("docker rm bot")
    os.system("docker build -t bot .")
    local_ip = get_local_ip()
    password = readLineFromFile("C:/Users/Server/Documents/overflow/bot_password.txt")
    subprocess.Popen([
    "docker", "run", "-d", "-e", f"LOCAL_IP={local_ip}", "-e", f"PASSWORD={password}", "--name", "bot", "bot"])

def deploy_sql_migrations():
    os.chdir("C:/Users/Server/Desktop")
    os.system("rmdir /S /Q sql-overflow")
    os.system("git clone https://github.com/2412rock/sql-overflow")
    os.chdir("C:/Users/Server/Desktop/sql-overflow")

    os.system("docker cp init.sql sql-server:/usr/src")
    os.system("docker cp populate.sql sql-server:/usr/src")
    #docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P MyP@ssword1! -d master -i /usr/src/init.sql
    os.system(f'docker exec -it sql-server /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/init.sql')
    os.system(f'docker exec -it sql-server /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/populate.sql')


def deploy_sql_server():
    os.chdir("C:/Users/Server/Desktop")
    os.system("rmdir /S /Q sql-overflow ")
    os.system("git clone https://github.com/2412rock/sql-overflow")
    os.chdir("C:/Users/Server/Desktop/sql-overflow")
    os.system("docker stop sql-server")
    os.system("docker rm sql-server")
    os.system("docker build -t sql-server .")
    #docker run -e SA_PASSWORD=MyP@ssword1! -d -p 1433:1433 --name sql-overflow sql-overflow
    subprocess.Popen([
    "docker", "run", "-d", "-e", f'SA_PASSWORD={getSqlPassword()}',
     "-p", "1433:1433", "--name", "sql-server", "sql-server"
])
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
    os.chdir("C:/Users/Server/Desktop")
    os.system("rmdir /S /Q overflow-backend")
    os.system("git clone https://github.com/2412rock/overflow-backend")
    os.chdir("C:/Users/Server/Desktop/overflow-backend")
    os.system("docker stop backend")
    os.system("docker rm backend")
    os.system("docker build -t backend .")

    pfx_pass_file = open('C:/Users/Server/Documents/overflow/pfx_pass.txt', 'r')
    pfx_pass = pfx_pass_file.readline()
    pfx_pass_file.close()
    local_ip = get_local_ip()

    jwt_secret = readLineFromFile("C:/Users/Server/Documents/overflow/JWT_SECRET.txt")
    minio_password = readLineFromFile("C:/Users/Server/Documents/overflow/minio_password.txt")
    email_password = readLineFromFile("C:/Users/Server/Documents/overflow/emailpasswd.txt")
    subprocess.Popen(["docker", "run", "-d",
                      "-v",  "C:/Users/Server/docker-logs:/app/logs",
                      "-e", f'SA_PASSWORD={getSqlPassword()}',
                      "-e", f'LOCAL_IP={local_ip}',
                       "-e", f'PFX_PASS={pfx_pass}',
                       "-e", f"JWT_SECRET={jwt_secret}",
                       "-e", f"MINIO_PASS={minio_password}",
                       "-e", f"EMAIL_PASSWD={email_password}",
                         "--name" ,"backend", "-p" ,"4200:4200" ,"backend"])
    
if __name__ == '__main__':
    app.run(host="10.244.17.97", port="8080",debug=True)
