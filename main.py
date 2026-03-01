from __future__ import annotations

import json
import os
import random
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.spinner import SpinnerOption

# Armenian font so letters display correctly (not boxes)
def _register_armenian_font():
    root = os.path.dirname(__file__)
    font_path = os.path.join(root, "assets", "fonts", "NotoSansArmenian-Regular.ttf")
    if os.path.exists(font_path):
        try:
            LabelBase.register(name="Armenian", fn_regular=font_path)
            return "Armenian"
        except Exception:
            pass
    return None

FONT_ARMENIAN = _register_armenian_font()


class ArmenianSpinnerOption(SpinnerOption):
    """Spinner dropdown option with Armenian font so Ա, Բ, Գ render (no squares)."""
    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_ARMENIAN or "Roboto")
        super().__init__(**kwargs)


# Armenian numerals 1–15 to avoid digit rendering as squares
_ARM_NUMS = "ԱԲԳԴԵԶԷԸԹԺԻԼԽԾԿ"

def _to_arm(n: int) -> str:
    if 1 <= n <= 15:
        return _ARM_NUMS[n - 1]
    return str(n)

def _from_arm(s: str) -> int:
    if len(s) == 1 and s in _ARM_NUMS:
        return _ARM_NUMS.index(s) + 1
    try:
        return int(s)
    except ValueError:
        return 1

# Strip adjective prefixes so we show only name/place (no "կենտրոնական Իջևան", just "Իջևան")
_ARMENIAN_ADJECTIVES = {
    "կենտրոնական", "գեղեցիկ", "հին", "նոր", "աֆրիկյան", "ասիական", "պատմական",
    "լեռնային", "զբոսաշրջային", "ծովափնյա", "գիշերային", "արևոտ", "անձրևոտ",
    "մշակութային", "ապակյա", "պլաստիկ", "փայլուն", "դասական", "ժամանակակից", "թանկ",
    "բանկային", "միկրոալիքային", "Հայ", "աշխարհի", "հայտնի", "երաժիշտ", "երգիչ", "դերասան",
    "մոդել", "ֆուտբոլիստ", "գիտնական", "բլոգեր", "ռեժիսոր", "գործարար", "քաղաքական",
    "շախմատիստ", "եղջյուրավոր",
}
_TWO_WORD_PREFIXES = {"Հայ հայտնի", "աշխարհի հայտնի"}

def _word_without_adjective(word: str) -> str:
    if not word or " " not in word:
        return word.strip()
    parts = word.split()
    while len(parts) >= 2 and parts[0] in _ARMENIAN_ADJECTIVES:
        parts.pop(0)
    while len(parts) >= 3 and (parts[0] + " " + parts[1]) in _TWO_WORD_PREFIXES:
        parts.pop(0)
        parts.pop(0)
    while len(parts) >= 2 and parts[0] in _ARMENIAN_ADJECTIVES:
        parts.pop(0)
    return " ".join(parts).strip() if parts else word.strip()

# Blur in background so UI does not lag
def _do_blur(menu_path: str, out_path: str, radius: int = 14) -> bool:
    try:
        from PIL import Image, ImageFilter
    except Exception:
        return False
    if not os.path.exists(menu_path) or os.path.exists(out_path):
        return os.path.exists(out_path)
    try:
        img = Image.open(menu_path).convert("RGB")
        img.filter(ImageFilter.GaussianBlur(radius=radius)).save(out_path, "JPEG", quality=85)
        return True
    except Exception:
        return False

@dataclass
class GameConfig:
    category: str = "Բոլորը"
    players: int = 4
    impostors: int = 1
    round_minutes: int = 2
    round_seconds: int = 120

@dataclass
class GameState:
    word: str = ""
    impostor_ids: List[int] = field(default_factory=list)  # 1-based
    reveal_index: int = 1  # current player to reveal

