# fluo-proto-factory

Monorepo that produces throwaway prototypes for product design, user testing, and fast iteration at [Plateforme de l'inclusion](https://inclusion.gouv.fr). Each prototype looks identical to [les-emplois](https://github.com/gip-inclusion/les-emplois) but implements different domain logic.

See [`PROTOTYPE.md`](PROTOTYPE.md) to build a new proto, and [`CLAUDE.md`](CLAUDE.md) for the factory layout.

## Quick start

```bash
make new <name>            # scaffold from _template/
make provision <name>      # create Scaleway container + DB
make dev <name>            # hot reload on localhost:8002
make deploy <name>         # build + push + deploy
```

`make help` lists all targets.
