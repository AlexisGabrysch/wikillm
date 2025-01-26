from database import DatabaseManager

# Initialize the database manager
db_manager = DatabaseManager()

# Simulated data
article_title = "Python (programming language)"
article_content = """
Python is an interpreted, high-level and general-purpose programming language. Python's design philosophy emphasizes code readability with its notable use of significant whitespace.
"""
article_links = ["Guido van Rossum", "Programming language", "Interpreted language"]
article_metadata = {"category": "Programming Languages", "last_updated": "2023-10-01"}

# Add the article to the database
db_manager.add_article(title=article_title, content=article_content, links=article_links, metadata=article_metadata)

# Query the article from the database
queried_article = db_manager.query_article(title="Python (programming language)")
print(queried_article)