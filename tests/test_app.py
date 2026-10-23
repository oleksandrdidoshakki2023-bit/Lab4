"""
Тести для Flask-застосунку (app.py).
Використовують Flask test client і тимчасові нотатки (tmp_path).
"""

import os
import pytest
from app import app
from notes import CATEGORIES


# ---------------------------------------------------------------------------
# Фікстури
# ---------------------------------------------------------------------------

SAMPLE_NOTE = """\
---
title: "Тест Flask"
created: "2026-01-01T00:00:00+03:00"
updated: "2026-01-01T00:00:00+03:00"
type: note
status: active
tags:
  - flask
  - тест
source: "тест"
---

Тестова нотатка для Flask. Посилається на [[Неіснуюча]].
"""

SAMPLE_NOTE_2 = """\
---
title: "Друга нотатка"
created: "2026-01-02T00:00:00+03:00"
updated: "2026-01-02T00:00:00+03:00"
type: note
status: active
tags:
  - python
source: "тест"
---

Друга нотатка. Посилається на [[Тест Flask]].
"""


@pytest.fixture
def client(tmp_path):
    """Flask test client з тимчасовими нотатками."""
    for cat in CATEGORIES:
        (tmp_path / cat).mkdir()

    (tmp_path / 'Resources' / 'Тест Flask.md').write_text(
        SAMPLE_NOTE, encoding='utf-8')
    (tmp_path / 'Inbox' / 'Друга нотатка.md').write_text(
        SAMPLE_NOTE_2, encoding='utf-8')

    app.config['TESTING'] = True
    app.config['NOTES_DIR'] = str(tmp_path)

    with app.test_client() as client:
        yield client


# ---------------------------------------------------------------------------
# Тести: головна сторінка
# ---------------------------------------------------------------------------

def test_index_returns_200(client):
    """Головна сторінка повертає 200."""
    response = client.get('/')
    assert response.status_code == 200


def test_index_contains_notes(client):
    """Головна сторінка містить назви нотаток."""
    response = client.get('/')
    data = response.data.decode('utf-8')
    assert 'Тест Flask' in data
    assert 'Друга нотатка' in data


def test_index_search(client):
    """Пошук на головній сторінці працює."""
    response = client.get('/?q=flask')
    data = response.data.decode('utf-8')
    assert 'Тест Flask' in data


def test_index_search_empty(client):
    """Порожній результат пошуку показує повідомлення."""
    response = client.get('/?q=абракадабра')
    data = response.data.decode('utf-8')
    assert 'Нічого не знайдено' in data


def test_index_filter_by_category(client):
    """Фільтр за категорією працює."""
    response = client.get('/?category=Inbox')
    data = response.data.decode('utf-8')
    assert 'Друга нотатка' in data


def test_index_filter_by_tag(client):
    """Фільтр за тегом працює."""
    response = client.get('/?tag=python')
    data = response.data.decode('utf-8')
    assert 'Друга нотатка' in data


# ---------------------------------------------------------------------------
# Тести: сторінка нотатки
# ---------------------------------------------------------------------------

def test_note_page_returns_200(client):
    """Сторінка нотатки повертає 200."""
    response = client.get('/note/Resources/%D0%A2%D0%B5%D1%81%D1%82%20Flask.md')
    assert response.status_code == 200


def test_note_page_renders_content(client):
    """Сторінка нотатки рендерить вміст."""
    response = client.get('/note/Resources/%D0%A2%D0%B5%D1%81%D1%82%20Flask.md')
    data = response.data.decode('utf-8')
    assert 'Тестова нотатка для Flask' in data


def test_note_page_broken_link(client):
    """Бите посилання відображається з класом broken-link."""
    response = client.get('/note/Resources/%D0%A2%D0%B5%D1%81%D1%82%20Flask.md')
    data = response.data.decode('utf-8')
    assert 'broken-link' in data


def test_note_page_valid_link(client):
    """Валідне посилання відображається з класом wiki-link."""
    response = client.get('/note/Inbox/%D0%94%D1%80%D1%83%D0%B3%D0%B0%20%D0%BD%D0%BE%D1%82%D0%B0%D1%82%D0%BA%D0%B0.md')
    data = response.data.decode('utf-8')
    assert 'wiki-link' in data


def test_note_page_backlinks(client):
    """Сторінка нотатки показує backlinks."""
    response = client.get('/note/Resources/%D0%A2%D0%B5%D1%81%D1%82%20Flask.md')
    data = response.data.decode('utf-8')
    assert 'Друга нотатка' in data


def test_note_page_404(client):
    """Неіснуюча нотатка повертає 404."""
    response = client.get('/note/Resources/nonexistent.md')
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Тести: створення нотатки
# ---------------------------------------------------------------------------

def test_new_note_get(client):
    """Форма створення нотатки повертає 200."""
    response = client.get('/new')
    assert response.status_code == 200


def test_new_note_post(client):
    """Створення нотатки через POST і редірект."""
    response = client.post('/new', data={
        'title': 'Нотатка з тесту',
        'content': 'Створена в тесті.',
        'tags': 'тест, автоматичний',
        'type': 'note',
        'source': 'pytest',
    }, follow_redirects=True)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert 'Нотатка з тесту' in data


# ---------------------------------------------------------------------------
# Тести: редагування нотатки
# ---------------------------------------------------------------------------

def test_edit_note_get(client):
    """Форма редагування повертає 200."""
    response = client.get('/edit/Resources/%D0%A2%D0%B5%D1%81%D1%82%20Flask.md')
    assert response.status_code == 200


def test_edit_note_post(client):
    """Редагування нотатки через POST."""
    response = client.post(
        '/edit/Resources/%D0%A2%D0%B5%D1%81%D1%82%20Flask.md',
        data={
            'title': 'Тест Flask',
            'content': 'Оновлений вміст.',
            'tags': 'flask, оновлено',
            'type': 'note',
            'status': 'active',
            'source': 'pytest',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert 'Оновлений вміст' in data
