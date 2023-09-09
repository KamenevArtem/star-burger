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