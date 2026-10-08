from flask import Flask,render_template,request,jsonify
from pathlib import Path
import sqlite3,hashlib
app=Flask(__name__); DB="integrity.db"; BASE=Path("monitored_files"); BASE.mkdir(exist_ok=True)
def con():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def h(p):
 x=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): x.update(b)
 return x.hexdigest()
def init():
 c=con(); c.execute("CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY,filename TEXT UNIQUE,hash TEXT)"); c.commit(); c.close()
@app.get("/")
def home(): return render_template("index.html")
@app.get("/api/files")
def files():
 c=con(); rs=c.execute("SELECT * FROM files").fetchall(); c.close(); out=[]
 for r in rs:
  p=BASE/r["filename"]; status="Missing" if not p.exists() else ("Unchanged" if h(p)==r["hash"] else "Modified")
  out.append({**dict(r),"status":status})
 return jsonify(out)
@app.post("/api/add")
def add():
 name=request.form.get("filename","").strip()
 if not name or "/" in name or "\\" in name:return jsonify(error="Invalid filename"),400
 p=BASE/name
 if not p.exists():return jsonify(error="Put the file inside monitored_files first"),404
 c=con()
 try:c.execute("INSERT INTO files(filename,hash) VALUES(?,?)",(name,h(p)));c.commit()
 except sqlite3.IntegrityError:c.close();return jsonify(error="Already registered"),400
 c.close();return jsonify(ok=True)
@app.delete("/api/remove/<int:i>")
def remove(i):
 c=con();c.execute("DELETE FROM files WHERE id=?",(i,));c.commit();c.close();return jsonify(ok=True)
init()
if __name__=="__main__":app.run(debug=True)
