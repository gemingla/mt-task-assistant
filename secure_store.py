"""
敏感信息加密存储（API Key 等）

Windows 上使用 DPAPI（CryptProtectData）：密文与当前 Windows 用户绑定，
其他用户或其他电脑无法解密。通过 ctypes 调用，无需额外依赖。
非 Windows 平台退化为明文（加 plain: 前缀以便区分）。
"""

import base64
import sys

DPAPI_PREFIX = "dpapi:"
PLAIN_PREFIX = "plain:"
_ENTROPY = b"MT-Task-Assistant"  # 额外熵，避免其他程序直接用同一接口解出

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _DataBlob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32
    _CRYPTPROTECT_UI_FORBIDDEN = 0x01

    def _blob(data: bytes):
        buf = ctypes.create_string_buffer(data, len(data))
        return _DataBlob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf

    def _call(func, data: bytes) -> bytes:
        in_blob, _in_buf = _blob(data)
        entropy, _ent_buf = _blob(_ENTROPY)
        out_blob = _DataBlob()
        ok = func(ctypes.byref(in_blob), None, ctypes.byref(entropy), None, None,
                  _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(out_blob))
        if not ok:
            raise OSError(ctypes.GetLastError(), "DPAPI 调用失败")
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            _kernel32.LocalFree(out_blob.pbData)

    def _protect(data: bytes) -> bytes:
        return _call(lambda i, d, e, r, p, f, o: _crypt32.CryptProtectData(i, "MT Task Assistant", e, r, p, f, o), data)

    def _unprotect(data: bytes) -> bytes:
        return _call(lambda i, d, e, r, p, f, o: _crypt32.CryptUnprotectData(i, None, e, r, p, f, o), data)
else:
    _protect = _unprotect = None


def protect(secret: str) -> str:
    """加密字符串，返回可写入 JSON 的文本"""
    if not secret:
        return ""
    if _protect is None:
        return PLAIN_PREFIX + secret
    return DPAPI_PREFIX + base64.b64encode(_protect(secret.encode("utf-8"))).decode("ascii")


def unprotect(token: str) -> str:
    """解密 protect() 的结果；无法解密（如换了电脑/用户）时抛出 ValueError"""
    if not token:
        return ""
    if token.startswith(PLAIN_PREFIX):
        return token[len(PLAIN_PREFIX):]
    if token.startswith(DPAPI_PREFIX) and _unprotect is not None:
        try:
            return _unprotect(base64.b64decode(token[len(DPAPI_PREFIX):])).decode("utf-8")
        except Exception as e:
            raise ValueError("无法解密（可能来自其他电脑或 Windows 用户）") from e
    raise ValueError("未知的加密格式")
