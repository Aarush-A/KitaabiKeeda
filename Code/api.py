from flask import request, jsonify
from flask_restful import Resource
from matplotlib import pyplot as plt
import os
import sqlite3
import fpdf


class user_api(Resource):    
    def get(self):
        data=request.get_json()
        username=data.get('username')
        password=data.get('password')
        conn=sqlite3.connect('maindb.db')
        x=conn.execute("SELECT * FROM users where username=? AND password=?", (username, password)).fetchone()
        if x:
            role = {
                'role' : x[5]
            }
            return role, 200

    def post(self):
        data=request.get_json()
        fname=data.get('fname')
        lname=data.get('lname')
        email=data.get('email')
        username=data.get('username')
        password=data.get('password')
        role=data.get('role')
        conn=sqlite3.connect('maindb.db')
        x=conn.execute("SELECT * FROM users WHERE username=?",(username,)).fetchall()
        if len(x) == 0:
            conn.execute('INSERT INTO users (fname, lname, email, username, password, role) VALUES (?, ?, ?, ?, ?, ?)',
                         (fname, lname, email, username, password, role))
            conn.commit()
            
            return '',201
        else:
            
            return '',409
        
class section_api(Resource):

    def get(self):
        conn=sqlite3.connect('maindb.db')
        x=conn.execute('select * from sections').fetchall()
        return jsonify(x)
    
    def post(self,secname):
        conn=sqlite3.connect('maindb.db')
        x=conn.execute('SELECT * FROM sections where secname=?', (secname,)).fetchall()
        if (len(x)==0):
            conn.execute('INSERT INTO sections (secname) VALUES (?)', (secname,))
            conn.commit()
            conn.close()
            return '',201
        else:
            return '',409
        
    def delete(self, secname):
        conn=sqlite3.connect('maindb.db')
        conn.execute('DELETE FROM sections WHERE secname=?', (secname,))
        conn.commit()        
        conn.close()


class books_api(Resource):

    def get(self):
        conn=sqlite3.connect('maindb.db')
        x=conn.execute('select * from books').fetchall()
        return jsonify(x)
        
    def delete(self, isbn):
        conn=sqlite3.connect('maindb.db')
        conn.execute('DELETE from books where isbn=?', (isbn,))
        conn.commit()
        conn.close()
        return '',204
    
    def post(self):
        data=request.get_json()
        isbn=data.get('isbn')
        bname=data.get('bname')
        author=data.get('author')
        content=data.get('content')
        section=data.get('secname')
        conn=sqlite3.connect('maindb.db')
        x=conn.execute('SELECT * FROM books where bname=? or isbn=?', (bname,isbn,)).fetchall()
        if (len(x)==0):
            conn.execute('INSERT INTO books (isbn, bname, author, content, secname) VALUES (?,?,?,?,?)', (isbn,bname, author, content, section))
            conn.commit()
            conn.close()
            return '',201
        else:
            return '',409

    def put(self):
        data=request.get_json()
        isbn=data.get('isbn')
        conn=sqlite3.connect('maindb.db')
        prev=conn.execute('SELECT bname from books where isbn=?', (isbn,)).fetchone()
        bname=data.get('bname')
        author=data.get('author')
        content=data.get('content')
        section=data.get('section')
        if(bname not in prev):
            x=conn.execute('SELECT * FROM books where bname=?', (bname,)).fetchall()
        else:
            x=[]
        if (len(x)==0):
            conn.execute('UPDATE books SET bname=?, author=?, content=?, secname=? where isbn=?', (bname,author,content,section, isbn,))
            conn.commit()
            conn.close()
            return '',201
        else:
            return '',409

class graphs_api(Resource):
    def post(self):
        conn=sqlite3.connect('maindb.db')
        data=conn.execute('select secname, COUNT(*) from books group by secname').fetchall()
        x=[]
        y=[]
        for sets in data:
            x.append(sets[0])
            y.append(sets[1])
        plt.bar(x,y, color='green')
        plt.title("Books Under Section")
        plt.savefig(os.path.join('static', 'secgraph.png'))
        plt.close()

        ax=conn.execute("select b.bname, count(*) from books b join issuedata i on b.isbn=i.isbn group by b.bname").fetchall()
        x1=[]
        y1=[]
        for book in ax:
            x1.append(book[0])
            y1.append(book[1])
        plt.bar(x1,y1, color='green')
        plt.title("No. Of Issues Per Book")
        plt.savefig(os.path.join('static', 'issuegraph.png'))
        plt.close()

        ax=conn.execute("select b.secname, count(*) from books b join issuedata i on b.isbn=i.isbn group by b.secname").fetchall()
        x1=[]
        y1=[]
        for book in ax:
            x1.append(book[0])
            y1.append(book[1])
        plt.bar(x1,y1, color='green')
        plt.title("No. Of Issues Per Section")
        plt.savefig(os.path.join('static', 'secissuegraph.png'))
        plt.close()

class req_api(Resource):
    
    def get(self):
        conn=sqlite3.connect('maindb.db')
        x=conn.execute('select i.isbn, b.bname, b.author, i.username, i.duration from issuerequest i inner join books b on i.isbn=b.isbn where i.status="Pending"').fetchall()
        return jsonify(x)
    
    def put(self,isbn,user):
        conn=sqlite3.connect('maindb.db')
        conn.execute('UPDATE issuerequest SET status = "Approved" WHERE isbn=? AND username=?',(isbn,user))
        conn.commit()
        conn.close()

class pdf_api(Resource):
    def post(self,isbn):
        conn = sqlite3.connect('maindb.db')
        data = conn.execute('select content from books where isbn=?', (isbn,)).fetchone()     
        content = data[0]
        content = content.encode('ascii', 'ignore').decode('ascii')
        pdf = fpdf.FPDF(format='letter')
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt = content)
        pdf.output("static/content.pdf")
        conn.close()
