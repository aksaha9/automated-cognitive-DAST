from fastapi import FastAPI, HTTPException
import sqlite3
import os

app = FastAPI()

# Setup dummy database
DB_FILE = "test.db"
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'secret123')")
cursor.execute("INSERT INTO users (username, password) VALUES ('user', 'password')")
conn.commit()

@app.get("/")
def read_root():
    return {"message": "Vulnerable API is running"}

@app.get("/search")
def search_users(q: str):
    # Intentional SQL Injection Vulnerability
    query = f"SELECT * FROM users WHERE username = '{q}'"
    print(f"Executing Query: {query}")
    try:
        # Cursor is not thread safe, create new one
        local_conn = sqlite3.connect(DB_FILE)
        local_cursor = local_conn.cursor()
        local_cursor.execute(query)
        results = local_cursor.fetchall()
        local_conn.close()
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": str(e), "query": query}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
