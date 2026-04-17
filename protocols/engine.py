"""
Protocol Engine — runs Alice (server) and Bob (client) in-process.
All steps emit events via a callback so the GUI can visualize them.
"""
import secrets
import socket
import threading
import queue
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from common import Extra, XORSHIFT, Divisor_utils, Prime_Utils
from common import sawme_cipher

HOST = '127.0.0.1'
PORT = 65433
BUFSIZE = 4096


class ProtocolEvent:
    """Emitted at each step of the handshake."""
    def __init__(self, actor, step, label, detail, data=None):
        self.actor = actor      # 'alice' | 'bob' | 'both'
        self.step = step        # int step number
        self.label = label      # short title
        self.detail = detail    # full text description
        self.data = data or {}  # extra fields for the transparency panel


def _make_event(actor, step, label, detail, **kw):
    return ProtocolEvent(actor, step, label, detail, kw)


# ─────────────────────────── SERVER (Alice) ───────────────────────────

class AliceThread(threading.Thread):
    def __init__(self, event_cb, msg_cb, ready_cb):
        super().__init__(daemon=True)
        self.event_cb = event_cb   # fn(ProtocolEvent)
        self.msg_cb   = msg_cb     # fn(sender, plaintext)
        self.ready_cb = ready_cb   # fn(send_fn)  — called once handshake done
        self.conn = None
        self._shared_key = None
        self._sawme_key  = None

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((HOST, PORT))
            srv.listen(1)
            self.event_cb(_make_event('alice', 0, '🔌 Listening',
                f'Alice bound to {HOST}:{PORT} — waiting for Bob…'))
            conn, addr = srv.accept()
            self.conn = conn
            self.event_cb(_make_event('alice', 1, '🤝 Connection',
                f'Bob connected from {addr}'))

        # ── Step 1 : Time-ping handshake ──────────────────────────────
        data = conn.recv(BUFSIZE)
        prebeta = data.decode()
        if not Extra.timecheck(prebeta):
            self.event_cb(_make_event('alice', 2, '❌ Ping Failed',
                f'Timestamp mismatch. Got: {prebeta}'))
            conn.close(); return
        conn.sendall("CKDUM".encode())
        self.event_cb(_make_event('alice', 2, '✅ Ping OK',
            f'Time-stamp ping verified.',
            prebeta=prebeta))

        # ── Step 2 : Generate Alice's values ─────────────────────────
        bitsize = 4
        Beta = XORSHIFT.Beta(prebeta)
        bitss = secrets.token_bytes(bitsize)
        b = int.from_bytes(bitss, 'big')
        Lb = Divisor_utils.count_divisors(b)
        genB = int.from_bytes(secrets.token_bytes(bitsize), 'big')
        PB   = int.from_bytes(secrets.token_bytes(bitsize), 'big')

        self.event_cb(_make_event('alice', 3, '🎲 Alice Generates',
            f'Alice creates her secret (b), generator (genB), public param (PB), and divisor count (Lb).',
            b=b, genB=genB, PB=PB, Lb=Lb, Beta=Beta))

        # ── Step 3 : Send genB ────────────────────────────────────────
        conn.sendall(str(genB).encode())
        self.event_cb(_make_event('alice', 4, '📤 Alice → Bob: genB',
            f'Alice sends her generator genB = {genB}',
            sent='genB', value=genB))

        # ── Step 4 : Receive Combine1, PA  ───────────────────────────
        raw = conn.recv(BUFSIZE).decode().strip()
        parts = raw.split('|')
        Combine1 = int(parts[0])
        PA_raw   = int(parts[1])
        genA = (Combine1 ^ genB) ^ PA_raw
        PA   = PA_raw
        self.event_cb(_make_event('alice', 5, '📥 Bob → Alice: Combine1 & PA',
            f'Alice receives Combine1={Combine1} and PA={PA}\n'
            f'Decodes: genA = Combine1 ^ genB ^ PA = {genA}',
            Combine1=Combine1, PA=PA, genA=genA))

        # ── Step 5 : Send Combine2 ────────────────────────────────────
        Combine2 = Combine1 ^ PB
        conn.sendall(str(Combine2).encode())
        self.event_cb(_make_event('alice', 6, '📤 Alice → Bob: Combine2',
            f'Alice sends Combine2 = Combine1 ^ PB = {Combine2}',
            sent='Combine2', value=Combine2))

        # ── Step 6 : Exchange La, Lb ──────────────────────────────────
        La = int(conn.recv(BUFSIZE).decode())
        conn.sendall(str(Lb).encode())
        self.event_cb(_make_event('alice', 7, '🔁 Divisor Exchange',
            f'Received La={La} from Bob. Sent Lb={Lb} to Bob.',
            La=La, Lb=Lb))

        # ── Step 7 : Compute shared secret ───────────────────────────
        Lembda = Divisor_utils.FdivisorMixer(La, Lb)
        prime  = Prime_Utils.PrimeFun(PA, PB)
        B_val  = pow(genA * genB * Lembda, b, prime) ^ Beta

        A_val = int(conn.recv(BUFSIZE).decode()) ^ Beta
        conn.sendall(str(B_val).encode())

        sk = pow(A_val, b, prime)
        self._shared_key = sk

        # Sawme cipher key = hex of shared key (truncated to 16 chars)
        self._sawme_key = hex(sk)[2:18] or 'defaultkey123456'

        self.event_cb(_make_event('alice', 8, '🔑 Shared Secret Computed',
            f'Alice computes:\n'
            f'  prime   = {prime}\n'
            f'  Lembda  = {Lembda}\n'
            f'  B_val   = pow(genA×genB×Lembda, b, prime) ^ Beta = {B_val}\n'
            f'  A_val   = {A_val}\n'
            f'  SK      = pow(A_val, b, prime) = {sk}',
            prime=prime, Lembda=Lembda, B_val=B_val, A_val=A_val,
            shared_key=sk, sawme_key=self._sawme_key))

        self.event_cb(_make_event('both', 9, '🎉 Handshake Complete',
            f'Both parties now share the same secret key.\n'
            f'Shared Key = {sk}\n'
            f'Sawme Cipher Key = {self._sawme_key}',
            shared_key=sk))

        # Ready — expose send function to GUI
        def send_fn(msg):
            try:
                ct, ts, _ = sawme_cipher.encrypt(msg, self._sawme_key)
                payload = f"ENC:{ct}".encode()
                conn.sendall(payload)
                self.event_cb(_make_event('alice', 99, '📨 Alice Sent',
                    f'Plaintext: {msg}\nEncrypted (Sawme): {ct}',
                    plaintext=msg, ciphertext=ct))
            except Exception as e:
                pass

        self.ready_cb('alice', send_fn, sk, self._sawme_key)

        # ── Receive loop ─────────────────────────────────────────────
        while True:
            try:
                data = conn.recv(BUFSIZE)
                if not data: break
                text = data.decode()
                if text.startswith("ENC:"):
                    ct = text[4:]
                    try:
                        plain = sawme_cipher.decrypt(ct, self._sawme_key)
                    except:
                        plain = f"<decrypt error: {ct}>"
                    self.event_cb(_make_event('bob', 98, '📨 Bob → Alice',
                        f'Ciphertext: {ct}\nDecrypted: {plain}',
                        ciphertext=ct, plaintext=plain))
                    self.msg_cb('Bob', plain)
                else:
                    self.msg_cb('Bob', text)
            except:
                break


