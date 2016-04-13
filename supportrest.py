#!/usr/bin/env python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

import pymssql
from os import getenv

server = getenv("SD_SERVER")
user = getenv("SD_USERNAME")
password = getenv("SD_PASSWORD")
db = getenv("SD_DB")

class DatabaseResource:
    def __enter__(self):
        class Database:
            def __init__(self):
                self.conn = pymssql.connect(server, user, password, db)
                self.cur = self.conn.cursor(as_dict=True)
            def close(self):
                self.conn.close()
            def get_event_notes(self, e):
                query = """
                SELECT * FROM super.F0006_SUPREPLY
                WHERE eventref LIKE '%%%u'
                """ % e
                self.cur.execute(query)

                notes = []

                row = self.cur.fetchone()
                while row:
                    note = {}
                    note['author'] = row['RESPONDENT']
                    note['content'] = row['REPLY']
                    notes.append(note)
                    row = self.cur.fetchone()
                return notes
                
            def get_event(self, e):
                query = """
                SELECT * FROM super.F0006_SUPEVENT
                WHERE reference LIKE '%%%u'
                """ % e
                self.cur.execute(query)
                row = self.cur.fetchone()

                # Stuff it all in a dictionary
                event = {}
                print row
                event['owner'] = row['HANDLERTAG']
                event['notes'] = self.get_event_notes(e)
                return event
        self.db = Database()
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()

    def get_event(self, event):
        return self.db.get_event(event)
        

#with DatabaseResource() as db:
#    print db.get_event(56310)
    
#cursor = conn.cursor()
#cursor.execute("""
#select * from sys.tables
#""")
##kselect * from SupportDesk.super.HIST_SUPEVENT
#
#tables = []
#row = cursor.fetchone()
#while row:
#	name = row[0]
#	if name.endswith("SUPEVENT"):
#		tables.append(name)
#	row = cursor.fetchone()
#total = 0
#max_id = 0
#tables = ["F0006_SUPEVENT"]
#for table in tables:
#
#	print "%s +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" % table
#	cursor.execute("""
#	select * from super.%s
#	ORDER BY reference ASC
#	""" % (table))
#	num = 0
#	row = cursor.fetchone()
#	while row:
#		max_id = max(max_id, row[0])
#		row = cursor.fetchone()
#		num += 1
#	total += num
#	print num
#
#print "Total records: %s" % total
#print "Max record ID: %s" % max_id
#
#	
#conn.close()

if __name__ == '__main__':
    app.run(debug=True)
