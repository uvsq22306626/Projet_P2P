import socket
from ftplib import FTP
import os
import getpass


# 📌 Configuration du serveur central
SERVER_IP = "10.188.142.246"  # Remplace par l'IP du serveur central
SERVER_PORT = 5000

# 📂 Dossier où seront stockés les fichiers téléchargés
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # Crée le dossier s'il n'existe pas

# 📂 Port FTP utilisé pour partager les fichiers
FTP_PORT = 21
current_user = None

def send_request(request):
    """Envoie une requête au serveur P2P"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, SERVER_PORT))
        client.send(request.encode())
        response = client.recv(4096).decode()
        client.close()
        return response
    except Exception as e:
        print(f"❌ Erreur de connexion au serveur : {e}")
        return None

def download_file_via_ftp(server_ip, server_port, filename):
    """Télécharge un fichier depuis un serveur FTP distant"""
    try:
        ftp = FTP()
        ftp.connect(server_ip, int(server_port))
        ftp.login("user", "password")  # Identifiants définis dans `ftp_server.py`

        with open(f"{DOWNLOAD_FOLDER}/{filename}", "wb") as file:
            ftp.retrbinary(f"RETR {filename}", file.write)

        ftp.quit()
        print(f"✅ Fichier '{filename}' téléchargé avec succès dans '{DOWNLOAD_FOLDER}/'.")
    except Exception as e:
        print(f"❌ Erreur de téléchargement via FTP : {e}")

# 📌 Interface utilisateur
while True:
    print("\n1. S'inscrire")
    print("2. Se connecter")
    print("3. Partager un fichier")
    print("4. Rechercher un fichier")
    print("5. Télécharger un fichier")
    print("6. Quitter")

    choix = input("Choisissez une option : ")

    if choix == "1":  # Inscription
        username = input("Nom d'utilisateur : ")
        password = getpass.getpass("Mot de passe (caché) : ")
        response = send_request(f"REGISTER {username} {password}")
        print(response if response else "❌ Erreur lors de l'inscription.")

    elif choix == "2":  # Connexion
        username = input("Nom d'utilisateur : ")
        password = getpass.getpass("Mot de passe (caché) : ")
        ftp_ip = socket.gethostbyname(socket.gethostname())  # Récupère l'IP locale
        response = send_request(f"LOGIN {username} {password} {ftp_ip} {FTP_PORT}")

        if response == "LOGIN_SUCCESS":
            current_user = username
            print("✅ Connexion réussie.")
        else:
            print("❌ Échec de connexion.")

    elif choix == "3" and current_user:  # Partager un fichier
        filename = input("Nom du fichier à partager : ")
        description = input("Description du fichier : ")
        response = send_request(f"UPLOAD {current_user} {filename} {description}")
        print(response if response else "❌ Erreur lors du partage.")

    elif choix == "4" and current_user:  # Rechercher un fichier
        keyword = input("Mot-clé de recherche : ")
        sort_by = input("Trier par (nom/date/propriétaire) : ")
        response = send_request(f"SEARCH {current_user} {keyword} {sort_by}")
        print(response if response else "❌ Aucun fichier trouvé.")

    elif choix == "5" and current_user:  # Télécharger un fichier
        filename = input("Entrez le nom du fichier à télécharger : ")
        response = send_request(f"DOWNLOAD {current_user} {filename}")

        if "Disponible chez" in response:
            owner_info = response.split("(")[-1].strip(")")
            owner_ip, owner_port = owner_info.split(":")
            print(f"📥 Téléchargement depuis FTP {owner_ip}:{owner_port}...")

            try:
                download_file_via_ftp(owner_ip, owner_port, filename)
            except Exception as e:
                print(f"❌ Erreur de téléchargement : {e}")
        else:
            print("❌ Fichier introuvable.")

    elif choix == "6":  # Quitter
        if current_user:
            send_request(f"LOGOUT {current_user}")
        print("👋 Déconnexion... Au revoir !")
        break

    else:
        print("❌ Option invalide ou vous devez d'abord vous connecter.")
