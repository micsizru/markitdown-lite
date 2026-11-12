"""Yeniden kullanılabilir modern koyu tema Tkinter arayüz bileşenleri."""

import tkinter as tk
from typing import Any, Callable

from app.config import COLORS, FONTS


class ToolTip:
    """Fare bir bileşenin üzerine geldiğinde koyu temalı bilgi baloncuğu (tooltip) gösterir."""

    def __init__(self, widget: tk.Widget, text: str = "") -> None:
        self.widget = widget
        self.text = text
        self._tip_window: tk.Toplevel | None = None

        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def set_text(self, text: str) -> None:
        self.text = text
        if self._tip_window is not None:
            self._hide()

    def _on_enter(self, _event: tk.Event | None = None) -> None:
        if not self.text:
            return
        try:
            self.widget.config(fg=COLORS["accent_lilac"])
        except Exception:
            pass
        self._show()

    def _on_leave(self, _event: tk.Event | None = None) -> None:
        try:
            self.widget.config(fg=COLORS["text_light"])
        except Exception:
            pass
        self._hide()

    def _show(self) -> None:
        if self._tip_window is not None or not self.text:
            return

        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        try:
            tw.wm_attributes("-topmost", True)
        except Exception:
            pass

        frame = tk.Frame(
            tw,
            bg="#0d0f17",
            padx=14,
            pady=10,
            highlightbackground=COLORS["border_active"],
            highlightthickness=1,
        )
        frame.pack()

        lbl = tk.Label(
            frame,
            text=self.text,
            justify=tk.LEFT,
            bg="#0d0f17",
            fg=COLORS["text_main"],
            font=FONTS["option_desc"],
            wraplength=360,
        )
        lbl.pack()

        tw.update_idletasks()
        tip_w = tw.winfo_reqwidth()
        tip_h = tw.winfo_reqheight()

        screen_w = self.widget.winfo_screenwidth()
        screen_h = self.widget.winfo_screenheight()
        wx = self.widget.winfo_rootx()
        wy = self.widget.winfo_rooty()
        wh = self.widget.winfo_height()
        ww = self.widget.winfo_width()

        # İkonun sağ kenarından sola doğru hizala; ekran dışına taşmasını önle
        x = wx + ww - tip_w
        if x < 12:
            x = wx
        if x + tip_w > screen_w - 12:
            x = max(12, screen_w - tip_w - 12)

        # Alt kısımda yer yoksa baloncuğu ikonun ÜSTÜNDE aç
        if wy + wh + 10 + tip_h > screen_h - 60 and wy - tip_h - 8 > 12:
            y = wy - tip_h - 8
        else:
            y = wy + wh + 8

        tw.wm_geometry(f"+{x}+{y}")
        self._tip_window = tw

    def _hide(self) -> None:
        if self._tip_window is not None:
            try:
                self._tip_window.destroy()
            except Exception:
                pass
            self._tip_window = None


