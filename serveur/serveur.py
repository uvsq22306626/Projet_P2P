import socket
import sqlite3
import threading
import bcrypt  
import time

# === Initialisation de la base de données ===
conn = sqlite3.connect("p2p_db.sqlite", check_same_thread=False)
cursor = conn.cursor()

# Création des tables pour stocker les utilisateurs, fichiers et sessions
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT UNIQUE, 
        password TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY, 
        filename TEXT, 
        owner TEXT,
        description TEXT
    )
""")
cursor.execute("CREATE TABLE IF NOT EXISTS sessions (username TEXT, ip TEXT, last_ping REAL)")  
conn.commit()

# === Vérifier si un utilisateur est connecté ===
def is_user_connected(username):
    cursor.execute("SELECT username FROM sessions WHERE username=?", (username,))
    return cursor.fetchone() is not None

# === Supprimer les utilisateurs inactifs ===
def remove_inactive_users():
    """Supprime les utilisateurs inactifs après 60 secondes"""
    while True:
        cursor.execute("SELECT username, last_ping FROM sessions")
        users = cursor.fetchall()

        for user in users:
            username, last_ping = user
            if time.time() - last_ping > 60:  
                cursor.execute("DELETE FROM files WHERE owner=?", (username,))
                cursor.execute("DELETE FROM sessions WHERE username=?", (username,))
                conn.commit()
                print(f"🔴 Utilisateur {username} déconnecté automatiquement.")

        time.sleep(30)  

# Lancer le nettoyage des utilisateurs inactifs en parallèle
threading.Thread(target=remove_inactive_users, daemon=True).start()

# === Gestion d'un client ===
def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        print(f"📩 Requête reçue : {request}")

        if request.startswith("REGISTER"):
            _, username, hashed_password = request.split(maxsplit=2)  
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                client_socket.send(b"REGISTER_SUCCESS")
            except sqlite3.IntegrityError:
                client_socket.send(b"REGISTER_FAILED")  

        elif request.startswith("LOGIN"):
            try:
                _, username, password, ip = request.split()
                cursor.execute("SELECT password FROM users WHERE username=?", (username,))
                user = cursor.fetchone()

                if user and bcrypt.checkpw(password.encode(), user[0].encode()):  
                    cursor.execute("INSERT INTO sessions (username, ip, last_ping) VALUES (?, ?, ?)", (username, ip, time.time()))
                    conn.commit()
                    client_socket.send(b"LOGIN_SUCCESS")
                else:
                    client_socket.send(b"LOGIN_FAILED")
            except ValueError:
                client_socket.send(b"LOGIN_FAILED")  

        elif request.startswith("PING"):
            _, username = request.split()
            cursor.execute("UPDATE sessions SET last_ping=? WHERE username=?", (time.time(), username))
            conn.commit()
            client_socket.send(b"PING_OK")

        elif request.startswith("UPLOAD") or request.startswith("SEARCH") or request.startswith("DOWNLOAD"):
            parts = request.split(maxsplit=3)  
            username = parts[1]  

            if not is_user_connected(username):
                client_socket.send(b"ACCESS_DENIED")  
                return

            if request.startswith("UPLOAD"):
                _, username, filename, description = parts
                cursor.execute("INSERT INTO files (filename, owner, description) VALUES (?, ?, ?)", (filename, username, description))
                conn.commit()
                client_socket.send(b"UPLOAD_SUCCESS")

            elif request.startswith("SEARCH"):
                _, username, keyword, sort_by = parts  
                sort_column = "filename"  
                if sort_by == "date":
                    sort_column = "id"  
                elif sort_by == "owner":
                    sort_column = "owner"

                sql_query = f"""
                    SELECT filename, owner, description 
                    FROM files 
                    WHERE filename LIKE ? OR description LIKE ?
                    ORDER BY {sort_column} ASC
                """

                cursor.execute(sql_query, ('%' + keyword + '%', '%' + keyword + '%'))
                results = cursor.fetchall()

                if results:
                    response = "\n".join([f"📂 {r[0]} - {r[2]} (Partagé par: {r[1]})" for r in results])
                else:
                    response = "❌ Aucun fichier trouvé."

                client_socket.send(response.encode())

            elif request.startswith("DOWNLOAD"):
                _, username, filename = request.split()  

                cursor.execute("SELECT owner, ip FROM sessions JOIN files ON sessions.username = files.owner WHERE files.filename=?", (filename,))
                file_owner = cursor.fetchone()

                if file_owner:
                    response = f"{filename} - Disponible chez: {file_owner[0]} ({file_owner[1]})"
                else:
                    response = "❌ Fichier introuvable."

                client_socket.send(response.encode())


        elif request.startswith("LOGOUT"):
            _, username = request.split()
            cursor.execute("DELETE FROM files WHERE owner=?", (username,))
            cursor.execute("DELETE FROM sessions WHERE username=?", (username,))
            conn.commit()
            client_socket.send(b"LOGOUT_SUCCESS")

    except Exception as e:
        print(f"❌ Erreur lors du traitement de la requête : {e}")

    finally:
        client_socket.close()

# === Démarrer le serveur ===
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 5000))  
server.listen(5)
print("🚀 Serveur P2P sécurisé démarré sur le port 5000...")

while True:
    client, addr = server.accept()
    print(f"🔗 Connexion établie avec {addr}")
    threading.Thread(target=handle_client, args=(client,)).start()
