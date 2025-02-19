from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import socket
import os

# 📂 Dossier où seront stockés les fichiers partagés
SHARE_FOLDER = "shared_files"
os.makedirs(SHARE_FOLDER, exist_ok=True)  # Crée le dossier s'il n'existe pas

def get_local_ip():
    """Retourne l'adresse IP locale de la machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def start_ftp_server():
    """Démarre un serveur FTP sur le port 21"""
    authorizer = DummyAuthorizer()
    authorizer.add_user("user", "password", SHARE_FOLDER, perm="elradfmw")  # Identifiants FTP

    handler = FTPHandler
    handler.authorizer = authorizer

    ip = get_local_ip()
    print(f"🚀 Serveur FTP démarré sur {ip}:21")

    server = FTPServer(("0.0.0.0", 21), handler)
    server.serve_forever()

if __name__ == "__main__":
    start_ftp_server()
