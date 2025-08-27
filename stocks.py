#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import random
import yfinance as yf

# ---------------------------------- constants --------------------------------

STARTING_CASH = 25000.0
TARGET_NET_WORTH = 5000000.0
ANNUAL_BANK_RATE = 0.05
LOAN_INTEREST     = 0.05
MAX_LOAN          = 100000.0

STOCKS = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOG": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.", "TSLA": "Tesla Inc.", "JPM":  "JP Morgan Chase & Co.",
    "XOM":  "Exxon Mobil Corp.", "NVDA": "NVIDIA Corp.", "V":    "Visa Inc.",
    "NFLX": "Netflix Inc.", "DIS":  "The Walt Disney Company", "BAC":  "Bank of America Corp.",
    "INTC": "Intel Corp.", "KO":   "Coca‑Cola Co.", "PEP":  "PepsiCo Inc.", "SBUX": "Starbucks Corp.",
    "MCD":  "McDonald’s Corp.", "BA":   "Boeing Co.", "CSCO": "Cisco Systems Inc.", "ADBE": "Adobe Inc.",
    "PYPL": "PayPal Holdings Inc.", "CRM":  "Salesforce Inc.", "ORCL": "Oracle Corp.",
    "T":    "AT&T Inc.", "GE":   "General Electric Co.", "HON":  "Honeywell International",
    "WMT":  "Walmart Inc.", "CVX":  "Chevron Corp.", "F":    "Ford Motor Co.", "GM":   "General Motors Co.",
}

STOCK_GRAPHICS = {
    "AAPL": "🍏", "MSFT": "🪟", "GOOG": "🔍", "AMZN": "🛒", "TSLA": "🚗",
    "JPM":  "🏦", "XOM":  "🛢️", "NVDA": "💻", "V":    "💳", "NFLX": "📺",
    "DIS":  "🏰", "BAC":  "🏦", "INTC": "🔌", "KO":   "🥤", "PEP":  "🥤",
    "SBUX": "☕",  "MCD":  "🍔", "BA":   "✈️",  "CSCO": "📡", "ADBE": "🖌️",
    "PYPL": "💸",  "CRM":  "☁️", "ORCL": "🗃️", "T":    "📞", "GE":   "⚙️",
    "HON":  "🏭",  "WMT":  "🏬", "CVX":  "⛽",  "F":    "🚙", "GM":   "🚙",
}

# -------------------------------- events (always positive) -----------------------

COOL_EVENTS = [
    {"name": "AI Breakthrough!", "desc": "AI beats all benchmarks, tech stocks skyrocket!",
     "targets": ["AAPL", "MSFT", "GOOG", "NVDA", "ADBE", "CRM", "ORCL"], "factor_range": (1.1, 2.0)},
    {"name": "Technology Surge", "desc": "Broad tech rally boosts all tech names.",
     "targets": list(STOCKS.keys()), "factor_range": (1.05, 1.15)},
    {"name": "Bullish Momentum", "desc": "Strong market momentum pushes all values up.",
     "targets": list(STOCKS.keys()), "factor_range": (1.02, 1.07)},
]

FRIENDS_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Avery", "Riley", "Sam"]

# -------------------------------- models -----------------------------------------

class Portfolio:
    def __init__(self, cash=STARTING_CASH):
        self.cash = cash
        self.holdings = {sym: 0 for sym in STOCKS}
        self.total_paid   = {sym: 0.0 for sym in STOCKS}
        self.total_bought = {sym: 0 for sym in STOCKS}

    def buy(self, sym, shares, price):
        if shares <= 0 or shares * price > self.cash:
            return False, "Invalid share count or insufficient cash."
        self.cash -= shares * price
        self.holdings[sym] += shares
        self.total_paid[sym]   += shares * price
        self.total_bought[sym] += shares
        return True, f"Bought {shares} shares of {sym} at ${price:.2f} each (${shares * price:.2f} total)."

    def sell(self, sym, shares, price):
        if shares <= 0 or shares > self.holdings[sym]:
            return False, "Invalid share count."
        proceeds = shares * price
        self.cash += proceeds
        self.holdings[sym] -= shares
        if self.total_bought[sym] > 0:
            frac = shares / self.total_bought[sym]
            self.total_paid[sym] -= self.total_paid[sym] * frac
            self.total_bought[sym] -= shares
            if self.holdings[sym] == 0 or self.total_bought[sym] == 0:
                self.total_paid[sym] = 0
                self.total_bought[sym] = 0
        return True, f"Sold {shares} shares of {sym} at ${price:.2f} each (${proceeds:.2f} total)."

