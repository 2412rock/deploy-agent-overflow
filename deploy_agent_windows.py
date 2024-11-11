from flask import Flask, request, jsonify
import os
import subprocess
import socket
import time

app = Flask(__name__)

@app.route('/api/deploy', methods=['POST'])
def post_data():
    # Get the JSON data from the request
    data = request.get_json()
    password = read_password_from_file('C:/Users/Server/Documents/overflow/password.txt')
    
    if password == data.get("password"):
        deploy_be = data.get("deploy_backend")
        should_deploy_sql = data.get("deploy_sql")
        should_deploy_bot = data.get("deploy_bot")
        
        # Collect outputs from deployment tasks
        result = []
        
        if deploy_be:
            result.append(deploy_backend())
        if should_deploy_sql:
            result.append(deploy_sql_server())
        if should_deploy_bot:
            result.append(deploy_bot())
        
        result.append(deploy_sql_migrations())  # SQL migrations are always run

        return jsonify({"status": "ok", "details": result}), 200
    
    return jsonify({"status": "error", "message": "Bad password"}), 400


def read_password_from_file(file_path):
    """Reads the first line from a file and returns it."""
    try:
        with open(file_path, 'r') as f:
            return f.readline().strip()
    except FileNotFoundError:
        return None


def get_local_ip():
    """Gets the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("192.168.1.1", 80))  # Common LAN IP as a dummy destination
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip


def deploy_backend():
    """Deploys the backend container and returns the result."""
    os.chdir("C:/Users/Server/Desktop")
    os.system("rmdir /S /Q overflow-backend")
    os.system("git clone https://github.com/2412rock/overflow-backend")
    os.chdir("C:/Users/Server/Desktop/overflow-backend")
    
    # Stop and remove any existing container
    os.system("docker stop backend")
    os.system("docker rm backend")
    os.system("docker build -t backend .")

    pfx_pass = read_password_from_file('C:/Users/Server/Documents/overflow/pfx_pass.txt')
    local_ip = get_local_ip()

    # Read all required passwords from their respective files
    jwt_secret = read_password_from_file("C:/Users/Server/Documents/overflow/JWT_SECRET.txt")
    minio_password = read_password_from_file("C:/Users/Server/Documents/overflow/minio_password.txt")
    email_password = read_password_from_file("C:/Users/Server/Documents/overflow/emailpasswd.txt")
    
    # Run the backend container
    command = [
        "docker", "run", "-d",
        "-v", "C:/Users/Server/docker-logs:/app/logs",
        "-e", f'SA_PASSWORD={getSqlPassword()}',
        "-e", f'LOCAL_IP={local_ip}',
        "-e", f'PFX_PASS={pfx_pass}',
        "-e", f"JWT_SECRET={jwt_secret}",
        "-e", f"MINIO_PASS={minio_password}",
        "-e", f"EMAIL_PASSWD={email_password}",
        "--name", "backend", "-p", "4200:4200", "backend"
    ]
    
    return execute_command(command)


def deploy_sql_server():
    """Deploys the SQL Server container and returns the result."""
    os.chdir("C:/Users/Server/Desktop")
    os.system("rmdir /S /Q sql-overflow")
    os.system("git clone https://github.com/2412rock/sql-overflow")
    os.chdir("C:/Users/Server/Desktop/sql-overflow")
    
    os.system("docker stop sql-server")
    os.system("docker rm sql-server")
    os.system("docker build -t sql-server .")
    
    command = [
        "docker", "run", "-d",
        "-e", f'SA_PASSWORD={getSqlPassword()}',
        "-p", "1433:1433", "--name", "sql-server", "sql-server"
    ]
    
    result = execute_command(command)

    print('Waiting for server to start')
    time.sleep(10)
    
    os.system("docker cp init.sql sql-server:/usr/src")
    os.system("docker cp populate.sql sql-server:/usr/src")
    os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/init.sql")
    os.system(f"docker exec -it sql-server /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/populate.sql")

    return result


def deploy_bot():
    """Deploys the bot container and returns the result."""
    os.chdir("C:/Users/Server/Desktop")
    os.system("rmdir /S /Q overflow-bot")
    os.system("git clone https://github.com/2412rock/overflow-bot")
    os.chdir("C:/Users/Server/Desktop/overflow-bot")
    os.system("docker stop bot")
    os.system("docker rm bot")
    os.system("docker build -t bot .")
    
    local_ip = get_local_ip()
    password = read_password_from_file("C:/Users/Server/Documents/overflow/bot_password.txt")
    
    command = [
        "docker", "run", "-d", 
        "-e", f"LOCAL_IP={local_ip}", 
        "-e", f"PASSWORD={password}", 
        "--name", "bot", "bot"
    ]
    
    return execute_command(command)


def deploy_sql_migrations():
    """Deploys SQL migrations and returns the result."""
    os.chdir("C:/Users/Server/Desktop")
    os.system("rmdir /S /Q sql-overflow")
    os.system("git clone https://github.com/2412rock/sql-overflow")
    os.chdir("C:/Users/Server/Desktop/sql-overflow")

    os.system("docker cp init.sql sql-server:/usr/src")
    os.system("docker cp populate.sql sql-server:/usr/src")
    os.system(f'docker exec -it sql-server /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/init.sql')
    os.system(f'docker exec -it sql-server /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P {getSqlPassword()} -d master -i /usr/src/populate.sql')

    return "SQL migrations applied."


def execute_command(command):
    """Executes a command and returns the result."""
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        return f"Command executed successfully: {result}"
    except subprocess.CalledProcessError as e:
        return f"Command failed with error: {e.output}"


def getSqlPassword():
    """Fetches the SQL password."""
    return read_password_from_file('C:/Users/Server/Documents/overflow/sql_password.txt')


if __name__ == '__main__':
    app.run(host="10.244.17.97", port="80", debug=True)
