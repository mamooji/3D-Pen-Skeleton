# Build the frontend, then serve it and the API from one Python image.

FROM node:24-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    U2NET_HOME=/opt/models \
    NUMBA_CACHE_DIR=/opt/numba-cache
WORKDIR /srv/backend

COPY backend/requirements.txt ./
# numba keys its cache on source mtimes, and image layers drop sub-second mtimes,
# so round pymatting's to whole seconds or the cache built below never matches at runtime.
RUN pip install -r requirements.txt \
    && find /usr/local/lib/python3.12/site-packages/pymatting -name "*.py" -exec touch -d "2000-01-01 00:00:00" {} +

# Ship the background-removal model (~180 MB) in the image so the first upload doesn't download it.
# Importing rembg also JIT-compiles pymatting with numba, so its cache ships in the image too.
RUN python -c "from rembg import new_session; new_session('isnet-general-use')"

# numba needs to write to its cache dir, even when it only reads the compiled functions.
# The downloaded model is root-only (0600).
RUN useradd --system --no-create-home app && mkdir -p /opt/numba-cache && chown -R app /opt/numba-cache \
    && chmod -R a+rX /opt/models
USER app
# Fail the build, not the first upload, if the app user can't load the model.
RUN python -c "from rembg import new_session; new_session('isnet-general-use')"

COPY backend/app ./app
# main.py serves ../../frontend/dist relative to itself.
COPY --from=frontend /src/frontend/dist /srv/frontend/dist

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"
# One worker: background removal already uses every core, and the upload cache lives in memory.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
