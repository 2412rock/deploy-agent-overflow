
from flask import Flask, request, jsonify
import os
import subprocess
import shutil
import glob
import socket
import time

app = Flask(__name__)

@app.route('/api/deploy', methods=['POST'])
def post_data():
    # Get the JSON data from the request
    data = request.get_json()
    f = open('/home/app/keys/password.txt', 'r')
    password = f.readline()
    f.close()
    if password == data["password"]:
        deploy_be = data["deploy_backend"]
        should_deploy_sql = data["deploy_sql"]
        #should_deploy_minio = data["deploy_minio"]
        
        if deploy_be:
            deploy_backend()
        if should_deploy_sql:
            deploy_sql_server()
        # if should_deploy_minio:
        #     deploy_minio_server()
        deploy_sql_migrations()
        # Return a JSON response
        return jsonify("ok"), 200
    return jsonify("Bad password"), 400

def getSqlPassword():
    f = open('/home/app/keys/sql_password.txt', 'r')
    password = f.readline()
    f.close()
    return password

def deploy_sql_migrations():
    os.chdir("/home/app/code")
    os.system("rm -rf sql-overflow")
    os.system("git clone https://github.com/2412rock/sql-overflow")
    os.chdir("/home/app/code/sql-overflow")

    os.system("docker cp init.sql sql-server:/usr/src")
    os.system("docker cp populate.sql sql-server:/usr/src")
    #docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P MyP@ssword1! -d master -i /usr/src/init.sql
    os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/init.sql")
    os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/populate.sql")


def deploy_sql_server():
    os.chdir("/home/app/code")
    os.system("rm -rf sql-overflow ")
    os.system("git clone https://github.com/2412rock/sql-overflow")
    os.chdir("/home/app/code/sql-overflow")
    os.system("docker stop sql-server")
    os.system("docker rm sql-server")
    os.system("docker build -t sql-server .")
    #docker run -e SA_PASSWORD=MyP@ssword1! -d -p 1433:1433 --name sql-overflow sql-overflow
    subprocess.Popen([
    "docker", "run", "-e", f'SA_PASSWORD={getSqlPassword()}',
    "-d", "-p", "1433:1433", "--name", "sql-server", "sql-server"
])
    print('Waiting for server to start')
    time.sleep(10)
    os.system("docker cp init.sql sql-overflow:/usr/src")
    os.system("docker cp pupulate_with_data.sql sql-server:/usr/src")
    #docker exec -it sql-overflow /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P MyP@ssword1! -d master -i /usr/src/init.sql
    os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/init.sql")
    os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/pupulate_with_data.sql")

def readLineFromFile(file):
    f = open(file)
    result = f.readline()
    f.close()
    return result

def deploy_backend():
    os.chdir("/home/app/code")
    os.system("rm -rf overflow-backend")
    os.system("git clone https://github.com/2412rock/overflow-backend")
    shutil.copy("/home/app/keys/backendcertificate.pfx", "/home/app/code/overflow-backend")
    os.chdir("/home/app/code/overflow-backend")
    os.system("docker stop backend")
    os.system("docker rm backend")
    os.system("docker build -t backend .")

    pfx_pass_file = open('/home/app/keys/pfx_pass.txt', 'r')
    pfx_pass = pfx_pass_file.readline()
    pfx_pass_file.close()

    jwt_secret = readLineFromFile("/home/app/keys/JWT_SECRET.txt")
    minio_password = readLineFromFile("/home/app/keys/minio_password.txt")
    subprocess.Popen(["docker", "run", "-e", f'SA_PASSWORD={getSqlPassword()}',
                       "-e", f'PFX_PASS={pfx_pass}',
                       "-e", f"JWT_SECRET={jwt_secret}",
                       "-e", f"MINIO_PASS={minio_password}",
                         "--name" ,"backend", "-p" ,"4200:4200" ,"backend"])