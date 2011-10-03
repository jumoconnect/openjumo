from __future__ import with_statement
from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner, dependency_ordered
from django_jenkins.runner import CITestSuiteRunner
import sys

EXCLUDED_APPS = getattr(settings, "EXCLUDED_TEST_PACKAGES", [])

def create_test_db(connection, verbosity, autoclobber=False):
    test_db_name = connection.creation._create_test_db(verbosity, autoclobber=autoclobber)
    connection.close()
    connection.settings_dict["NAME"] = test_db_name
    can_rollback = connection.creation._rollback_works()
    connection.settings_dict["SUPPORTS_TRANSACTIONS"] = can_rollback
    return test_db_name



class JumoTestSuiteRunner(CITestSuiteRunner):
    def setup_databases(self, **kwargs):
        from django.db import connections, DEFAULT_DB_ALIAS

        # First pass -- work out which databases actually need to be created,
        # and which ones are test mirrors or duplicate entries in DATABASES
        mirrored_aliases = {}
        test_databases = {}
        dependencies = {}
        for alias in connections:
            connection = connections[alias]
            if connection.settings_dict['TEST_MIRROR']:
                # If the database is marked as a test mirror, save
                # the alias.
                mirrored_aliases[alias] = connection.settings_dict['TEST_MIRROR']
            else:
                # Store the (engine, name) pair. If we have two aliases
                # with the same pair, we only need to create the test database
                # once.
                test_databases.setdefault((
                        connection.settings_dict['HOST'],
                        connection.settings_dict['PORT'],
                        connection.settings_dict['ENGINE'],
                        connection.settings_dict['NAME'],
                    ), []).append(alias)

                if 'TEST_DEPENDENCIES' in connection.settings_dict:
                    dependencies[alias] = connection.settings_dict['TEST_DEPENDENCIES']
                else:
                    if alias != 'default':
                        dependencies[alias] = connection.settings_dict.get('TEST_DEPENDENCIES', ['default'])

        # Second pass -- actually create the databases.
        old_names = []
        mirrors = []
        db_schemas = settings.DATABASE_CREATE_SCHEMAS
        for (host, port, engine, db_name), aliases in dependency_ordered(test_databases.items(), dependencies):
            # Actually create the database for the first connection
            connection = connections[aliases[0]]
            old_names.append((connection, db_name, True))
            #test_db_name = connection.creation._create_test_db(self.verbosity, autoclobber=not self.interactive)
            test_db_name = create_test_db(connection, self.verbosity, not self.interactive)

            #Create Tables Via Schema File
            try:

                schema_file = db_schemas[aliases[0]]
                schema_string = ""
                with open(schema_file) as fh:
                    schema_string = fh.read()

                print "Building Tables For %s from %s" % (test_db_name, schema_file)
                cursor = connection.cursor()
                connection.autocommit = True
                cursor.execute(schema_string)
                cursor.close()
            except Exception, e:
                sys.stderr.write("Got an loading the schema file database: %s\n" % e)
                print "Tests Canceled"
                sys.exit(1)

            for alias in aliases[1:]:
                connection = connections[alias]
                if db_name:
                    old_names.append((connection, db_name, False))
                    connection.settings_dict['NAME'] = test_db_name
                else:
                    # If settings_dict['NAME'] isn't defined, we have a backend where
                    # the name isn't important -- e.g., SQLite, which uses :memory:.
                    # Force create the database instead of assuming it's a duplicate.
                    old_names.append((connection, db_name, True))
                    connection.creation.create_test_db(self.verbosity, autoclobber=not self.interactive)

        from django.core.management import call_command
        from django.contrib.contenttypes.management import update_all_contenttypes
        update_all_contenttypes()

        call_command('loaddata', 'initial_data', verbosity=self.verbosity, database=DEFAULT_DB_ALIAS)

        for alias, mirror_alias in mirrored_aliases.items():
            mirrors.append((alias, connections[alias].settings_dict['NAME']))
            connections[alias].settings_dict['NAME'] = connections[mirror_alias].settings_dict['NAME']

        return old_names, mirrors

    def build_suite(self, *args, **kwargs):
        suite = super(JumoTestSuiteRunner, self).build_suite(*args, **kwargs)
        if not args[0]:
            tests = []
            for case in suite:
                pkg = case.__class__.__module__.split('.')[0]
                if pkg not in EXCLUDED_APPS:
                    tests.append(case)
            suite._tests = tests
        return suite
