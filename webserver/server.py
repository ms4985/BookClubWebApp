#!/usr/bin/env python2.7

# assume user will only input locations/books that we have?
# assume 1 club per zipcode

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.

eugene wu 2015
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, Session, flash, request, render_template, g, redirect, Response
import string

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
session = {}
session['logged_in'] = False
session['admin'] = False

#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111db1.cloudapp.net:5432/proj1part2
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@w4111db1.cloudapp.net:5432/proj1part2"
#
#DATABASEURI = "sqlite:///test.db"
DATABASEURI = "postgresql://crf2133:279@w4111db1.cloudapp.net:5432/proj1part2"

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)



@app.route("/hello/", methods=["POST", "GET"])
def function():

	return "hello"
 


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a POST or GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
# 
@app.route('/', methods=["POST", "GET"])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  #print request.args

  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  admin = []

  if session['logged_in'] == False:
	return render_template("start.html")
  elif ((session['admin'] == True) & (session['admin'] == True)):
	admin.append("True")
	context = dict(data = admin)
	return render_template("index.html", **context)
  else:
	admin.append("False")
	context = dict(data = admin)
	return render_template("index.html", **context)

def check_auth(first, last):

  flag = False	
  cursor = g.conn.execute("SELECT name FROM users")
  names = []
  for result in cursor:
    names.append(result['name']) 
  cursor.close()

  for name in names:
    name = name.split()
    if first == name[0]:
	if last == name[1]:
	  flag = True

  return flag

@app.route("/login", methods=["GET", "POST"])
def login():
  first = request.form["first"]
  last = request.form["last"]

  if request.method == "POST":
    if first == 'admin':
	session['admin'] = True
	flash("you were logged in as admin")
	return render_template("index.html")
    elif check_auth(first, last) == True:
	session["logged_in"] = True
	flash("you were logged in")
	return render_template("index.html")
    else:
	flash("Invalid Login")
  return render_template("start.html")

@app.route("/logout")
def logout():
  session["logged_in"] == False
  session['admin'] == False
  flash("you were logged out")
  return render_template("start.html")

@app.route("/clubs/", methods=["POST", "GET"])
def showClubs():

  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM clubs")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()


  context = dict( data = names )
  return render_template("clubs/index.html", **context)

@app.route("/books/", methods=["POST", "GET"])
def showBooks():

  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT title FROM books")
  names = []
  for result in cursor:
    names.append(result['title'])  # can also be accessed using result[0]
  cursor.close()


  context = dict( data = names )
  return render_template("books/index.html", **context)


@app.route("/users/", methods=["POST", "GET"])
def showUsers():

  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM users")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()


  context = dict( data = names )
  return render_template("users/index.html", **context)


@app.route("/users/add/", methods=["POST"])
def addUsersPost():
  cursor = g.conn.execute("SELECT * FROM users")
  uid = cursor.rowcount+1
  name = request.form["name"]
  bday = request.form["birthday"]
  zipcode = int(request.form["zipcode"])
  cursor = g.conn.execute("SELECT lid FROM locations WHERE zip=%d" % (zipcode))
  loc = cursor.fetchone()
  if loc:
    loc = int(loc[0])
  else:
    print "location not found"
    return render_template("locations/add/index.html")
  
  cursor = g.conn.execute("SELECT cid FROM clubs WHERE location=%d" %(loc))
  club = cursor.fetchone()

  if club:
    club = int(club[0])
  else:
    print "no clubs in that zipcode"
    return render_template("clubs/add/index.html")
  
  gen = request.form["genre"]
  fav = request.form["favorite"]
  cursor = g.conn.execute("SELECT bid FROM books WHERE title='%s'" %(fav))
  bid = cursor.fetchone()

  if bid:
    bid = int(bid[0])
  else:
    print "no books matching that name"
    return render_template("books/add/index.html")
  
  cursor = g.conn.execute("INSERT INTO users(uid, name, birthday, location, genre, favorite, club) VALUES(%d,'%s','%s',%d,'%s',%d,%d)" %(uid,name,bday,loc,gen,bid,club)) 
  
  cursor.close()
  return render_template("users/add/index.html")

@app.route("/users/add/", methods=["GET"])
def addUsers():

  return render_template("users/add/index.html")

@app.route("/books/add/", methods=["POST"])
def addBooksPost():
  cursor = g.conn.execute("SELECT * FROM books")
  bid = cursor.rowcount + 1
  cursor.close()
  
  title = request.form["title"]
  author = request.form["author"]
  genre = request.form["genre"]
  isbn = request.form["isbn"]
  cursor = g.conn.execute("INSERT INTO books VALUES('%s','%s','%s',%d,'%s')" %(title,author,genre,bid,isbn)) 
  # go to new user page after adding a book
  return render_template("users/add/index.html")

