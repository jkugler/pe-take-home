"""
Please note that this app does *not* demonstrate Flask best practice!

It is much better to place views, controllers, configuration
files, and the like in their own directories.
"""

import json
import os
import sqlite3

from flask import Flask, render_template, request, send_from_directory
from flask_api import FlaskAPI, status, exceptions

from werkzeug.exceptions import NotFound
from werkzeug.middleware.proxy_fix import ProxyFix

app = FlaskAPI(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

class IncidentDAO:
    def __init__(self, db_path='db/incident.db'):
        os.makedirs('db/', exist_ok=True)
        db_exists = os.path.exists(db_path)
        # Yup...this will be local, and only to this container
        # See notes in README
        self.conn =  sqlite3.connect(db_path)
        if not db_exists:
            cur = self.conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS "incidents" (
            "id" TEXT NOT NULL,
            "address" TEXT NOT NULL,
            "latitude" TEXT NOT NULL,
            "longitude" TEXT NOT NULL,
            "comment"  TEXT NOT NULL,
            "event_opened" TEXT NOT NULL,
            "event_closed" TEXT NOT NULL,
            "data" TEXT NOT NULL,
            PRIMARY KEY("id")
            )
            """
            cur.execute(sql)
            self.conn.commit()

    def _extract_data(self, data):
        # This should do a full schema validation, but a schema was not provided
        try:
            inc_id = data['description']['incident_number']
            address = data['address']['address_line1']
            latitude = data['address']['latitude']
            longitude = data['address']['longitude']
            comment = data['description']['comments']
            event_opened = data['description']['event_opened']
            event_closed = data['description']['event_opened']
        except KeyError as err:
            raise ValueError(f'Invalid data structure. Missing key {err.args[0]}')

        return [inc_id, address, latitude, longitude, comment, event_opened, event_closed,
                json.dumps(data)]

    def get(self, inc_id):
        cur = self.conn.cursor()
        cur.execute('SELECT *  FROM incidents WHERE id=?', (inc_id,))
        row = cur.fetchone()
        cur.description
        if row is not None:
            return dict(zip([d[0] for d in cur.description], row))

        raise NotFound(f'No incident with given id: {inc_id}')

    def incedents(self):
        """Get *all* the incidents"""
        cur = self.conn.cursor()

        cur.execute('SELECT * FROM incidents')

        all_incedents = []

        for row in cur:
            all_incedents.append(dict(zip([d[0] for d in cur.description], row)))

        return all_incedents

    def create(self, data):
        cur = self.conn.cursor()
        fields = self._extract_data(data)

        try:
            cur.execute('INSERT INTO incidents VALUES (?, ?, ?, ?, ?, ?, ?, ?)', fields)
        except sqlite3.IntegrityError as err:
            if 'UNIQUE constraint failed: incidents.id' in err.args[0]:
                raise RuntimeError(f"Incident with given number already exists: '{fields[0]}'")
        self.conn.commit()

        return self.get(fields[0])

    def update(self, inc_id, data):
        # Check we have an incident with that ID already
        self.get(inc_id)
        fields = self._extract_data(data)


        if inc_id != fields[0]:
            raise ValueError(f'Given incident ID {inc_id}, but data contains incident id {fields[0]}')

        cur = self.conn.cursor()
        cur.execute('UPDATE incidents SET id = ?, address = ?, latitude = ?, longitude = ?, '
                    'comment = ?, event_opened = ?, event_closed = ?, data = ?', fields)
        self.conn.commit()

        return self.get(fields[0])

    def delete(self, inc_id):
        # Check we have an incident with that ID already
        self.get(inc_id)

        cur = self.conn.cursor()
        cur.execute('DELETE FROM incidents WHERE id = ?', (inc_id,))

        self.conn.commit()

# These are static routes, not part of the API
@app.route('/favicon.ico')
def favicon(): # pragma: nocover
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home(): # pragma: nocover
    return render_template("whale_hello.html")

@app.route('/env')
def env(): # pragma: nocover
    return '<pre>\n' + json.dumps(dict(os.environ), indent=4) + '\n</pre>\n'
# End static routs

@app.route("/api/", methods=['GET', 'POST'])
def incidents():
    #NOT best practice. :)
    incedent_dao = IncidentDAO()
    if request.method == 'POST':
        try:
            return incedent_dao.create(request.data), status.HTTP_201_CREATED
        except RuntimeError as err:
            return err.args[0], status.HTTP_400_BAD_REQUEST
    elif request.method == 'GET':
        return incedent_dao.incedents()

@app.route("/api/<inc_id>", methods=['GET', 'PUT', 'DELETE'])
def incident_detail(inc_id):
    #NOT best practice. :)
    incedent_dao = IncidentDAO()
    """Retreive, update, or delete an incident"""
    if request.method == 'PUT':
        try:
            return incedent_dao.update(inc_id, request.data)
        except NotFound:
            return '', status.HTTP_404_NOT_FOUND
        except ValueError as err:
            return err.args[0], status.HTTP_400_BAD_REQUEST
    elif request.method == 'DELETE':
        try:
            incedent_dao.delete(inc_id)
        except NotFound:
            return '', status.HTTP_404_NOT_FOUND
        return '', status.HTTP_204_NO_CONTENT
    elif request.method == 'GET':
        try:
            return incedent_dao.get(inc_id)
        except NotFound:
            return '', status.HTTP_404_NOT_FOUND

if __name__ == '__main__': # pragma: nocover
    app.run(host='0.0.0.0', port=8080)
