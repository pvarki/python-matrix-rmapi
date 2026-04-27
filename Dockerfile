# syntax=docker/dockerfile:1.1.7-experimental
#############################################
# Tox testsuite for multiple python version #
#############################################
FROM advian/tox-base:debian-bookworm as tox
ARG PYTHON_VERSIONS="3.11 3.12"
RUN export RESOLVED_VERSIONS=`pyenv_resolve $PYTHON_VERSIONS` \
    && echo RESOLVED_VERSIONS=$RESOLVED_VERSIONS \
    && for pyver in $RESOLVED_VERSIONS; do pyenv install -s $pyver; done \
    && pyenv global $RESOLVED_VERSIONS \
    && pip install -U uv tox tox-uv \
    && apt-get update && apt-get install -y \
        git \
    && rm -rf /var/lib/apt/lists/* \
    && true
COPY ./uv.lock ./pyproject.toml ./README.rst ./.pre-commit-config.yaml ./docker /app/
WORKDIR /app
RUN uv sync \
    && uv run docker/pre_commit_init.sh \
    && rm -rf .venv \
    && true

######################
# Base builder image #
######################
FROM python:3.11-bookworm as builder_base
ENV \
  # locale
  LC_ALL=C.UTF-8 \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_INDEX_URL=https://nexus.dev.pvarki.fi/repository/python/simple \
  # uv:
  UV_NO_CACHE=1 \
  UV_DEFAULT_INDEX=https://nexus.dev.pvarki.fi/repository/python/simple
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install -y \
        curl \
        git \
        bash \
        build-essential \
        libffi-dev \
        libssl-dev \
        libzmq3-dev \
        tini \
        openssh-client \
        cargo \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    # githublab ssh
    && mkdir -p -m 0700 ~/.ssh && ssh-keyscan gitlab.com github.com | sort > ~/.ssh/known_hosts \
    && true
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && corepack enable \
    && corepack prepare pnpm@latest --activate
SHELL ["/bin/bash", "-lc"]
# Copy only requirements, to cache them in docker layer:
WORKDIR /pysetup
COPY ./uv.lock ./pyproject.toml ./README.rst /pysetup/
# Install runtime requirements into a virtualenv
RUN --mount=type=ssh uv sync --no-dev --no-install-project \
    && echo 'source /pysetup/.venv/bin/activate' >>/root/.profile \
    && true


####################################
# Base stage for production builds #
####################################
FROM builder_base as production_build
# Copy entrypoint script
COPY ./docker/entrypoint.sh /docker-entrypoint.sh
COPY ./docker/container-init.sh /container-init.sh
# Only files needed by production setup
COPY ./uv.lock ./pyproject.toml ./README.rst /app/
COPY ./src /app/src/
COPY ./ui /ui/
WORKDIR /ui
RUN CI=true pnpm install && pnpm build
RUN mkdir -p /ui_build && cp -r dist/* /ui_build/
WORKDIR /app
# Build the wheel package with uv and add it to the wheelhouse
RUN --mount=type=ssh source /pysetup/.venv/bin/activate \
    && uv build --wheel \
    && mkdir -p /tmp/wheelhouse \
    && cp dist/*.whl /tmp/wheelhouse \
    && chmod a+x /docker-entrypoint.sh \
    && true


#########################
# Main production build #
#########################
FROM python:3.11-slim-bookworm as production
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=production_build /tmp/wheelhouse /tmp/wheelhouse
COPY --from=production_build /ui_build /ui_build
COPY --from=production_build /docker-entrypoint.sh /docker-entrypoint.sh
COPY --from=production_build /container-init.sh /container-init.sh
COPY --from=pvarki/kw_product_init:latest /kw_product_init /kw_product_init
COPY --from=pvarki/kc_client_init:latest /kc_client_init /kc_client_init
WORKDIR /app
# Install system level deps for running the package (not devel versions for building wheels)
# and install the wheels we built in the previous step. generate default config
RUN --mount=type=ssh apt-get update && apt-get install -y \
        bash \
        libffi8 \
        tini \
        git \
        openssh-client \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && chmod a+x /docker-entrypoint.sh \
    && chmod a+x /container-init.sh \
    && WHEELFILE=`echo /tmp/wheelhouse/matrixrmapi-*.whl` \
    && pip3 install --index-url https://nexus.dev.pvarki.fi/repository/python/simple "$WHEELFILE" \
    && rm -rf /tmp/wheelhouse/ \
    # Do whatever else you need to
    && true
ENTRYPOINT ["/usr/bin/tini", "--", "/docker-entrypoint.sh"]


#####################################
# Base stage for development builds #
#####################################
FROM builder_base as devel_build
# Install deps
COPY . /app
COPY ./docker/entrypoint-dev.sh /entrypoint-dev.sh
RUN chmod +x /entrypoint-dev.sh
WORKDIR /app
RUN --mount=type=ssh uv sync \
    && true


##############
# Run tests #
#############
FROM devel_build as test
WORKDIR /app
ENTRYPOINT ["/usr/bin/tini", "--", "docker/entrypoint-test.sh"]
# Re run install to get the service itself installed
RUN --mount=type=ssh uv sync \
    && ln -s /app/docker/container-init.sh /container-init.sh \
    && uv run docker/pre_commit_init.sh \
    && true


###########
# Hacking #
###########
FROM devel_build as devel_shell
# Copy everything to the image
COPY --from=pvarki/kw_product_init:latest /kw_product_init /kw_product_init
COPY --from=pvarki/kc_client_init:latest /kc_client_init /kc_client_init
WORKDIR /app
RUN apt-get update && apt-get install -y zsh \
    && sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
    && echo "source /root/.profile" >>/root/.zshrc \
    && pip3 install git-up \
    && ln -s /app/docker/container-init.sh /container-init.sh \
    && true
ENTRYPOINT ["/bin/zsh", "-l"]
