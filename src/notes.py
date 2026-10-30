"""
Модуль доступу до даних Second Brain.
Завантаження, пошук, фільтрація, посилання та збереження Markdown-нотаток.
Не залежить від Flask — можна тестувати окремо.
"""

import os
import re
from datetime import datetime
from urllib.parse import quote

import frontmatter

# Кореневі константи
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_DIR = os.path.join(BASE_DIR, 'notes')
CATEGORIES = ['Inbox', 'Projects', 'Areas', 'Resources', 'Archives']


# ---------------------------------------------------------------------------
# Завантаження
# ---------------------------------------------------------------------------

def load_all_notes(notes_dir=None):
    """Завантажити всі .md-нотатки з усіх категорій."""
    if notes_dir is None:
        notes_dir = NOTES_DIR
    notes = []
    for category in CATEGORIES:
        cat_dir = os.path.join(notes_dir, category)
        if not os.path.isdir(cat_dir):
            continue
        for filename in sorted(os.listdir(cat_dir)):
            if not filename.endswith('.md'):
                continue
            filepath = os.path.join(cat_dir, filename)
            note = _load_note(filepath, category)
            if note is not None:
                notes.append(note)
    return notes


def _load_note(filepath, category):
    """Завантажити одну нотатку з .md-файлу."""
    try:
        post = frontmatter.load(filepath, encoding='utf-8')
        return {
            'title': post.get('title', ''),
            'created': str(post.get('created', '')),
            'updated': str(post.get('updated', '')),
            'type': post.get('type', 'note'),
            'status': post.get('status', 'inbox'),
            'tags': post.get('tags') or [],
            'source': post.get('source', ''),
            'content': post.content,
            'category': category,
            'filepath': filepath,
            'filename': os.path.basename(filepath),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Пошук і фільтрація
# ---------------------------------------------------------------------------

def search(notes, query):
    """Регістронезалежний пошук підрядка в title, tags і тілі нотатки."""
    q = query.lower()
    results = []
    for n in notes:
        title = n['title'].lower()
        body = n['content'].lower()
        tags = ' '.join(n.get('tags') or []).lower()
        if q in title or q in body or q in tags:
            results.append(n)
    return results


def filter_by(notes, tag=None, category=None):
    """Фільтрувати нотатки за тегом та/або категорією."""
    result = notes
    if category:
        result = [n for n in result if n['category'] == category]
    if tag:
        result = [n for n in result if tag in (n.get('tags') or [])]
    return result


# ---------------------------------------------------------------------------
# Посилання [[…]]
# ---------------------------------------------------------------------------

def find_note_by_title(notes, title):
    """Знайти нотатку за title (без урахування регістру та зайвих пробілів)."""
    t = title.strip().casefold()
    for n in notes:
        if n['title'].strip().casefold() == t:
            return n
    return None


def extract_wiki_links(text):
    """Витягнути всі [[…]] посилання з тексту."""
    return re.findall(r'\[\[(.+?)\]\]', text)


def get_backlinks(notes, title):
    """Знайти всі нотатки, що посилаються на задану назву."""
    t = title.lower()
    result = []
    for n in notes:
        for link in extract_wiki_links(n['content']):
            if link.lower() == t:
                result.append(n)
                break
    return result


def resolve_links(html, notes):
    """Замінити [[Назва]] на HTML-посилання. Биті — червоним."""
    def _replace(match):
        link_title = match.group(1)
        target = find_note_by_title(notes, link_title)
        if target:
            cat = quote(target['category'], safe='')
            fname = quote(target['filename'], safe='')
            return (f'<a href="/note/{cat}/{fname}" '
                    f'class="wiki-link">{link_title}</a>')
        return f'<span class="broken-link">{link_title}</span>'

    return re.sub(r'\[\[(.+?)\]\]', _replace, html)


# ---------------------------------------------------------------------------
# Допоміжні
# ---------------------------------------------------------------------------

def get_all_tags(notes):
    """Отримати відсортований список усіх унікальних тегів."""
    tags = set()
    for n in notes:
        for t in (n.get('tags') or []):
            tags.add(t)
    return sorted(tags)


# ---------------------------------------------------------------------------
# Збереження
# ---------------------------------------------------------------------------

def save_note(title, content, tags, category, note_type, status,
              source='', notes_dir=None, filepath=None):
    """Зберегти нотатку на диск. Якщо filepath задано — оновити, інакше створити."""
    if notes_dir is None:
        notes_dir = NOTES_DIR

    now = datetime.now().astimezone().isoformat()

    if filepath and os.path.exists(filepath):
        # Оновлення існуючої
        post = frontmatter.load(filepath, encoding='utf-8')
        post['title'] = title
        post['updated'] = now
        post['tags'] = tags
        post['type'] = note_type
        post['status'] = status
        post['source'] = source
        post.content = content
    else:
        # Створення нової
        post = frontmatter.Post(content)
        post['title'] = title
        post['created'] = now
        post['updated'] = now
        post['type'] = note_type
        post['status'] = status
        post['tags'] = tags
        post['source'] = source

        cat_dir = os.path.join(notes_dir, category)
        os.makedirs(cat_dir, exist_ok=True)
        filepath = os.path.join(cat_dir, title + '.md')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))

    return filepath
