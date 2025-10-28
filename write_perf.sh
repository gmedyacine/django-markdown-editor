export PIP_INDEX_URL="https://repo.artifactory-dogen.group.echonet/artifactory/api/pypi/pypi/simple"
export PIP_TRUSTED_HOST="repo.artifactory-dogen.group.echonet"

pip-compile --generate-hashes --resolver=backtracking \
  --pip-args="--only-binary=:none:" \
  -o requirements.txt requirements.in

python -m pip install --no-cache-dir pip-audit
pip-audit -r requirements.in -f cyclonedx-json -o gl-sbom-report.cdx.json

pip-audit -r requirements.in -f sarif -o gl-sast-report.sarif

python -m piptools compile requirements.txt --generate-hashes --no-index -o requirements.lock
