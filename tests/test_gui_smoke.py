"""Construction smoke tests for all four GUIs.

Nothing tested these before the RFIGen_1/RFIGen_2 merge, so a broken widget
callback could rot silently. Each app is built against a withdrawn Tk root:
no window is shown, but every widget and command binding is exercised.
"""

import pytest

tk = pytest.importorskip("tkinter")


@pytest.fixture()
def root():
    try:
        instance = tk.Tk()
    except tk.TclError:  # pragma: no cover - headless CI
        pytest.skip("no display available for tkinter")
    instance.withdraw()
    yield instance
    instance.destroy()


def test_core_gui_builds(root):
    from rfigen.gui import RFIGenApp

    app = RFIGenApp(root)
    assert app.dataset is not None, "core GUI generates a dataset on construction"


def test_legacy_gui_builds(root):
    from rfigen.legacy.gui import RFIGeneratorGUI

    app = RFIGeneratorGUI(root)
    assert app.config != {}, "legacy GUI loads a default config on construction"


def test_mp3000a_gui_builds(root):
    from rfigen.legacy.mp3000a_gui import MP3000App

    app = MP3000App(root)
    assert app.clean_df is None
    assert app.rfi_source_type.get() == "5G"


def test_signal_gui_builds(root):
    from rfigen.legacy.signal_gui import SignalApp

    app = SignalApp(root)
    assert app.root is root
