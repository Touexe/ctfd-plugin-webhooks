# syntax=docker/dockerfile:1

ARG CTFD_VERSION=latest

# --- Stage 1: fetch the plugin (keeps git out of the final image) ---
FROM alpine/git AS plugin
ARG PLUGIN_REPO=https://github.com/Touexe/ctfd-plugin-webhooks.git
# Branch, tag or commit SHA. Pin this for reproducible builds.
ARG PLUGIN_REF=main
RUN git clone --depth 1 --branch "${PLUGIN_REF}" "${PLUGIN_REPO}" /plugin \
    && rm -rf /plugin/.git /plugin/tests /plugin/.assets

# --- Stage 2: CTFd with the plugin pre-installed ---
FROM ctfd/ctfd:${CTFD_VERSION}

# Directory name becomes the plugin name; matches /admin/plugins/ctfd-plugin-webhooks
COPY --from=plugin --chown=ctfd:ctfd /plugin /opt/CTFd/CTFd/plugins/ctfd-plugin-webhooks
