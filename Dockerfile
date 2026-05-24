# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Working directory inside the container.
# When users build FROM this image, their app files go here.
WORKDIR /app

# ── Install Sucuri ─────────────────────────────────────────────────────────────
# Copy only the files needed to install the package, so that the source
# tree is not baked into the final image.
COPY setup.py setup.cfg ./
COPY sucuri/ ./sucuri/

RUN pip install --no-cache-dir . && \
    # Remove build artefacts — the installed package stays in site-packages
    rm -rf setup.py setup.cfg sucuri/

# ── Runtime ────────────────────────────────────────────────────────────────────
# Sucuri's default port. Override with -e PORT=… or in your own CMD / compose.
EXPOSE 8080

# Default entrypoint: run the live server for the app file at /app/app.py.
# Users override this in their own Dockerfile:
#
#   FROM marcosstefani/sucuri
#   COPY . .
#   CMD ["sucuri", "serve", "main.py", "--host", "0.0.0.0"]
#
CMD ["sucuri", "serve", "app.py", "--host", "0.0.0.0"]
