"""
Тести для модуля notes.py.
Усі тести працюють на тимчасовій копії нотаток (tmp_path).
"""

import os
import pytest
from notes import (
    load_all_notes, search, filter_by, find_note_by_title,
    extract_wiki_links, get_backlinks, resolve_links,
    get_all_tags, save_note, CATEGORIES,
)


# ---------------------------------------------------------------------------
# Фікстури
# ---------------------------------------------------------------------------

SAMPLE_NOTE_A = """\
---
title: "Тестова нотатка А"
created: "2026-01-01T00:00:00+03:00"
updated: "2026-01-01T00:00:00+03:00"
type: note
status: active
tags:
  - python
  - тест
source: "тест"
---

Це тестова нотатка А. Вона посилається на [[Тестова нотатка Б]].
"""

SAMPLE_NOTE_B = """\
---
title: "Тестова нотатка Б"
created: "2026-01-02T00:00:00+03:00"
updated: "2026-01-02T00:00:00+03:00"
type: note
status: active
tags:
  - flask
  - тест
source: "тест"
---

Це тестова нотатка Б. Вона посилається на [[Тестова нотатка А]].
Також на [[Неіснуюча нотатка]].
"""

SAMPLE_NOTE_INBOX = """\
---
title: "Нова ідея"
created: "2026-01-03T00:00:00+03:00"
updated: "2026-01-03T00:00:00+03:00"
type: note
status: inbox
tags: []
source: ""
---

Щось нове, без тегів.
"""


@pytest.fixture
def notes_dir(tmp_path):
    """Створити тимчасову структуру нотаток."""
    for cat in CATEGORIES:
        (tmp_path / cat).mkdir()

    (tmp_path / 'Resources' / 'Тестова нотатка А.md').write_text(
        SAMPLE_NOTE_A, encoding='utf-8')
    (tmp_path / 'Resources' / 'Тестова нотатка Б.md').write_text(
        SAMPLE_NOTE_B, encoding='utf-8')
    (tmp_path / 'Inbox' / 'Нова ідея.md').write_text(
        SAMPLE_NOTE_INBOX, encoding='utf-8')
    return tmp_path


# ---------------------------------------------------------------------------
# Тести: парсинг frontmatter
# ---------------------------------------------------------------------------

def test_load_all_notes(notes_dir):
    """Завантаження нотаток повертає правильну кількість."""
    notes = load_all_notes(str(notes_dir))
    assert len(notes) == 3


def test_frontmatter_fields(notes_dir):
    """Парсинг frontmatter повертає всі поля."""
    notes = load_all_notes(str(notes_dir))
    note_a = find_note_by_title(notes, 'Тестова нотатка А')
    assert note_a is not None
    assert note_a['title'] == 'Тестова нотатка А'
    assert note_a['type'] == 'note'
    assert note_a['status'] == 'active'
    assert 'python' in note_a['tags']
    assert note_a['category'] == 'Resources'


# ---------------------------------------------------------------------------
# Тести: пошук
# ---------------------------------------------------------------------------

def test_search_by_title(notes_dir):
    """Пошук за словом у назві (регістронезалежний)."""
    notes = load_all_notes(str(notes_dir))
    results = search(notes, 'ТЕСТОВА')
    assert len(results) == 2


def test_search_by_content(notes_dir):
    """Пошук за словом у тілі нотатки."""
    notes = load_all_notes(str(notes_dir))
    results = search(notes, 'нова ідея')
    # Слово "нове" є в тілі нотатки "Нова ідея" (title), а "ідея" теж
    # Шукаємо "щось" — воно є тільки в нотатці Inbox
    results2 = search(notes, 'щось')
    assert len(results2) == 1
    assert results2[0]['title'] == 'Нова ідея'


def test_search_by_tag(notes_dir):
    """Пошук за словом у тегах."""
    notes = load_all_notes(str(notes_dir))
    results = search(notes, 'flask')
    assert len(results) == 1
    assert results[0]['title'] == 'Тестова нотатка Б'


def test_search_empty_result(notes_dir):
    """Порожній результат пошуку."""
    notes = load_all_notes(str(notes_dir))
    results = search(notes, 'абракадабра')
    assert len(results) == 0


def test_search_case_insensitive(notes_dir):
    """Пошук регістронезалежний."""
    notes = load_all_notes(str(notes_dir))
    results_lower = search(notes, 'python')
    results_upper = search(notes, 'PYTHON')
    assert len(results_lower) == len(results_upper)


# ---------------------------------------------------------------------------
# Тести: фільтрація
# ---------------------------------------------------------------------------

def test_filter_by_tag(notes_dir):
    """Фільтр за тегом."""
    notes = load_all_notes(str(notes_dir))
    results = filter_by(notes, tag='python')
    assert len(results) == 1
    assert results[0]['title'] == 'Тестова нотатка А'


