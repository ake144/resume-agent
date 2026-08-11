from logging.config import fileConfig

from alembic import context

from app.core.database import Base, engine
import app.db.models  # noqa: F401  (side effect: registers all tables on Base.metadata)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_name(name, type_, parent_names):
    """Exclude PGVector's own tables from autogenerate's view of the schema.

    langchain_postgres creates langchain_pg_collection/langchain_pg_embedding
    against its own private declarative base, completely separate from this
    app's Base. Without this filter, autogenerate reflects the full connected
    schema, sees those tables as "not in target_metadata", and proposes
    DROP TABLE for them - including the live resume knowledge base.
    """
    if type_ == "table" and name is not None and name.startswith("langchain_pg_"):
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Reuses the app's own engine (app.core.database.engine, built from
    settings.database_url) rather than building a second one from
    alembic.ini, so Alembic can never point at a different DB than the app.
    """
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
