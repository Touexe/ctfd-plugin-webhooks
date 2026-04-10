import pathlib
import sys
import types


PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_ALIAS = "ctfd_plugin_webhooks"

package = sys.modules.get(PACKAGE_ALIAS)
if package is None:
    package = types.ModuleType(PACKAGE_ALIAS)
    package.__path__ = [str(PLUGIN_ROOT)]
    sys.modules[PACKAGE_ALIAS] = package