def test_filter_by_category(notes_dir):
    """Фільтр за категорією."""
    notes = load_all_notes(str(notes_dir))
    results = filter_by(notes, category='Inbox')
    assert len(results) == 1
    assert results[0]['title'] == 'Нова ідея'


def test_filter_by_tag_and_category(notes_dir):
    """Комбінований фільтр: тег + категорія."""
    notes = load_all_notes(str(notes_dir))
    results = filter_by(notes, tag='тест', category='Resources')
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Тести: посилання [[…]]
# ---------------------------------------------------------------------------

def test_extract_wiki_links():
    """Витягування [[…]] посилань з тексту."""
    text = 'Дивись [[Нотатка 1]] і [[Нотатка 2]].'
    links = extract_wiki_links(text)
    assert links == ['Нотатка 1', 'Нотатка 2']


def test_resolve_links_valid(notes_dir):
    """Резолв валідного посилання — створює <a> з класом wiki-link."""
    notes = load_all_notes(str(notes_dir))
    html = resolve_links('Дивись [[Тестова нотатка А]].', notes)
    assert 'class="wiki-link"' in html
    assert 'Тестова нотатка А' in html
    assert '<a href=' in html


def test_resolve_links_broken(notes_dir):
    """Резолв битого посилання — створює <span> з класом broken-link."""
    notes = load_all_notes(str(notes_dir))
    html = resolve_links('Дивись [[Неіснуюча]].', notes)
    assert 'class="broken-link"' in html
    assert 'Неіснуюча' in html


def test_find_note_by_title_case_insensitive(notes_dir):
    """Пошук за title ігнорує регістр."""
    notes = load_all_notes(str(notes_dir))
    note = find_note_by_title(notes, 'тестова нотатка а')
    assert note is not None
    assert note['title'] == 'Тестова нотатка А'


# ---------------------------------------------------------------------------
# Тести: backlinks
# ---------------------------------------------------------------------------

def test_backlinks(notes_dir):
    """Нотатка А посилається на Б → Б має backlink на А."""
    notes = load_all_notes(str(notes_dir))
    backlinks = get_backlinks(notes, 'Тестова нотатка Б')
    titles = [n['title'] for n in backlinks]
    assert 'Тестова нотатка А' in titles


def test_backlinks_bidirectional(notes_dir):
    """Обидві нотатки посилаються одна на одну."""
    notes = load_all_notes(str(notes_dir))
    bl_a = get_backlinks(notes, 'Тестова нотатка А')
    bl_b = get_backlinks(notes, 'Тестова нотатка Б')
    assert any(n['title'] == 'Тестова нотатка Б' for n in bl_a)
    assert any(n['title'] == 'Тестова нотатка А' for n in bl_b)


# ---------------------------------------------------------------------------
# Тести: збереження
# ---------------------------------------------------------------------------

def test_save_new_note(notes_dir):
    """Створення нотатки зберігає файл і він читається після «перезапуску»."""
    filepath = save_note(
        title='Нова тестова',
        content='Текст нової нотатки.',
        tags=['тест', 'нова'],
        category='Inbox',
        note_type='note',
        status='inbox',
        source='тест',
        notes_dir=str(notes_dir),
    )

    assert os.path.exists(filepath)

    # «Перезапуск» — новий виклик завантаження
    notes = load_all_notes(str(notes_dir))
    new_note = find_note_by_title(notes, 'Нова тестова')
    assert new_note is not None
    assert new_note['title'] == 'Нова тестова'
    assert 'тест' in new_note['tags']
    assert 'Текст нової нотатки.' in new_note['content']


def test_save_updates_updated_field(notes_dir):
    """Оновлення нотатки змінює поле updated."""
    notes = load_all_notes(str(notes_dir))
    note_a = find_note_by_title(notes, 'Тестова нотатка А')
    old_updated = note_a['updated']

    save_note(
        title='Тестова нотатка А',
        content='Оновлений текст.',
        tags=['python'],
        category='Resources',
        note_type='note',
        status='active',
        source='тест',
        notes_dir=str(notes_dir),
        filepath=note_a['filepath'],
    )

    notes2 = load_all_notes(str(notes_dir))
    note_a2 = find_note_by_title(notes2, 'Тестова нотатка А')
    assert note_a2['updated'] != old_updated
    assert 'Оновлений текст.' in note_a2['content']


# ---------------------------------------------------------------------------
# Тести: допоміжні
# ---------------------------------------------------------------------------

def test_get_all_tags(notes_dir):
    """Отримання всіх унікальних тегів."""
    notes = load_all_notes(str(notes_dir))
    tags = get_all_tags(notes)
    assert 'python' in tags
    assert 'flask' in tags
    assert 'тест' in tags
