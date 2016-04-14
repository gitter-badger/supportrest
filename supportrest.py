#!/usr/bin/env python
from flask import Flask, jsonify
import pymssql
from os import getenv

server = getenv("SD_SERVER")
user = getenv("SD_USERNAME")
password = getenv("SD_PASSWORD")
db = getenv("SD_DB")

API_VERSION = '0.1'

class DatabaseResource:
    def __enter__(self):
        class Database:
            def __init__(self):
                self.conn = pymssql.connect(server, user, password, db)
                self.cur = self.conn.cursor(as_dict=True)
                
            def close(self):
                self.conn.close()
                                        
            def multi_row_query(self, query):
                self.cur.execute(query)
                return self.cur.fetchall()
                
            def single_row_query(self, query):
                self.cur.execute(query)
                return self.cur.fetchone()

        class SDDatabase(Database):
            def __init__(self):
                Database.__init__(self)
                            
            def make_event(self, row):
                event = {}
                event_id = int(row['REFERENCE'])
                event['id'] = event_id
                event['owner'] = row['HANDLERTAG']
                event['subject'] = row['TITLE']
                event['notes'] = self.get_event_notes(event_id)
                return event

            def get_event_notes(self, e):
                query = """
                SELECT * FROM super.F0006_SUPREPLY
                WHERE eventref LIKE '%%%u'
                ORDER BY replyno
                """ % e
                rows = self.multi_row_query(query)
                notes = []
                for row in rows:
                    note = {}
                    note['author'] = row['RESPONDENT']
                    note['content'] = row['REPLY']
                    notes.append(note)
                return notes
                
            def get_assigned_events(self, user):
                query = """
                SELECT * FROM super.F0006_SUPEVENT
                WHERE handlertag LIKE '%%%s%%'
                """ % user                
                rows = self.multi_row_query(query)
                events = []
                for row in rows:
                    events.append(self.make_event(row)) 
                return {"events" : events}

            def get_event(self, e):
                query = """
                SELECT * FROM super.F0006_SUPEVENT
                WHERE reference LIKE '%%%u'
                """ % e
                row = self.single_row_query(query)
                                
                if row is None:
                    return None
                else:
                    # Stuff it all in a dictionary
                    event = self.make_event(row)
                    return event
                    
        self.db = SDDatabase()
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()

    def get_event(self, event):
        return self.db.get_event(event)

    def get_assigned_events(self, user):
        return self.db.get_assigned_events(user)

def get_url(suffix):
    return '/api/v%s/%s' % (API_VERSION, suffix)

app = Flask(__name__)

@app.route('/')
def root():
    return "SupportREST";

@app.route(get_url('event/<int:event_id>'), methods=['GET'])
def get_event(event_id):
    with DatabaseResource() as db:
        event = db.get_event(event_id)
        if event is None:
            abort(404)
        else:
            return jsonify(event)
            
@app.route(get_url('user/assigned/<string:user_id>'), methods=['GET'])
def get_assigned_events(user_id):
    with DatabaseResource() as db:
        events = db.get_assigned_events(user_id)
        if events is None:
            abort(404)
        else:
            return jsonify(events)

@app.route(get_url('user/created/<string:user_id>'), methods=['GET'])
def get_created_events(user_id):
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)
