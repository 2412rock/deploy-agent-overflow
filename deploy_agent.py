
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
    f = open('/home/dorelapp1/keys/password.txt', 'r')
    password = f.readline()
    f.close()
    if password == data["password"]:
        deploy_fe = data["deploy_frontend"]
        deploy_be = data["deploy_backend"]
        should_deploy_redis = data["deploy_redis"]
        should_deploy_sql = data["deploy_sql"]
        should_deploy_minio = data["deploy_minio"]

        deploy_sql_migrations()
        
        if should_deploy_redis:
            deploy_redis_server()
        if should_deploy_sql:
            deploy_sql_server()
        if deploy_fe:
            deploy_frontend()
        if deploy_be:
            deploy_backend()
        if should_deploy_minio:
            deploy_minio_server()

        # Return a JSON response
        return jsonify("ok"), 200
    return jsonify("Bad password"), 400

def deploy_sql_server():
    os.chdir("/home/dorelapp1/code")
    os.system("rm -rf sql-server-docker")
    os.system("git clone https://github.com/2412rock/sql-server-overflow")
    os.chdir("/home/dorelapp1/code/sql-server-overflow")
    os.system("docker stop sql-server")
    os.system("docker rm sql-server")
    os.system("docker build -t sql-server .")
    #docker run, -e, SA_PASSWORD=MyP@ssword1!,-d -p 1433:1433 --name sql-server sql-server
    subprocess.Popen([
    "docker", "run", "-e", f'SA_PASSWORD={getSqlPassword()}',
    "-d", "-p", "1433:1433", "--name", "sql-server", "sql-server"
])
    print('Waiting for server to start')
    time.sleep(10)
    os.system("docker cp init.sql sql-server:/usr/src")
    os.system("docker cp pupulate_with_data.sql sql-server:/usr/src")
    #docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P MyP@ssword1! -d master -i /usr/src/init.sql
    os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/init.sql")
    os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/pupulate_with_data.sql")
