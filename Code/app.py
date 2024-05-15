from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
from flask_restful import Api
from api import user_api,section_api, books_api, req_api, graphs_api, pdf_api
import requests as rq
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

api = Api(app)
api.add_resource(user_api, '/api/user')
api.add_resource(section_api, '/api/section', '/api/section/<string:secname>')
api.add_resource(books_api, '/api/books', '/api/books/<int:isbn>')
api.add_resource(req_api, '/api/request', '/api/request/<string:user>/<int:isbn>')
api.add_resource(graphs_api, '/api/graph')
api.add_resource(pdf_api, '/api/pdf/<int:isbn>')

def getdb():
    conn=sqlite3.connect('maindb.db')
    return conn

@app.route('/')
def index():
    return render_template('login.html')

#REGISTRATION LOGIC
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method=='POST':
        form_data = {
        'fname': request.form['fname'],
        'lname': request.form['lname'],
        'email': request.form['email'],
        'username': request.form['username'],
        'password': request.form['password'],
        'role': request.form['role']
        }
        if rq.post(url=request.url_root+'/api/user', json=form_data).status_code == 201:
            return redirect(url_for('login'))
        else:
            error_message = "Username already exists. Please choose a different username."
            return render_template('register.html', error_message=error_message)
    return render_template('register.html')

#LOGIN LOGIC
@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        login={
            'username': request.form['username'],
            'password': request.form['password'],    
        }
        res=rq.get(request.url_root+'api/user', json=login)
        if res.status_code==200:
            session['username']=login['username']
            role_json = res.json()
            if role_json:
                role=role_json.get('role')
                if role=='admin':
                    return redirect(url_for('admindash'))
                else:
                    return redirect(url_for('userdash'))
            else:
                return render_template('login.html', err="Wrong Username Or Password")
        else:
            return render_template('login.html', err="Wrong Username Or Password")
    return render_template('login.html')

#LANDING PAGE FOR LIBRARIAN LOGIN
@app.route('/admindash', methods=['POST', 'GET'])
def admindash():
    rq.post(request.url_root+'api/graph')
    secresp=rq.get(request.url_root+'/api/section').json()
    books=rq.get(request.url_root+'/api/books').json()
    reqs=rq.get(request.url_root+'/api/request').json()
    return  render_template('admindash.html', sec=secresp, books=books, reqs=reqs)

#LOGIC TO ADD NEW SECTION IN ADMIN DASHBOARD
@app.route('/admindash/newsection', methods=['POST','GET'])
def admindash_newsection():
    if request.method == 'POST':
        secname = request.form['secname']
        send=rq.post(url=request.url_root+'/api/section/'+secname)
        if send.status_code == 201:
            return redirect(url_for('admindash'))
        else:
            return render_template('newsection.html', err="Section already exists")
    return render_template('newsection.html')

@app.route('/admindash/<string:secname>/deletesection', methods=['GET'])
def deletesection(secname):
    rq.delete(url=request.url_root+'/api/section/'+secname)
    return redirect(url_for('admindash'))


#LOGIC TO APPROVE REQUEST IN ADMIN DASHBOARD
@app.route('/admindash/approverequest/<string:user>/<int:isbn>', methods=['POST','GET'])
def approverequest(user,isbn):
    rq.put(url=request.url_root+'/api/request/'+user+'/'+str(isbn))
    conn=getdb()
    cursor = conn.execute('SELECT duration FROM issuerequest WHERE isbn=? AND username=? AND status="Approved"', (isbn, user))
    duration_row = cursor.fetchone()
    if duration_row:
        duration = duration_row[0] 
    currdate = datetime.now().date()
    issuedate = currdate
    returndate = currdate + timedelta(days=duration)
    conn.execute('INSERT INTO issuedata (isbn, issue_date, return_date, username) VALUES (?, ?, ?, ?)', (isbn, issuedate, returndate, user))
    conn.commit()
    return redirect(url_for('admindash'))

#LOGIC TO REJECT REQUEST IN ADMIN DASHBOARD
@app.route('/admindash/rejectrequest/<string:user>/<int:isbn>', methods=['POST','GET'])
def rejectrequest(user,isbn):
    conn=getdb()
    conn.execute('UPDATE issuerequest SET status = "Rejected" WHERE isbn=? AND username=?',(isbn,user))
    conn.commit()
    return redirect(url_for('admindash'))

#LOGIC TO REVOKE ACCESS OF A BOOK FOR USER IN ADMIN DASHBOARD
@app.route('/admindash/revoke/<string:user>/<int:isbn>', methods=['POST', 'GET'])
def revokeaccess(user,isbn):
    conn=getdb()
    conn.execute('delete from issuedata WHERE isbn=? AND username=?',(isbn,user))
    conn.commit()
    conn.execute('update issuerequest SET status="Revoked" where isbn=? AND username=?',(isbn,user))
    conn.commit()
    return redirect(url_for('admindash'))

