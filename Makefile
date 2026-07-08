COMPOSE_LOCAL=docker compose --env-file .env -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.local.yml
COMPOSE_PROD=docker compose --env-file .env -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.prod.yml

up:
	$(COMPOSE_LOCAL) up -d --build

down:
	$(COMPOSE_LOCAL) down

logs:
	$(COMPOSE_LOCAL) logs -f --tail=200

ps:
	$(COMPOSE_LOCAL) ps

restart:
	$(COMPOSE_LOCAL) restart
