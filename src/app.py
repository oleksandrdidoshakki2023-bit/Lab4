"""
Flask-застосунок Second Brain.
Головна сторінка, перегляд нотатки, створення та редагування.
"""

import os
import sys

# Додаємо директорію файлу в sys.path для надійного імпорту notes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import markdown as md
from flask import Flask, render_template, request, redirect, url_for

from notes import (
    load_all_notes, search, filter_by,
    resolve_links, get_backlinks, get_all_tags, save_note,
    CATEGORIES,
)

# ---------------------------------------------------------------------------
# Ініціалізація
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_DIR = os.path.join(BASE_DIR, 'notes')

app = Flask(__name__)
app.config['NOTES_DIR'] = NOTES_DIR


# ---------------------------------------------------------------------------
# Маршрути
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Головна сторінка: список нотаток, пошук, фільтри."""
    notes_dir = app.config['NOTES_DIR']
    all_notes = load_all_notes(notes_dir)

    query = request.args.get('q', '').strip()
    tag = request.args.get('tag', '').strip()
    category = request.args.get('category', '').strip()

    filtered = all_notes
    if query:
        filtered = search(filtered, query)
    if tag or category:
        filtered = filter_by(filtered, tag=tag or None, category=category or None)

    all_tags = get_all_tags(all_notes)

    return render_template(
        'index.html',
        notes=filtered,
        query=query,
        current_tag=tag,
        current_category=category,
        categories=CATEGORIES,
        all_tags=all_tags,
        total=len(filtered),
    )


@app.route('/note/<category>/<filename>')
def view_note(category, filename):
    """Перегляд нотатки: рендер Markdown, [[посилання]], backlinks."""
    notes_dir = app.config['NOTES_DIR']
    all_notes = load_all_notes(notes_dir)

    filepath = os.path.join(notes_dir, category, filename)
    note = None
    for n in all_notes:
        if n['filepath'] == filepath:
            note = n
            break

    if note is None:
        return render_template('index.html', notes=[], query='',
                               current_tag='', current_category='',
                               categories=CATEGORIES, all_tags=[],
                               total=0, error='Нотатку не знайдено'), 404

    # Markdown → HTML → [[посилання]]
    html_content = md.markdown(note['content'], extensions=['extra'])
    html_content = resolve_links(html_content, all_notes)
    backlinks = get_backlinks(all_notes, note['title'])

    return render_template(
        'note.html',
        note=note,
        html_content=html_content,
        backlinks=backlinks,
    )


@app.route('/new', methods=['GET', 'POST'])
def new_note():
    """Створення нової нотатки (за замовчуванням — Inbox)."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        tags_str = request.form.get('tags', '').strip()
        note_type = request.form.get('type', 'note')
        status = 'inbox'
        source = request.form.get('source', '').strip()

        tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

        save_note(title, content, tags, 'Inbox', note_type, status,
                  source, notes_dir=app.config['NOTES_DIR'])
        return redirect(url_for('index'))

    return render_template('edit.html', note=None, categories=CATEGORIES)


@app.route('/edit/<category>/<filename>', methods=['GET', 'POST'])
def edit_note(category, filename):
    """Редагування існуючої нотатки."""
    notes_dir = app.config['NOTES_DIR']
    all_notes = load_all_notes(notes_dir)

    filepath = os.path.join(notes_dir, category, filename)
    note = None
    for n in all_notes:
        if n['filepath'] == filepath:
            note = n
            break

    if note is None:
        return 'Нотатку не знайдено', 404

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        tags_str = request.form.get('tags', '').strip()
        note_type = request.form.get('type', 'note')
        status = request.form.get('status', note['status'])
        source = request.form.get('source', '').strip()

        tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

        save_note(title, content, tags, category, note_type, status,
                  source, notes_dir=notes_dir, filepath=filepath)
        return redirect(url_for('view_note', category=category,
                                filename=filename))

    return render_template('edit.html', note=note, categories=CATEGORIES)


# ---------------------------------------------------------------------------
# Запуск
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
