# Deploying MedTwin AI to a server (24/7 public access)

This packages the whole stack — MySQL, Spring Boot API, Python AI service and
the web app — into Docker containers. Once deployed to a cloud server, your
link works for anyone, any time, even when your Mac is off.

## What you need

1. A server (VPS). Good options:
   - **Oracle Cloud Free Tier** — always-free small VM
   - **Hetzner** (~€4/mo), **DigitalOcean** (~$6/mo), **AWS Lightsail** (~$5/mo)
   - Ubuntu 22.04/24.04 recommended
2. (Optional) A domain name pointing to the server IP.

## One-time server setup

```bash
ssh root@YOUR_SERVER_IP

# install docker
curl -fsSL https://get.docker.com | sh

# get the project
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git medtwin
cd medtwin
```

## Configure and launch

```bash
cp docker/.env.example .env
nano .env        # set MYSQL_ROOT_PASSWORD and PUBLIC_URL

docker compose -f docker-compose.prod.yml up -d --build
```

First build takes a few minutes. Then initialise the database once:

```bash
# load the schema
docker compose -f docker-compose.prod.yml exec -T mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" medtwin < db/schema.sql

# seed demo data (demo accounts, doctors, sample records)
docker compose -f docker-compose.prod.yml exec -w /srv/backend ai python manage.py seed_demo
```

Open `http://YOUR_SERVER_IP` — the app is live. Log in with the demo
accounts (`patient@medtwin.dev` / `doctor@medtwin.dev` / `admin@medtwin.dev`,
password `MedTwin@2026`).

## HTTPS + a real domain (recommended)

Point your domain's A record at the server IP, then add Cloudflare in front
(free): set the DNS record in Cloudflare with proxy enabled (orange cloud) and
add an SSL/TLS rule "Flexible". You get a permanent `https://your-domain` URL
with TLS, DDoS protection and caching at no cost.

Alternatively run Caddy or certbot on the server for Let's Encrypt certificates
(terminate TLS on port 443 and proxy to the `web` container).

## Updating the app later

```bash
cd medtwin && git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Useful commands

```bash
docker compose -f docker-compose.prod.yml ps          # status
docker compose -f docker-compose.prod.yml logs -f spring   # API logs
docker compose -f docker-compose.prod.yml logs -f ai       # AI logs
docker compose -f docker-compose.prod.yml down        # stop everything
```

## Production hardening checklist

- [ ] Change every demo password before real use
- [ ] Use a dedicated MySQL user instead of root (create in the container, then
      set `SPRING_DATASOURCE_USERNAME/PASSWORD` and `DB_USER/DB_PASSWORD`)
- [ ] Set strong `MEDTWIN_AI_SHARED_SECRET` on both Spring and AI containers
- [ ] Enable HTTPS (Cloudflare proxy or certbot) — cookies require it in prod
- [ ] Back up the `mysqldata` volume regularly
- [ ] For reliable video calls across networks, run `docker-compose.coturn.yml`
      on the same server and set `MEDTWIN_TURN_URL/USERNAME/CREDENTIAL` on the
      spring container
