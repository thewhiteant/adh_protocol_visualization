"""
SawmeCrypto — Transparent Key Exchange Visualizer + Chat
=========================================================
Run: python app.py
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, font
import threading
import queue
import sys, os, time

sys.path.insert(0, os.path.dirname(__file__))
from protocols.engine import AliceThread, BobThread

# ─── Colour palette ───────────────────────────────────────────────────────────
BG       = "#0a0e1a"
BG2      = "#0f1424"
BG3      = "#141929"
PANEL    = "#161c2e"
BORDER   = "#1e2a45"
ALICE_C  = "#00c8ff"   # cyan  – Alice
BOB_C    = "#ff6b35"   # orange – Bob
BOTH_C   = "#a855f7"   # purple – shared
SUCCESS  = "#22c55e"
WARN     = "#facc15"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
STEP_BG  = "#1a2236"

ALICE_LABEL = "🔵 Alice (Server)"
BOB_LABEL   = "🟠 Bob  (Client)"

STEP_COLORS = {
    'alice': ALICE_C,
    'bob'  : BOB_C,
    'both' : BOTH_C,
}

# ─── Fonts ─────────────────────────────────────────────────────────────────────
def setup_fonts():
    return {
        'title'  : ("Courier New", 18, "bold"),
        'heading': ("Courier New", 11, "bold"),
        'mono'   : ("Courier New", 9),
        'body'   : ("Courier New", 10),
        'small'  : ("Courier New", 8),
        'label'  : ("Courier New", 9, "bold"),
        'chat'   : ("Courier New", 10),
    }


class StepCard(tk.Frame):
    """One animated step card in the timeline."""
    def __init__(self, parent, event, fonts, **kwargs):
        super().__init__(parent, bg=STEP_BG, bd=0, **kwargs)
        color = STEP_COLORS.get(event.actor, MUTED)

        # left accent bar
        bar = tk.Frame(self, bg=color, width=4)
        bar.pack(side=tk.LEFT, fill=tk.Y)

        inner = tk.Frame(self, bg=STEP_BG)
        inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)

        # header row
        hdr = tk.Frame(inner, bg=STEP_BG)
        hdr.pack(fill=tk.X)

        actor_map = {'alice': ALICE_LABEL, 'bob': BOB_LABEL, 'both': '🟣 Both Parties'}
        actor_txt = actor_map.get(event.actor, event.actor.upper())
        tk.Label(hdr, text=actor_txt, font=fonts['label'],
                 fg=color, bg=STEP_BG).pack(side=tk.LEFT)
        tk.Label(hdr, text=f"  Step {event.step}", font=fonts['small'],
                 fg=MUTED, bg=STEP_BG).pack(side=tk.LEFT)

        # title
        tk.Label(inner, text=event.label, font=fonts['heading'],
                 fg=TEXT, bg=STEP_BG, anchor='w').pack(fill=tk.X)

        # detail (multiline, expandable)
        detail_var = tk.StringVar(value=event.detail)
        detail_lbl = tk.Label(inner, textvariable=detail_var,
                              font=fonts['small'], fg=MUTED, bg=STEP_BG,
                              justify=tk.LEFT, anchor='w', wraplength=420)
        detail_lbl.pack(fill=tk.X)

        # data fields
        if event.data:
            data_frame = tk.Frame(inner, bg=STEP_BG)
            data_frame.pack(fill=tk.X, pady=(2,0))
            for k, v in event.data.items():
                row = tk.Frame(data_frame, bg=STEP_BG)
                row.pack(fill=tk.X)
                tk.Label(row, text=f"{k}:", font=fonts['small'],
                         fg=color, bg=STEP_BG, width=12, anchor='w').pack(side=tk.LEFT)
                val_str = str(v)
                if len(val_str) > 50:
                    val_str = val_str[:50] + "…"
                tk.Label(row, text=val_str, font=fonts['mono'],
                         fg=TEXT, bg=STEP_BG, anchor='w').pack(side=tk.LEFT)

        # separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, side=tk.BOTTOM)


class ChatBubble(tk.Frame):
    """A single chat message bubble."""
    def __init__(self, parent, sender, msg, fonts, is_alice, **kwargs):
        super().__init__(parent, bg=BG2, **kwargs)
        color  = ALICE_C if is_alice else BOB_C
        align  = tk.LEFT if is_alice else tk.RIGHT
        pad_l  = 0 if is_alice else 60
        pad_r  = 60 if is_alice else 0

        outer = tk.Frame(self, bg=BG2)
        outer.pack(fill=tk.X, padx=(pad_l, pad_r), pady=3)

        bubble = tk.Frame(outer, bg=PANEL, bd=1, relief=tk.FLAT)
        bubble.pack(anchor='w' if is_alice else 'e')

        tk.Label(bubble, text=f"  {sender}  ", font=fonts['label'],
                 fg=color, bg=PANEL).pack(anchor='w', padx=4, pady=(4,0))
        tk.Label(bubble, text=msg, font=fonts['chat'],
                 fg=TEXT, bg=PANEL, wraplength=280, justify=tk.LEFT).pack(
                 anchor='w', padx=8, pady=(0,6))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚗  SawmeCrypto — Transparent Key Exchange")
        self.configure(bg=BG)
        self.geometry("1280x820")
        self.minsize(1100, 700)

        self.fonts = setup_fonts()
        self._eq   = queue.Queue()   # event queue (thread → GUI)
        self._mq   = queue.Queue()   # message queue

        self._alice_send = None
        self._bob_send   = None
        self._shared_key = None
        self._handshake_done = False

        self._build_ui()
        self._start_protocol()
        self.after(50, self._poll)

                # FULLSCREEN ENABLE
        self.fullscreen = True
        self.attributes("-fullscreen", True)

        # TOGGLE CONTROLS
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)


    # ── UI Construction ───────────────────────────────────────────────────────


    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self, event=None):
        self.fullscreen = False
        self.attributes("-fullscreen", False)



    def _build_ui(self):
        # ── Top bar ──────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=BG, height=56)
        topbar.pack(fill=tk.X, side=tk.TOP)
        topbar.pack_propagate(False)

        tk.Label(topbar, text="⚗  AntSaw", font=self.fonts['title'],
                 fg=ALICE_C, bg=BG).pack(side=tk.LEFT, padx=20, pady=8)
        tk.Label(topbar, text="⚗  AntSaw — Transparent Key Exchange",
                 font=self.fonts['body'], fg=MUTED, bg=BG).pack(side=tk.LEFT)



        self.status_lbl = tk.Label(topbar, text="● Initialising…",
                                   font=self.fonts['label'], fg=WARN, bg=BG)
        self.status_lbl.pack(side=tk.RIGHT, padx=20)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Main 3-column layout ─────────────────────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(fill=tk.BOTH, expand=True)

        # Column 1: Alice panel
        self._alice_panel = self._make_node_panel(main, "🔵 ALICE", ALICE_C, side=tk.LEFT)

        # Column 2: Timeline (center)
        center = tk.Frame(main, bg=BG2, width=500)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        center.pack_propagate(False)
        self._build_center(center)

        # Column 3: Bob panel
        self._bob_panel = self._make_node_panel(main, "🟠 BOB", BOB_C, side=tk.RIGHT)

    def _make_node_panel(self, parent, title, color, side):
        frame = tk.Frame(parent, bg=PANEL, width=220)
        frame.pack(side=side, fill=tk.Y)
        frame.pack_propagate(False)

        hdr = tk.Frame(frame, bg=color, height=36)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title, font=self.fonts['heading'],
                 fg=BG, bg=color).pack(pady=6)

        fields_frame = tk.Frame(frame, bg=PANEL)
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        fields = {}
        rows = [
            ('secret', 'Secret'),
            ('generator', 'Generator'),
            ('public_p', 'Public P'),
            ('divisors', 'Divisors (L)'),
            ('beta', 'Beta'),
            ('prime', 'Prime'),
            ('lembda', 'Lembda'),
            ('session_val', 'Session Val'),
            ('shared_key', 'Shared Key ✓'),
            ('sawme_key', 'Sawme Key'),
        ]
        for key, lbl in rows:
            r = tk.Frame(fields_frame, bg=PANEL)
            r.pack(fill=tk.X, pady=1)
            tk.Label(r, text=lbl+":", font=self.fonts['small'],
                     fg=color, bg=PANEL, width=13, anchor='w').pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(r, textvariable=var, font=self.fonts['mono'],
                     fg=TEXT, bg=PANEL, anchor='w').pack(side=tk.LEFT)
            fields[key] = var

        # separator
        tk.Frame(frame, bg=BORDER, height=1).pack(fill=tk.X)

        # chat section for this node
        tk.Label(frame, text="CHAT", font=self.fonts['label'],
                 fg=color, bg=PANEL).pack(pady=(6,2))

        chat_input = tk.Frame(frame, bg=PANEL)
        chat_input.pack(fill=tk.X, padx=6, pady=(0,6))
        entry = tk.Entry(chat_input, bg=BG3, fg=TEXT, insertbackground=TEXT,
                         font=self.fonts['chat'], relief=tk.FLAT, bd=4)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        btn = tk.Button(chat_input, text="▶", bg=color, fg=BG,
                        font=self.fonts['label'], relief=tk.FLAT, padx=4,
                        state=tk.DISABLED)
        btn.pack(side=tk.RIGHT)

        panel_obj = {
            'fields': fields,
            'entry': entry,
            'btn': btn,
            'color': color,
        }

        if title.startswith("🔵"):
            self._alice_ui = panel_obj
        else:
            self._bob_ui   = panel_obj

        return frame

    def _build_center(self, parent):
        # Header
        hdr = tk.Frame(parent, bg=BORDER, height=36)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙  PROTOCOL TIMELINE  (live)",
                 font=self.fonts['heading'], fg=BOTH_C, bg=BORDER).pack(pady=8, padx=8)

        # Tabs: Timeline | Chat | Key Inspector
        self._nb = ttk.Notebook(parent)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=BG2, borderwidth=0)
        style.configure('TNotebook.Tab', background=BG3, foreground=TEXT,
                        font=("Courier New", 9, "bold"), padding=[10,4])
        style.map('TNotebook.Tab', background=[('selected', PANEL)],
                  foreground=[('selected', BOTH_C)])
        self._nb.pack(fill=tk.BOTH, expand=True, pady=4, padx=4)

        # Tab 1: Timeline
        timeline_tab = tk.Frame(self._nb, bg=BG2)
        self._nb.add(timeline_tab, text="  📋 Timeline  ")
        self._build_timeline(timeline_tab)

        # Tab 2: Chat
        chat_tab = tk.Frame(self._nb, bg=BG2)
        self._nb.add(chat_tab, text="  💬 Secure Chat  ")
        self._build_chat_tab(chat_tab)

        # Tab 3: Key Inspector
        key_tab = tk.Frame(self._nb, bg=BG2)
        self._nb.add(key_tab, text="  🔑 Key Inspector  ")
        self._build_key_tab(key_tab)

    def _build_timeline(self, parent):
        canvas = tk.Canvas(parent, bg=BG2, highlightthickness=0)
        scroll = tk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(fill=tk.BOTH, expand=True)

        self._timeline_frame = tk.Frame(canvas, bg=BG2)
        self._timeline_win   = canvas.create_window((0,0), window=self._timeline_frame,
                                                    anchor='nw')

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfig(self._timeline_win, width=canvas.winfo_width())

        self._timeline_frame.bind('<Configure>', on_configure)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(
            self._timeline_win, width=e.width))
        self._timeline_canvas = canvas

        # Mouse-wheel scroll
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            -1*(e.delta//120), "units"))

    def _build_chat_tab(self, parent):
        # Two columns: Alice chat | Bob chat
        tk.Label(parent, text="Messages appear here once handshake completes.",
                 font=self.fonts['small'], fg=MUTED, bg=BG2).pack(pady=4)

        mid = tk.Frame(parent, bg=BG2)
        mid.pack(fill=tk.BOTH, expand=True)

        # Shared chat log
        log_frame = tk.Frame(mid, bg=BG2)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self._chat_canvas = tk.Canvas(log_frame, bg=BG2, highlightthickness=0)
        sc = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self._chat_canvas.yview)
        self._chat_canvas.configure(yscrollcommand=sc.set)
        sc.pack(side=tk.RIGHT, fill=tk.Y)
        self._chat_canvas.pack(fill=tk.BOTH, expand=True)

        self._chat_inner = tk.Frame(self._chat_canvas, bg=BG2)
        self._chat_win   = self._chat_canvas.create_window((0,0), window=self._chat_inner,
                                                           anchor='nw')

        def on_configure(e):
            self._chat_canvas.configure(scrollregion=self._chat_canvas.bbox('all'))
            self._chat_canvas.itemconfig(self._chat_win, width=self._chat_canvas.winfo_width())

        self._chat_inner.bind('<Configure>', on_configure)
        self._chat_canvas.bind('<Configure>', lambda e: self._chat_canvas.itemconfig(
            self._chat_win, width=e.width))

    def _build_key_tab(self, parent):
        tk.Label(parent, text="Full Key Exchange Inspection",
                 font=self.fonts['heading'], fg=BOTH_C, bg=BG2).pack(pady=8)
        self._key_text = scrolledtext.ScrolledText(
            parent, bg=BG3, fg=TEXT, font=self.fonts['mono'],
            relief=tk.FLAT, bd=8, state=tk.DISABLED, wrap=tk.WORD)
        self._key_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Tag colours
        self._key_text.tag_config('alice', foreground=ALICE_C)
        self._key_text.tag_config('bob',   foreground=BOB_C)
        self._key_text.tag_config('both',  foreground=BOTH_C)
        self._key_text.tag_config('key',   foreground=SUCCESS)
        self._key_text.tag_config('label', foreground=WARN)

    # ── Protocol startup ──────────────────────────────────────────────────────

    def _start_protocol(self):
        def on_event(ev):
            self._eq.put(('event', ev))

        def on_msg(sender, text):
            self._mq.put((sender, text))

        def on_ready(role, send_fn, sk, sawme_key):
            self._eq.put(('ready', role, send_fn, sk, sawme_key))

        self._alice_t = AliceThread(on_event, on_msg, on_ready)
        self._bob_t   = BobThread(on_event, on_msg, on_ready)
        self._alice_t.start()
        self._bob_t.start()

    # ── Poll queue (main thread) ──────────────────────────────────────────────

    def _poll(self):
        # Process events
        while not self._eq.empty():
            item = self._eq.get_nowait()
            if item[0] == 'event':
                self._handle_event(item[1])
            elif item[0] == 'ready':
                _, role, send_fn, sk, sawme_key = item
                self._handle_ready(role, send_fn, sk, sawme_key)

        # Process messages
        while not self._mq.empty():
            sender, text = self._mq.get_nowait()
            self._add_chat_message(sender, text)

        self.after(50, self._poll)

    def _handle_event(self, ev):
        # Add step card to timeline
        card = StepCard(self._timeline_frame, ev, self.fonts)
        card.pack(fill=tk.X, padx=4, pady=2)
        self._timeline_canvas.after(10, lambda: self._timeline_canvas.yview_moveto(1.0))

        # Update key inspector
        self._key_text.configure(state=tk.NORMAL)
        tag = ev.actor
        self._key_text.insert(tk.END, f"\n{'─'*60}\n", 'label')
        self._key_text.insert(tk.END, f"[Step {ev.step}] {ev.label}\n", tag)
        self._key_text.insert(tk.END, f"{ev.detail}\n", 'label')
        for k, v in ev.data.items():
            self._key_text.insert(tk.END, f"  {k:15} = {v}\n", tag)
        self._key_text.configure(state=tk.DISABLED)
        self._key_text.see(tk.END)

        # Update side panels
        self._update_side_panels(ev)

        # Update status
        if ev.step == 9:
            self.status_lbl.config(text="● Handshake Complete — Chat Active",
                                   fg=SUCCESS)
        elif ev.step >= 3:
            self.status_lbl.config(text=f"● Step {ev.step}: {ev.label}", fg=WARN)

    def _update_side_panels(self, ev):
        d = ev.data
        if ev.actor == 'alice' or ev.actor == 'both':
            f = self._alice_ui['fields']
            if 'b' in d:       f['secret'].set(str(d['b'])[:12])
            if 'genB' in d:    f['generator'].set(str(d['genB'])[:12])
            if 'PB' in d:      f['public_p'].set(str(d['PB'])[:12])
            if 'Lb' in d:      f['divisors'].set(str(d['Lb']))
            if 'Beta' in d:    f['beta'].set(str(d['Beta'])[:12])
            if 'prime' in d:   f['prime'].set(str(d['prime'])[:12])
            if 'Lembda' in d:  f['lembda'].set(str(d['Lembda']))
            if 'B_val' in d:   f['session_val'].set(str(d['B_val'])[:12])
            if 'shared_key' in d:
                f['shared_key'].set(str(d['shared_key'])[:14])
            if 'sawme_key' in d:
                f['sawme_key'].set(str(d['sawme_key']))

        if ev.actor == 'bob' or ev.actor == 'both':
            f = self._bob_ui['fields']
            if 'a' in d:       f['secret'].set(str(d['a'])[:12])
            if 'genA' in d:    f['generator'].set(str(d['genA'])[:12])
            if 'PA' in d:      f['public_p'].set(str(d['PA'])[:12])
            if 'La' in d:      f['divisors'].set(str(d['La']))
            if 'Beta' in d:    f['beta'].set(str(d['Beta'])[:12])
            if 'prime' in d:   f['prime'].set(str(d['prime'])[:12])
            if 'Lembda' in d:  f['lembda'].set(str(d['Lembda']))
            if 'A_val' in d:   f['session_val'].set(str(d['A_val'])[:12])
            if 'shared_key' in d:
                f['shared_key'].set(str(d['shared_key'])[:14])
            if 'sawme_key' in d:
                f['sawme_key'].set(str(d['sawme_key']))

    def _handle_ready(self, role, send_fn, sk, sawme_key):
        if role == 'alice':
            self._alice_send = send_fn
            self._alice_ui['btn'].configure(
                state=tk.NORMAL,
                command=self._make_send_cmd('alice'))
            self._alice_ui['entry'].bind('<Return>', lambda e: self._send('alice'))
        else:
            self._bob_send = send_fn
            self._bob_ui['btn'].configure(
                state=tk.NORMAL,
                command=self._make_send_cmd('bob'))
            self._bob_ui['entry'].bind('<Return>', lambda e: self._send('bob'))

        if self._alice_send and self._bob_send:
            self._handshake_done = True
            self._nb.select(1)  # switch to chat tab

    def _make_send_cmd(self, role):
        return lambda: self._send(role)

    def _send(self, role):
        if role == 'alice':
            ui   = self._alice_ui
            fn   = self._alice_send
            name = 'Alice'
        else:
            ui   = self._bob_ui
            fn   = self._bob_send
            name = 'Bob'

        msg = ui['entry'].get().strip()
        if not msg or fn is None: return
        ui['entry'].delete(0, tk.END)
        fn(msg)
        self._add_chat_message(name, msg, sent_by_me=True,
                               is_alice=(role == 'alice'))

    def _add_chat_message(self, sender, text, sent_by_me=False, is_alice=None):
        if is_alice is None:
            is_alice = (sender in ('Alice', 'alice'))
        bubble = ChatBubble(self._chat_inner, sender, text, self.fonts,
                            is_alice=is_alice)
        bubble.pack(fill=tk.X)
        self._chat_canvas.after(10, lambda: self._chat_canvas.yview_moveto(1.0))


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
