import socket
import getpass  
import threading
import time
import bcrypt

current_user = None  

def send_request(request):
    """Envoie une requête au serveur et reçoit la réponse"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", 5000))  
        client.send(request.encode())
        response = client.recv(4096).decode()
        print(response)
        client.close()
        return response
    except ConnectionResetError:
        print("❌ Erreur : Connexion au serveur perdue.")
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")

def get_local_ip():
    """Retourne l'adresse IP locale de la machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def send_ping():
    """Envoie un PING toutes les 30 secondes pour indiquer que l'utilisateur est actif"""
    while current_user:
        send_request(f"PING {current_user}")
        time.sleep(30)  

# === Menu du client ===
while True:
    print("\n1. S'inscrire")
    print("2. Se connecter")
    print("3. Partager un fichier")
    print("4. Rechercher un fichier")
    print("5. Télécharger un fichier")
    print("6. Se déconnecter")
    print("7. Quitter")

    choix = input("Choisissez une option : ")

    if choix == "1":  # S'inscrire
        username = input("Nom d'utilisateur : ")
        password = getpass.getpass("Mot de passe (caché) : ")  
        
        # 🔒 Hachage du mot de passe avant de l'envoyer
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        send_request(f"REGISTER {username} {hashed_password}")  

    elif choix == "2":  # Se connecter
        username = input("Nom d'utilisateur : ")
        password = getpass.getpass("Mot de passe (caché) : ")
        ip = get_local_ip()  
        response = send_request(f"LOGIN {username} {password} {ip}")  
        
        if response == "LOGIN_SUCCESS":
            current_user = username  
            threading.Thread(target=send_ping, daemon=True).start()  # 🔄 Lancer le PING automatique
        else:
            print("❌ Échec de connexion.")

    elif choix == "3" and current_user:  # Partager un fichier
        filename = input("Nom du fichier à partager : ")
        description = input("Description du fichier : ")
        send_request(f"UPLOAD {current_user} {filename} {description}")

    elif choix == "4" and current_user:  # Rechercher un fichier
        keyword = input("Mot-clé de recherche : ")
        sort_by = input("Trier par (nom/date/propriétaire) : ").lower()

        # Vérifier si l'utilisateur entre un bon type de tri
        if sort_by not in ["nom", "date", "propriétaire"]:
            print("❌ Option invalide pour le tri. Utilisation par défaut : nom.")
            sort_by = "nom"

        request = f"SEARCH {current_user} {keyword} {sort_by}"
        print(f"🟢 Envoi de la requête au serveur : {request}")  # DEBUG
        
        response = send_request(request)
        print(f"🔵 Réponse reçue : {response}")  # DEBUG

    elif choix == "5" and current_user:  # Télécharger un fichier
        filename = input("Entrez le nom du fichier à télécharger : ")
        response = send_request(f"DOWNLOAD {current_user} {filename}")  

        if "Disponible chez" in response:
            owner_ip = response.split("(")[-1].strip(")")
            print(f"📥 Téléchargement depuis {owner_ip}...")

            try:
                from file_client import download_file
                download_file(owner_ip, filename)
            except Exception as e:
                print(f"❌ Erreur de téléchargement : {e}")
        else:
           print("❌ Fichier introuvable.")


    elif choix == "6":  # Se déconnecter
        send_request(f"LOGOUT {current_user}")
        current_user = None
        print("✅ Déconnexion réussie.")

    elif choix == "7":  # Quitter
        print("🔴 Fermeture du client...")
        break

    else:
        print("❌ Option invalide, réessayez.")
