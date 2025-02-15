import socket
import os

# === Configuration ===
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # Crée le dossier s'il n'existe pas

def download_file(server_ip, filename):
    """Télécharge un fichier depuis un autre utilisateur (P2P)"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, 6000))  # Connexion au serveur FTP distant
        client.send(filename.encode())  # Demande du fichier

        data = client.recv(4096)
        if data != b"Fichier introuvable":
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            with open(filepath, "wb") as file:
                file.write(data)
            print(f"✅ Fichier '{filename}' téléchargé avec succès dans '{DOWNLOAD_FOLDER}/'.")
        else:
            print("❌ Fichier introuvable sur l'utilisateur distant.")

        client.close()

    except Exception as e:
        print(f"❌ Erreur lors du téléchargement : {e}")

# === Test de téléchargement ===
if __name__ == "__main__":
    server_ip = input("Entrez l'IP de l'utilisateur partageant le fichier : ")
    filename = input("Nom du fichier à télécharger : ")
    download_file(server_ip, filename)
