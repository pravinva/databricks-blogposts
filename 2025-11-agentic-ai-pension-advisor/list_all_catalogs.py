#!/usr/bin/env python3
"""
List all available catalogs and schemas to find member data
"""

from databricks.sdk import WorkspaceClient

def list_catalogs():
    """List all catalogs and their schemas"""

    w = WorkspaceClient()

    print("=" * 80)
    print("Available Catalogs and Schemas:")
    print("=" * 80)

    try:
        catalogs = w.catalogs.list()

        for catalog in catalogs:
            print(f"\nCatalog: {catalog.name}")

            try:
                schemas = w.schemas.list(catalog_name=catalog.name)
                for schema in schemas:
                    print(f"  └─ Schema: {schema.name}")

                    # Try to find member_profiles table
                    try:
                        tables = w.tables.list(catalog_name=catalog.name, schema_name=schema.name)
                        for table in tables:
                            if 'member' in table.name.lower() or 'profile' in table.name.lower():
                                print(f"      └─ Table: {table.name} ⭐")
                    except:
                        pass

            except Exception as e:
                print(f"  └─ (Cannot list schemas: {e})")

    except Exception as e:
        print(f"Error listing catalogs: {e}")

if __name__ == "__main__":
    list_catalogs()
