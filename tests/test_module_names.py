"""拆分后的界面模块：所有用到的名字都必须能解析（`from ui_common import *` 不会导出下划线开头的名字，
漏掉的名字只有在对应对话框被打开时才会 NameError，这里提前静态检查）"""
import ast
import builtins
import importlib
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_PACKAGES = ("widgets", "dialogs", "tabs")


def ui_files():
    files = ["main.py"]
    for pkg in UI_PACKAGES:
        for name in sorted(os.listdir(os.path.join(ROOT, pkg))):
            if name.endswith(".py") and name != "__init__.py":
                files.append(f"{pkg}/{name}")
    return files


def undefined_names(path, exported):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    defined = set(exported) | set(dir(builtins)) | {"__file__", "__name__"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            defined.add(node.name)
        if isinstance(node, (ast.FunctionDef, ast.Lambda)):
            args = node.args
            for arg in args.args + args.kwonlyargs + args.posonlyargs:
                defined.add(arg.arg)
            for extra in (args.vararg, args.kwarg):
                if extra:
                    defined.add(extra.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name != "*":
                    defined.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            defined.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            defined.add(node.name)
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return sorted(used - defined)


@pytest.fixture(scope="module")
def exported_names(qapp):
    module = importlib.import_module("ui_common")
    # 与 `import *` 的语义一致：不含下划线开头的名字
    return {n for n in dir(module) if not n.startswith("_")}


@pytest.mark.parametrize("path", ui_files())
def test_no_undefined_names(path, exported_names):
    assert undefined_names(path, exported_names) == []


def test_all_ui_modules_import(qapp):
    for path in ui_files():
        importlib.import_module(path[:-3].replace("/", "."))
