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
                                        
            def multi_row_fetch(self, query):
                self.cur.execute(query)
                return self.cur.fetchall()
                
            def single_row_query(self, query):
                self.cur.execute(query)
                return self.cur.fetchone()

        class SDDatabase(Database):
            def __init__(self):
                Database.__init__(self)
                            
            def make_event(self, e, row):
                event = {}
                event['id'] = e
                event['owner'] = row['HANDLERTAG']
                event['notes'] = self.get_event_notes(e)

            def get_event_notes(self, e):
                query = """
                SELECT * FROM super.F0006_SUPREPLY
                WHERE eventref LIKE '%%%u'
                """ % e
                rows = multi_row_fetch(query)
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
                WHERE respondent LIKE '%%%s'
                """ % user                
                rows = multi_row_fetch(query)
                            
            def get_event(self, e):
                query = """
                SELECT * FROM super.F0006_SUPEVENT
                WHERE reference LIKE '%%%u'
                """ % e
                row = single_row_query(query)
                                
                if row is None:
                    return None
                else:
                    # Stuff it all in a dictionary
                    event = self.make_event(row, e)
                    return event
                    
        self.db = SDDatabase()
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()

    def get_event(self, event):
        return self.db.get_event(event)
        
def get_url(suffix):
    return '/api/v%s/%s' % (API_VERSION, suffix)

app = Flask(__name__)

@app.route(get_url('event/<int:event_id>'), methods=['GET'])
def get_event(event_id):
    with DatabaseResource() as db:
        event = ds.get_event(event_id)
        if event is None:
            abort(404)
        else:
            return jsonify(event)
            
@app.route(get_url('user/assigned/<string:user_id>'), methods=['GET'])
def get_assigned_events(user_id):
    with DatabaseResource() as db:
        events = ds.get_assigned_events(user_id)
        if events is None:
            abort(404)
        else:
            return jsonify(events)

@app.route(get_url('user/created/<string:user_id>'), methods=['GET'])
def get_created_events(user_id):
    with DatabaseResource() as db:
        events = ds.get_created_events(user_id)
        if events is None:
            abort(404)
        else:
            return jsonify(events)


if __name__ == '__main__':
    app.run(debug=True)