class HoverButton(tk.Button):
    """Fare üzerine geldiğinde (<Enter>/<Leave>) arka plan rengini otomatik değiştiren buton."""

    def __init__(
        self,
        master: tk.Misc,
        normal_bg: str,
        hover_bg: str,
        normal_fg: str = "#f1f5f9",
        disabled_bg: str = COLORS["disabled_bg"],
        disabled_fg: str = COLORS["disabled_fg"],
        border_color: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.normal_bg = normal_bg
        self.hover_bg = hover_bg
        self.normal_fg = normal_fg
        self.disabled_bg = disabled_bg
        self.disabled_fg = disabled_fg

        hl_thickness = kwargs.pop("highlightthickness", 1 if border_color else 0)
        hl_bg = kwargs.pop("highlightbackground", border_color or normal_bg)
        hl_color = kwargs.pop("highlightcolor", border_color or hover_bg)

        super().__init__(
            master,
            bg=normal_bg,
            fg=normal_fg,
            activebackground=hover_bg,
            activeforeground=normal_fg,
            disabledforeground=disabled_fg,
            bd=0,
            highlightthickness=hl_thickness,
            highlightbackground=hl_bg,
            highlightcolor=hl_color,
            **kwargs,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event: tk.Event) -> None:
        if str(self["state"]) == tk.NORMAL:
            self.config(bg=self.hover_bg)

    def _on_leave(self, _event: tk.Event) -> None:
        if str(self["state"]) == tk.NORMAL:
            self.config(bg=self.normal_bg)

    def set_palette(self, normal_bg: str, hover_bg: str, normal_fg: str = "#ffffff") -> None:
        """Butonun aktif renk paletini çalışma zamanında değiştirir."""
        self.normal_bg = normal_bg
        self.hover_bg = hover_bg
        self.normal_fg = normal_fg
        if str(self["state"]) == tk.NORMAL:
            self.config(
                bg=normal_bg,
                fg=normal_fg,
                activebackground=hover_bg,
                activeforeground=normal_fg,
            )

    def set_enabled(self, enabled: bool, text: str | None = None) -> None:
        """Butonu aktif veya pasif duruma geçirir ve renklerini günceller."""
        if text is not None:
            self.config(text=text)
        if enabled:
            self.config(
                state=tk.NORMAL,
                bg=self.normal_bg,
                fg=self.normal_fg,
                cursor="hand2",
            )
        else:
            self.config(
                state=tk.DISABLED,
                bg=self.disabled_bg,
                fg=self.disabled_fg,
                cursor="arrow",
            )


class ToggleOptionRow(tk.Frame):
    """Yuvarlak Canvas pill-switch ve sağ bilgi (i) baloncuğuna sahip modern ayar satırı."""

    def __init__(
        self,
        master: tk.Misc,
        variable: tk.BooleanVar,
        title: str,
        description: str,
        on_change: Callable[[], None] | None = None,
        on_text: str = "✓ On",
        off_text: str = "Off",
        tooltip_text: str = "",
    ) -> None:
        super().__init__(
            master,
            bg=COLORS["card_bg"],
            padx=6,
            pady=8,
            cursor="hand2",
        )
        self.variable = variable
        self.on_change = on_change
        self.on_text = on_text
        self.off_text = off_text

        self.columnconfigure(1, weight=1)

        # Sol: Canvas tabanlı yuvarlak Pill Switch (46x24)
        self.switch_canvas = tk.Canvas(
            self,
            width=46,
            height=24,
            bg=COLORS["card_bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.switch_canvas.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="w")

        # Geriye dönük test uyumluluğu için gizli lbl_badge referansı
        self.lbl_badge = tk.Label(self, text=on_text, bg=COLORS["card_bg"], fg=COLORS["text_main"])

        # Orta: Başlık ve Açıklama
        self.lbl_title = tk.Label(
            self,
            text=title,
            font=FONTS["option_title"],
            fg=COLORS["text_main"],
            bg=COLORS["card_bg"],
            anchor="w",
            cursor="hand2",
        )
        self.lbl_title.grid(row=0, column=1, sticky="ew")

        self.lbl_desc = tk.Label(
            self,
            text=description,
            font=FONTS["option_desc"],
            fg=COLORS["text_muted"],
            bg=COLORS["card_bg"],
            anchor="w",
            justify=tk.LEFT,
            wraplength=420,
            cursor="hand2",
        )
        self.lbl_desc.grid(row=1, column=1, sticky="ew", pady=(2, 0))

        # Sağ: ⓘ bilgi ikonu (üzerine gelince detaylı bilgi baloncuğu açar)
        self.lbl_info_icon = tk.Label(
            self,
            text="ⓘ",
            font=("Segoe UI", 12),
            fg=COLORS["text_light"],
            bg=COLORS["card_bg"],
            padx=8,
            cursor="hand2",
        )
        self.lbl_info_icon.grid(row=0, column=2, rowspan=2, sticky="e")
        self.tooltip = ToolTip(self.lbl_info_icon, tooltip_text or description)

        for widget in (self, self.switch_canvas, self.lbl_title, self.lbl_desc):
            widget.bind("<Button-1>", self._toggle)

        self.bind("<Configure>", self._on_configure)
        self._refresh_visuals()

    def _on_configure(self, event: tk.Event) -> None:
        avail_w = max(240, event.width - 110)
        self.lbl_desc.config(wraplength=avail_w)

    def _draw_pill_switch(self, is_on: bool) -> None:
        c = self.switch_canvas
        c.delete("all")
        track_color = COLORS["switch_on_bg"] if is_on else COLORS["switch_off_bg"]
        knob_color = COLORS["switch_knob"] if is_on else COLORS["switch_knob_off"]

        # Yuvarlatılmış kapsül gövdesi (Sol daire + Orta dikdörtgen + Sağ daire)
        c.create_oval(2, 2, 22, 22, fill=track_color, outline=track_color)
        c.create_rectangle(12, 2, 34, 22, fill=track_color, outline=track_color)
        c.create_oval(24, 2, 44, 22, fill=track_color, outline=track_color)

        # İç daire (Knob)
        if is_on:
            c.create_oval(26, 5, 40, 19, fill=knob_color, outline=knob_color)
        else:
            c.create_oval(6, 5, 20, 19, fill=knob_color, outline=knob_color)

    def update_texts(
        self,
        title: str,
        description: str,
        on_text: str,
        off_text: str,
        tooltip_text: str | None = None,
    ) -> None:
        """Çalışma zamanında başlık, açıklama, rozet ve bilgi baloncuğu metinlerini günceller."""
        self.on_text = on_text
        self.off_text = off_text
        self.lbl_title.config(text=title)
        self.lbl_desc.config(text=description)
        self.tooltip.set_text(tooltip_text if tooltip_text is not None else description)
        self._refresh_visuals()

    def _toggle(self, _event: tk.Event | None = None) -> None:
        self.variable.set(not self.variable.get())
        self._refresh_visuals()
        if self.on_change is not None:
            self.on_change()

    def _refresh_visuals(self) -> None:
        is_on = bool(self.variable.get())
        self._draw_pill_switch(is_on)
        self.lbl_badge.config(text=self.on_text if is_on else self.off_text)


class DashedDropZone(tk.Canvas):
    """Tıklanabilir kesikli çizgi (dashed) çerçeveli dosya seçme alanı."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        on_click: Callable[[], None],
        height: int = 86,
    ) -> None:
        super().__init__(
            master,
            height=height,
            bg=COLORS["drop_bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._prompt_text = text
        self._on_click = on_click
        self._is_hovered = False

        self.bind("<Configure>", self._redraw)
        self.bind("<Button-1>", lambda _e: self._on_click())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def set_text(self, text: str) -> None:
        self._prompt_text = text
        self._redraw()

    def _on_enter(self, _event: tk.Event) -> None:
        self._is_hovered = True
        self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        self._is_hovered = False
        self._redraw()

    def _redraw(self, _event: tk.Event | None = None) -> None:
        self.delete("all")
        w = max(self.winfo_width(), 200)
        h = max(self.winfo_height(), 60)
        border_col = COLORS["accent_lilac"] if self._is_hovered else COLORS["dashed_border"]
        text_col = COLORS["text_main"] if self._is_hovered else COLORS["text_muted"]

        self.create_rectangle(
            4,
            4,
            w - 4,
            h - 4,
            outline=border_col,
            width=1,
            dash=(5, 4),
        )
        self.create_text(
            w // 2,
            h // 2,
            text=self._prompt_text,
            fill=text_col,
            font=FONTS["drop_zone"],
            width=max(160, w - 32),
            justify=tk.CENTER,
        )


class DarkProgressBar(tk.Canvas):
    """Yüzde metni ve yumuşak mor/indigo dolum çubuğu içeren modern ilerleme bileşeni."""

    def __init__(self, master: tk.Misc, height: int = 14) -> None:
        super().__init__(
            master,
            height=height,
            bg=COLORS["progress_track"],
            highlightthickness=0,
            bd=0,
        )
        self._value: float = 0.0
        self.bind("<Configure>", self._redraw)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(100.0, float(value)))
        self._redraw()

    def _redraw(self, _event: tk.Event | None = None) -> None:
        self.delete("all")
        w = max(self.winfo_width(), 100)
        h = max(self.winfo_height(), 10)
        self.create_rectangle(0, 0, w, h, fill=COLORS["progress_track"], outline="")
        if self._value > 0:
            fill_w = int((self._value / 100.0) * w)
            if fill_w > 0:
                self.create_rectangle(
                    0,
                    0,
                    fill_w,
                    h,
                    fill=COLORS["progress_fill"],
                    outline="",
                )
