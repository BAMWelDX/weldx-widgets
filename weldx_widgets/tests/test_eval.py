"""Test for WidgetEvaluateSinglePassWeld."""
from weldx import WeldxFile
from weldx.asdf.cli.welding_schema import single_pass_weld_example
from weldx_widgets.widget_evaluate import WidgetEvaluateSinglePassWeld


def test_evaluate():
    """Primitive test for exception safety."""
    buff, tree = single_pass_weld_example(None)
    wx = WeldxFile(buff)
    WidgetEvaluateSinglePassWeld(wx)
