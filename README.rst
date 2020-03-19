Coding Exercise - URL Lookup Service
====================================

Installation
------------

::

  git clone https://github.com/glennmatthews/webservice_exercise.git
  cd webservice_exercise/
  python3 -m venv django
  source django/bin/activate
  pip install -r requirements.txt
  python manage.py runserver

The server will run at ``127.0.0.1:8000``. Try the following queries:

- http://127.0.0.1:8000/urlinfo/1/allgood.here/ - returns ``{safe: true}``
- http://127.0.0.1:8000/urlinfo/1/malware.bad/ - returns ``{safe: false}``
- http://127.0.0.1:8000/urlinfo/1/mixed.bag:1234/- returns ``{safe: true}``
- http://127.0.0.1:8000/urlinfo/1/mixed.bag:666/- returns ``{safe: false}``
- http://127.0.0.1:8000/urlinfo/1/mixed.bag/totally/safe/path - returns ``{safe: true}``
- http://127.0.0.1:8000/urlinfo/1/mixed.bag/totally/unsafe/path - returns ``{safe: false}``
- http://127.0.0.1:8000/urlinfo/1/mixed.bag/files - returns ``{safe: true}``
- http://127.0.0.1:8000/urlinfo/1/mixed.bag/files?unsafe=true&malware=true - returns ``{safe: false}``

You can also run the included test suite with ``python manage.py test url_lookup -v 2``

Administration
--------------

You can administer the installation (managing database entries) by connecting
to http://127.0.0.1:8000/admin/ as ``admin`` / ``superadmin``.
Obviously this is a toy DB and so we don't particularly care about security
for purposes of the demo - in a real deployment we would need to follow various
Django best practices to make things more secure.

Design and Implementation
-------------------------

As per the requirements given for this exercise, the API takes a simple URL pattern:

``GET /urlinfo/1/{hostname_and_port}/{original_path_and_query_string}``

Although not clearly stated in the requirements, I do allow the
``original_path_and_query_string`` to be empty, and the port can be omitted
as well (defaulting to port 80 if unspecified).

As this is v1 of the API and the goal is explicitly stated to be "start[ing]
with very simple implementations and progressively make them more capable,
scalable, and reliable", I currently have the API only return JSON with a
single key ``safe`` which can either be ``true`` or ``false``. In the future
we can easily add additional fields to the JSON, such as indicating which
database(s) (in the case of multiple malware databases) flagged as malware,
or how precise the flagging is (domain-level versus file-level).

The database is designed around the idea that in many cases we will simply have
domain-level blacklists (a given hostname is flagged as unsafe regardless of
the specific port, path, and query string) while in some cases we will need to
be more discriminating, either disallowing specific ports on a domain (say,
a rogue secondary webserver instance that's distributing malware while the
primary webserver is uncompromised) or even specific paths or queries on a
domain (say, a single file that's known to be malware). The hope is that by
creating a hierarchy of tables (Domain -> Port -> Path -> Query) we can scale
more efficiently than a single flat database would allow, though this would
need to be tested at scale to confirm this assumption.

Future Considerations
---------------------

- Database scalability - currently this is using a simple SQLite database
  on localhost. Django makes it relatively straightforward to swap in a
  different tech such as MySQL or PostgreSQL for better scalability, and it's
  also possible to host the database on a separate filesystem or a separate
  host altogether if needed for even greater scale.
- Service scalability - if needed, it should be feasible to run multiple
  Django instances on separate hosts or containers behind a load-balancer.
- Database updates - currently this is done manually either through the
  admin web service or through ``python manage.py shell``, but we need
  a way to push bulk updates on a regular schedule. I'll try and tackle this.
- Containerization - shouldn't be too difficult to implement.
