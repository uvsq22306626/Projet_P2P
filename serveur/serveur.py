import socket
import threading
import sqlite3
import time
import bcrypt

# 📌 Configuration du serveur
HOST = "0.0.0.0"
PORT = 5000

# 📂 Connexion à la base de données SQLite
conn = sqlite3.connect("p2p_db.sqlite", check_same_thread=False)
cursor = conn.cursor()

# 📌 Création des tables si elles n'existent pas
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        filename TEXT, 
        description TEXT, 
        owner TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        username TEXT, 
        ip TEXT, 
        ftp_port INTEGER, 
        last_ping REAL
    )
""")
conn.commit()

def handle_client(client_socket):
    """Gère les requêtes du client"""
    try:
        request = client_socket.recv(1024).decode()
        print(f"📩 Requête reçue : {request}")

        if request.startswith("REGISTER"):
            _, username, password = request.split()
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            client_socket.send(b"REGISTER_SUCCESS")

        elif request.startswith("LOGIN"):
            try:
                _, username, password, ip, ftp_port = request.split()
                cursor.execute("SELECT password FROM users WHERE username=?", (username,))
                user = cursor.fetchone()

                if user and bcrypt.checkpw(password.encode(), user[0].encode()):  
                    cursor.execute("INSERT INTO sessions (username, ip, ftp_port, last_ping) VALUES (?, ?, ?, ?)", 
                                   (username, ip, int(ftp_port), time.time()))
                    conn.commit()
                    client_socket.send(b"LOGIN_SUCCESS")
                else:
                    client_socket.send(b"LOGIN_FAILED")
            except ValueError:
                client_socket.send(b"LOGIN_FAILED")

        elif request.startswith("UPLOAD"):
            _, username, filename, description = request.split(maxsplit=3)
            cursor.execute("INSERT INTO files (filename, description, owner) VALUES (?, ?, ?)", 
                           (filename, description, username))
            conn.commit()
            client_socket.send(b"UPLOAD_SUCCESS")

        elif request.startswith("SEARCH"):
            _, username, keyword, sort_by = request.split(maxsplit=3)
            if sort_by not in ["nom", "date", "propriétaire"]:
                sort_by = "nom"

            query = "SELECT filename, description, owner FROM files WHERE description LIKE ?"
            cursor.execute(query, ('%' + keyword + '%',))
            results = cursor.fetchall()

            response = "\n".join([f"{file[0]} - {file[1]} - {file[2]}" for file in results]) if results else "Aucun fichier trouvé."
            client_socket.send(response.encode())

        elif request.startswith("DOWNLOAD"):
            _, username, filename = request.split()
            cursor.execute("SELECT owner, ip, ftp_port FROM sessions JOIN files ON sessions.username = files.owner WHERE files.filename=?", (filename,))
            file_owner = cursor.fetchone()

            if file_owner:
                response = f"{filename} - Disponible chez: {file_owner[0]} ({file_owner[1]}:{file_owner[2]})"
            else:
                response = "❌ Fichier introuvable."
            
            client_socket.send(response.encode())

        elif request.startswith("LOGOUT"):
            _, username = request.split()
            cursor.execute("DELETE FROM sessions WHERE username=?", (username,))
            conn.commit()
            client_socket.send(b"LOGOUT_SUCCESS")

        elif request.startswith("PING"):
            _, username = request.split()
            cursor.execute("UPDATE sessions SET last_ping=? WHERE username=?", (time.time(), username))
            conn.commit()

    except Exception as e:
        print(f"❌ Erreur lors du traitement de la requête : {e}")

    finally:
        client_socket.close()

def start_server():
    """Démarre le serveur P2P"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"🚀 Serveur P2P démarré sur le port {PORT}...")

    while True:
        client, addr = server.accept()
        print(f"🔗 Connexion de {addr}")
        threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == "__main__":
    start_server()
