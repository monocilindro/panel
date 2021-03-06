import os
import json
import glob

from io import StringIO

from panel import Row
from panel.io.notebook import ipywidget
from panel.config import config
from panel.io.embed import embed_state
from panel.pane import Str
from panel.widgets import Select, FloatSlider, Checkbox

from .util import jb_available


def test_embed_discrete(document, comm):
    select = Select(options=['A', 'B', 'C'])
    string = Str()
    select.link(string, value='object')
    panel = Row(select, string)
    with config.set(embed=True):
        model = panel.get_root(document, comm)
    embed_state(panel, model, document)
    _, state = document.roots
    assert set(state.state) == {'A', 'B', 'C'}
    for k, v in state.state.items():
        content = json.loads(v['content'])
        assert 'events' in content
        events = content['events']
        assert len(events) == 1
        event = events[0]
        assert event['kind'] == 'ModelChanged'
        assert event['attr'] == 'text'
        assert event['model'] == model.children[1].ref
        assert event['new'] == '&lt;pre&gt;%s&lt;/pre&gt;' % k


def test_embed_continuous(document, comm):
    select = FloatSlider(start=0, end=10)
    string = Str()
    select.link(string, value='object')
    panel = Row(select, string)
    with config.set(embed=True):
        model = panel.get_root(document, comm)
    embed_state(panel, model, document)
    _, state = document.roots
    assert set(state.state) == {0, 1, 2}
    values = [0, 5, 10]
    for k, v in state.state.items():
        content = json.loads(v['content'])
        assert 'events' in content
        events = content['events']
        assert len(events) == 1
        event = events[0]
        assert event['kind'] == 'ModelChanged'
        assert event['attr'] == 'text'
        assert event['model'] == model.children[1].ref
        assert event['new'] == '&lt;pre&gt;%.1f&lt;/pre&gt;' % values[k]


def test_embed_checkbox(document, comm):
    checkbox = Checkbox()
    string = Str()
    checkbox.link(string, value='object')
    panel = Row(checkbox, string)
    with config.set(embed=True):
        model = panel.get_root(document, comm)
    embed_state(panel, model, document)
    _, state = document.roots
    assert set(state.state) == {'false', 'true'}
    for k, v in state.state.items():
        content = json.loads(v['content'])
        assert 'events' in content
        events = content['events']
        assert len(events) == 1
        event = events[0]
        assert event['kind'] == 'ModelChanged'
        assert event['attr'] == 'text'
        assert event['model'] == model.children[1].ref
        assert event['new'] == '&lt;pre&gt;%s&lt;/pre&gt;' % k.title()


def test_save_embed_bytesio():
    checkbox = Checkbox()
    string = Str()
    checkbox.link(string, value='object')
    panel = Row(checkbox, string)
    stringio = StringIO()
    panel.save(stringio, embed=True)
    stringio.seek(0)
    utf = stringio.read()
    print(utf)
    assert "&amp;lt;pre&amp;gt;False&amp;lt;/pre&amp;gt;" in utf
    assert "&amp;lt;pre&amp;gt;True&amp;lt;/pre&amp;gt;" in utf


def test_save_embed(tmpdir):
    checkbox = Checkbox()
    string = Str()
    checkbox.link(string, value='object')
    panel = Row(checkbox, string)
    filename = os.path.join(str(tmpdir), 'test.html')
    panel.save(filename, embed=True)
    assert os.path.isfile(filename)


def test_save_embed_json(tmpdir):
    checkbox = Checkbox()
    string = Str()
    checkbox.link(string, value='object')
    panel = Row(checkbox, string)
    filename = os.path.join(str(tmpdir), 'test.html')
    panel.save(filename, embed=True, embed_json=True,
               save_path=str(tmpdir))
    assert os.path.isfile(filename)
    paths = glob.glob(os.path.join(str(tmpdir), '*'))
    paths.remove(filename)
    assert len(paths) == 1
    json_files = sorted(glob.glob(os.path.join(paths[0], '*.json')))
    assert len(json_files) == 2

    for jf, v in zip(json_files, ('False', 'True')):
        with open(jf) as f:
            state = json.load(f)
        assert 'content' in state
        assert 'events' in state['content']
        events = json.loads(state['content'])['events']
        assert len(events) == 1
        event = events[0]
        assert event['kind'] == 'ModelChanged'
        assert event['attr'] == 'text'
        assert event['new'] == '&lt;pre&gt;%s&lt;/pre&gt;' % v


@jb_available
def test_ipywidget():
    pane = Str('A')
    widget = ipywidget(pane)

    assert widget._view_count == 0
    assert len(pane._models) == 1

    init_id = list(pane._models)[0]

    widget._view_count = 1

    assert widget._view_count == 1
    assert init_id in pane._models

    widget._view_count = 0

    assert len(pane._models) == 0

    widget._view_count = 1

    assert len(pane._models) == 1
    prev_id = list(pane._models)[0]

    widget.notify_change({'new': 1, 'old': 1, 'name': '_view_count',
                          'type': 'change', 'model': widget})
    assert prev_id in pane._models
    assert len(pane._models) == 1

    widget._view_count = 2

    assert prev_id in pane._models
    assert len(pane._models) == 1
