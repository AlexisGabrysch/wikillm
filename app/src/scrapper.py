import requests
from bs4 import BeautifulSoup
import wikipedia
from app.src.db.utils import create_db_courses, insert_course

class SearchEngine:
    def __init__(self):
        self.url = None
        
    def get_soup(self, url):
        
        self.url = url
        
        response = requests.get(url)
         
        if response.status_code == 200:
            
            return BeautifulSoup(response.text, 'html.parser')
        else:
            print(f"Error: {response.status_code}")
            return None


class SchoolMoveScrapper(SearchEngine):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.schoolmouv.fr"
        
    def get_content_course(self,url: str) -> str:
        soup = self.get_soup(url)
        container  = soup.find('div', class_="luna-content_luna-content__section__z7rg5")
        if not container:
            return ""
        else:
            return container.get_text(separator=' ', strip=True)


    def get_courses_from_html(self,url: str) -> dict:
        soup = self.get_soup(url)
        container = soup.find("div", class_="program-template_program__content__w3oIs")
        chapters = {}
        if not container:
            return chapters

        chapter_divs = container.find_all("div", class_="course-list_chapter__13m89")
        courses_list = []
        for chapter in chapter_divs:
            # Récupérer le titre du chapitre depuis le h2
            header = chapter.find("div", class_="course-list_chapter__title--without-cups__dehJf")
            h2 = header.find("h2") if header else None
            chapter_title = h2.get_text(strip=True) if h2 else "Sans titre"

            
            ul = chapter.find("ul", class_="course-list_chapter__course-list__x_5Q6")
            if ul:
                for li in ul.find_all("li", class_="course-list_chapter__course-list--item-without-cups__CJUPl"):
                    a = li.find("a", class_="course-title-card-module_course-title-card__YrMOq")
                    if a:
                        link = a.get("href")
                        p = a.find("p")
                        course_title = p.get_text(strip=True) if p else ""
                        courses_list.append({
                            "link": link,
                            "title": course_title,
                            "content": self.get_content_course(link),
                            "theme": chapter_title
                        })
        return courses_list


    def run(self, url, db_path="app/src/db/courses.db", theme="Histoire"):
        courses = self.get_courses_from_html(url)
        create_db_courses(db_path)
        for course in courses:
            insert_course( db_path, "schoolmouv", theme, course["theme"], course["title"], course["content"], course["link"])
            print(f"Inserted course: {course['title']}")
        print("SchoolMove Done!")
    
    
    
    

class WikipediaScrapper:
    def __init__(self, lang="fr"):
        self.lang = lang
        wikipedia.set_lang(lang)
        
    def scrape_wikipedia_fr(keyword):
        url = f"https://fr.wikipedia.org/wiki/{keyword.replace(' ', '_')}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.find("div", {"class": "mw-parser-output"})
            if content:
                paragraph = content.find("p")
                return paragraph.get_text(strip=True) if paragraph else None
        return None

    def scrape_wikipedia_api(keyword):
        # Définir la langue de Wikipedia en français
        wikipedia.set_lang("fr")
        keyword = keyword + "/"
        # Rechercher le mot-clé sur Wikipedia
        search_results = wikipedia.search(keyword, results=5)
        print(search_results)  # Affiche les résultats de recherche
        
        if not search_results:
            return None

        
        # Obtenir la page Wikipedia pour le mot-clé
        print(search_results[0])  # Affiche le premier résultat de recherche
        search_page = search_results[0]+"/"
        page = wikipedia.page(search_page)
        print(page.content)  # Affiche le contenu de la page
        return page
    





if __name__ == "__main__":
    scrap = SchoolMoveScrapper()
    scrap.run("https://www.schoolmouv.fr/3eme/physique-chimie" , db_path="app/src/db/courses.db", theme="Physique-chimie")