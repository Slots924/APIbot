# src/core/actions/action_testing.py
import json
import unicodedata
import time
from pathlib import Path
from typing import Sequence, Any

# ===================== ПУБЛІЧНИЙ ВХІД =====================
def action_testing(ads, payload: Sequence[Any]) -> bool:
    """
    Викликається раннером як action_testing_action(self.ads, payload).
    payload -> [serial_numbers: list[int|str], comments_json_path: str]
    """
    print("[action_testing] ✅ Entry. Payload:", payload, flush=True)

    try:
        serial_numbers, comments_path = payload
    except Exception as e:
        print("[action_testing] ❌ Bad payload. Expected [serial_numbers, comments_json_path]. Error:", e, flush=True)
        return False

    try:
        ok = _test_comments_flow(ads, [serial_numbers, comments_path])
        print("[action_testing] ✅ Done with status:", ok, flush=True)
        return bool(ok)
    except Exception as e:
        print("[action_testing] ❌ Unhandled error:", e, flush=True)
        return False


# ===================== УТИЛІТИ =====================
def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", (text or "")).strip().lower()
    return " ".join(text.split())

def _parse_order(v) -> tuple:
    s = str(v).replace(",", ".")
    parts = [p for p in s.split(".") if p != ""]
    try:
        return tuple(int(p) for p in parts) if parts else (999999,)
    except ValueError:
        return (999999,)

def _is_reply(order_tuple: tuple) -> bool:
    return len(order_tuple) > 1

def _parent_order(order_tuple: tuple) -> tuple:
    return order_tuple[:-1]


# ===================== ФУНКЦІЯ SAFE-GET =====================
def _safe_get_gender(ads, serial_number: str, delay: float = 1.0, retries: int = 3):
    """
    Безпечне отримання статі з повторними спробами.
    Повертає 'Male' або 'Female', або None, якщо не вдалося.
    """
    for attempt in range(1, retries + 1):
        try:
            g = ads.get_profil_gender_by_serial_number(serial_number)
            print(f"[API] serial={serial_number} attempt={attempt}/{retries} → {g}", flush=True)
            if isinstance(g, str) and g in ("Male", "Female"):
                return g
        except Exception as e:
            print(f"[API] ⚠️ Exception for serial={serial_number}: {e}", flush=True)

        print(f"[API] ⏳ retrying in {delay}s...", flush=True)
        time.sleep(delay)

    print(f"[API] ❌ Не вдалося отримати стать після {retries} спроб для serial={serial_number}", flush=True)
    return None


