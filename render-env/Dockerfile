FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    ffmpeg libegl1 libpango1.0-dev libcairo2-dev pkg-config \
    texlive-latex-base texlive-latex-extra texlive-fonts-recommended \
    dvisvgm cm-super ghostscript \
    libgl1-mesa-glx libglib2.0-0 \
    fonts-dejavu fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY reels/shipstack/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/shipstack-venv && \
    /opt/shipstack-venv/bin/pip install --upgrade pip setuptools wheel && \
    /opt/shipstack-venv/bin/pip install -r /tmp/requirements.txt \
      latex2mathml==3.78.0 lxml==5.3.0

ENV PATH="/opt/shipstack-venv/bin:$PATH"
COPY . /workspace

RUN python3 - <<'PY'
import manim, latex2mathml, lxml
print("preview environment ready")
print("manim", manim.__version__)
print("latex2mathml", latex2mathml.__version__)
PY

CMD ["python3", "-m", "reels.shipstack", "--list"]
