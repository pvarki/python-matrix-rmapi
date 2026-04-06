===================
python-matrix-rmapi
===================

Matrix service RASENMAEHER integration API service. Serves as a reference implementation for a new integration into the deploy app ecosystem.

Operation
---------

matrixrmapi is the Deploy App integration layer for Matrix/Synapse. It has two responsibilities:

1. **Synapse bootstrap** — on startup it registers an admin bot, creates the deployment's Space and rooms,
   and configures their state.
2. **User lifecycle** — it receives CRUD callbacks from Rasenmaeher over mTLS and reflects each event into
   Synapse.

Authentication
^^^^^^^^^^^^^^

All ``/api/v1/users/*`` endpoints require a valid mTLS client certificate whose CN matches the Rasenmaeher
service certificate (taken from the kraftwerk manifest). Any other caller receives ``403 Forbidden``.

Startup sequence
^^^^^^^^^^^^^^^^

The startup runs as a background task so the HTTP server is available immediately::

    1. Poll GET /health on Synapse until it responds 200 (up to 5 minutes).
    2. Acquire a file lock and register the admin bot via the Synapse HMAC-signed
       registration endpoint (idempotent: if a valid token file already exists,
       re-registration is skipped).
    3. Remove rate-limiting for the bot user so concurrent room operations never hit 429.
    4. Ensure the Space and four rooms exist (creates them if missing, looks them up by
       alias otherwise).
    5. Apply idempotent state events to every room: name, encryption, join rules,
       history visibility, topics.
    6. Expose ``app.state.rooms`` — this is the gate that CRUD endpoints check.
    7. Drain any promotions/demotions that arrived while rooms were not yet ready
       (see "Deferred queue" below).

The admin bot is created at power level 200 in all rooms via ``power_level_content_override``
so it can always demote admins (who are at level 100). This is a Matrix spec requirement:
a user cannot lower the power level of another user at an equal-or-higher level.

Rooms created
^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Key
     - Alias
     - Notes
   * - space
     - ``#<deployment>-space:<domain>``
     - Top-level Space; join rule: invite
   * - general
     - ``#<deployment>-general:<domain>``
     - Public room; join rule: restricted (Space membership)
   * - helpdesk
     - ``#<deployment>-helpdesk:<domain>``
     - Public room; join rule: restricted (Space membership)
   * - offtopic
     - ``#<deployment>-offtopic:<domain>``
     - Public room; join rule: restricted (Space membership)
   * - admin
     - ``#<deployment>-admin:<domain>``
     - Private room; only admins are joined

All non-space rooms use ``m.megolm.v1.aes-sha2`` encryption and ``joined`` history visibility.

User lifecycle endpoints
^^^^^^^^^^^^^^^^^^^^^^^^

``POST /api/v1/users/created``
    New device certificate created. Force-joins the user to the Space and all three public rooms.
    If Synapse is not yet ready, logs a warning and returns success — ``auto_join_rooms`` in
    ``homeserver.yaml`` will join the user when they first log in via OIDC.

``POST /api/v1/users/revoked``
    Device certificate revoked. Deactivates and erases the user from Synapse (their messages
    are removed from the server). If Synapse is not ready yet, returns success with a warning.

``POST /api/v1/users/promoted``
    User promoted to admin in Deploy App. Sets the user's power level to 100 in the Space and
    all public rooms, then force-joins them to the admin channel.
    If Synapse is not yet ready, the action is queued (see "Deferred queue").

``POST /api/v1/users/demoted``
    User demoted from admin. Resets power level to 0 in the Space and public rooms, and kicks
    the user from the admin channel.
    If Synapse is not yet ready, the action is queued (see "Deferred queue").

``PUT /api/v1/users/updated``
    Callsign updated. No-op — a callsign change requires a new Matrix account and is not
    handled automatically.

Deferred queue
^^^^^^^^^^^^^^

Because Synapse takes time to start, ``/promoted`` and ``/demoted`` calls can arrive before
``app.state.rooms`` is set. In that case the uid and action (``"promote"`` or ``"demote"``) are
stored in ``app.state.pending_promotions``. After startup completes and rooms are exposed, the
queue is drained in order. If a user is promoted and then demoted before Synapse is ready, only
the last action survives (the dict key is overwritten).

Configuration
^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Environment variable
     - Default
     - Description
   * - ``SYNAPSE_URL``
     - ``http://synapse:8008``
     - Internal URL of the Synapse homeserver
   * - ``SYNAPSE_REGISTRATION_SECRET``
     - *(required)*
     - Shared secret for bot registration (HMAC-SHA1)
   * - ``SYNAPSE_BOT_USERNAME``
     - ``matrixrmapi-bot``
     - Local part of the admin bot Matrix user
   * - ``SYNAPSE_TOKEN_FILE``
     - ``/data/persistent/synapse_admin_token``
     - File where the bot's access token is cached between restarts
   * - ``SERVER_DOMAIN``
     - *(from kraftwerk manifest)*
     - Matrix server_name; derived automatically from the product DNS label

Docker
------

For more controlled deployments and to get rid of "works on my computer" -syndrome, we always
make sure our software works under docker.

It's also a quick way to get started with a standard development environment.

SSH agent forwarding
^^^^^^^^^^^^^^^^^^^^

We need buildkit_::

    export DOCKER_BUILDKIT=1

.. _buildkit: https://docs.docker.com/develop/develop-images/build_enhancements/

And also the exact way for forwarding agent to running instance is different on OSX::

    export DOCKER_SSHAGENT="-v /run/host-services/ssh-auth.sock:/run/host-services/ssh-auth.sock -e SSH_AUTH_SOCK=/run/host-services/ssh-auth.sock"

and Linux::

    export DOCKER_SSHAGENT="-v $SSH_AUTH_SOCK:$SSH_AUTH_SOCK -e SSH_AUTH_SOCK"

Creating a development container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build image, create container and start it::

    docker build --ssh default --target devel_shell -t matrixrmapi:devel_shell .
    docker create --name matrixrmapi_devel -p 4625:4625 -v `pwd`":/app" -it `echo $DOCKER_SSHAGENT` matrixrmapi:devel_shell
    docker start -i matrixrmapi_devel


In the shell you can start the uvicorn devel server with (binding to 0.0.0.0 is important!)::

    uvicorn "matrixrmapi.app:get_app" --factory --host 0.0.0.0 --port 4625 --reload --log-level debug


pre-commit considerations
^^^^^^^^^^^^^^^^^^^^^^^^^

If working in Docker instead of native env you need to run the pre-commit checks in docker too::

    docker exec -i matrixrmapi_devel /bin/bash -c "pre-commit install  --install-hooks"
    docker exec -i matrixrmapi_devel /bin/bash -c "pre-commit run --all-files"

You need to have the container running, see above. Or alternatively use the docker run syntax but using
the running container is faster::

    docker run --rm -it -v `pwd`":/app" matrixrmapi:devel_shell -c "pre-commit run --all-files"

Test suite
^^^^^^^^^^

You can use the devel shell to run py.test when doing development, for CI use
the "tox" target in the Dockerfile::

    docker build --ssh default --target tox -t matrixrmapi:tox .
    docker run --rm -it -v `pwd`":/app" `echo $DOCKER_SSHAGENT` matrixrmapi:tox

Production docker
^^^^^^^^^^^^^^^^^

There's a "production" target as well for running the application, remember to change that
architecture tag to arm64 if building on ARM::

    docker build --ssh default --target production -t matrixrmapi:latest .
    docker run -it --name matrixrmapi -p 4625:4625 matrixrmapi:amd64-latest

Development
-----------

TLDR:

- Create and activate a Python 3.11 virtualenv (assuming virtualenvwrapper)::

   mkvirtualenv -p `which python3.11` my_virtualenv

- change to a branch::

    git checkout -b my_branch

- install Poetry: https://python-poetry.org/docs/#installation
- Install project deps and pre-commit hooks::

    poetry install
    pre-commit install --install-hooks
    pre-commit run --all-files

- Ready to go.

Remember to activate your virtualenv whenever working on the repo, this is needed
because pylint and mypy pre-commit hooks use the "system" python for now (because reasons).

Testing a local Synapse server
------------------------------
Aka, how to connect a Matrix client to your server to see how things work out.
1. Make sure you trust your localmaeher's self-signed certs at https://synapse.localmaeher.dev.pvarki.fi:4439/. Navigate to that page, click accept the risk.
2. Run the following command to set up an Element Web service as a client:

    docker run --rm -p 8088:80 \
    -e ELEMENT_WEB_CONFIG='{"default_server_config":{"m.homeserver":{"base_url":"https://synapse.localmaeher.dev.pvarki.fi:4439"}}}' \
    vectorim/element-web

3. Now navigate to http://localhost:8080. Log in to localmaeher's Synapse as usual.