# ─────────────────────────── CLIENT (Bob) ─────────────────────────────

class BobThread(threading.Thread):
    def __init__(self, event_cb, msg_cb, ready_cb):
        super().__init__(daemon=True)
        self.event_cb = event_cb
        self.msg_cb   = msg_cb
        self.ready_cb = ready_cb
        self._shared_key = None
        self._sawme_key  = None

    def run(self):
        import time
        time.sleep(0.3)   # let Alice bind first

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        self.event_cb(_make_event('bob', 1, '🔌 Bob Connects',
            f'Bob connected to Alice at {HOST}:{PORT}'))

        # ── Step 1 : Time-ping ────────────────────────────────────────
        prebeta = Extra.timenow()
        s.sendall(prebeta.encode())
        self.event_cb(_make_event('bob', 2, '📤 Bob → Alice: Ping',
            f'Bob sends timestamp ping: {prebeta}',
            prebeta=prebeta))

        response = s.recv(BUFSIZE).decode()
        if response != "CKDUM":
            self.event_cb(_make_event('bob', 2, '❌ Ping Failed',
                f'Expected CKDUM, got: {response}')); s.close(); return
        self.event_cb(_make_event('bob', 2, '✅ Ping Confirmed',
            f'Alice confirmed ping with CKDUM'))

        # ── Step 2 : Generate Bob's values ───────────────────────────
        bitsize = 4
        Beta = XORSHIFT.Beta(prebeta)
        bitss = secrets.token_bytes(bitsize)
        a     = int.from_bytes(bitss, 'big')
        La    = Divisor_utils.count_divisors(a)
        genA  = int.from_bytes(secrets.token_bytes(bitsize), 'big')
        PA    = int.from_bytes(secrets.token_bytes(bitsize), 'big')

        self.event_cb(_make_event('bob', 3, '🎲 Bob Generates',
            f'Bob creates his secret (a), generator (genA), public param (PA), and divisor count (La).',
            a=a, genA=genA, PA=PA, La=La, Beta=Beta))

        # ── Step 3 : Receive genB ─────────────────────────────────────
        genB = int(s.recv(BUFSIZE).decode())
        self.event_cb(_make_event('bob', 4, '📥 Alice → Bob: genB',
            f'Bob receives Alice\'s generator genB = {genB}',
            genB=genB))

        # ── Step 4 : Send Combine1 & PA ──────────────────────────────
        Combine1 = genA ^ genB ^ PA
        s.sendall(f"{Combine1}|{PA}".encode())
        self.event_cb(_make_event('bob', 5, '📤 Bob → Alice: Combine1 & PA',
            f'Bob sends Combine1 = genA^genB^PA = {Combine1}\nand PA = {PA}',
            Combine1=Combine1, PA=PA))

        # ── Step 5 : Receive Combine2 ────────────────────────────────
        Combine2 = int(s.recv(BUFSIZE).decode())
        PB = Combine2 ^ PA ^ genA
        self.event_cb(_make_event('bob', 6, '📥 Alice → Bob: Combine2',
            f'Bob receives Combine2={Combine2}\nDecodes: PB = Combine2^PA^genA = {PB}',
            Combine2=Combine2, PB=PB))

        # ── Step 6 : Exchange La, Lb ─────────────────────────────────
        s.sendall(str(La).encode())
        Lb = int(s.recv(BUFSIZE).decode())
        self.event_cb(_make_event('bob', 7, '🔁 Divisor Exchange',
            f'Bob sent La={La}. Received Lb={Lb} from Alice.',
            La=La, Lb=Lb))

        # ── Step 7 : Compute shared secret ───────────────────────────
        Lembda = Divisor_utils.FdivisorMixer(La, Lb)
        prime  = Prime_Utils.PrimeFun(PA, PB)
        A_val  = pow(genA * genB * Lembda, a, prime) ^ Beta
        s.sendall(str(A_val).encode())

        B_val  = int(s.recv(BUFSIZE).decode()) ^ Beta
        sk     = pow(B_val, a, prime)
        self._shared_key = sk
        self._sawme_key  = hex(sk)[2:18] or 'defaultkey123456'

        self.event_cb(_make_event('bob', 8, '🔑 Shared Secret Computed',
            f'Bob computes:\n'
            f'  prime   = {prime}\n'
            f'  Lembda  = {Lembda}\n'
            f'  A_val   = pow(genA×genB×Lembda, a, prime) ^ Beta = {A_val}\n'
            f'  B_val   = {B_val}\n'
            f'  SK      = pow(B_val, a, prime) = {sk}',
            prime=prime, Lembda=Lembda, A_val=A_val, B_val=B_val,
            shared_key=sk, sawme_key=self._sawme_key))

        def send_fn(msg):
            try:
                ct, ts, _ = sawme_cipher.encrypt(msg, self._sawme_key)
                payload = f"ENC:{ct}".encode()
                s.sendall(payload)
                self.event_cb(_make_event('bob', 99, '📨 Bob Sent',
                    f'Plaintext: {msg}\nEncrypted (Sawme): {ct}',
                    plaintext=msg, ciphertext=ct))
            except Exception as e:
                pass

        self.ready_cb('bob', send_fn, sk, self._sawme_key)

        # ── Receive loop ─────────────────────────────────────────────
        while True:
            try:
                data = s.recv(BUFSIZE)
                if not data: break
                text = data.decode()
                if text.startswith("ENC:"):
                    ct = text[4:]
                    try:
                        plain = sawme_cipher.decrypt(ct, self._sawme_key)
                    except:
                        plain = f"<decrypt error>"
                    self.event_cb(_make_event('alice', 98, '📨 Alice → Bob',
                        f'Ciphertext: {ct}\nDecrypted: {plain}',
                        ciphertext=ct, plaintext=plain))
                    self.msg_cb('Alice', plain)
                else:
                    self.msg_cb('Alice', text)
            except:
                break
