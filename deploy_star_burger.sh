set -e
cd /opt/star-burger/
git pull
source .venv/bin/activate
pip3 install -r requirements.txt
npm ci --dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
systemctl daemon-reload
systemctl restart starburger
systemctl reload nginx

export $(xargs <.env)
curl -H "X-Rollbar-Access-Token: ${ROLLBAR_TOKEN}" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "${ROLLBAR_ENV}", "revision": "'$(git rev-parse --short HEAD)'"}'
echo "Deployment has been successful"