KV = r"""
#:kivy 2.3.0

<RedButton@Button>:
    background_normal: ""
    background_down: ""
    background_color: (0.85, 0.12, 0.12, 1)
    color: (1, 1, 1, 1)
    font_name: app.font_armenian if app.font_armenian else "Roboto"
    font_size: "20sp"
    bold: True
    size_hint: (None, None)
    size: ("280dp", "54dp")
    pos_hint: {"center_x": 0.5}

<GhostButton@Button>:
    background_normal: ""
    background_down: ""
    background_color: (0, 0, 0, 0.35)
    color: (1, 1, 1, 1)
    font_name: app.font_armenian if app.font_armenian else "Roboto"
    font_size: "18sp"
    bold: True
    size_hint: (None, None)
    size: ("280dp", "50dp")
    pos_hint: {"center_x": 0.5}

<TitleLabel@Label>:
    color: (1, 1, 1, 1)
    font_name: app.font_armenian if app.font_armenian else "Roboto"
    font_size: "28sp"
    bold: True
    size_hint_y: None
    height: self.texture_size[1] + dp(10)
    halign: "center"
    text_size: self.size

<SubLabel@Label>:
    color: (1, 1, 1, 1)
    font_name: app.font_armenian if app.font_armenian else "Roboto"
    font_size: "18sp"
    size_hint_y: None
    height: self.texture_size[1] + dp(6)
    halign: "center"
    text_size: self.size

<BGImage@FloatLayout>:
    bg_source: ""
    canvas.before:
        Rectangle:
            pos: self.pos
            size: self.size
            source: root.bg_source
        Color:
            rgba: (0, 0, 0, 0.55)
        Rectangle:
            pos: self.pos
            size: self.size

<MenuScreen>:
    name: "menu"
    BGImage:
        bg_source: app.menu_image
        FloatLayout:
            BoxLayout:
                orientation: "vertical"
                size_hint: (0.9, 0.85)
                pos_hint: {"center_x": 0.5, "center_y": 0.78}
                padding: "20dp"
                spacing: "14dp"
                Image:
                    source: app.logo_image
                    allow_stretch: True
                    keep_ratio: True
                    size_hint_y: None
                    height: 0 if not app.logo_image else dp(170)
                Widget:
                    size_hint_y: 1
                RedButton:
                    text: "Սկսել խաղը"
                    on_release: app.go_setup()
                Widget:
                    size_hint_y: None
                    height: "10dp"

<CategoryScreen>:
    name: "categories"
    BGImage:
        bg_source: app.menu_blur_image
        FloatLayout:
            BoxLayout:
                orientation: "vertical"
                size_hint: (0.9, 0.85)
                pos_hint: {"center_x": 0.5, "center_y": 0.52}
                padding: "20dp"
                spacing: "8dp"
                TitleLabel:
                    text: "Ընտրիր կատեգորիան"
                    halign: "center"
                    text_size: self.size
                SubLabel:
                    text: "Բառերը հայերեն են։"
                    halign: "center"
                    text_size: self.size
                Widget:
                    size_hint_y: None
                    height: "6dp"
                RedButton:
                    text: "Հայ հայտնիներ"
                    on_release: app.select_category(self.text)
                RedButton:
                    text: "Համաշխարհային հայտնիներ"
                    on_release: app.select_category(self.text)
                RedButton:
                    text: "Կենդանիներ"
                    on_release: app.select_category(self.text)
                RedButton:
                    text: "Առարկաներ"
                    on_release: app.select_category(self.text)
                RedButton:
                    text: "Վայրեր"
                    on_release: app.select_category(self.text)
                RedButton:
                    text: "Բոլորը"
                    on_release: app.select_category(self.text)
                Widget:
                    size_hint_y: 1
                GhostButton:
                    text: "Հետ"
                    on_release: app.sm.current = "menu"

<SetupScreen>:
    name: "setup"
    BGImage:
        bg_source: app.menu_blur_image
        FloatLayout:
            BoxLayout:
                orientation: "vertical"
                size_hint: (0.9, 0.85)
                pos_hint: {"center_x": 0.5, "center_y": 0.65}
                padding: "20dp"
                spacing: "10dp"

                TitleLabel:
                    text: "Կարգավորումներ"
                    halign: "center"
                    text_size: self.size

                BoxLayout:
                    size_hint_y: None
                    height: "62dp"
                    spacing: "10dp"
                    Label:
                        text: "Մասնակիցներ"
                        color: (1,1,1,1)
                        font_name: app.font_armenian if app.font_armenian else "Roboto"
                        font_size: "18sp"
                        halign: "center"
                        text_size: self.size
                    Spinner:
                        id: sp_players
                        font_name: "Roboto"
                        text: str(app.cfg.players)
                        values: [str(x) for x in range(3, 16)]
                        on_text: app.set_players(int(self.text) if self.text.isdigit() else 4)

                BoxLayout:
                    size_hint_y: None
                    height: "62dp"
                    spacing: "10dp"
                    Label:
                        text: "Իմպոստոր-ներ"
                        color: (1,1,1,1)
                        font_name: app.font_armenian if app.font_armenian else "Roboto"
                        font_size: "18sp"
                        halign: "center"
                        text_size: self.size
                    Spinner:
                        id: sp_impostors
                        font_name: "Roboto"
                        text: str(app.cfg.impostors)
                        values: [str(x) for x in range(1, 6)]
                        on_text: app.set_impostors(int(self.text) if self.text.isdigit() else 1)

                BoxLayout:
                    size_hint_y: None
                    height: "62dp"
                    spacing: "10dp"
                    Label:
                        text: "Թայմեր րոպե"
                        color: (1,1,1,1)
                        font_name: app.font_armenian if app.font_armenian else "Roboto"
                        font_size: "18sp"
                        halign: "center"
                        text_size: self.size
                    Spinner:
                        id: sp_timer
                        font_name: "Roboto"
                        text: str(app.cfg.round_minutes)
                        values: ["1","2","3","4","5","7","10"]
                        on_text: app.set_timer_minutes(int(self.text) if self.text.isdigit() else 2)

                Widget:
                    size_hint_y: 1

                RedButton:
                    text: "Շարունակել"
                    on_release: app.go_categories()

<RevealScreen>:
    name: "reveal"
    BGImage:
        bg_source: app.menu_blur_image
        FloatLayout:
            BoxLayout:
                orientation: "vertical"
                size_hint: (0.9, 0.85)
                pos_hint: {"center_x": 0.5, "center_y": 0.78}
                padding: "20dp"
                spacing: "12dp"

                TitleLabel:
                    id: reveal_title
                    text: "Խաղացող Ա"
                    halign: "center"
                    text_size: self.size

                SubLabel:
                    text: "Սեղմիր՝ ցույց տալու համար"
                    halign: "center"
                    text_size: self.size

                Widget:
                    size_hint_y: None
                    height: "10dp"

                Label:
                    id: secret_label
                    text: ""
                    color: (1,1,1,1)
                    font_name: app.font_armenian if app.font_armenian else "Roboto"
                    font_size: "30sp"
                    bold: True
                    halign: "center"
                    valign: "middle"
                    text_size: self.size

                Widget:
                    size_hint_y: 1

                RedButton:
                    id: btn_toggle
                    text: "Ցույց տալ"
                    on_release: app.toggle_secret()

                GhostButton:
                    text: "Վերադառնալ"
                    on_release: app.reset_to_setup()

<RoundScreen>:
    name: "round"
    BGImage:
        bg_source: app.menu_blur_image
        FloatLayout:
            BoxLayout:
                orientation: "vertical"
                size_hint: (0.9, 0.85)
                pos_hint: {"center_x": 0.5, "center_y": 0.78}
                padding: "20dp"
                spacing: "12dp"

                TitleLabel:
                    text: "Ռաունդ"
                    halign: "center"
                    text_size: self.size

                SubLabel:
                    text: "Խոսեք հերթով՝ 1-2 բառով հուշում/ասոցիացիա"
                    halign: "center"
                    text_size: self.size

                Label:
                    id: timer_label
                    text: app.timer_display
                    color: (1,1,1,1)
                    font_name: "Roboto"
                    font_size: "48sp"
                    bold: True
                    halign: "center"
                    valign: "middle"
                    text_size: self.size

                Widget:
                    size_hint_y: 1

                RedButton:
                    text: "Քվեարկություն"
                    on_release: app.go_vote()

                GhostButton:
                    text: "Վերջացնել ռաունդը"
                    on_release: app.finish_round()

<VoteScreen>:
    name: "vote"
    BGImage:
        bg_source: app.menu_blur_image
        FloatLayout:
            BoxLayout:
                orientation: "vertical"
                size_hint: (0.9, 0.85)
                pos_hint: {"center_x": 0.5, "center_y": 0.78}
                padding: "20dp"
                spacing: "10dp"

                TitleLabel:
                    text: "Քվեարկություն"
                    halign: "center"
                    text_size: self.size

                SubLabel:
                    text: "Ո՞վ է իմպոստոր-ը"
                    halign: "center"
                    text_size: self.size

                Spinner:
                    id: sp_vote
                    text: "Ընտրել խաղացող"
                    font_name: app.font_armenian if app.font_armenian else "Roboto"
                    values: [f"Խաղացող {i}" for i in range(1, app.cfg.players+1)]
                    size_hint_y: None
                    height: "56dp"

                Widget:
                    size_hint_y: 1

                RedButton:
                    text: "Ստուգել"
                    on_release: app.check_vote()

                GhostButton:
                    text: "Վերադառնալ ռաունդ"
                    on_release: app.sm.current = "round"

<ResultScreen>:
    name: "result"
    BGImage:
        bg_source: app.menu_blur_image
        FloatLayout:
            BoxLayout:
                orientation: "vertical"
                size_hint: (0.9, 0.85)
                pos_hint: {"center_x": 0.5, "center_y": 0.78}
                padding: "20dp"
                spacing: "14dp"

                TitleLabel:
                    id: res_title
                    text: ""
                    font_name: app.font_armenian if app.font_armenian else "Roboto"
                    font_size: "32sp"
                    halign: "center"
                    text_size: self.size
                    size_hint_y: None
                    height: self.texture_size[1] + dp(16)

                SubLabel:
                    id: res_details
                    text: ""
                    font_name: app.font_armenian if app.font_armenian else "Roboto"
                    font_size: "20sp"
                    halign: "center"
                    text_size: self.size
                    size_hint_y: None
                    height: self.texture_size[1] + dp(12)

                Widget:
                    size_hint_y: None
                    height: "24dp"

                RedButton:
                    text: "Նոր խաղ"
                    on_release: app.new_game()

                GhostButton:
                    text: "Գլխավոր մենյու"
                    on_release: app.sm.current = "menu"
"""