@app.route("/books/add/", methods=["GET"])
def addBooks():

  return render_template("books/add/index.html")

@app.route("/clubs/add/", methods=["POST"])
def addClubsPost():
  cursor = g.conn.execute("SELECT * FROM clubs")
  cid = cursor.rowcount+1
  
  name = request.form["name"]
  zipcode = int(request.form["zipcode"])
  cursor = g.conn.execute("SELECT lid FROM locations WHERE zip=%d" % (zipcode))
  loc = cursor.fetchone()
  if loc:
    loc = int(loc[0])
  else:
    print "location not found"
    return render_template("locations/add/index.html")
  meeting_day = request.form["meeting_day"]
  meeting_time = request.form["meeting_time"]
  cursor = g.conn.execute("INSERT INTO clubs VALUES(%d,'%s',%d,'%s','%s')" %(cid,name,loc,meeting_day,meeting_time)) 
  # go to new user page after creating a club
  return render_template("users/add/index.html")

@app.route("/clubs/add/", methods=["GET"])
def addClubs():

  return render_template("clubs/add/index.html")


@app.route("/clubs/info", methods=["GET"])
def clubSearch():

  return render_template("clubs/info/index.html")


# get all members of a club
@app.route("/clubs/info/club_members", methods=["POST"])
def clubMembers():
  name = request.form["name1"]
  cursor = g.conn.execute("SELECT cid FROM clubs WHERE name='%s'" % (name))
  cid = cursor.fetchone()
  if cid:
    cid = int(cid[0])
  else:
    print "club not found"
    return render_template("clubs/info/index.html")
  
  cursor = g.conn.execute("SELECT name FROM users WHERE club=%d" %(cid))
  names = []
  for result in cursor:
    names.append(result['name'])
  cursor.close()

  heading = "Club members of " + name
  context = dict( data = names, title = heading )
  return render_template("clubs/info/list.html", **context)



# get all speakers of a genre
@app.route("/clubs/info/speakers_list", methods=["POST"])
def speakerList():
  genre = request.form["genre2"]
  cursor = g.conn.execute("SELECT name FROM speakers WHERE genre='%s'" %(genre))
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  heading = "Speakers for "+genre
  context = dict( data = names, title = heading )
  return render_template("clubs/info/list.html", **context)



# get unread books of a genre
@app.route("/clubs/info/new_books", methods=["POST"])
def newBooks():
  club = request.form["name3"]
  genre = request.form["genre3"]
  cursor = g.conn.execute("SELECT cid FROM clubs WHERE name='%s'" %(club))
  cid = cursor.fetchone()
  if cid:
    cid = int(cid[0])
  else:
    print "club not found"
    return render_template("clubs/info/index.html")
  
  cursor = g.conn.execute("SELECT title FROM books WHERE genre='%s' and bid NOT IN (SELECT book FROM discuss WHERE club=%d)" %(genre, cid))
  names = []
  for result in cursor:
    names.append(result['title'])  # can also be accessed using result[0]
  cursor.close()


  heading = "Recommended "+genre+" books for "+club
  context = dict( data = names, title = heading )
  return render_template("clubs/info/list.html", **context)



# add book/club pair to table and update users who read the book
@app.route("/clubs/info/read", methods=["POST"])
def read():
  club = request.form["name4"]
  title = request.form["title4"]
  cursor = g.conn.execute("SELECT cid FROM clubs WHERE name='%s'" %(club))
  cid = cursor.fetchone()
  if cid:
    cid = int(cid[0])
  else:
    print "club not found"
    return render_template("clubs/info/index.html")
  
  cursor = g.conn.execute("SELECT bid FROM books WHERE title='%s'" %(title))
  bid = cursor.fetchone()
  if bid:
    bid = int(bid[0])
  else:
    print "book not found"
    return render_template("clubs/info/index.html")

  cursor = g.conn.execute("SELECT * FROM discuss")
  did = cursor.rowcount+1
  
  # update discuss table
  cursor = g.conn.execute("INSERT INTO discuss VALUES(%d,%d,%d)" %(did,bid,cid))

  cursor = g.conn.execute("SELECT * FROM read")
  rid = cursor.rowcount+1

  cursor = g.conn.execute("SELECT uid, name FROM users WHERE club=%d" %(cid))
  names = []
  UIDs = []
  for result in cursor:
    UIDs.append(result['uid'])
    names.append(result['name'])

  # update read table
  for uid in UIDs:
    cursor = g.conn.execute("INSERT INTO read VALUES(%d,%d,%d)" %(rid,uid,bid))
    rid+=1

  cursor.close()


  heading = "Users from "+club+" who just read "+title
  context = dict( data = names, title = heading )
  return render_template("clubs/info/list.html", **context)