#LOGIC TO ADD NEW BOOK VIA ADMIN DASHBOARD
@app.route('/admindash/newbook', methods=['POST','GET'])
def admindash_newbook():
    conn = getdb()
    sec=conn.execute('SELECT * FROM sections').fetchall()
    if request.method == 'POST':
        data={
            'isbn': request.form['isbn'],
            'bname': request.form['bname'],
            'author': request.form['author'],
            'content': request.form['content'],
            'secname': request.form['secval'],
        }

        x=rq.post(url=request.url_root+'api/books', json=data)
        
        if x.status_code==201:
            return redirect(url_for('admindash'))
        elif x.status_code==409:
            error="ISBN/BOOK already exists"
            return render_template('newbook.html', sec=sec, error=error)
    return render_template('newbook.html', sec=sec)

#VIEW ALL ISSUE DETAILS FOR A BOOK
@app.route('/admindash/<int:isbn>/issuedetails', methods=['POST', 'GET'])
def issuedetails(isbn):
    conn=getdb()
    bookname=conn.execute('SELECT distinct bname from books where isbn=?', (isbn,)).fetchone()
    books=conn.execute("SELECT * FROM issuedata where isbn=? and return_date>DATE('now')",(isbn,)).fetchall()
    return render_template('allissues.html', bookname=bookname, books=books, isbn=isbn)

@app.route('/admindash/<int:isbn>/editbook', methods=['GET', 'POST'])
def editbook(isbn):
    conn=getdb()
    data=conn.execute('SELECT * FROM books where isbn=?', (isbn,)).fetchone()
    sec=conn.execute('SELECT * FROM sections').fetchall()
    if request.method == 'POST':
        data={
        'isbn':request.form['isbn'],
        'bname': request.form['bname'],
        'author':request.form['author'],
        'content':request.form['content'],
        'section':request.form['secval'],
        }
        x=rq.put(url=request.url_root+'/api/books', json=data)
        if x.status_code==201:
            return redirect(url_for('admindash'))
        elif x.status_code==409:
            data=conn.execute('SELECT * FROM books where isbn=?', (isbn,)).fetchone()
            sec=conn.execute('SELECT * FROM sections').fetchall()
            return render_template('editbook.html', data=data, sec=sec, error="Book Name Already Exists")
    return render_template('editbook.html', data=data, sec=sec)

#DELETE BOOK
@app.route('/admindash/<int:isbn>/deletebook', methods=['POST', 'GET'])
def deletebook(isbn):
    x=rq.delete(url=request.url_root+'api/books/'+str(isbn))
    if x.status_code==204:
        return redirect(url_for('admindash'))

#Let Admin Read Book Content
@app.route('/admindash/readbook/<int:isbn>', methods=['POST', 'GET'])
def adminreadbook(isbn):
    conn=getdb()
    content=conn.execute('SELECT content, bname, author from books where isbn=?', (isbn,)).fetchall()
    return render_template('readbookadmin.html', content=content, isbn=isbn)



#LANDING PAGE FOR USER 
@app.route('/userdash', methods=['POST', 'GET'])
def userdash():
    conn = getdb()
    sec=rq.get(request.url_root+'/api/section').json()
    books=conn.execute("SELECT b.*, CASE WHEN i.username IS NULL THEN 'None' ELSE i.status END AS status, avgrating.avgrating FROM books b LEFT JOIN issuerequest i ON b.isbn = i.isbn AND i.username = ? LEFT JOIN (SELECT isbn, AVG(rating) AS avgrating FROM feedback GROUP BY isbn) AS avgrating ON b.ISBN = avgrating.ISBN order by avgrating desc", (session['username'],)).fetchall()
    currdate = datetime.now().date()
    conn.execute('UPDATE issuerequest SET status = "Expired" WHERE EXISTS (SELECT 1 FROM issuedata WHERE issuedata.isbn = issuerequest.isbn AND issuedata.return_date < ?)', (currdate,))
    
    x=conn.execute('select count(*) from issuerequest i where (i.status="Approved" or i.status="Pending") and username=?', (session['username'],)).fetchone()
    if((int(x[0])+1)>=5):
        lim="Borrow Limit Exceeded"
        return  render_template('userdash.html', sec=sec, books=books, lim=lim)
    return  render_template('userdash.html', sec=sec, books=books)

@app.route('/userdash/userprofile', methods=['POST', 'GET'])
def userprofile():
    conn = getdb()
    reqs = conn.execute('SELECT i.isbn, b.bname, b.author, i.status FROM issuerequest i INNER JOIN books b ON i.isbn = b.isbn WHERE i.username = ?', (session['username'],)).fetchall()
    currdate = datetime.now().date()
    appbooks = conn.execute('SELECT i.isbn, b.bname, b.author, b.content, i.return_date, b.secname FROM issuedata i INNER JOIN books b ON i.isbn = b.isbn WHERE i.username=? AND i.return_date >= ?', (session['username'], currdate)).fetchall()
    countappr=[]
    for i in range(1, len(appbooks)+1):
        countappr.append(i)
    appbooks = zip(countappr, appbooks)
    userdetails=conn.execute('SELECT fname,lname FROM users where username=?', (session['username'],)).fetchall()
    return render_template('profile.html', appbooks=appbooks, reqs=reqs, userdetails=userdetails)

