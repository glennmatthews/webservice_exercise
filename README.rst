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

The server will run at ``127.0.0.1:8000``.

The provided database (``db.sqlite3``) includes examples of:
- blacklisting by domain name
- whitelisting a subdomain of an otherwise blacklisted domain
- blacklisting and whitelisting specific ports on a given domain
- blacklisting and whitelisting specific paths on a given domain/port
- blacklisting specific HTTP GET query parameters on a given domain/port/path

Try the following queries to demonstrate this functionality:

- http://127.0.0.1:8000/urlinfo/1/example.com/ - returns ``{safe: true}``
  because there's no database entry for example.com
- http://127.0.0.1:8000/urlinfo/1/allgood.here/ - returns ``{safe: true}``
  because there's a database entry for allgood.here but it's whitelisted (not flagged as unsafe)
- http://127.0.0.1:8000/urlinfo/1/malware.bad/ - returns ``{safe: false}``
  because there's a blacklist database entry for malware.bad.
  Similarly:

    - http://127.0.0.1:8000/urlinfo/1/malware.bad:443 also returns ``{safe: false}``
      because the entire domain is blacklisted, regardless of port number.
    - http://127.0.0.1:8000/urlinfo/1/malware.bad/some/path/here also returns ``{safe: false}``
      because the entire domain is blacklisted, regardless of directory path.

- http://127.0.0.1:8000/urlinfo/1/all.malware.bad/ - returns ``{safe: false}``
  because there's a blacklist database entry for its parent domain malware.bad
- http://127.0.0.1:8000/urlinfo/1/not.all.malware.bad/ - returns ``{safe: true}``
  because there's a whitelist database entry for this specific subdomain
- http://127.0.0.1:8000/urlinfo/1/mixed.bag:1234/- returns ``{safe: true}``
  because there's a whitelist database entry for this specific port on this domain
- http://127.0.0.1:8000/urlinfo/1/mixed.bag:666/- returns ``{safe: false}``
  because there's a blacklist database entry for this specific port on this domain
- http://127.0.0.1:8000/urlinfo/1/mixed.bag/totally/safe/path - returns ``{safe: true}``
  because there's a whitelist database entry for this path on this domain (and implied port 80)
- http://127.0.0.1:8000/urlinfo/1/mixed.bag/totally/unsafe/path - returns ``{safe: false}``
  because there's a blacklist database entry for this path on this domain (and implied port 80)
- http://127.0.0.1:8000/urlinfo/1/mixed.bag/files?unsafe=true&malware=true - returns ``{safe: false}``
  because there's a blacklist database entry for these query parameters on this domain/port/path

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