# list past speakers for a club
@app.route("/clubs/info/past_speakers", methods=["POST"])
def pastSpeakers():
  club = request.form["name5"]
  speaker = request.form["speaker5"]
  cursor = g.conn.execute("SELECT cid FROM clubs WHERE name='%s'" %(club))
  cid = cursor.fetchone()
  if cid:
    cid = int(cid[0])
  else:
    print "club not found"
    return render_template("clubs/info/index.html")
  
  cursor = g.conn.execute("SELECT sid FROM speakers WHERE name='%s'" %(speaker))
  sid = cursor.fetchone()
  if sid:
    sid = int(sid[0])
  else:
    print "speaker not found"
    return render_template("clubs/info/index.html")

  cursor = g.conn.execute("SELECT * FROM speak_at")
  spid = cursor.rowcount+1
  
  cursor = g.conn.execute("INSERT INTO speak_at VALUES(%d,%d,%d)" %(spid,sid,cid))

  cursor = g.conn.execute("SELECT name FROM speakers WHERE sid IN (SELECT speaker FROM speak_at WHERE club=%d)" %(cid))
   
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()


  heading = "Past speakers for "+club
  context = dict( data = names, title = heading )
  return render_template("clubs/info/index.html", **context)


# list users in club who read a certain book
@app.route("/clubs/info/read_by", methods=["POST"])
def readBy():
  club = request.form["name6"]
  title = request.form["title6"]
  cursor = g.conn.execute("SELECT cid FROM clubs WHERE name='%s'" %(club))
  cid = cursor.fetchone()
  if cid:
    cid = int(cid[0])
  else:
    print "club not found"
    return render_template("clubs/info/index.html")
  
  cursor = g.conn.execute("SELECT bid FROM books WHERE title='%s'" %(title))
  bid = cursor.fetchone()
  if bid:
    bid = int(bid[0])
  else:
    print "book not found"
    return render_template("clubs/info/index.html")

  # 
  cursor = g.conn.execute("SELECT name FROM users WHERE club=%d AND uid IN (SELECT usr FROM read WHERE book=%d)" %(cid,bid))
  

  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()


  heading = "Members of " + club+ " who have read "+title
  context = dict( data = names, title = heading )
  return render_template("clubs/info/list.html", **context)








@app.route("/speakers/add/", methods=["POST"])
def addSpeakersPost():
  cursor = g.conn.execute("SELECT * FROM speakers")
  sid = cursor.rowcount + 1
  cursor.close()
  
  name = request.form["name"]
  
  zipcode = int(request.form["zipcode"])
  cursor = g.conn.execute("SELECT lid FROM locations WHERE zip=%d" % (zipcode))
  loc = cursor.fetchone()
  if loc:
    loc = int(loc[0])
  else:
    print "location not found"
    return render_template("locations/add/index.html")
  
  genre = request.form["genre"]
  cursor = g.conn.execute("INSERT INTO speakers VALUES(%d,'%s',%d,'%s')" %(sid,name,loc,genre)) 
  return render_template("speakers/add/index.html")

@app.route("/speakers/add/", methods=["GET"])
def addSpeakers():

  return render_template("speakers/add/index.html")

@app.route("/locations/add/", methods=["POST"])
def addLocationsPost():
  cursor = g.conn.execute("SELECT * FROM locations")
  lid = cursor.rowcount + 1
  cursor.close()
  
  city = request.form["city"]
  state = request.form["state"]
  zipcode = int(request.form["zipcode"])
  country = request.form["country"]
  cursor = g.conn.execute("INSERT INTO locations VALUES(%d,'%s','%s',%d,'%s')" %(lid,city,state,zipcode,country)) 
  # go back to new club page after creating a new location
  return render_template("clubs/add/index.html")

@app.route("/locations/add/", methods=["GET"])
def addLocations():

  return render_template("locations/add/index.html")


@app.route("/speakers/", methods=["POST", "GET"])
def showSpeakers():

  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM speakers")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()


  context = dict( data = names )
  return render_template("speakers/index.html", **context)

@app.route("/locations/", methods=["POST", "GET"])
def showLocations():

  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT city FROM locations")
  names = []
  for result in cursor:
    names.append(result['city'])  # can also be accessed using result[0]
  cursor.close()


  context = dict( data = names )
  return render_template("locations/index.html", **context)





if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