@app.route('/userdash/readbook/<int:isbn>', methods=['POST', 'GET'])
def readbook(isbn):
    conn=getdb()
    content=conn.execute('SELECT content, bname, author from books where isbn=?', (isbn,)).fetchall()
    return render_template('readbook.html', content=content, isbn=isbn)

@app.route('/userdash/returnbook/<int:isbn>', methods=['POST', 'GET'])
def returnbook(isbn):
    conn=getdb()
    conn.execute('update issuerequest set status="Returned" where isbn=? and username=?',(isbn, session['username'],))
    conn.commit()
    conn.execute('delete from issuedata where isbn=? and username=?',(isbn, session['username'],))
    conn.commit()
    return redirect(url_for('userprofile'))

@app.route('/userdash/sections/<string:section>', methods=['POST', 'GET'])
def sections(section):
    conn=getdb()
    books=conn.execute('select distinct b.*,i.status  from books b left join issuerequest i  on b.isbn=i.isbn and i.username=? where b.secname=?',(session['username'], section)).fetchall()
    x=conn.execute('select count(*) from issuerequest i where (i.status="Approved" or i.status="Pending") and username=?', (session['username'],)).fetchone()
    if((int(x[0])+1)>=5):
        lim="Borrow Limit Exceeded"
        return  render_template('section.html', section=section, books=books, lim=lim)
    return  render_template('section.html', section=section, books=books)

@app.route('/adminsections/<string:section>', methods=['POST', 'GET'])
def adminsections(section):
    conn=getdb()
    books=conn.execute('select distinct b.*  from books b where b.secname=?',(section,)).fetchall()
    return  render_template('adminsection.html', section=section, books=books)

@app.route('/userdash/requestbook/<int:isbn>', methods=['POST','GET'])
def requestbook(isbn):
    if request.method == 'POST':
        days=request.form['days']
        conn=getdb()
        test=conn.execute("select * from issuerequest where isbn=? and username=?",(isbn,session['username'],)).fetchall()
        if len(test)!=0:
            conn.execute('update issuerequest set status="Pending", duration=? where isbn=? and username=?',(days,isbn,session['username'],))
            conn.commit()
        else:
            conn.execute("INSERT INTO issuerequest(isbn, username, duration, status) VALUES (?,?,?,?)",(isbn, session['username'], days, 'Pending'))
            conn.commit()
            conn.close()
        return redirect(url_for('userdash'))
    return render_template('requestbook.html', isbn=isbn)

@app.route('/userdash/reviewbook/<int:isbn>', methods=['POST', 'GET'])
def reviewbook(isbn):
    if request.method == 'POST':
        rating=request.form['rating']
        review=request.form['review']
        conn=getdb()
        conn.execute("INSERT INTO feedback(isbn,username,rating,feedback) VALUES (?,?,?,?)", (isbn,session['username'],rating,review))
        conn.commit()
        return redirect(url_for('userprofile'))
    return render_template('review.html', isbn=isbn, username=session['username'])

@app.route('/userdash/searchsection', methods=['POST', 'GET'])
def searchsec():
    if request.method=='POST':
        secname=request.form['sec_search']
        conn=getdb()
        srch='%'+secname+'%'
        x=conn.execute("SELECT secname FROM sections WHERE secname like ?", (srch,)).fetchall()
        return render_template('sectionsearch.html', sec=x)
    
@app.route('/userdash/searchbook', methods=['POST', 'GET'])
def searchbook():
    if request.method=='POST':
        secname=request.form['sec_search']
        filval=request.form['filter']
        srch='%'+secname+'%'
        conn=getdb()
        if filval=='bname':
            books=conn.execute("SELECT b.*, CASE WHEN i.username IS NULL THEN 'None' ELSE i.status END AS status, avgrating.avgrating FROM books b LEFT JOIN issuerequest i ON b.isbn = i.isbn AND i.username = ? LEFT JOIN (SELECT isbn, AVG(rating) AS avgrating FROM feedback GROUP BY isbn) AS avgrating ON b.ISBN = avgrating.ISBN where b.bname like ? order by avgrating desc", (session['username'],srch,)).fetchall()
            return render_template('booksearch.html', books=books)
        else:
            books=conn.execute("SELECT b.*, CASE WHEN i.username IS NULL THEN 'None' ELSE i.status END AS status, avgrating.avgrating FROM books b LEFT JOIN issuerequest i ON b.isbn = i.isbn AND i.username = ? LEFT JOIN (SELECT isbn, AVG(rating) AS avgrating FROM feedback GROUP BY isbn) AS avgrating ON b.ISBN = avgrating.ISBN where b.author like ? order by avgrating desc", (session['username'],srch,)).fetchall()
            return render_template('booksearch.html', books=books)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()  
    return redirect(url_for('login'))  

@app.route('/buypdf/<int:isbn>', methods=['POST', 'GET'])
def buypdf(isbn):
    if request.method=='POST':
        rq.post(request.url_root+'api/pdf/'+str(isbn))
        return redirect(url_for('static', filename='content.pdf'))
    return render_template('buypdf.html', isbn=isbn, username=session['username'])

if __name__ == '__main__':
    app.run(debug=True)