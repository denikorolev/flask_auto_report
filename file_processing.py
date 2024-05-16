def generate_sql(column_count):
    columns = [f"column{i} TEXT" for i in range(1, column_count + 1)]
    columns_sql = ", ".join(columns)
    create_table_sql = f"CREATE TABLE my_table ({columns_sql});"
    return create_table_sql


column_count = 15  
sql_query = generate_sql(column_count)

print(sql_query)

