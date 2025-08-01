import requests
from bs4 import BeautifulSoup
import re
from collections import deque
import time

def search_actor_id(actor_name):
    """
    IMDb에서 배우 이름을 검색해 첫 번째 결과의 ID(nmXXXXXXX)를 반환.
    """
    q = actor_name.replace(' ', '+')
    url = f"https://www.imdb.com/find/?q={q}&s=nm"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    sec = soup.find('section', {'data-testid': 'find-results-section-name'})
    if not sec:
        return None
    a = sec.find('a', href=re.compile(r'/name/nm\d+/'))
    if not a:
        return None

    m = re.search(r'nm\d+', a['href'])
    return m.group(0) if m else None

def get_movies_of_actor(actor_name, max_movies=20):
    """
    주어진 배우 이름의 필모그래피에서 영화 ID와 제목 리스트를 반환.
    [(movie_id, movie_title), …]
    """
    nm_id = search_actor_id(actor_name)
    if not nm_id:
        return []

    url = f"https://www.imdb.com/name/{nm_id}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    result = []
    seen = set()
    for li in soup.select('li.ipc-metadata-list-summary-item'):
        a = li.select_one('a.ipc-metadata-list-summary-item__t')
        if not a:
            continue
        href = a['href']
        title = a.get_text(strip=True)
        m = re.search(r'/title/(tt\d+)', href)
        if m:
            mid = m.group(1)
            if mid not in seen:
                seen.add(mid)
                result.append((mid, title))
                if len(result) >= max_movies:
                    break
    return result

def get_cast_of_movie(movie_id, max_cast=20):
    """
    주어진 영화 ID의 출연진 리스트를 반환.
    [(actor_id, actor_name), …]
    """
    url = f"https://www.imdb.com/title/{movie_id}/fullcredits"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    ul = soup.find('ul', class_=re.compile('full-credits-page-list'))
    if not ul:
        return []

    cast = []
    for li in ul.find_all('li', class_=re.compile('ipc-metadata-list-summary-item')):
        a = li.find('a', class_=re.compile('name-credits--title-text'))
        if not a:
            continue
        m = re.search(r'(nm\d+)', a['href'])
        if m:
            aid = m.group(1)
            name = a.get_text(strip=True)
            cast.append((aid, name))
            if len(cast) >= max_cast:
                break
    return cast

def find_connection(actor1, actor2, max_depth=4):
    """
    BFS로 actor1 → actor2 사이의 최소 연결 경로를 찾음.
    경로 탐색 과정을 상세히 출력하며, [(actor1, movie, actor2), …] 또는 None 반환.
    """
    print(f"🔍 탐색 시작: '{actor1}' → '{actor2}' (max_depth={max_depth})")
    queue = deque([(actor1, [])])
    visited = {actor1}

    while queue:
        current, path = queue.popleft()
        depth = len(path)
        print(f"\n➡️ 현재 배우: {current} (깊이 {depth})")

        if depth >= max_depth * 2:
            print("  깊이 제한 초과, 다음으로 넘어갑니다.")
            continue

        movies = get_movies_of_actor(current)
        print(f"  ▶️ '{current}' 출연 영화 수: {len(movies)}")
        time.sleep(0.2)

        for mid, title in movies:
            print(f"    🎬 영화 탐색: {title} ({mid})")
            cast = get_cast_of_movie(mid)
            print(f"      👥 출연 배우 수: {len(cast)}")
            time.sleep(0.2)

            for aid, name in cast:
                print(f"        - 공저자: {name} ({aid})")
                if name == actor2:
                    new_path = path + [(current, title, name)]
                    print("\n✅ 연결 경로 발견!")
                    return new_path
                if name not in visited:
                    visited.add(name)
                    new_path = path + [(current, title, name)]
                    print(f"        ➕ 큐에 추가: {name} (깊이 {len(new_path)})")
                    queue.append((name, new_path))

    print("\n❌ 연결 경로를 찾을 수 없습니다.")
    return None

if __name__ == "__main__":
    start = "Tom Cruise"
    target = "Robert De Niro"
    path = find_connection(start, target, max_depth=6)

    if path is None:
        print(f"'{start}'에서 '{target}'로 가는 경로가 없습니다.")
    elif not path:
        print(f"🎬 '{start}'는 '{target}'과 동일 배우입니다. 거리: 0")
    else:
        print(f"\n🎯 최종 경로 (거리 {len(path)}):")
        for i, (a1, movie, a2) in enumerate(path, 1):
            print(f"  {i}. {a1} → [{movie}] → {a2}")