class Bank:
    def __init__(self, annual_rate=ANNUAL_BANK_RATE):
        self.balance = 0.0
        self.annual_rate = annual_rate
        self.loan = 0.0

    def deposit(self, amt, avail_cash):
        if amt <= 0 or amt > avail_cash:
            return False, "Invalid deposit amount."
        self.balance += amt
        return True, f"Deposited ${amt:.2f}."

    def withdraw(self, amt):
        if amt <= 0 or amt > self.balance:
            return False, "Invalid withdraw amount."
        self.balance -= amt
        return True, f"Withdrew ${amt:.2f}."

    def apply_monthly_interest(self):
        self.balance *= 1 + self.annual_rate / 12.0

    def borrow(self, amt):
        if amt <= 0 or self.loan + amt > MAX_LOAN:
            return False, "Invalid or excessive loan."
        self.loan += amt
        return True, f"Borrowed ${amt:.2f}."

    def repay(self, amt, avail_cash):
        if amt <= 0 or amt > avail_cash:
            return False, "Invalid or insufficient cash."
        amt = min(amt, self.loan)
        self.loan -= amt
        return True, f"Repaid ${amt:.2f}. Remaining loan: ${self.loan:.2f}"

    def apply_loan_interest(self):
        if self.loan > 0:
            inter = self.loan * LOAN_INTEREST
            self.loan += inter
            return inter
        return 0.0

# -------------------------------- UI ---------------------------------------------

class StockTreasureGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌟 Stock Treasure Game 🌟")
        self.configure(bg="#16161a")
        self.attributes("-fullscreen", True)

        self.day = 1
        self.portfolio = Portfolio()
        self.bank = Bank()
        self.prices = {sym: 1.0 for sym in STOCKS}
        self.price_history = {sym: [1.0] for sym in STOCKS}
        self.pending_hint = None

        # Build list of symbols once and keep it sorted for readability
        self.stock_options = sorted(STOCKS.keys())

        self.create_widgets()
        self.fetch_prices()
        self.refresh_view()

    # ---------------------------------------------------------------------------

    def create_widgets(self):
        # Info frame
        info = tk.Frame(self, bg="#16151a")
        info.pack(pady=8, fill="x")
        self.lbl_day = tk.Label(info, text="", font=("Segoe UI Semibold", 20),
                                fg="#b8c1ec", bg="#16161a")
        self.lbl_day.grid(row=0, column=0, padx=14)
        self.lbl_cash = tk.Label(info, text="", font=("Segoe UI", 16),
                                 fg="#eebbc3", bg="#16161a")
        self.lbl_cash.grid(row=0, column=1, padx=14)
        self.lbl_bank = tk.Label(info, text="", font=("Segoe UI", 16),
                                 fg="#a6e3e9", bg="#16161a")
        self.lbl_bank.grid(row=0, column=2, padx=14)
        self.lbl_loan = tk.Label(info, text="", font=("Segoe UI", 16),
                                 fg="#e76f51", bg="#16161a")
        self.lbl_loan.grid(row=0, column=3, padx=14)
        self.lbl_networth = tk.Label(info, text="", font=("Segoe UI Semibold", 16),
                                     fg="#b8c1ec", bg="#16161a")
        self.lbl_networth.grid(row=0, column=4, padx=14)

        # Table
        tbl = tk.Frame(self, bg="#16161a")
        tbl.pack(pady=8, fill="both", expand=True)
        cols = ("graphic", "sym", "name", "shares", "avg_paid",
                "total_paid", "price", "value", "gainloss")
        self.tree = ttk.Treeview(tbl, columns=cols, show="headings", height=13)
        for c in cols:
            self.tree.heading(c, text=c.replace("_", " ").title())
            width = 52 if c == "graphic" else 125
            self.tree.column(c, anchor="center", width=width, stretch=False)
        self.tree.pack(fill="x", padx=10)
        self.tree.bind("<Double-1>", self.on_stock_double_click)

        # Chart
        chart = tk.Frame(self, bg="#16161a")
        chart.pack(pady=(8, 2), fill="x")
        tk.Label(chart, text="Stock Chart", font=("Segoe UI Semibold", 15),
                 fg="#eebbc3", bg="#16161a").pack()
        self.stock_var = tk.StringVar(value="AAPL")
        self.stock_menu = ttk.Combobox(chart, textvariable=self.stock_var,
                                      values=self.stock_options, state="readonly",
                                      width=8, height=12)  # increased height for visibility
        self.stock_menu.pack(side="left", padx=10)
        self.stock_menu.bind("<<ComboboxSelected>>", lambda _: self.draw_chart())
        self.chart_canvas = tk.Canvas(chart, width=600, height=160,
                                      bg="#232946", highlightthickness=0)
        self.chart_canvas.pack(side="left", padx=12)
        self.draw_chart()

        # Controls – only bank actions now
        ctrl = tk.Frame(self, bg="#16161a")
        ctrl.pack(pady=10, fill="x")

        # Bank related actions
        tk.Button(ctrl, text="Deposit", font=("Segoe UI Semibold", 13),
                  bg="#a6e3e9", fg="#232946",
                  command=self.bank_deposit, width=10,
                  relief="flat").pack(side="left", padx=9)
        tk.Button(ctrl, text="Withdraw", font=("Segoe UI Semibold", 13),
                  bg="#121629", fg="#eebbc3",
                  command=self.bank_withdraw, width=10,
                  relief="flat").pack(side="left", padx=9)
        tk.Button(ctrl, text="Borrow", font=("Segoe UI Semibold", 13),
                  bg="#f4a261", fg="#232946",
                  command=self.bank_borrow, width=10,
                  relief="flat").pack(side="left", padx=9)
        tk.Button(ctrl, text="Repay Loan", font=("Segoe UI Semibold", 13),
                  bg="#b8c1ec", fg="#232946",
                  command=self.bank_repay, width=11,
                  relief="flat").pack(side="left", padx=9)
        tk.Button(ctrl, text="Advance Day", font=("Segoe UI Semibold", 13),
                  bg="#232946", fg="#eebbc3",
                  command=self.next_day, width=13,
                  relief="flat").pack(side="left", padx=12)
        tk.Button(ctrl, text="❌ Exit", font=("Segoe UI", 13, "bold"),
                  bg="#e76f51", fg="#22223b",
                  command=self.quit,
                  relief="flat", borderwidth=0,
                  highlightthickness=0, width=10).pack(side="left", padx=9)

        # Log
        log = tk.Frame(self, bg="#16161a")
        log.pack(pady=(8, 0), fill="both", expand=False)
        tk.Label(log, text="Game Log", font=("Segoe UI Semibold", 13),
                 fg="#eebbc3", bg="#16161a").pack(anchor="w", padx=10)
        self.log_scroll = tk.Scrollbar(log)
        self.log_scroll.pack(side="right", fill="y")
        self.log = tk.Text(log, height=14, width=120,
                           bg="#232946", fg="#eebbc3",
                           font=("Consolas", 11), relief="flat",
                           wrap="word", yscrollcommand=self.log_scroll.set)
        self.log.pack(fill="x", padx=10)
        self.log_scroll.config(command=self.log.yview)

    # -------------------------------------------------------------------------

    def fetch_prices(self):
        for sym in STOCKS:
            try:
                tkr = yf.Ticker(sym)
                hist = tkr.history(period="5d", interval="1d")
                if not hist.empty:
                    self.prices[sym] = float(hist["Close"][-1])
                    self.add_log(f"Initial price for {sym}: ${self.prices[sym]:.2f}")
            except Exception:
                pass

    # -------------------------------------------------------------------------

    def random_fluctuations(self):
        if random.random() < 0.15:
            event = random.choice(COOL_EVENTS)
            f_min, f_max = event["factor_range"]
            self.add_log(f"💥 {event['name']} – {event['desc']}")
            for sym in event["targets"]:
                factor = random.uniform(f_min, f_max)
                old = self.prices.get(sym, 1.0)
                self.prices[sym] = max(old * factor, old)
                self.add_log(f"    {STOCK_GRAPHICS.get(sym,'')} {sym}: +{(factor-1)*100:.1f}% (${old:.2f}→${self.prices[sym]:.2f})")
                self.price_history[sym].append(self.prices[sym])
        else:
            for sym in self.prices:
                factor = random.uniform(1.0001, 1.03)
                old = self.prices[sym]
                new = max(old * factor, old)
                self.prices[sym] = new
                self.add_log(f"{STOCK_GRAPHICS.get(sym,'')} {sym} daily growth: +{(factor-1)*100:+.1f}% (${old:.2f}→${new:.2f})")
                self.price_history[sym].append(new)

        if self.pending_hint is None and random.random() < 0.18:
            friend  = random.choice(FRIENDS_NAMES)
            hint_sym = random.choice(list(STOCKS.keys()))
            self.pending_hint = (self.day + 2, hint_sym, friend)
            self.add_log(f"💬 Your friend {friend} whispers: \"I heard {STOCK_GRAPHICS.get(hint_sym,'')} {hint_sym} will jump in 2 days!\"")

    def apply_hint(self):
        if self.pending_hint and self.day == self.pending_hint[0]:
            sym, friend = self.pending_hint[1], self.pending_hint[2]
            boost = random.uniform(0.25, 0.45)
            old = self.prices[sym]
            new = max(old * (1 + boost), old)
            self.prices[sym] = new
            self.price_history[sym][-1] = new
            self.add_log(f"🚀 {friend}'s tip comes true! {STOCK_GRAPHICS.get(sym,'')} {sym} jumps +{boost*100:.1f}% (${old:.2f}→${new:.2f})")
            self.pending_hint = None

    # -------------------------------------------------------------------------

    def next_day(self):
        self.day += 1
        self.add_log(f"\n=== Day {self.day} ===")
        self.random_fluctuations()
        self.apply_hint()
        if self.day % 30 == 0:
            self.bank.apply_monthly_interest()
            self.add_log("Bank interest applied.")
            inter = self.bank.apply_loan_interest()
            if inter > 0:
                self.add_log(f"💸 Loan interest applied: ${inter:.2f}")
        self.refresh_view()

    # -------------------------------------------------------------------------

    def refresh_view(self):
        self.lbl_day.config(text=f"Day {self.day}")
        self.lbl_cash.config(text=f"💵 Cash: ${self.portfolio.cash:,.2f}")
        self.lbl_bank.config(text=f"🏦 Bank: ${self.bank.balance:,.2f}")
        self.lbl_loan.config(text=f"💳 Loan: ${self.bank.loan:,.2f}")
        net = self.portfolio.cash + self.bank.balance
        for sym, shares in self.portfolio.holdings.items():
            net += shares * self.prices[sym]
        self.lbl_networth.config(text=f"🌍 Net Worth: ${net:,.2f} / ${TARGET_NET_WORTH:,.2f}")

        for r in self.tree.get_children():
            self.tree.delete(r)
        for sym in STOCKS:
            shares   = self.portfolio.holdings[sym]
            paid     = self.portfolio.total_paid[sym]
            bought   = self.portfolio.total_bought[sym]
            avg_paid = paid / bought if bought else 0.0
            price    = self.prices[sym]
            value    = shares * price
            gain     = value - (avg_paid * shares)
            self.tree.insert("", "end", values=(
                STOCK_GRAPHICS.get(sym,""),
                sym,
                STOCKS[sym],
                shares,
                f"${avg_paid:.2f}",
                f"${paid:.2f}",
                f"${price:.2f}",
                f"${value:.2f}",
                f"${gain:.2f}"
            ))
        self.draw_chart()

    def draw_chart(self):
        sym = self.stock_var.get()
        prices = self.price_history.get(sym, [1.0])
        canvas = self.chart_canvas
        canvas.delete("all")
        if len(prices) < 2:
            return
        mn, mx = min(prices), max(prices)
        spread = mx - mn or 1
        h, w = 120, 570
        pad = 10
        canvas.create_line(pad, h+pad, w+pad, h+pad, fill="#eebc3", width=2)
        canvas.create_line(pad, pad, pad, h+pad, fill="#eebc3", width=2)
        xs, ys = [], []
        for i, p in enumerate(prices[-40:]):
            xs.append(pad + i*(w/min(39,len(prices)-1)))
            ys.append(pad + h - int((p-mn)/spread*h))
        for i in range(1, len(xs)):
            canvas.create_line(xs[i-1], ys[i-1], xs[i], ys[i],
                               fill="#a6e3e9", width=3)
        for x, y in zip(xs, ys):
            canvas.create_oval(x-3, y-3, x+3, y+3, fill="#eebc3", outline="#232946")
        canvas.create_text(w+pad-10, pad+20,
                           text=f"${prices[-1]:.2f}",
                           font=("Segoe UI",13), fill="#eebc3")
        canvas.create_text(pad+20, h+pad+20,
                           text=f"Min: ${mn:.2f}",
                           font=("Segoe UI",11), fill="#b8c1ec")
        canvas.create_text(w+pad-30, h+pad+20,
                           text=f"Max: ${mx:.2f}",
                           font=("Segoe UI",11), fill="#b8c1ec")
        canvas.create_text(w//2, pad+10,
                           text=f"{STOCK_GRAPHICS.get(sym,'')} {sym}",
                           font=("Segoe UI Semibold",16), fill="#b8c1ec")

    def add_log(self, msg):
        self.log.insert("end", msg+"\n")
        self.log.see("end")

    # -------------------------------------------------------------------------

    def on_stock_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return
        values = self.tree.item(item, "values")
        sym = values[1]
        price = self.prices[sym]
        action = simpledialog.askstring("Buy / Sell",
                                        "Enter 'B' to buy, 'S' to sell:",
                                        initialvalue="B", parent=self)
        if not action:
            return
        action = action.upper()
        if action not in ("B", "S"):
            messagebox.showerror("Error", "Invalid choice (must be B or S).", parent=self)
            return
        try:
            shares = int(simpledialog.askstring("Shares", "How many shares?", parent=self))
        except Exception:
            messagebox.showerror("Error", "Invalid number of shares.", parent=self)
            return
        if shares <= 0:
            messagebox.showerror("Error", "Shares must be positive.", parent=self)
            return

        if action == "B":
            ok, msg = self.portfolio.buy(sym, shares, price)
        else:
            ok, msg = self.portfolio.sell(sym, shares, price)

        if ok:
            self.add_log(msg)
        else:
            messagebox.showerror("Error", msg, parent=self)
        self.refresh_view()

    # -------------------------------------------------------------------------

    def bank_deposit(self):
        try:
            amt = float(simpledialog.askstring("Deposit", "Amount?", initialvalue="100", parent=self))
        except Exception:
            messagebox.showerror("Error", "Invalid amount.", parent=self)
            return
        ok, msg = self.bank.deposit(amt, self.portfolio.cash)
        if ok:
            self.portfolio.cash -= amt
            self.add_log(msg)
        else:
            messagebox.showerror("Error", msg, parent=self)
        self.refresh_view()

    def bank_withdraw(self):
        try:
            amt = float(simpledialog.askstring("Withdraw", "Amount?", initialvalue="100", parent=self))
        except Exception:
            messagebox.showerror("Error", "Invalid amount.", parent=self)
            return
        ok, msg = self.bank.withdraw(amt)
        if ok:
            self.portfolio.cash += amt
            self.add_log(msg)
        else:
            messagebox.showerror("Error", msg, parent=self)
        self.refresh_view()

    def bank_borrow(self):
        try:
            amt = float(simpledialog.askstring("Borrow", "Amount to borrow (max $100,000)?",
                                               initialvalue="1000", parent=self))
        except Exception:
            messagebox.showerror("Error", "Invalid amount.", parent=self)
            return
        ok, msg = self.bank.borrow(amt)
        if ok:
            self.portfolio.cash += amt
            self.add_log(msg)
        else:
            messagebox.showerror("Error", msg, parent=self)
        self.refresh_view()

    def bank_repay(self):
        try:
            amt = float(simpledialog.askstring("Repay Loan", "Amount to repay?",
                                               initialvalue="1000", parent=self))
        except Exception:
            messagebox.showerror("Error", "Invalid amount.", parent=self)
            return
        ok, msg = self.bank.repay(amt, self.portfolio.cash)
        if ok:
            self.portfolio.cash -= min(amt, self.bank.loan + amt)
            self.add_log(msg)
        else:
            messagebox.showerror("Error", msg, parent=self)
        self.refresh_view()

# --------------------- run -----------------------------------------------------------

if __name__ == "__main__":
    StockTreasureGame().mainloop()
