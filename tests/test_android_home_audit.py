import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/android-home-audit.py"
SPEC = importlib.util.spec_from_file_location("android_home_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_parse_widget_and_hotseat_order():
    xml = """<hierarchy><node resource-id="com.google.android.apps.nexuslauncher:id/workspace">
      <node class="com.android.launcher3.widget.LauncherAppWidgetHostView" package="com.google.android.apps.nexuslauncher" content-desc="Weather" bounds="[0,0][500,500]">
        <node package="com.example.weather" text="Tokyo" content-desc="" />
      </node>
      <node text="Camera" content-desc="Camera" clickable="true" long-clickable="true" bounds="[800,1500][1000,1700]" />
      <node resource-id="com.google.android.apps.nexuslauncher:id/hotseat">
        <node text="Chrome" content-desc="Chrome" clickable="true" long-clickable="true" bounds="[500,1900][700,2100]" />
        <node text="Music" content-desc="Predicted app: Music" clickable="true" long-clickable="true" bounds="[250,1900][450,2100]" />
        <node text="" content-desc="Folder: Messages, 2 items" clickable="true" long-clickable="false" bounds="[0,1900][200,2100]" />
      </node>
    </node></hierarchy>"""
    page = MODULE.parse_page(xml, 1)
    assert page["widgets"][0]["package"] == "com.example.weather"
    assert page["widgets"][0]["visible_labels"] == ["Weather", "Tokyo"]
    assert page["workspace_items"][0]["name"] == "Camera"
    assert [item["name"] for item in page["hotseat"]] == ["Messages", "Music", "Chrome"]
    assert page["hotseat"][1]["type"] == "predicted_app"
