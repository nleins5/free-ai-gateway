import re
from ddgs import DDGS

q = "anh huỳnh vũ tuấn tú là ai?"

def perform_web_search(q):
    try:
        with DDGS() as ddgs:
            print(f"Primary search: {q}")
            results = list(ddgs.text(q, max_results=5))
            
            # Find capitalized words (proper nouns)
            proper_nouns = re.findall(r'\b[A-ZÀ-Ỹ][a-zà-ỹ]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]*)*\b', q)
            proper_nouns = [name for name in proper_nouns if len(name.split()) >= 2]
            
            print(f"Extracted proper nouns: {proper_nouns}")
            
            # Add fallback if no proper nouns
            if not proper_nouns:
                clean_q = re.sub(r'(anh|chị|ông|bà|là ai|ở đâu|thế nào|\?)', '', q, flags=re.IGNORECASE).strip()
                if clean_q:
                    proper_nouns = [clean_q]
            
            for name in proper_nouns:
                # Query 1: exact match
                print(f"Query 1: '\"{name}\"'")
                try:
                    results.extend(list(ddgs.text(f'"{name}"', max_results=3)))
                except Exception as e:
                    print(f"Query 1 failed: {e}")
                
                # Query 2: name + uef
                print(f"Query 2: '\"{name}\" uef'")
                try:
                    results.extend(list(ddgs.text(f'"{name}" uef', max_results=3)))
                except Exception as e:
                    print(f"Query 2 failed: {e}")
                
                # Query 3: site:uef.edu.vn
                print(f"Query 3: '\"{name}\" site:uef.edu.vn'")
                try:
                    results.extend(list(ddgs.text(f'"{name}" site:uef.edu.vn', max_results=3)))
                except Exception as e:
                    print(f"Query 3 failed: {e}")
            
            # De-duplicate by URL
            seen_urls = set()
            unique_results = []
            for r in results:
                href = r.get("href")
                if href and href not in seen_urls:
                    seen_urls.add(href)
                    unique_results.append(r)
            
            return unique_results[:8]
    except Exception as e:
        print(f"Overall Search failed: {e}")
        return []

res = perform_web_search(q)
print("\n--- RESULTS ---")
for idx, r in enumerate(res):
    print(f"[{idx}] {r.get('title')} -> {r.get('href')}")