class MenuScreen(Screen): pass
class CategoryScreen(Screen): pass
class SetupScreen(Screen): pass
class RevealScreen(Screen): pass
class RoundScreen(Screen): pass
class VoteScreen(Screen): pass
class ResultScreen(Screen): pass

class ArmImposterApp(App):
    menu_image = StringProperty("")
    menu_blur_image = StringProperty("")
    logo_image = StringProperty("")
    font_armenian = StringProperty("")

    cfg = GameConfig()
    state = GameState(word="", impostor_ids=[], reveal_index=1)

    _secret_visible = BooleanProperty(False)
    _timer_ev = None
    _remaining = NumericProperty(0)
    timer_display = StringProperty("00:00")

    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        self.font_armenian = FONT_ARMENIAN or ""
        # Mobile-first size (portrait phone)
        from kivy.metrics import dp
        Window.size = (dp(360), dp(640))
        self._load_assets()
        Builder.load_string(KV)

        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(MenuScreen())
        self.sm.add_widget(CategoryScreen())
        self.sm.add_widget(SetupScreen())
        self.sm.add_widget(RevealScreen())
        self.sm.add_widget(RoundScreen())
        self.sm.add_widget(VoteScreen())
        self.sm.add_widget(ResultScreen())
        # Spinner dropdown options must use Armenian font (set in Python so it applies on open)
        self.sm.get_screen("vote").ids.sp_vote.option_cls = ArmenianSpinnerOption
        return self.sm

    def _load_assets(self):
        root = os.path.dirname(__file__)
        assets = os.path.join(root, "assets")
        data = os.path.join(root, "data")
        os.makedirs(assets, exist_ok=True)

        menu_path = os.path.join(assets, "menu.JPG")
        logo_path = os.path.join(assets, "logo.JPG")
        blur_path = os.path.join(assets, "menu_blur.JPG")
        self.menu_image = menu_path if os.path.exists(menu_path) else ""
        self.logo_image = logo_path if os.path.exists(logo_path) else ""
        # Use blur if already exists; else show menu first, generate blur in background
        if os.path.exists(blur_path):
            self.menu_blur_image = blur_path
        else:
            self.menu_blur_image = menu_path if os.path.exists(menu_path) else ""
            app_ref = self

            def _blur_done(dt):
                try:
                    from kivy.app import App
                    if App.get_running_app() is app_ref and os.path.exists(blur_path):
                        app_ref.menu_blur_image = blur_path
                except Exception:
                    pass

            def _run_blur():
                if _do_blur(menu_path, blur_path):
                    Clock.schedule_once(_blur_done, 0)
            threading.Thread(target=_run_blur, daemon=True).start()

        words_path = os.path.join(data, "words_hy.json")
        self.words: Dict[str, List[str]] = {}
        try:
            if os.path.exists(words_path):
                with open(words_path, "r", encoding="utf-8") as f:
                    self.words = json.load(f)
            if not self.words:
                self.words = {"Բոլորը": ["բառ"]}
        except Exception:
            self.words = {"Բոլորը": ["բառ"]}

    # Navigation
    def go_setup(self):
        def _switch(dt):
            self.cfg.category = self.cfg.category or "Բոլորը"
            sm = getattr(self, "sm", None) or self.root
            if sm and hasattr(sm, "current"):
                sm.current = "setup"
        Clock.schedule_once(_switch, 0)

    def go_categories(self):
        def _switch(dt):
            sm = getattr(self, "sm", None) or self.root
            if sm and hasattr(sm, "current"):
                sm.current = "categories"
        Clock.schedule_once(_switch, 0)

    def select_category(self, category: str):
        self.cfg.category = category
        self.start_game()

    def set_players(self, n: int):
        self.cfg.players = max(3, min(15, n))
        self.cfg.impostors = min(self.cfg.impostors, max(1, self.cfg.players // 2))
        sm = getattr(self, "sm", None)
        if sm:
            try:
                scr = sm.get_screen("setup")
                scr.ids.sp_impostors.text = str(self.cfg.impostors)
            except Exception:
                pass

    def set_impostors(self, n: int):
        self.cfg.impostors = max(1, min(n, max(1, self.cfg.players // 2)))
        sm = getattr(self, "sm", None)
        if sm:
            try:
                scr = sm.get_screen("setup")
                scr.ids.sp_impostors.text = str(self.cfg.impostors)
            except Exception:
                pass

    def set_timer(self, sec: int):
        self.cfg.round_seconds = max(60, int(sec))

    def set_timer_minutes(self, minutes: int):
        self.cfg.round_minutes = max(1, min(10, int(minutes)))
        if self.cfg.round_minutes not in (1, 2, 3, 4, 5, 7, 10):
            self.cfg.round_minutes = 2
        self.cfg.round_seconds = self.cfg.round_minutes * 60
        sm = getattr(self, "sm", None)
        if sm:
            try:
                scr = sm.get_screen("setup")
                scr.ids.sp_timer.text = str(self.cfg.round_minutes)
            except Exception:
                pass

    def reset_to_setup(self):
        self._stop_timer()
        sm = getattr(self, "sm", None)
        if sm:
            sm.current = "setup"

    # Game
    def start_game(self):
        self.cfg.category = self.cfg.category or "Բոլորը"
        self.cfg.players = max(3, min(15, self.cfg.players))
        self.cfg.impostors = max(1, min(self.cfg.impostors, self.cfg.players // 2))
        self.cfg.round_minutes = max(1, min(10, self.cfg.round_minutes))
        self.cfg.round_seconds = self.cfg.round_minutes * 60
        pool = self.words.get(self.cfg.category) or []
        if not pool or not isinstance(pool, list):
            self._toast("Բառերի ցուցակը դատարկ է")
            return
        self.state.word = _word_without_adjective(random.choice(pool))

        # pick impostor ids (1-based)
        ids = list(range(1, self.cfg.players + 1))
        random.shuffle(ids)
        self.state.impostor_ids = sorted(ids[: self.cfg.impostors])

        self.state.reveal_index = 1
        self._secret_visible = False
        self._update_reveal_content()
        sm = getattr(self, "sm", None)
        if sm:
            sm.current = "reveal"

    def toggle_secret(self):
        scr: RevealScreen = self.sm.get_screen("reveal")
        was_visible = self._secret_visible
        self._secret_visible = not self._secret_visible
        self._update_reveal_content()

        # If user just hid it (was visible -> now hidden), go next player
        if was_visible and not self._secret_visible:
            self._next_reveal()

    def _update_reveal_content(self):
        sm = getattr(self, "sm", None)
        if not sm:
            return
        scr = sm.get_screen("reveal")
        player = self.state.reveal_index
        impostors = self.state.impostor_ids or []
        is_impostor = player in impostors

        scr.ids.reveal_title.text = f"Խաղացող {_to_arm(player)}"

        if self._secret_visible:
            scr.ids.secret_label.text = "ԻՄՊՈՍՏՈՐ" if is_impostor else self.state.word
            scr.ids.btn_toggle.text = "Թաքցնել հաջորդը"
        else:
            scr.ids.secret_label.text = "••••••"
            scr.ids.btn_toggle.text = "Ցույց տալ"

    def _next_reveal(self):
        if self.state.reveal_index < self.cfg.players:
            self.state.reveal_index += 1
            self._secret_visible = False
            self._update_reveal_content()
        else:
            # all revealed -> start round
            self.start_round()

    def start_round(self):
        self.cfg.round_seconds = max(60, self.cfg.round_minutes * 60)
        self._remaining = int(self.cfg.round_seconds)
        self._stop_timer()
        self._update_timer_display()
        self._timer_ev = Clock.schedule_interval(self._tick, 1.0)
        sm = getattr(self, "sm", None)
        if sm:
            sm.current = "round"

    def _tick(self, dt):
        self._remaining -= 1
        if self._remaining <= 0:
            self._remaining = 0
            self._update_timer_display()
            self._stop_timer()
            self.finish_round(time_ran_out=True)
            return False
        self._update_timer_display()
        return True

    def _update_timer_display(self):
        r = max(0, int(self._remaining))
        self.timer_display = f"{r // 60:02d}:{r % 60:02d}"

    def _stop_timer(self):
        if self._timer_ev is not None:
            try:
                self._timer_ev.cancel()
            except Exception:
                pass
            self._timer_ev = None

    def go_vote(self):
        self._stop_timer()
        sm = getattr(self, "sm", None)
        if not sm:
            return
        vote_scr = sm.get_screen("vote")
        vote_scr.ids.sp_vote.values = [f"Խաղացող {_to_arm(i)}" for i in range(1, self.cfg.players + 1)]
        if vote_scr.ids.sp_vote.values:
            vote_scr.ids.sp_vote.text = vote_scr.ids.sp_vote.values[0]
        sm.current = "vote"

    def finish_round(self, time_ran_out: bool = False):
        self._stop_timer()
        if time_ran_out:
            self._show_result(team_won=False)
            return
        sm = getattr(self, "sm", None)
        if sm:
            sm.current = "vote"

    def check_vote(self, selection: Optional[str] = None):
        sm = getattr(self, "sm", None)
        if sm:
            try:
                vote_scr = sm.get_screen("vote")
                selection = vote_scr.ids.sp_vote.text
            except Exception:
                selection = selection or ""
        else:
            selection = selection or ""
        if not selection or not selection.startswith("Խաղացող"):
            self._toast("Ընտրիր խաղացող")
            return
        part = selection.split()[-1]
        n = _from_arm(part)
        if n < 1 or n > self.cfg.players:
            self._toast("Սխալ ընտրություն")
            return

        caught = n in self.state.impostor_ids
        res_scr: ResultScreen = self.sm.get_screen("result")

        if caught:
            self._show_result(team_won=True)
        else:
            self._remaining += 60
            self._update_timer_display()
            self._timer_ev = Clock.schedule_interval(self._tick, 1.0)
            sm = getattr(self, "sm", None)
            if sm:
                sm.current = "round"

    def _show_result(self, team_won: bool):
        sm = getattr(self, "sm", None)
        if not sm:
            return
        res_scr = sm.get_screen("result")
        if team_won:
            res_scr.ids.res_title.text = "Հաղթանակ"
            res_scr.ids.res_title.color = (0, 0.85, 0.2, 1)
        else:
            res_scr.ids.res_title.text = "Հաղթեց իմպոստորը"
            res_scr.ids.res_title.color = (0.95, 0.2, 0.2, 1)
        impostors_str = ", ".join(_to_arm(i) for i in (self.state.impostor_ids or []))
        res_scr.ids.res_details.text = f"Բառը՝ {self.state.word}\nԻմպոստոր-ներ՝ {impostors_str}"
        res_scr.ids.res_details.color = (1, 1, 1, 1)
        sm.current = "result"

    def new_game(self):
        self._stop_timer()
        self.state = GameState(word="", impostor_ids=[], reveal_index=1)
        sm = getattr(self, "sm", None)
        if sm:
            sm.current = "setup"

    def _toast(self, text: str):
        lbl = Label(text=text, color=(1,1,1,1))
        if FONT_ARMENIAN:
            lbl.font_name = FONT_ARMENIAN
        Popup(title="",
              content=lbl,
              size_hint=(0.8, 0.25),
              auto_dismiss=True).open()

if __name__ == "__main__":
    ArmImposterApp().run()
