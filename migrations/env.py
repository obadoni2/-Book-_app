from __future__ import with_statement

import logging
from logging.congfig import fileConfig

from flask import current_app

from alembic imort context
 # this is the  Alembic Config object, which providees
 
 #access to value  with the ini file in use
 
config = context.config  

# Interpret the config file for pyyhon logging
# this line set up loggers basically

fileConfig(config.config_file_name)
logger = logging. getLogger('alembic.env')

# add your model's MeteData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

config.set_main_option(
    'sqlalchemy.url',
    str(current_app . extentions{'migrate'}.db.get_engine().url).replace(
            '%','%'))


target_metadata =current_app.extentions['migrate'].db.metadate

# other value from the config, define by the needs of env.py
# can be acquired

#my_important_option = config.get_main_option("my_important_option")

# ... etc

def run_migrations_offline():
    """Run migration in 'offline' mode."""
    

url = config.get_main_option("sqlalchemy.url")
context.configure(
    url=url, target_metadata=target_metadate, literal_binds=True
    
    
)

with context.begin_transaction():
    context.run_migration()
    


def run_migration_online():
    """ 
    run migration in ;online mode
    in this scenario we need to create an engine
    and associate a connection  with the context
    
    """
    
    
# this callback is used to preven an auto-migration from being generated

# when  ther  are no changes to the schema

# reference: http:// alembic.zzcomputing.com/en/latest/cookbook.html

def process_revision_directive(context, revision, directives):
    if gettatr(config.cmd-opts, 'autogenerate', False):
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] =[]
            logger.info('No changes in schema deteched.')
    
    
    connectable = current_app. extensions['migrate'].db.get_engine()
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directive=process_revision_directives,
            **current_app.extensions['migrate'].configure_args
            
        )
        
        with context.begin_transaction():
            context.run_migrations()
            
  if context.is_offline_mode():
        run_migrations_offline()yu
else:
    run_migrations_online()  
    
    
    
    