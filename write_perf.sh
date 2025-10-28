export PIP_INDEX_URL="https://repo.artifactory-dogen.group.echonet/artifactory/api/pypi/pypi/simple"
export PIP_TRUSTED_HOST="repo.artifactory-dogen.group.echonet"

pip-compile --generate-hashes --resolver=backtracking \
  --pip-args="--only-binary=:none:" \
  -o requirements.txt requirements.in
