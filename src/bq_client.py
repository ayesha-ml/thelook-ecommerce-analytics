import pydata_google_auth
from google.cloud import bigquery


def get_client():
    credentials = pydata_google_auth.get_user_credentials(
        scopes=["https://www.googleapis.com/auth/bigquery"],
    )
    return bigquery.Client(
        project="thelook-analytics-engine",
        credentials=credentials
    )

def run_query(sql: str):
    client = get_client()
    return client.query(sql).to_dataframe()

if __name__ == "__main__":
    df = run_query("""
        SELECT *
        FROM `bigquery-public-data.thelook_ecommerce.orders`
        LIMIT 10
    """)
    print(df)
    print("CONNECTION WORKS")