# ===================== ТЕСТОВИЙ СЦЕНАРІЙ =====================
def _test_comments_flow(ads, args):
    """
    ads  -> має метод ads.get_profil_gender_by_serial_number(serial_number) -> 'Male'|'Female'
    args -> [serial_numbers: list[int|str], comments_json_path: str]
    JSON-файл:
    [
      {"order": "1",   "text": "Great post!",       "gender": "Female"},
      {"order": "2",   "text": "I totally agree!",  "gender": "Male"},
      {"order": "3",   "text": "Interesting idea!", "gender": "Female"},
      {"order": "3.1", "text": "Thanks!",           "gender": "Male"}
    ]
    """
    print("[flow] === Старт тестового сценарію ===", flush=True)

    serial_numbers, comments_path = args
    print(f"[flow] 📦 serial_numbers: {serial_numbers}", flush=True)
    print(f"[flow] 📄 comments_path: {comments_path}", flush=True)

    path = Path(str(comments_path))
    if not path.exists():
        print(f"[flow] ❌ Файл не знайдено: {path}", flush=True)
        return False

    try:
        comments = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[flow] ❌ Неможливо прочитати/розпарсити JSON: {e}", flush=True)
        return False

    if not isinstance(comments, list):
        print("[flow] ❌ JSON має бути списком коментарів.", flush=True)
        return False

    # Підготовка
    for c in comments:
        c["__order_tuple"] = _parse_order(c.get("order"))
        c["__norm_text"]   = _normalize_text(c.get("text", ""))

    by_order = {c["__order_tuple"]: c for c in comments}
    comments.sort(key=lambda x: x["__order_tuple"])

    remaining_serials = [str(s) for s in serial_numbers]
    failed_steps = []
    posted_orders = set()
    normalized_existing_on_page = set()

    print(f"[flow] 🔢 Кроків до виконання: {len(comments)}", flush=True)
    print("[flow] ▶ Починаю обробку по порядку…", flush=True)

    for item in comments:
        order_t   = item["__order_tuple"]
        order_str = ".".join(map(str, order_t))
        target_gender = (item.get("gender") or "").strip()
        target_text   = item.get("text", "")
        norm_target   = item["__norm_text"]

        print(f"\n[step #{order_str}] ➜ gender={target_gender} | text=«{target_text}»", flush=True)

        parent_snippet = None
        if _is_reply(order_t):
            p_order = _parent_order(order_t)
            parent_item = by_order.get(p_order)
            if not parent_item:
                print(f"[step #{order_str}] ❌ Нема батьківського коментаря для #{'.'.join(map(str, p_order))}.", flush=True)
                failed_steps.append(item)
                break
            parent_text = parent_item.get("text", "")
            parent_snippet = _normalize_text(parent_text)[:60]
            print(f"[step #{order_str}] 💬 Це REPLY до #{'.'.join(map(str, p_order))}. Уривок: «{parent_snippet}»", flush=True)

        picked_serial = None
        picked_gender = None
        print(f"[step #{order_str}] 🔎 Шукаю профіль статі '{target_gender}' у пулі: {remaining_serials}", flush=True)

        for sn in list(remaining_serials):
            g = _safe_get_gender(ads, sn, delay=1.0, retries=3)
            time.sleep(1.0)  # затримка між кожним запитом незалежно від результату

            if not g:
                print(f"[step #{order_str}] ⚠️ Не вдалося отримати стать для serial={sn}.", flush=True)
                continue

            if g == target_gender:
                picked_serial = sn
                picked_gender = g
                break

        if picked_serial is None:
            print(f"[step #{order_str}] ❌ Нема профілю статі '{target_gender}'. Завершую сценарій.", flush=True)
            failed_steps.append(item)
            break

        # Перевірка дубля (імітація)
        if norm_target in normalized_existing_on_page:
            print(f"[step #{order_str}] ⚪ Коментар уже існує → пропуск. (serial={picked_serial})", flush=True)
            posted_orders.add(tuple(order_t))
            remaining_serials.remove(picked_serial)
            continue

        # Імітація дії
        if parent_snippet is None:
            print(f"акаунт {picked_serial} - пише коментар: #{order_str} ({picked_gender}) {target_text}", flush=True)
        else:
            parent_ord_str = ".".join(map(str, _parent_order(order_t)))
            print(f"акаунт {picked_serial} - пише РЕПЛАЙ на #{parent_ord_str}: "
                  f"#{order_str} ({picked_gender}) {target_text}", flush=True)

        normalized_existing_on_page.add(norm_target)
        print(f"[step #{order_str}] ✅ Перевірка появи: успішно.", flush=True)

        if picked_serial in remaining_serials:
            remaining_serials.remove(picked_serial)
        posted_orders.add(tuple(order_t))
        print(f"[step #{order_str}] ✔ Готово. Залишок профілів: {remaining_serials}", flush=True)

    print("\n[flow] === ПІДСУМОК ===", flush=True)
    if failed_steps:
        for c in failed_steps:
            o = ".".join(map(str, _parse_order(c.get("order"))))
            print(f"[flow] ⛔ Не виконано: #{o} | gender={c.get('gender')} | text=«{c.get('text','')}»", flush=True)
        print("[flow] ❗ Завершено з помилками.", flush=True)
        return False
    else:
        print("[flow] ✅ Всі кроки виконані успішно.", flush=True)
        return True
