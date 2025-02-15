import socket
import threading
import os

# === Configuration ===
HOST = "0.0.0.0"  # Accepter les connexions de n'importe où
PORT = 6000  # Port FTP utilisé pour le P2P

# === Dossier de partage des fichiers ===
SHARE_FOLDER = "shared_files"
os.makedirs(SHARE_FOLDER, exist_ok=True)  # Crée le dossier s'il n'existe pas

def handle_client(client_socket):
    """Gère une demande de téléchargement de fichier"""
    try:
        filename = client_socket.recv(1024).decode()
        filepath = os.path.join(SHARE_FOLDER, filename)
        
        if os.path.exists(filepath):
            with open(filepath, "rb") as file:
                client_socket.sendall(file.read())  # Envoie du fichier
            print(f"📤 Fichier '{filename}' envoyé avec succès.")
        else:
            client_socket.send(b"Fichier introuvable")
            print(f"❌ Fichier '{filename}' introuvable.")

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du fichier : {e}")

    finally:
        client_socket.close()

def start_file_server():
    """Démarre le serveur de partage de fichiers"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"🚀 Serveur de fichiers démarré sur le port {PORT}...")

    while True:
        client, addr = server.accept()
        print(f"🔗 Connexion de {addr} pour téléchargement")
        threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == "__main__":
    start_file_server()
